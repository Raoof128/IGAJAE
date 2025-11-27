import logging
from typing import Any, Dict, List

logger = logging.getLogger("GitHubConnector")


class GitHubConnector:
    def __init__(self) -> None:
        self.users: Dict[str, Dict[str, Any]] = {}  # username -> user_data
        self.teams: Dict[str, List[str]] = {
            "Engineering": [],
            "DevOps": [],
            "Frontend": [],
            "Backend": [],
        }

    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        username = (
            f"{user_data['first_name'].lower()}{user_data['last_name'].lower()}"
        )
        user = {
            "username": username,
            "email": user_data["email"],
            "name": f"{user_data['first_name']} {user_data['last_name']}",
        }
        self.users[username] = user
        return user

    def add_to_team(self, username: str, team_name: str) -> Dict[str, Any]:
        if team_name not in self.teams:
            self.teams[team_name] = []

        if username not in self.teams[team_name]:
            self.teams[team_name].append(username)

        return {"status": "success", "team": team_name, "member": username}

    def remove_from_team(self, username: str, team_name: str) -> Dict[str, Any]:
        if team_name in self.teams and username in self.teams[team_name]:
            self.teams[team_name].remove(username)
        return {"status": "success", "team": team_name, "member": username}

    def remove_user(self, username: str) -> Dict[str, Any]:
        if username in self.users:
            del self.users[username]
            # Also remove from all teams
            for team in self.teams.values():
                if username in team:
                    team.remove(username)
            return {"status": "success", "username": username}
        return {"status": "error", "message": "User not found"}


github_connector = GitHubConnector()
