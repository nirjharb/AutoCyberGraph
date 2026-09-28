#!/usr/bin/env bash
# Run all test suites (backend pytest + frontend vitest + lint).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "== Backend lint =="
(cd "$ROOT/backend" && python3 -m ruff check app/ tests/ --select E,F,I --ignore E501)

echo "== Backend tests =="
(cd "$ROOT/backend" && python3 -m pytest tests/ -q)

echo "== Frontend tests =="
(cd "$ROOT/frontend" && npx vitest run)

echo "== Frontend build =="
(cd "$ROOT/frontend" && npm run build)

echo "All checks passed."
