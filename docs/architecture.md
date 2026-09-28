# Architecture

> AutoCyberGraph is an engineering and evidence-management platform. It does not
> provide legal, regulatory, certification, or compliance advice.

*(Canonical content lives in the repository root [`ARCHITECTURE.md`](../ARCHITECTURE.md) — this page summarizes and links.)*

## System overview

- **Frontend:** React 18 + TypeScript + Vite + Tailwind + TanStack Query + Recharts + Cytoscape.js
- **Backend:** FastAPI + Pydantic v2 + SQLAlchemy 2.0 (portable SQLite/PostgreSQL)
- **Auth:** JWT (HS256) + bcrypt + role-based access control
- **Graph:** `GraphService` abstraction — relational adjacency today, Neo4j-ready protocol

## Key subsystems

| Subsystem | Module | Notes |
|-----------|--------|-------|
| Change Impact Engine | `backend/app/services/impact.py` | BFS over the traceability graph; per-object reasons |
| Release Gate | `backend/app/services/release_gate.py` | Deterministic checks → PASS/REVIEW/HOLD |
| TARA risk method | `backend/app/services/risk.py` | Configurable matrix (see [tara.md](tara.md)) |
| SBOM parsing | `backend/app/services/sbom.py` | CycloneDX robust, SPDX JSON basic |
| CyberAdvisor | `backend/app/services/cyberadvisor.py` | DB-grounded rule engine, LLM-ready adapter |

## Data model

See the entity list in [`ARCHITECTURE.md` §3](../ARCHITECTURE.md#3-domain-model-summary)
and the live OpenAPI schema at `/api/docs` (Swagger UI) when the server runs.

## Deployment topology

Frontend static build (Vercel or served by FastAPI) + containerized backend
(Railway/Render/Docker) + managed PostgreSQL. See `docker-compose.yml` and
[getting-started.md](getting-started.md).
