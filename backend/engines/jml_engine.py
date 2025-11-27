import logging
from typing import Any, Dict, List
from backend.stores.identity_store import IdentityProfile, identity_store
from backend.stores.audit_log import audit_log_store
from backend.engines.policy_engine import policy_engine
from connectors.azuread_connector import azure_ad_connector
from connectors.github_connector import github_connector
from connectors.slack_connector import slack_connector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JMLEngine")


class JMLEngine:
    def process_event(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Processing event: {event_type} for {payload.get('email')}")

        try:
            if event_type == "EmployeeCreated":
                return self._handle_joiner(payload)
            elif event_type == "EmployeeUpdated":
                return self._handle_mover(payload)
            elif event_type == "EmployeeTerminated":
                return self._handle_leaver(payload)
            else:
                logger.warning(f"Unknown event type: {event_type}")
                return {"status": "ignored", "message": "Unknown event type"}
        except Exception as e:
            logger.error(f"Error processing event {event_type}: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    def _handle_joiner(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process joiner (new hire) event.

        Joiner Flow:
        1. Create Identity
        2. Calculate Access
        3. Provision Downstream Systems
        """
        logger.info("Starting Joiner Flow...")

        # 1. Create Identity
        try:
            identity = identity_store.create_identity(data)
            audit_log_store.log_event("create_identity", identity.email, details=data)
        except ValueError as e:
            logger.error(f"Identity creation failed: {e}")
            return {"status": "error", "message": str(e)}

        # 2. Calculate Access
        entitlements = policy_engine.calculate_birthright_access(identity.department)
        logger.info(f"Calculated birthright entitlements: {entitlements}")

        # 3. Provision Systems
        accounts = {}

        # Azure AD
        azure_user = azure_ad_connector.create_user(
            {
                "first_name": identity.first_name,
                "last_name": identity.last_name,
                "job_title": identity.job_title,
                "department": identity.department,
            }
        )
        accounts["azure_ad"] = azure_user["userPrincipalName"]
        audit_log_store.log_event(
            "provision_account", identity.email, details={"system": "AzureAD"}
        )

        # Slack (Everyone)
        slack_user = slack_connector.create_user(
            {
                "email": identity.email,
                "first_name": identity.first_name,
                "last_name": identity.last_name,
            }
        )
        accounts["slack"] = slack_user["id"]
        audit_log_store.log_event(
            "provision_account", identity.email, details={"system": "Slack"}
        )

        # GitHub (Engineering only logic handled by policy,
        # but we need to check if we should provision the user first)
        if any(e.startswith("GitHub:") for e in entitlements):
            gh_user = github_connector.create_user(
                {
                    "first_name": identity.first_name,
                    "last_name": identity.last_name,
                    "email": identity.email,
                }
            )
            accounts["github"] = gh_user["username"]
            audit_log_store.log_event(
                "provision_account", identity.email, details={"system": "GitHub"}
            )

        # Assign Entitlements (Groups/Teams)
        self._provision_entitlements(identity, accounts, entitlements)

        # Update Identity
        identity_store.update_identity(
            identity.id, {"accounts": accounts, "entitlements": entitlements}
        )

        logger.info("Joiner Flow Completed Successfully.")
        return {"status": "success", "identity_id": identity.id}

    def _handle_mover(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process mover (transfer) event.

        Mover Flow:
        1. Update Identity
        2. Calculate New Access & Revocation List
        3. Provision New Access
        4. Revoke Old Access
        """
        logger.info("Starting Mover Flow...")
        identity = identity_store.get_identity_by_employee_id(data["employee_id"])
        if not identity:
            return {"status": "error", "message": "Identity not found"}

        old_dept = identity.department
        new_dept = data.get("department", old_dept)

        # 1. Update Identity
        updated_identity = identity_store.update_identity(identity.id, data)
        audit_log_store.log_event("update_identity", identity.email, details=data)

        if old_dept != new_dept:
            logger.info(f"Department change detected: {old_dept} -> {new_dept}")

            # 2. Calculate Access
            new_entitlements = policy_engine.calculate_birthright_access(new_dept)
            to_revoke = policy_engine.get_revocation_list(old_dept, new_dept)

            # 3. Provision New Access
            self._provision_entitlements(
                updated_identity, updated_identity.accounts, new_entitlements
            )

            # 4. Revoke Old Access
            self._revoke_entitlements(
                updated_identity, updated_identity.accounts, to_revoke
            )

            # Update Store
            final_entitlements = list(
                set(updated_identity.entitlements) - set(to_revoke)
                | set(new_entitlements)
            )
            identity_store.update_identity(
                identity.id, {"entitlements": final_entitlements}
            )

        return {"status": "success", "message": "Mover processed"}

    def _handle_leaver(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process leaver (termination) event.

        Leaver Flow:
        1. Disable Accounts
        2. Revoke All Access
        3. Update Identity Status
        """
        logger.info("Starting Leaver Flow...")
        identity = identity_store.get_identity_by_employee_id(data["employee_id"])
        if not identity:
            return {"status": "error", "message": "Identity not found"}

        accounts = identity.accounts

        # 1. Disable Azure AD
        if "azure_ad" in accounts:
            # We need objectId, but we only stored UPN. In a real app we'd store both.
            # For simulation, we assume we can find it or the connector handles UPN.
            # Let's fix the connector usage or store objectId.
            # Hack for simulation: iterate connector users to find ID.
            for uid, u in azure_ad_connector.users.items():
                if u["userPrincipalName"] == accounts["azure_ad"]:
                    azure_ad_connector.disable_account(uid)
                    audit_log_store.log_event(
                        "disable_account", identity.email, details={"system": "AzureAD"}
                    )
                    break

        # 2. Suspend GitHub
        if "github" in accounts:
            github_connector.remove_user(accounts["github"])
            audit_log_store.log_event(
                "disable_account", identity.email, details={"system": "GitHub"}
            )

        # 3. Deactivate Slack
        if "slack" in accounts:
            slack_connector.deactivate_user(identity.email)
            audit_log_store.log_event(
                "disable_account", identity.email, details={"system": "Slack"}
            )

        # 4. Update Status
        identity_store.update_identity(
            identity.id,
            {
                "status": "terminated",
                "lifecycle_state": "leaver",
                "entitlements": [],  # Clear all
            },
        )
        audit_log_store.log_event("terminate_identity", identity.email)

        return {"status": "success", "message": "Leaver processed"}

    def provision_entitlement(self, identity_id: str, entitlement: str) -> None:
        """Process leaver (termination) event.

        Used by Access Request Engine.
        """
        identity = identity_store.get_identity(identity_id)
        if not identity:
            raise ValueError("Identity not found")

        logger.info(
            f"Provisioning ad-hoc entitlement {entitlement} for {identity.email}"
        )
        self._provision_entitlements(identity, identity.accounts, [entitlement])

        # Update Identity Store
        if entitlement not in identity.entitlements:
            new_entitlements = identity.entitlements + [entitlement]
            identity_store.update_identity(
                identity.id, {"entitlements": new_entitlements}
            )

        audit_log_store.log_event(
            "grant_access",
            identity.email,
            details={"entitlement": entitlement, "source": "access_request"},
        )

    def _provision_entitlements(
        self,
        identity: IdentityProfile,
        accounts: Dict[str, str],
        entitlements: List[str],
    ) -> None:
        """Assign groups/teams based on entitlement strings."""
        for ent in entitlements:
            system, group = ent.split(":", 1)

            if system == "AzureAD" and "azure_ad" in accounts:
                # Find ID again (inefficient but works for sim)
                for uid, u in azure_ad_connector.users.items():
                    if u["userPrincipalName"] == accounts["azure_ad"]:
                        azure_ad_connector.add_to_group(uid, group)
                        break

            elif system == "GitHub" and "github" in accounts:
                github_connector.add_to_team(accounts["github"], group)

            elif system == "Slack" and "slack" in accounts:
                slack_connector.add_to_channel(identity.email, group)

    def _revoke_entitlements(
        self,
        identity: IdentityProfile,
        accounts: Dict[str, str],
        entitlements: List[str],
    ) -> None:
        """Remove groups/teams."""
        for ent in entitlements:
            system, group = ent.split(":", 1)

            if system == "AzureAD" and "azure_ad" in accounts:
                for uid, u in azure_ad_connector.users.items():
                    if u["userPrincipalName"] == accounts["azure_ad"]:
                        azure_ad_connector.remove_from_group(uid, group)
                        audit_log_store.log_event(
                            "revoke_access",
                            identity.email,
                            details={"entitlement": f"AzureAD:{group}"},
                        )
                        break

            elif system == "GitHub" and "github" in accounts:
                github_connector.remove_from_team(accounts["github"], group)
                audit_log_store.log_event(
                    "revoke_access",
                    identity.email,
                    details={"entitlement": f"GitHub:{group}"},
                )

            elif system == "Slack" and "slack" in accounts:
                slack_connector.remove_from_channel(identity.email, group)
                audit_log_store.log_event(
                    "revoke_access",
                    identity.email,
                    details={"entitlement": f"Slack:{group}"},
                )


jml_engine = JMLEngine()
