from typing import Generator
import pytest
from backend.engines.request_engine import request_engine
from backend.stores.request_store import request_store
from backend.stores.identity_store import identity_store
from backend.stores.audit_log import audit_log_store


@pytest.fixture(autouse=True)
def run_around_tests() -> Generator[None, None, None]:
    # Setup
    identity_store._identities = {}
    request_store._requests = []
    audit_log_store._logs = []
    yield
    # Teardown


def test_access_request_flow() -> None:
    # 1. Create Requester and Approver
    requester = identity_store.create_identity(
        {
            "employee_id": "REQ001",
            "first_name": "Alice",
            "last_name": "Requester",
            "email": "alice@example.com",
            "department": "Engineering",
            "job_title": "Engineer",
        }
    )

    approver = identity_store.create_identity(
        {
            "employee_id": "APP001",
            "first_name": "Bob",
            "last_name": "Manager",
            "email": "bob@example.com",
            "department": "Engineering",
            "job_title": "Manager",
        }
    )

    # 2. Submit Request
    req = request_engine.submit_request(
        requester.id, "GitHub:SuperAdmin", "Need admin access"
    )
    assert req.status == "pending"
    assert req.requester_id == requester.id

    # 3. Approve Request (Success)
    approved_req = request_engine.approve_request(req.id, approver.id)
    assert approved_req.status == "approved"
    assert approved_req.approver_id == approver.id

    # 4. Verify Provisioning
    updated_requester = identity_store.get_identity(requester.id)
    assert updated_requester is not None
    assert "GitHub:SuperAdmin" in updated_requester.entitlements


def test_self_approval_prevention() -> None:
    # 1. Create User
    user = identity_store.create_identity(
        {
            "employee_id": "SELF001",
            "first_name": "Self",
            "last_name": "Approver",
            "email": "self@example.com",
            "department": "Engineering",
            "job_title": "Hacker",
        }
    )

    # 2. Submit Request
    req = request_engine.submit_request(user.id, "GitHub:Admin", "I want power")

    # 3. Try to Approve as Self
    with pytest.raises(ValueError, match="Self-approval is not allowed"):
        request_engine.approve_request(req.id, user.id)


def test_sod_warning() -> None:
    # 1. Create User with Sales Access
    user = identity_store.create_identity(
        {
            "employee_id": "SOD001",
            "first_name": "Conflict",
            "last_name": "User",
            "email": "conflict@example.com",
            "department": "Sales",
            "job_title": "Sales Rep",
            "entitlements": ["AzureAD:Sales"],
        }
    )

    # 2. Request Finance Access (Conflict defined in Policy Engine)
    # Policy: Sales + Finance-Admin = Critical SoD
    req = request_engine.submit_request(user.id, "AzureAD:Finance-Admin", "Bad idea")

    # Currently we just log it, but the request should still be created
    assert req.status == "pending"
    # In a real system, this might auto-reject or require 2-step approval.
