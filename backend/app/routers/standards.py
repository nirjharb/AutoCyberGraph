"""
Standards mapping layer.

ISO/SAE 21434, UNECE R155, UNECE R156, NIST SP 800-53 and AUTOSAR security are
represented as reference/mapping concepts. AutoCyberGraph is NOT an official
implementation of any of these and does not reproduce their text.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    AutosarMechanism,
    ComplianceMapping,
    Control,
    MechanismImplementation,
    RequirementControlLink,
    RequirementMechanismLink,
    Standard,
    User,
)
from ..schemas import (
    ComplianceMappingCreate,
    ComplianceMappingOut,
    ControlOut,
    MechanismOut,
)
from ..security import audit, get_current_user, require_write

router = APIRouter(prefix="/api", tags=["standards"])


@router.get("/standards", response_model=list[dict])
def list_standards(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rows = list(db.scalars(select(Standard)))
    return [
        {
            "id": s.id, "key": s.key, "name": s.name, "description": s.description,
            "reference_url": s.reference_url,
            "control_count": len(s.controls),
        }
        for s in rows
    ]


@router.get("/controls", response_model=list[ControlOut])
def list_controls(standard_key: str | None = None, category: str | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    q = select(Control)
    rows = list(db.scalars(q))
    if standard_key:
        std = db.scalars(select(Standard).where(Standard.key == standard_key)).first()
        rows = [c for c in rows if std and c.standard_id == std.id]
    if category:
        rows = [c for c in rows if c.category.upper() == category.upper()]
    return rows


@router.get("/controls/{control_id}/mappings")
def control_mappings(control_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    control = db.get(Control, control_id)
    if control is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Control not found")
    req_links = [{"requirement_id": lnk.requirement_id, "requirement_ref": lnk.requirement.requirement_id, "notes": lnk.notes}
                 for lnk in db.scalars(select(RequirementControlLink).where(RequirementControlLink.control_id == control_id))]
    return {
        "control": ControlOut.model_validate(control).model_dump(),
        "standard": control.standard.name,
        "requirements": req_links,
    }


@router.get("/autosar/mechanisms", response_model=list[MechanismOut])
def list_mechanisms(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return list(db.scalars(select(AutosarMechanism)))


@router.get("/autosar/mechanisms/{mechanism_id}")
def mechanism_detail(mechanism_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    mech = db.get(AutosarMechanism, mechanism_id)
    if mech is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mechanism not found")
    links = list(db.scalars(select(RequirementMechanismLink).where(
        RequirementMechanismLink.mechanism_id == mechanism_id)))
    impls = list(db.scalars(select(MechanismImplementation).where(MechanismImplementation.mechanism_id == mechanism_id)))
    return {
        "id": mech.id, "name": mech.name, "category": mech.category, "description": mech.description,
        "requirements": [{"id": lnk.requirement.id, "requirement_id": lnk.requirement.requirement_id,
                          "title": lnk.requirement.title, "notes": lnk.notes} for lnk in links],
        "implementations": [{"ecu_id": i.ecu_id, "ecu_name": i.ecu.name, "status": i.status, "notes": i.notes}
                            for i in impls],
    }


@router.get("/mappings", response_model=list[ComplianceMappingOut])
def list_mappings(
    standard: str | None = None,
    source_entity: str | None = None,
    mapping_type: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rows = list(db.scalars(select(ComplianceMapping)))
    if standard:
        rows = [r for r in rows if standard.lower() in r.standard.lower()]
    if source_entity:
        rows = [r for r in rows if r.source_entity == source_entity]
    if mapping_type:
        rows = [r for r in rows if r.mapping_type == mapping_type]
    return rows


@router.post("/mappings", response_model=ComplianceMappingOut, status_code=status.HTTP_201_CREATED)
def create_mapping(payload: ComplianceMappingCreate, db: Session = Depends(get_db), user: User = Depends(require_write)):
    mapping = ComplianceMapping(**payload.model_dump())
    db.add(mapping)
    db.commit()
    audit(db, user.email, "mapping.create", "ComplianceMapping", mapping.id, f"{mapping.standard} {mapping.control_id}")
    return mapping
