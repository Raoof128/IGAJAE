# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-11-28

### Added
-   **Access Request Workflow**: Self-service access request system with approval/rejection logic.
-   **Request Engine**: Core logic for handling access requests and SoD checks.
-   **Request Store**: In-memory storage for access requests.
-   **Frontend Tab**: New "Access Requests" tab in the dashboard for submitting and approving requests.
-   **Tests**: Comprehensive tests for the access request flow (`tests/test_access_request.py`).

### Changed
-   **JMLEngine**: Exposed `provision_entitlement` method for ad-hoc access granting.
-   **Frontend**: Updated UI to support role switching (Requester/Approver) for simulation.

## [1.0.0] - 2025-11-28

### Added
-   **Core Platform**: Initial release of the IGA Platform.
-   **Identity Store**: Centralized identity registry.
-   **JML Engine**: Joiner, Mover, and Leaver automation flows.
-   **Policy Engine**: Birthright access policies and Separation of Duties (SoD) checks.
-   **Connectors**: Simulated connectors for Azure AD, GitHub, and Slack.
-   **Audit Logging**: Centralized audit log store and viewer.
-   **Dashboard**: React-based frontend for HR simulation and identity visibility.
