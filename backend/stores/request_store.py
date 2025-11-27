import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AccessRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    requester_id: str  # The identity ID of the user requesting access
    # The identity ID who will receive access (usually same as requester)
    target_identity_id: str
    entitlement: str  # e.g. "GitHub:SuperAdmin"
    justification: str
    status: str = "pending"  # pending, approved, rejected, failed
    approver_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    comments: Optional[str] = None


class RequestStore:
    def __init__(self) -> None:
        self._requests: List[AccessRequest] = []

    def create_request(self, request_data: Dict[str, Any]) -> AccessRequest:
        req = AccessRequest(**request_data)
        self._requests.append(req)
        return req

    def get_request(self, request_id: str) -> Optional[AccessRequest]:
        for req in self._requests:
            if req.id == request_id:
                return req
        return None

    def list_requests(self, status: Optional[str] = None) -> List[AccessRequest]:
        if status:
            return [r for r in self._requests if r.status == status]
        return sorted(self._requests, key=lambda x: x.created_at, reverse=True)

    def update_request(
        self, request_id: str, updates: Dict[str, Any]
    ) -> Optional[AccessRequest]:
        req = self.get_request(request_id)
        if not req:
            return None

        updated_data = req.dict()
        updated_data.update(updates)
        updated_data["updated_at"] = datetime.now()

        new_req = AccessRequest(**updated_data)
        # Replace in list
        self._requests = [r if r.id != request_id else new_req for r in self._requests]
        return new_req


# Singleton
request_store = RequestStore()
