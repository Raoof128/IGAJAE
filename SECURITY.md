# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please follow these steps:

1.  **Do NOT open a public issue.**
2.  Email the maintainers directly at `security@example.com` (replace with actual email if applicable).
3.  Include a detailed description of the vulnerability, steps to reproduce, and potential impact.
4.  We will acknowledge your report within 48 hours and provide an estimated timeline for a fix.

## Security Best Practices in This Project

-   **Simulated Environment**: This project is a simulation and should NOT be connected to real production identity providers (Azure AD, Okta, etc.) without significant modification and security review.
-   **No Real Data**: Do not use real PII (Personally Identifiable Information) in this system. Use the provided generators or mock data.
-   **Secrets Management**: In a real deployment, ensure all secrets (API keys, tokens) are managed via a secure vault or environment variables, not hardcoded.
