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

## VS Code

The repository ships ready-made VS Code configuration (`.vscode/`):

| Feature | How |
|---------|-----|
| Recommended extensions | Prompted automatically (`extensions.json`) |
| One-click setup | Terminal → Run Task → **`setup: install everything`** |
| Debug backend (breakpoints in FastAPI) | Run & Debug → **`Backend: FastAPI (debug)`** (F5) |
| Debug frontend dev server | **`Frontend: Vite dev server`** |
| Both at once | **`Full Stack (API + UI)`** compound |
| Run tests | Run Task → **`test: all`** (or `test: backend` / `test: frontend`) |
| Reset demo data | Run Task → **`reset: demo database`** |

Typical flow:

1. Open the repository root in VS Code (`File → Open Folder…`)
2. Accept the "Install recommended extensions" prompt
3. Terminal → **Run Task…** → `setup: install everything`
4. **F5** → pick `Full Stack (API + UI)`
   - API + UI dev: `http://localhost:5173` (proxies `/api` to :8000)
   - Or build once (`build: frontend`) and use just the backend at `http://localhost:8000`
5. Sign in with a demo account (see above)

> **Windows:** the `scripts/*.sh` tasks use bash — run them in **Git Bash** or **WSL**
> (VS Code's default terminal profile can be set to Git Bash). The direct commands
> (`python -m uvicorn …`, `npm run dev`) work in PowerShell too.

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
