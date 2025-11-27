import logging
import uuid
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AzureADConnector")


class AzureADConnector:
    def __init__(self) -> None:
        self.users: Dict[str, Dict[str, Any]] = {}  # objectId -> user_data
        self.groups: Dict[str, List[str]] = {
            "Engineering": [],
            "Sales": [],
            "Marketing": [],
            "HR": [],
            "Finance-Admin": [],
        }

    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate creating a user in Azure AD."""
        upn = (
            f"{user_data['first_name'].lower()}."
            f"{user_data['last_name'].lower()}@example.com"
        )
        object_id = str(uuid.uuid4())

        user = {
            "objectId": object_id,
            "userPrincipalName": upn,
            "displayName": f"{user_data['first_name']} {user_data['last_name']}",
            "department": user_data.get("department"),
            "jobTitle": user_data.get("job_title"),
            "accountEnabled": True,
        }
        self.users[object_id] = user
        logger.info(f"[AzureAD] Created user: {upn} ({object_id})")
        return user

    def get_user(self, email: str) -> Optional[Dict[str, Any]]:
        for user in self.users.values():
            if user["userPrincipalName"] == email:
                return user
        return None

    def add_to_group(self, user_id: str, group_name: str) -> Dict[str, Any]:
        if group_name not in self.groups:
            self.groups[group_name] = []

        if user_id not in self.groups[group_name]:
            self.groups[group_name].append(user_id)
            logger.info(f"[AzureAD] Added user {user_id} to group {group_name}")

        return {"status": "success", "group": group_name, "member": user_id}

    def remove_from_group(self, user_id: str, group_name: str) -> Dict[str, Any]:
        if group_name in self.groups and user_id in self.groups[group_name]:
            self.groups[group_name].remove(user_id)
            logger.info(f"[AzureAD] Removed user {user_id} from group {group_name}")
        return {"status": "success", "group": group_name, "member": user_id}

    def disable_account(self, user_id: str) -> Dict[str, Any]:
        if user_id in self.users:
            self.users[user_id]["accountEnabled"] = False
            logger.info(f"[AzureAD] Disabled user {user_id}")
            return {"status": "success", "objectId": user_id}
        return {"status": "error", "message": "User not found"}


# Singleton
azure_ad_connector = AzureADConnector()
