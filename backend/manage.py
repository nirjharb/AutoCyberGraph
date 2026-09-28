"""Cross-platform task runner — works on Windows/macOS/Linux.

Usage (from the backend/ folder):
    python manage.py seed     # create tables + load the Demo EV Platform dataset
    python manage.py reset    # delete the local database and reseed
    python manage.py run      # start the API server on http://localhost:8000
    python manage.py test     # run the backend test suite
"""
from __future__ import annotations

import os
import subprocess
import sys


def seed(reset: bool = False) -> None:
    if reset and os.path.exists("autocybergraph.db"):
        os.remove("autocybergraph.db")
        print("Removed autocybergraph.db")
    from app.database import Base, SessionLocal, engine
    from app.services.seed import seed_demo_data

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        print(seed_demo_data(db))
    finally:
        db.close()


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "seed":
        seed()
    elif cmd == "reset":
        seed(reset=True)
    elif cmd == "run":
        subprocess.run(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000"],
            check=False,
        )
    elif cmd == "test":
        raise SystemExit(subprocess.run([sys.executable, "-m", "pytest", "tests/", "-q"]).returncode)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
