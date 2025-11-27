from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from backend.config import settings
from backend.stores.audit_log import AuditEvent, audit_log_store
from backend.stores.identity_store import IdentityProfile, identity_store
from backend.engines.jml_engine import jml_engine
from connectors.azuread_connector import azure_ad_connector
from connectors.github_connector import github_connector
from connectors.slack_connector import slack_connector
from backend.stores.request_store import AccessRequest, request_store
from backend.engines.request_engine import request_engine

app = FastAPI(title=settings.APP_NAME, version=settings.VERSION)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HRFeedEvent(BaseModel):
    event_type: str
    employee_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    location: Optional[str] = None


@app.get("/")
def read_root() -> Dict[str, str]:
    return {"status": "IGA Platform Running", "version": settings.VERSION}


@app.post("/api/hr/event")
def trigger_hr_event(event: HRFeedEvent) -> Dict[str, Any]:
    """Simulate an event coming from the HR system (Workday/BambooHR)."""
    payload = event.dict(exclude_none=True)
    result = jml_engine.process_event(event.event_type, payload)
    return result


@app.get("/api/identities", response_model=List[IdentityProfile])
def list_identities() -> List[IdentityProfile]:
    return identity_store.list_identities()


@app.get("/api/identities/{identity_id}")
def get_identity(identity_id: str) -> IdentityProfile:
    identity = identity_store.get_identity(identity_id)
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")
    return identity


@app.get("/api/audit/logs", response_model=List[AuditEvent])
def list_audit_logs() -> List[AuditEvent]:
    return audit_log_store.get_logs()


# --- Access Request Endpoints ---


class AccessRequestCreate(BaseModel):
    requester_id: str
    entitlement: str
    justification: str


class AccessRequestAction(BaseModel):
    approver_id: str
    reason: Optional[str] = None


@app.post("/api/requests")
def submit_request(req: AccessRequestCreate) -> AccessRequest:
    try:
        return request_engine.submit_request(
            req.requester_id, req.entitlement, req.justification
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/requests")
def list_requests(status: Optional[str] = None) -> List[AccessRequest]:
    return request_store.list_requests(status)


@app.post("/api/requests/{request_id}/approve")
def approve_request(request_id: str, action: AccessRequestAction) -> AccessRequest:
    try:
        return request_engine.approve_request(request_id, action.approver_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/requests/{request_id}/reject")
def reject_request(request_id: str, action: AccessRequestAction) -> AccessRequest:
    try:
        return request_engine.reject_request(
            request_id, action.approver_id, action.reason or "No reason provided"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Connector Debug Endpoints ---
@app.get("/api/connectors/azuread/users")
def list_azure_users() -> Dict[str, Any]:
    return azure_ad_connector.users


@app.get("/api/connectors/github/users")
def list_github_users() -> Dict[str, Any]:
    return github_connector.users


@app.get("/api/connectors/slack/users")
def list_slack_users() -> Dict[str, Any]:
    return slack_connector.users


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
