"""Releases + Cybersecurity Release Gate."""
import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ECU, Release, User
from ..schemas import GateEvaluation, ReleaseCreate, ReleaseOut
from ..security import audit, get_current_user, require_analysis, require_write
from ..services.release_gate import evaluate_release

router = APIRouter(prefix="/api/releases", tags=["releases"])


@router.get("", response_model=list[ReleaseOut])
def list_releases(ecu_id: int | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    q = select(Release)
    if ecu_id:
        q = q.where(Release.ecu_id == ecu_id)
    return list(db.scalars(q))


@router.post("", response_model=ReleaseOut, status_code=status.HTTP_201_CREATED)
def create_release(payload: ReleaseCreate, db: Session = Depends(get_db), user: User = Depends(require_write)):
    if db.get(ECU, payload.ecu_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ECU not found")
    release = Release(**payload.model_dump())
    db.add(release)
    db.commit()
    audit(db, user.email, "release.create", "Release", release.id, release.version)
    return release


@router.get("/{release_id}", response_model=ReleaseOut)
def get_release(release_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    release = db.get(Release, release_id)
    if release is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Release not found")
    return release


@router.post("/{release_id}/evaluate", response_model=GateEvaluation)
def evaluate(release_id: int, db: Session = Depends(get_db), user: User = Depends(require_analysis)):
    release = db.get(Release, release_id)
    if release is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Release not found")
    evaluation = evaluate_release(db, release)
    release.gate_result = evaluation.result.value
    release.gate_reasons = [c.model_dump() for c in evaluation.checks]
    release.gate_evaluated_at = dt.datetime.now(dt.timezone.utc)
    if evaluation.result.value == "PASS" and release.status in ("PLANNED", "IN_VALIDATION"):
        release.status = "APPROVED"
    elif evaluation.result.value == "HOLD":
        release.status = "BLOCKED"
    db.commit()
    audit(db, user.email, "release.evaluate", "Release", release.id, evaluation.result.value)
    return evaluation
