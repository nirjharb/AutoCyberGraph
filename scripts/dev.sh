#!/usr/bin/env bash
# Run AutoCyberGraph locally: backend on :8000 (API + built frontend),
# frontend dev server on :5173 with /api proxy (optional).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [ ! -d "$ROOT/frontend/dist" ]; then
  echo "Building frontend…"
  (cd "$ROOT/frontend" && npm install && npm run build)
fi

if [ ! -f "$ROOT/backend/autocybergraph.db" ]; then
  echo "Seeding demo data…"
  bash "$ROOT/scripts/seed.sh"
fi

echo "Starting API + frontend on http://localhost:8000"
cd "$ROOT/backend"
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
