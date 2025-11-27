import logging
from typing import Any, Dict, List

logger = logging.getLogger("SlackConnector")


class SlackConnector:
    def __init__(self) -> None:
        self.users: Dict[str, Dict[str, Any]] = {}  # email -> user_data
        self.channels: Dict[str, List[str]] = {
            "general": [],
            "random": [],
            "engineering": [],
            "sales": [],
            "marketing": [],
        }

    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        user_id = f"U{len(self.users) + 1000}"
        user = {
            "id": user_id,
            "email": user_data["email"],
            "real_name": f"{user_data['first_name']} {user_data['last_name']}",
            "deleted": False,
        }
        self.users[user_data["email"]] = user
        return user

    def add_to_channel(self, email: str, channel_name: str) -> Dict[str, Any]:
        if channel_name not in self.channels:
            self.channels[channel_name] = []

        if email not in self.channels[channel_name]:
            self.channels[channel_name].append(email)

        return {"status": "success", "channel": channel_name, "member": email}

    def remove_from_channel(self, email: str, channel_name: str) -> Dict[str, Any]:
        if channel_name in self.channels and email in self.channels[channel_name]:
            self.channels[channel_name].remove(email)
        return {"status": "success", "channel": channel_name, "member": email}

    def deactivate_user(self, email: str) -> Dict[str, Any]:
        if email in self.users:
            self.users[email]["deleted"] = True
            return {"status": "success", "email": email}
        return {"status": "error", "message": "User not found"}


slack_connector = SlackConnector()
