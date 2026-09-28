#!/usr/bin/env bash
# One-shot bootstrap + serve. Survives missing deps/builds after sandbox resets.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if ! python3 -c "import uvicorn" 2>/dev/null; then
  echo "[serve] installing backend deps…"
  pip install -r "$ROOT/backend/requirements.txt" -q
fi

if [ ! -f "$ROOT/frontend/dist/index.html" ]; then
  echo "[serve] building frontend…"
  cd "$ROOT/frontend"
  [ -d node_modules ] || npm install --no-audit --no-fund --silent
  npm run build >/dev/null 2>&1
  cd "$ROOT"
fi

if [ ! -f "$ROOT/backend/autocybergraph.db" ]; then
  echo "[serve] seeding demo data…"
  bash "$ROOT/scripts/seed.sh"
fi

cd "$ROOT/backend"
echo "[serve] starting AutoCyberGraph on :8000"
while true; do
  python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
  echo "[serve] uvicorn exited (code $?) — restarting in 2s…"
  sleep 2
done
