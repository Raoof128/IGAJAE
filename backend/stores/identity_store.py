import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class IdentityProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    first_name: str
    last_name: str
    email: str
    department: str
    job_title: str
    manager_id: Optional[str] = None
    status: str = "active"  # active, inactive, pre-hire, terminated
    lifecycle_state: str = "joiner"  # joiner, mover, leaver, stable
    risk_score: str = "low"  # low, medium, high, critical
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    entitlements: List[str] = []
    accounts: Dict[
        str, str
    ] = {}  # e.g. {"azure_ad": "user_principal_name", "github": "username"}


class IdentityStore:
    def __init__(self) -> None:
        self._identities: Dict[str, IdentityProfile] = {}
        self._employee_id_map: Dict[str, str] = {}  # employee_id -> id

    def create_identity(self, profile_data: Dict[str, Any]) -> IdentityProfile:
        # Check uniqueness
        if profile_data.get("employee_id") in self._employee_id_map:
            raise ValueError(
                f"Identity with employee_id {profile_data['employee_id']} "
                "already exists."
            )

        profile = IdentityProfile(**profile_data)
        self._identities[profile.id] = profile
        self._employee_id_map[profile.employee_id] = profile.id
        return profile

    def get_identity(self, identity_id: str) -> Optional[IdentityProfile]:
        return self._identities.get(identity_id)

    def get_identity_by_employee_id(
        self, employee_id: str
    ) -> Optional[IdentityProfile]:
        identity_id = self._employee_id_map.get(employee_id)
        if identity_id:
            return self._identities.get(identity_id)
        return None

    def update_identity(
        self, identity_id: str, updates: Dict[str, Any]
    ) -> IdentityProfile:
        if identity_id not in self._identities:
            raise ValueError("Identity not found")

        identity = self._identities[identity_id]
        updated_data = identity.dict()
        updated_data.update(updates)
        updated_data["updated_at"] = datetime.now()

        new_identity = IdentityProfile(**updated_data)
        self._identities[identity_id] = new_identity
        return new_identity

    def list_identities(self) -> List[IdentityProfile]:
        return list(self._identities.values())


# Singleton instance
identity_store = IdentityStore()
