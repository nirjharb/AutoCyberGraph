# Security Policy

## Reporting a vulnerability

If you discover a security vulnerability in AutoCyberGraph, please report it
responsibly:

- **Email:** security@autocybergraph.example (placeholder — configure before public launch)
- **Do not** open a public GitHub issue for exploitable vulnerabilities.
- Include reproduction steps and impact assessment where possible.

We aim to acknowledge reports within 5 business days.

## Scope

This policy covers the **AutoCyberGraph application itself** (API, frontend,
authentication, data handling). It does not cover:

- The demo dataset (synthetic data, deliberately contains "open" demo CVEs)
- Third-party standards content (ISO/SAE 21434, UNECE R155/R156, NIST SP 800-53, AUTOSAR)

## Application security posture

Implemented controls (see `docs/security.md` for the threat model):

- Passwords hashed with bcrypt (cost 12); never logged or returned
- JWT authentication (HS256) with configurable secret and expiry via environment
- Role-based access control (7 roles) enforced per endpoint
- Organization-scoped authorization for supplier workflows
- Pydantic request validation on every endpoint
- Rate limiting on authentication and advisor endpoints
- Explicit CORS allowlist; security headers middleware (HSTS in production, CSP, X-Frame-Options, nosniff, Referrer-Policy, Permissions-Policy)
- Audit logging of security-relevant actions
- SBOM import size limits and strict schema validation
- Secrets exclusively via environment variables; `.env` git-ignored
- Non-root Docker container; health endpoint for orchestration

## Supported versions

| Version | Supported |
| ------- | --------- |
| 0.1.x   | ✅        |

## Preferred languages

English.
