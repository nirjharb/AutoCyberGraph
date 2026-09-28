# Getting Started

## Prerequisites

- Python 3.11+
- Node.js 20+
- (Optional) PostgreSQL 16 — SQLite is used by default for local development

## Quick start (single command)

```bash
git clone https://github.com/autocybergraph/autocybergraph
cd autocybergraph
bash scripts/dev.sh
```

Open **http://localhost:8000** and sign in with a demo account:

| Email | Role | Password |
|-------|------|----------|
| `engineer@autocybergraph.io` | Cybersecurity Engineer | `ChangeMe123!` |
| `admin@autocybergraph.io` | Admin | `ChangeMe123!` |
| `architect@autocybergraph.io` | Architect | `ChangeMe123!` |
| `tester@autocybergraph.io` | Tester | `ChangeMe123!` |
| `supplier@autocybergraph.io` | Supplier | `ChangeMe123!` |
| `auditor@autocybergraph.io` | Auditor | `ChangeMe123!` |
| `viewer@autocybergraph.io` | Viewer | `ChangeMe123!` |

> Change these passwords immediately for any shared deployment.

## Step by step

```bash
# 1. Backend
cd backend
pip install -r requirements.txt
cp ../.env.example .env           # adjust as needed
python -m uvicorn app.main:app --reload --port 8000

# 2. Demo data (separate shell)
bash scripts/seed.sh

# 3. Frontend dev server (optional; built frontend is served at :8000 already)
cd frontend
npm install
npm run dev                       # http://localhost:5173
```

## Tests

```bash
bash scripts/test-all.sh          # lint + pytest + vitest + production build
```

## Docker (self-hosted, includes PostgreSQL)

```bash
cp .env.example .env              # set JWT_SECRET and POSTGRES_PASSWORD
docker compose up --build
```

The API + UI are served on http://localhost:8000.

## Environment variables

Documented in [`.env.example`](../.env.example):

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | `sqlite:///./autocybergraph.db` or `postgresql+psycopg://…` |
| `JWT_SECRET` | **Required in production** — long random string |
| `CORS_ORIGINS` | Comma-separated frontend origin allowlist |
| `AI_API_KEY` / `AI_BACKEND` | Optional LLM CyberAdvisor backend |
| `STORAGE_*` | Evidence storage backend configuration |
| `SEED_DEMO_ON_STARTUP` | Auto-seed demo data (dev/demo deployments) |

## API documentation

- Swagger UI: `http://localhost:8000/api/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

See [api.md](api.md) for the endpoint overview.
