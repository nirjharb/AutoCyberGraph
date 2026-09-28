#!/usr/bin/env bash
# Seed (or reset) the AutoCyberGraph demo dataset.
set -euo pipefail
cd "$(dirname "$0")/../backend"
python3 - <<'EOF'
from app.database import Base, engine, SessionLocal
from app.services.seed import seed_demo_data

Base.metadata.create_all(bind=engine)
db = SessionLocal()
print(seed_demo_data(db))
db.close()
EOF
