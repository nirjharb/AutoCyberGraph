"""Admin utilities: health, audit log, demo seeding."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models import AuditLog, User
from ..schemas import AuditOut
from ..security import audit, require_admin
from ..services.seed import seed_demo_data

router = APIRouter(prefix="/api", tags=["admin"])


@router.get("/health")
def health(db: Session = Depends(get_db)):
    settings = get_settings()
    db_ok = True
    try:
        db.execute(select(1))
    except Exception:  # noqa: BLE001
        db_ok = False
    return {
        "status": "ok" if db_ok else "degraded",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": "connected" if db_ok else "unavailable",
    }


@router.get("/audit", response_model=list[AuditOut])
def audit_log(limit: int = 100, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return list(db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(min(limit, 500))))


@router.post("/admin/seed")
def seed(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    result = seed_demo_data(db)
    audit(db, user.email, "admin.seed", "Database", None, str(result))
    return result
