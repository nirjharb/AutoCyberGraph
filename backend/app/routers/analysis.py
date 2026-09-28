"""Assets, threats, TARA workflow (with documented risk calculation)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ECU, TARA, Asset, CybersecurityRequirement, Threat, User, utcnow
from ..schemas import (
    AssetCreate,
    AssetOut,
    TARACreate,
    TARAOut,
    TARAUpdate,
    ThreatCreate,
    ThreatOut,
)
from ..security import audit, get_current_user, require_analysis, require_write
from ..services.risk import calculate_risk

router = APIRouter(prefix="/api", tags=["analysis"])


# ---------- Assets ----------
@router.get("/assets", response_model=list[AssetOut])
def list_assets(ecu_id: int | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    q = select(Asset)
    if ecu_id:
        q = q.where(Asset.ecu_id == ecu_id)
    return list(db.scalars(q))


@router.post("/assets", response_model=AssetOut, status_code=status.HTTP_201_CREATED)
def create_asset(payload: AssetCreate, db: Session = Depends(get_db), user: User = Depends(require_write)):
    if db.get(ECU, payload.ecu_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ECU not found")
    asset = Asset(**payload.model_dump())
    db.add(asset)
    db.commit()
    audit(db, user.email, "asset.create", "Asset", asset.id, asset.name)
    return asset


# ---------- Threats ----------
@router.get("/threats", response_model=list[ThreatOut])
def list_threats(asset_id: int | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    q = select(Threat)
    if asset_id:
        q = q.where(Threat.asset_id == asset_id)
    return list(db.scalars(q))


@router.post("/threats", response_model=ThreatOut, status_code=status.HTTP_201_CREATED)
def create_threat(payload: ThreatCreate, db: Session = Depends(get_db), user: User = Depends(require_write)):
    if db.get(Asset, payload.asset_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Asset not found")
    threat = Threat(**payload.model_dump())
    db.add(threat)
    db.commit()
    audit(db, user.email, "threat.create", "Threat", threat.id, threat.name)
    return threat


# ---------- TARA ----------
def _apply_risk(tara: TARA, impact: str, feasibility: str) -> None:
    risk, impact_level, feasibility_level, _ = calculate_risk(impact, feasibility)
    tara.risk_level = risk
    tara.impact_level = impact_level
    tara.feasibility_level = feasibility_level


@router.get("/tara", response_model=list[TARAOut])
def list_tara(asset_id: int | None = None, risk_level: str | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    q = select(TARA)
    if asset_id:
        q = q.where(TARA.asset_id == asset_id)
    rows = list(db.scalars(q))
    if risk_level:
        rows = [t for t in rows if t.risk_level == risk_level.upper()]
    return rows


@router.post("/tara", response_model=TARAOut, status_code=status.HTTP_201_CREATED)
def create_tara(payload: TARACreate, db: Session = Depends(get_db), user: User = Depends(require_analysis)):
    if db.get(Asset, payload.asset_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Asset not found")
    if payload.threat_id is not None and db.get(Threat, payload.threat_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Threat not found")
    count = len(list(db.scalars(select(TARA)))) + 1
    tara = TARA(
        asset_id=payload.asset_id,
        threat_id=payload.threat_id,
        reference=f"TARA-{count:03d}",
        damage_scenario=payload.damage_scenario,
        threat_scenario=payload.threat_scenario,
        impact=payload.impact,
        attack_feasibility=payload.attack_feasibility,
        cybersecurity_goal=payload.cybersecurity_goal,
        status=payload.status,
    )
    _apply_risk(tara, payload.impact, payload.attack_feasibility)
    if payload.status in ("REVIEWED", "APPROVED"):
        tara.reviewed_at = utcnow()
    db.add(tara)
    db.commit()
    audit(db, user.email, "tara.create", "TARA", tara.id, tara.reference)
    return tara


@router.get("/tara/{tara_id}", response_model=TARAOut)
def get_tara(tara_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    tara = db.get(TARA, tara_id)
    if tara is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "TARA not found")
    return tara


@router.patch("/tara/{tara_id}", response_model=TARAOut)
def update_tara(tara_id: int, payload: TARAUpdate, db: Session = Depends(get_db), user: User = Depends(require_analysis)):
    tara = db.get(TARA, tara_id)
    if tara is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "TARA not found")
    data = payload.model_dump(exclude_unset=True)
    if "impact" in data or "attack_feasibility" in data:
        _apply_risk(tara, data.get("impact", tara.impact), data.get("attack_feasibility", tara.attack_feasibility))
    for key, value in data.items():
        if key not in ("impact", "attack_feasibility"):
            setattr(tara, key, value)
    if data.get("status") in ("REVIEWED", "APPROVED") and tara.reviewed_at is None:
        tara.reviewed_at = utcnow()
    db.commit()
    audit(db, user.email, "tara.update", "TARA", tara.id, tara.reference)
    return tara


@router.get("/tara/{tara_id}/requirements")
def tara_requirements(tara_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    tara = db.get(TARA, tara_id)
    if tara is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "TARA not found")
    reqs = list(db.scalars(select(CybersecurityRequirement).where(CybersecurityRequirement.tara_id == tara_id)))
    return {
        "tara_id": tara.id,
        "reference": tara.reference,
        "cybersecurity_goal": tara.cybersecurity_goal,
        "requirements": [
            {"id": r.id, "requirement_id": r.requirement_id, "title": r.title, "status": r.status}
            for r in reqs
        ],
    }
