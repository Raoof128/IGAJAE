from typing import Generator
import pytest
from backend.engines.jml_engine import jml_engine
from backend.stores.identity_store import identity_store
from backend.stores.audit_log import audit_log_store

from connectors.azuread_connector import azure_ad_connector
from connectors.github_connector import github_connector
from connectors.slack_connector import slack_connector


@pytest.fixture(autouse=True)
def run_around_tests() -> Generator[None, None, None]:
    # Setup: Clear stores and connectors
    identity_store._identities = {}
    identity_store._employee_id_map = {}
    audit_log_store._logs = []
    azure_ad_connector.users = {}
    azure_ad_connector.groups = {k: [] for k in azure_ad_connector.groups}
    github_connector.users = {}
    github_connector.teams = {k: [] for k in github_connector.teams}
    slack_connector.users = {}
    slack_connector.channels = {k: [] for k in slack_connector.channels}
    yield
    # Teardown


def test_joiner_flow() -> None:
    payload = {
        "employee_id": "EMP001",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "department": "Engineering",
        "job_title": "Software Engineer",
        "location": "NY",
    }

    result = jml_engine.process_event("EmployeeCreated", payload)

    if result["status"] != "success":
        print(f"Joiner Failed: {result}")

    assert result["status"] == "success"
    identity = identity_store.get_identity_by_employee_id("EMP001")
    assert identity is not None
    assert identity.status == "active"
    assert "GitHub:Engineering" in identity.entitlements
    assert "azure_ad" in identity.accounts
    assert "github" in identity.accounts


def test_mover_flow() -> None:
    # 1. Join as Engineering
    payload = {
        "employee_id": "EMP002",
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane.smith@example.com",
        "department": "Engineering",
        "job_title": "Dev",
        "location": "NY",
    }
    jml_engine.process_event("EmployeeCreated", payload)

    # 2. Move to Sales
    update_payload = {
        "employee_id": "EMP002",
        "department": "Sales",
        "job_title": "Sales Engineer",
    }
    result = jml_engine.process_event("EmployeeUpdated", update_payload)
    if result["status"] != "success":
        print(f"Mover Failed: {result}")

    identity = identity_store.get_identity_by_employee_id("EMP002")
    assert identity is not None
    assert identity.department == "Sales"
    # Should have Sales access
    assert "AzureAD:Sales" in identity.entitlements
    # Should NOT have Engineering access (revoked)
    assert "GitHub:Engineering" not in identity.entitlements


def test_leaver_flow() -> None:
    # 1. Join
    payload = {
        "employee_id": "EMP003",
        "first_name": "Bob",
        "last_name": "Jones",
        "email": "bob.jones@example.com",
        "department": "Marketing",
        "job_title": "Marketer",
        "location": "NY",
    }
    jml_engine.process_event("EmployeeCreated", payload)

    # 2. Leave
    term_payload = {"employee_id": "EMP003"}
    result = jml_engine.process_event("EmployeeTerminated", term_payload)
    if result["status"] != "success":
        print(f"Leaver Failed: {result}")

    identity = identity_store.get_identity_by_employee_id("EMP003")
    assert identity is not None
    assert identity.status == "terminated"
    assert identity.lifecycle_state == "leaver"
    assert len(identity.entitlements) == 0
