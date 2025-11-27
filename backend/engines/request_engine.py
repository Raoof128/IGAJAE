import logging

from backend.stores.request_store import AccessRequest, request_store
from backend.stores.identity_store import identity_store
from backend.stores.audit_log import audit_log_store
from backend.engines.jml_engine import jml_engine
from backend.engines.policy_engine import policy_engine

logger = logging.getLogger("RequestEngine")


class RequestEngine:
    def submit_request(
        self, requester_id: str, entitlement: str, justification: str
    ) -> AccessRequest:
        """Submit a new access request."""
        # Validate Identity
        identity = identity_store.get_identity(requester_id)
        if not identity:
            raise ValueError("Requester identity not found")

        # Validate Entitlement (Simple check: must contain :)
        if ":" not in entitlement:
            raise ValueError("Invalid entitlement format. Expected System:Group")

        # Check for SoD Violations (Pre-check)
        potential_entitlements = identity.entitlements + [entitlement]
        violations = policy_engine.check_sod_violations(potential_entitlements)

        if violations:
            logger.warning(f"SoD Violation detected for request: {violations}")
            # We allow submission but maybe flag it? For now, we proceed but log it.

        request = request_store.create_request(
            {
                "requester_id": requester_id,
                "target_identity_id": requester_id,  # Self-request for now
                "entitlement": entitlement,
                "justification": justification,
                "status": "pending",
            }
        )

        audit_log_store.log_event(
            "submit_request",
            identity.email,
            details={"entitlement": entitlement, "request_id": request.id},
        )
        logger.info(f"Access request submitted: {request.id} for {entitlement}")
        return request

    def approve_request(self, request_id: str, approver_id: str) -> AccessRequest:
        """Approve a request and triggers provisioning."""
        request = request_store.get_request(request_id)
        if not request:
            raise ValueError("Request not found")

        if request.status != "pending":
            raise ValueError(f"Request is in {request.status} state, cannot approve.")

        # Validate Approver
        approver = identity_store.get_identity(approver_id)
        if not approver:
            raise ValueError("Approver identity not found")

        # Prevent Self-Approval
        if request.requester_id == approver_id:
            raise ValueError("Self-approval is not allowed.")

        logger.info(f"Approving request {request_id} by {approver.email}")

        # Provision Access
        try:
            jml_engine.provision_entitlement(
                request.target_identity_id, request.entitlement
            )
            status = "approved"
            comments = "Approved via Access Request Workflow"
        except Exception as e:
            logger.error(f"Provisioning failed for request {request_id}: {e}")
            status = "failed"
            comments = f"Provisioning failed: {e}"
            # In a real system, we might keep it approved but flag provisioning error.
            # Here we fail the request for clarity.

        updated_req = request_store.update_request(
            request_id,
            {
                "status": status,
                "approver_id": approver_id,
                "comments": comments,
            },
        )
        if updated_req is None:
            raise ValueError("Failed to update request")

        audit_log_store.log_event(
            "approve_request",
            request.target_identity_id,
            actor=approver.email,
            details={"request_id": request_id, "status": status},
        )

        return updated_req

    def reject_request(
        self, request_id: str, approver_id: str, reason: str
    ) -> AccessRequest:
        """Reject a request."""
        request = request_store.get_request(request_id)
        if not request:
            raise ValueError("Request not found")

        updated_req = request_store.update_request(
            request_id,
            {"status": "rejected", "approver_id": approver_id, "comments": reason},
        )
        if updated_req is None:
            raise ValueError("Failed to update request")

        approver = identity_store.get_identity(approver_id)
        approver_email = approver.email if approver else "unknown"

        audit_log_store.log_event(
            "reject_request",
            request.target_identity_id,
            actor=approver_email,
            details={"request_id": request_id, "reason": reason},
        )

        return updated_req


request_engine = RequestEngine()
