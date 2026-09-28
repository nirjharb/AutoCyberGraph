# Application Security

> This document describes the security of the **AutoCyberGraph application**.
> It is not advice for vehicle cybersecurity programs.

## Threat model (STRIDE, abbreviated)

| Threat | Example | Mitigation |
|--------|---------|------------|
| **S**poofing | Attacker guesses a user password; fakes a JWT | bcrypt cost 12; HS256 JWT with server-side secret; expiry; rate-limited login |
| **T**ampering | Supplier edits another org's submission | Org-scoped authorization on every supplier route; audit log |
| **R**epudiation | "Who approved this evidence?" | `AuditLog` rows (actor, action, entity, timestamp) for all writes |
| **I**nformation disclosure | Viewer reads audit log or user hashes | Role checks (ADMIN-only endpoints); hashes/never serialized in responses |
| **D**enial of service | 10k login attempts; 50 MB SBOM upload | slowapi rate limits; SBOM size/component caps; validated JSON |
| **E**levation of privilege | Viewer creates requirements; self-registers as ADMIN | RBAC dependencies per route; registration clamps role below ADMIN |

## Control implementation

### Authentication
- bcrypt password hashing (cost 12), constant-time verification
- JWT HS256 access tokens; `JWT_SECRET` **must** be set in production
- Token payload: subject, role, org, expiry (`JWT_TTL_MINUTES`)
- Demo passwords are documented for demo purposes only

### Authorization (RBAC)

| Role | Read | Domain writes | Analysis (TARA/impact/gate) | Reviews / admin |
|------|------|---------------|------------------------------|-----------------|
| ADMIN | ✅ | ✅ | ✅ | ✅ |
| CYBERSECURITY_ENGINEER | ✅ | ✅ | ✅ | ✅ |
| ARCHITECT | ✅ | ✅ | ✅ | — |
| TESTER | ✅ | ✅ (tests/evidence) | — | — |
| SUPPLIER | ✅ (own org) | submissions only | — | — |
| AUDITOR | ✅ | — | — | — |
| VIEWER | ✅ | — | — | — |

Enforced by FastAPI dependencies (`require_roles`, `require_write`,
`require_analysis`, `require_reviewer`, `require_supplier_access`).

### Input validation & file handling
- Pydantic v2 schemas on all request bodies (types, lengths, enums)
- SBOM import: strict JSON, 10 MB / 5000 component caps, format detection
- Evidence `file_reference` is a validated string reference (URI/path) —
  blob storage is a pluggable backend (`STORAGE_BACKEND`), default local dir

### Transport & headers
- CORS explicit allowlist (`CORS_ORIGINS`); credentials + restricted headers
- Security headers middleware: `X-Content-Type-Options`, `X-Frame-Options: DENY`,
  `Referrer-Policy: no-referrer`, `Permissions-Policy`, HSTS + CSP in production
- TLS is terminated by the deployment provider (Railway/Render/Vercel)

### Secrets
- Everything via environment variables (`.env.example` provided)
- `.env`, keys and credentials are git-ignored; no secrets in code
- CI runs `pip-audit` / `npm audit` as basic dependency hygiene

### Audit logging
`audit_logs` table captures actor email, action, entity type/id and detail for
every mutation (create/update/review/evaluate/seed). Readable via `GET /api/audit`
(ADMIN).

### Rate limiting
slowapi on `/api/auth/*` (10/min default) and `/api/advisor/ask` (30/min default),
configurable via `RATE_LIMIT_AUTH`, `RATE_LIMIT_ADVISOR`.

## Data honesty

CyberAdvisor answers are computed from live database queries. When data cannot
answer a question, the response is exactly:

> Insufficient evidence in the project database.

No compliance or certification conclusions are generated, ever.

## Residual risks / roadmap

- Refresh-token rotation not implemented (short-lived access tokens only)
- File blob scanning (malware) delegated to storage provider — roadmap
- Single-tenant data model in MVP; row-level multi-tenancy is roadmap
- LLM CyberAdvisor backend (when enabled) must preserve the grounding/refusal
  contract — enforced around any backend implementation
