# AutoCyberGraph — Architecture

> **Disclaimer:** AutoCyberGraph is an engineering and evidence-management platform.
> It does not provide legal, regulatory, certification, or compliance advice.

## 1. System Overview

```
┌───────────────────────────────┐        ┌──────────────────────────────────────┐
│  Frontend (React + Vite + TS) │  HTTPS │  Backend (FastAPI + SQLAlchemy 2.0)  │
│  Tailwind · TanStack Query    │ ─────► │  JWT auth · RBAC · Pydantic v2       │
│  Recharts · Cytoscape.js      │  /api  │  Services: risk, impact, gate, SBOM  │
└───────────────────────────────┘        └───────────────┬──────────────────────┘
                                                         │ SQLAlchemy
                       ┌─────────────────────────────────▼─────────────────────┐
                       │  PostgreSQL (production)  /  SQLite (local default)   │
                       └───────────────────────────────────────────────────────┘
```

Production: frontend on Vercel (static build), backend containerized on
Railway/Render, managed PostgreSQL. The FastAPI app can also serve the built
frontend as static files (single-service deployment, used for demos).

## 2. Layered Backend

```
routers/   HTTP layer: validation (Pydantic), auth/RBAC dependencies, status codes
services/  Domain logic: risk calculation, change-impact traversal, release gate,
           SBOM parsing, CyberAdvisor query engine, seeding
graph.py   Graph abstraction (GraphService): adjacency built from relational
           edges; Neo4j adapter can be introduced without rewriting the app
models.py  SQLAlchemy 2.0 declarative models (portable across SQLite/PostgreSQL)
```

## 3. Domain Model (summary)

18 entity types: Organization, User, Vehicle, ECU, Network, Asset, Threat, TARA,
Cybersecurity Requirement, Standard, Control, AUTOSAR Security Mechanism,
Software Component, Vulnerability, SBOM, Test Case, Test Result, Evidence,
Release, Change, Compliance Mapping, Supplier.

The **traceability spine**:

```
Vehicle → ECU → Software Component → Asset → Threat → TARA → Cybersecurity Goal
→ Requirement → Control → AUTOSAR Mechanism → Test Case → Test Result
→ Evidence → Release
```

Side spines:
- `Software Component → SBOM → Vulnerability → ECU → Vehicle`
- `Change → Affected Entity → Affected Relationships → TARA → Requirements →
  Tests → Evidence → Release Gate`

## 4. Graph Abstraction (`app/graph.py`)

- `GraphService.neighbors(entity_type, entity_id, direction)` and
  `GraphService.bfs(entity, max_depth)` return typed nodes + **edge reasons**.
- MVP backend: adjacency computed from SQLAlchemy relationship tables
  (`edge_source`, `edge_target`, `edge_kind`, `edge_description`).
- Future: `Neo4jGraphService` implementing the same protocol; routers and the
  impact engine are written against the protocol only.

## 5. Change Impact Engine (`services/impact.py`)

1. Load the changed entity (software component, ECU, TARA, requirement, …).
2. BFS traversal over the edge set (both directions, depth-bounded).
3. Classify affected artifacts (requirements, TARA, tests, controls, evidence,
   releases, vulnerabilities, mechanisms, R155/R156 mappings).
4. Score impact level from artifact criticality + change type
   (`CRITICAL / HIGH / MEDIUM / LOW`).
5. Emit **per-object reasons**: the actual graph path that made it affected.
6. Emit recommended actions derived from what is affected (never guessed).

## 6. Release Gate (`services/release_gate.py`)

Deterministic checks over the release scope (ECU → vehicle):
TARA reviewed · requirements traced · tests executed/passing · critical
vulnerabilities resolved · SBOM available · AUTOSAR mappings present · evidence
present · security-impact analysis complete. Result is `PASS | REVIEW | HOLD`
with individual check results and reasons — **no composite "security score"**.

## 7. TARA Risk Method (`services/risk.py`)

`risk = f(impact, attack_feasibility)` via a configurable matrix →
`LOW | MEDIUM | HIGH | CRITICAL`. This is an *application implementation* of a
risk method, not an official certification methodology. The matrix is data-driven
(`RISK_MATRIX` + `DEFAULT_IMPACT_LEVELS`) and documented in `docs/tara.md`.

## 8. Security Architecture

- Passwords: bcrypt (cost 12), never logged, never returned.
- Auth: JWT (HS256, short-lived access tokens) via `Authorization: Bearer`.
- RBAC: 7 roles, enforced per-route with dependency injection
  (`require_roles(...)`), organization scoping for supplier workflows.
- Input validation: Pydantic v2 on every request body/query.
- Audit logging: `audit_logs` table (actor, action, entity, timestamp).
- Rate limiting: slowapi on auth + advisor endpoints.
- CORS: explicit allowlist via `CORS_ORIGINS` env var.
- Security headers middleware (HSTS, X-Content-Type-Options, X-Frame-Options,
  Referrer-Policy, CSP) — full CSP in production, relaxed for the Vite dev server.
- Secrets: environment variables only (`.env.example` provided; `.gitignore`
  excludes `.env`). No hardcoded credentials anywhere.
- SBOM import: strict schema validation, size limits, allowed extensions.
- App threat model: `docs/security.md`.

## 9. Frontend Architecture

```
src/
  api/        typed fetch client + TanStack Query hooks
  components/ UI kit (button, card, table, badge, dialog…) — shadcn-style, local
  pages/      route-level screens
  graphs/     Cytoscape wrappers (evidence graph, vehicle network)
  auth/       token store, route guards
```

State: TanStack Query for server state; minimal local state elsewhere.
Routing: React Router v6 with `RequireAuth` + `RequireRole` wrappers.

## 10. Data Flow — Change Impact Demo

```
POST /api/changes  (Crypto library v2.4 → v2.5 on Gateway ECU)
POST /api/changes/{id}/impact
   → GraphService BFS
   → affected: TARA · requirements · tests · vulns · evidence · releases
   → reasons per object + recommended actions
POST /api/releases/{id}/evaluate
   → gate checks fail on open critical vuln / unreviewed security impact
   → HOLD / REVIEW with reasons
```

## 11. Deployment Topology

| Piece | Local | Production |
|-------|-------|------------|
| Frontend | Vite dev server | Vercel (static) or served by FastAPI |
| Backend | uvicorn (SQLite) | Docker on Railway/Render |
| Database | SQLite file | Managed PostgreSQL (`DATABASE_URL`) |
| Secrets | `.env` | Platform env vars |

Migrations: Alembic wired to the same metadata (`backend/alembic`); startup
runs `create_all` for zero-friction demos and the Alembic path is used in
production CI. See `DECISIONS.md`.
