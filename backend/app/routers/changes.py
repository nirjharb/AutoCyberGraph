"""Change management + Change Impact Engine endpoints."""
import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..graph import resolve_entity_type
from ..models import Change, User
from ..schemas import ChangeCreate, ChangeOut, ImpactReport
from ..security import audit, get_current_user, require_analysis, require_write
from ..services.impact import compute_impact

router = APIRouter(prefix="/api/changes", tags=["changes"])


@router.get("", response_model=list[ChangeOut])
def list_changes(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return list(db.scalars(select(Change).order_by(Change.created_at.desc())))


@router.post("", response_model=ChangeOut, status_code=status.HTTP_201_CREATED)
def create_change(payload: ChangeCreate, db: Session = Depends(get_db), user: User = Depends(require_write)):
    entity_type = resolve_entity_type(payload.entity_type)
    change = Change(
        entity_type=entity_type,
        entity_id=payload.entity_id,
        change_type=payload.change_type,
        description=payload.description,
        created_by=user.email,
        security_assessment=payload.security_assessment,
    )
    db.add(change)
    db.commit()
    audit(db, user.email, "change.create", "Change", change.id, change.description[:120])
    return change


@router.get("/{change_id}", response_model=ChangeOut)
def get_change(change_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    change = db.get(Change, change_id)
    if change is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Change not found")
    return change


@router.post("/{change_id}/impact", response_model=ImpactReport)
def run_impact(change_id: int, db: Session = Depends(get_db), user: User = Depends(require_analysis)):
    change = db.get(Change, change_id)
    if change is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Change not found")
    result = compute_impact(db, change)
    change.impact_level = result["impact_level"].value
    change.impact_report = result["report"]
    change.impact_summary = result["summary"]
    change.analyzed_at = dt.datetime.now(dt.timezone.utc)
    db.commit()
    audit(db, user.email, "change.impact", "Change", change.id, result["impact_level"].value)
    return ImpactReport(
        change_id=change.id,
        impact_level=result["impact_level"],
        affected=result["affected"],
        summary=result["summary"],
        recommended_actions=result["recommended_actions"],
        rationale=result["rationale"],
    )
