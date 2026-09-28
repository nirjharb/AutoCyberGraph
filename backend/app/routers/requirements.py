"""Cybersecurity requirements + traceability + mechanism/control links."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..graph import SqlGraphService
from ..models import (
    TARA,
    AutosarMechanism,
    Control,
    CybersecurityRequirement,
    Evidence,
    RequirementControlLink,
    RequirementMechanismLink,
    User,
)
from ..schemas import (
    ControlLinkCreate,
    MechanismLinkCreate,
    RequirementCreate,
    RequirementOut,
    RequirementUpdate,
)
from ..security import audit, get_current_user, require_analysis, require_write

router = APIRouter(prefix="/api/requirements", tags=["requirements"])


@router.get("", response_model=list[RequirementOut])
def list_requirements(
    status_filter: str | None = None,
    missing: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rows = list(db.scalars(select(CybersecurityRequirement)))
    if status_filter:
        rows = [r for r in rows if r.status == status_filter.upper()]
    if missing == "evidence":
        rows = [r for r in rows if not list(db.scalars(select(Evidence).where(Evidence.requirement_id == r.id)))]
    if missing == "tests":
        rows = [r for r in rows if not r.test_cases]
    return rows


@router.post("", response_model=RequirementOut, status_code=status.HTTP_201_CREATED)
def create_requirement(payload: RequirementCreate, db: Session = Depends(get_db), user: User = Depends(require_analysis)):
    if db.scalars(select(CybersecurityRequirement).where(
            CybersecurityRequirement.requirement_id == payload.requirement_id)).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "requirement_id already exists")
    if payload.tara_id is not None and db.get(TARA, payload.tara_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "TARA not found")
    req = CybersecurityRequirement(**payload.model_dump())
    db.add(req)
    db.commit()
    audit(db, user.email, "requirement.create", "CybersecurityRequirement", req.id, req.requirement_id)
    return req


@router.get("/{req_id}")
def get_requirement(req_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    req = db.get(CybersecurityRequirement, req_id)
    if req is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Requirement not found")
    return _detail(req, db)


@router.patch("/{req_id}", response_model=RequirementOut)
def update_requirement(req_id: int, payload: RequirementUpdate, db: Session = Depends(get_db), user: User = Depends(require_analysis)):
    req = db.get(CybersecurityRequirement, req_id)
    if req is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Requirement not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(req, key, value)
    db.commit()
    audit(db, user.email, "requirement.update", "CybersecurityRequirement", req.id, req.requirement_id)
    return req


@router.get("/{req_id}/traceability")
def requirement_traceability(req_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Requirement → TARA → Asset → Threat → Control → Mechanism → Test → Evidence, with missing-link flags."""
    req = db.get(CybersecurityRequirement, req_id)
    if req is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Requirement not found")
    detail = _detail(req, db)
    checks = [
        {"key": "TARA", "present": req.tara is not None},
        {"key": "Asset", "present": req.tara is not None and req.tara.asset is not None},
        {"key": "Threat", "present": req.tara is not None and req.tara.threat is not None},
        {"key": "Control", "present": len(req.controls) > 0},
        {"key": "AUTOSAR mechanism", "present": len(req.mechanisms) > 0},
        {"key": "Test", "present": len(req.test_cases) > 0},
        {"key": "Evidence", "present": bool(detail["evidence"])},
    ]
    detail["trace_checks"] = checks
    detail["missing_links"] = [c["key"] for c in checks if not c["present"]]
    return detail


@router.post("/{req_id}/mechanisms", status_code=status.HTTP_201_CREATED)
def link_mechanism(req_id: int, payload: MechanismLinkCreate, db: Session = Depends(get_db), user: User = Depends(require_write)):
    req = db.get(CybersecurityRequirement, req_id)
    if req is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Requirement not found")
    if db.get(AutosarMechanism, payload.mechanism_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mechanism not found")
    existing = db.scalars(select(RequirementMechanismLink).where(
        RequirementMechanismLink.requirement_id == req_id,
        RequirementMechanismLink.mechanism_id == payload.mechanism_id)).first()
    if existing:
        return {"id": existing.id, "detail": "already linked"}
    link = RequirementMechanismLink(requirement_id=req_id, mechanism_id=payload.mechanism_id, notes=payload.notes)
    db.add(link)
    db.commit()
    audit(db, user.email, "requirement.link_mechanism", "CybersecurityRequirement", req_id)
    return {"id": link.id, "detail": "linked"}


@router.post("/{req_id}/controls", status_code=status.HTTP_201_CREATED)
def link_control(req_id: int, payload: ControlLinkCreate, db: Session = Depends(get_db), user: User = Depends(require_write)):
    req = db.get(CybersecurityRequirement, req_id)
    if req is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Requirement not found")
    if db.get(Control, payload.control_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Control not found")
    link = RequirementControlLink(requirement_id=req_id, control_id=payload.control_id, notes=payload.notes)
    db.add(link)
    db.commit()
    audit(db, user.email, "requirement.link_control", "CybersecurityRequirement", req_id)
    return {"id": link.id, "detail": "linked"}


def _detail(req: CybersecurityRequirement, db: Session) -> dict:
    tara = req.tara
    asset = tara.asset if tara else None
    threat = tara.threat if tara else None
    tests = list(req.test_cases)
    results = []
    for t in tests:
        results.extend(t.results)
    evidence = list(db.scalars(select(Evidence).where(Evidence.requirement_id == req.id)))
    graph = SqlGraphService(db)
    neighbors = graph.bfs("CybersecurityRequirement", req.id, max_depth=2)
    return {
        "id": req.id,
        "requirement_id": req.requirement_id,
        "title": req.title,
        "description": req.description,
        "priority": req.priority,
        "status": req.status,
        "tara": None if tara is None else {
            "id": tara.id, "reference": tara.reference, "risk_level": tara.risk_level,
            "cybersecurity_goal": tara.cybersecurity_goal,
        },
        "asset": None if asset is None else {"id": asset.id, "name": asset.name, "criticality": asset.criticality},
        "threat": None if threat is None else {"id": threat.id, "name": threat.name, "threat_type": threat.threat_type},
        "controls": [{"id": lnk.control.id, "control_id": lnk.control.control_id, "title": lnk.control.title,
                      "standard": lnk.control.standard.name} for lnk in req.controls],
        "mechanisms": [{"id": lnk.mechanism.id, "name": lnk.mechanism.name, "category": lnk.mechanism.category,
                        "notes": lnk.notes} for lnk in req.mechanisms],
        "tests": [{"id": t.id, "name": t.name, "status": t.status, "test_type": t.test_type} for t in tests],
        "test_results": [{"id": r.id, "test_case_id": r.test_case_id, "result": r.result.value,
                          "executed_at": r.executed_at.isoformat() if r.executed_at else None} for r in results],
        "evidence": [{"id": e.id, "name": e.name, "type": e.type, "status": e.status.value} for e in evidence],
        "graph_neighbors": [
            {"entity_type": n.entity_type, "entity_id": n.entity_id, "label": n.label, "depth": n.depth, "reason": n.reason}
            for n in neighbors
        ],
    }
