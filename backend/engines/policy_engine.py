from typing import List


class PolicyEngine:
    def __init__(self) -> None:
        # Define birthright policies: Department -> List of Entitlements
        # Entitlements format: "System:Group"
        self.birthright_policies = {
            "Engineering": [
                "AzureAD:Engineering",
                "GitHub:Engineering",
                "Slack:engineering",
            ],
            "Sales": ["AzureAD:Sales", "Slack:sales", "Salesforce:Users"],
            "Marketing": ["AzureAD:Marketing", "Slack:marketing"],
            "HR": ["AzureAD:HR", "Slack:general", "Workday:Users"],
        }

        # SoD Rules: Conflicting Groups
        self.sod_rules = [
            {
                "conflicting_groups": {"AzureAD:Engineering", "AzureAD:HR"},
                "severity": "high",
            },
            {
                "conflicting_groups": {"AzureAD:Sales", "AzureAD:Finance-Admin"},
                "severity": "critical",
            },
        ]

    def calculate_birthright_access(self, department: str) -> List[str]:
        """Calculate birthright access based on department."""
        # Everyone gets basic access
        base_access = ["AzureAD:All Users", "Slack:general", "Slack:random"]
        dept_access = self.birthright_policies.get(department, [])
        return list(set(base_access + dept_access))

    def check_sod_violations(self, entitlements: List[str]) -> List[str]:
        """Check for Separation of Duties violations.

        Returns a list of violation messages.
        """
        violations = []
        user_entitlements = set(entitlements)

        for rule in self.sod_rules:
            conflict = rule["conflicting_groups"]
            if isinstance(conflict, set) and conflict.issubset(user_entitlements):
                violations.append(
                    f"User has conflicting entitlements: {conflict} "
                    f"(Severity: {rule['severity']})"
                )
        return violations

    def get_revocation_list(
        self, old_department: str, new_department: str
    ) -> List[str]:
        """Calculate revocation list.

        Calculates which entitlements should be removed when moving departments.
        Simple logic: Remove anything in old_dept that is NOT in new_dept.
        """
        old_access = set(self.calculate_birthright_access(old_department))
        new_access = set(self.calculate_birthright_access(new_department))

        # We only revoke things that are strictly departmental.
        # Base access (All Users) is in both, so it won't be revoked.
        to_revoke = list(old_access - new_access)
        return to_revoke


policy_engine = PolicyEngine()
