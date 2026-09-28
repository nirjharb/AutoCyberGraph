"""Software components, SBOM import, vulnerability management."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    ECU,
    SBOM,
    SbomComponent,
    SoftwareComponent,
    User,
    Vehicle,
    Vulnerability,
)
from ..schemas import (
    ComponentCreate,
    ComponentOut,
    ComponentUpdate,
    SbomImportRequest,
    SbomOut,
    VulnerabilityCreate,
    VulnerabilityOut,
    VulnerabilityUpdate,
)
from ..security import audit, get_current_user, require_analysis, require_write
from ..services.sbom import SbomParseError, parse_sbom

router = APIRouter(prefix="/api", tags=["supply-chain"])


# ---------- Components ----------
@router.get("/components", response_model=list[ComponentOut])
def list_components(ecu_id: int | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    q = select(SoftwareComponent)
    if ecu_id:
        q = q.where(SoftwareComponent.ecu_id == ecu_id)
    return list(db.scalars(q))


@router.post("/components", response_model=ComponentOut, status_code=status.HTTP_201_CREATED)
def create_component(payload: ComponentCreate, db: Session = Depends(get_db), user: User = Depends(require_write)):
    if db.get(ECU, payload.ecu_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ECU not found")
    comp = SoftwareComponent(**payload.model_dump())
    db.add(comp)
    db.commit()
    audit(db, user.email, "component.create", "SoftwareComponent", comp.id, f"{comp.name} {comp.version}")
    return comp


@router.get("/components/{component_id}")
def get_component(component_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    comp = db.get(SoftwareComponent, component_id)
    if comp is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Component not found")
    vulns = list(db.scalars(select(Vulnerability).where(Vulnerability.component_id == component_id)))
    return {
        "component": ComponentOut.model_validate(comp).model_dump(),
        "ecu": {"id": comp.ecu.id, "name": comp.ecu.name, "vehicle_id": comp.ecu.vehicle_id},
        "vulnerabilities": [VulnerabilityOut.model_validate(v).model_dump() for v in vulns],
    }


@router.patch("/components/{component_id}", response_model=ComponentOut)
def update_component(component_id: int, payload: ComponentUpdate, db: Session = Depends(get_db), user: User = Depends(require_write)):
    comp = db.get(SoftwareComponent, component_id)
    if comp is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Component not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(comp, key, value)
    db.commit()
    audit(db, user.email, "component.update", "SoftwareComponent", comp.id, f"{comp.name} {comp.version}")
    return comp


# ---------- Vulnerabilities ----------
@router.get("/vulnerabilities", response_model=list[VulnerabilityOut])
def list_vulnerabilities(
    status_filter: str | None = None,
    severity: str | None = None,
    component_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(Vulnerability)
    if component_id:
        q = q.where(Vulnerability.component_id == component_id)
    rows = list(db.scalars(q))
    if status_filter:
        rows = [v for v in rows if v.status == status_filter.upper()]
    if severity:
        rows = [v for v in rows if v.severity.value == severity.upper()]
    return rows


@router.post("/vulnerabilities", response_model=VulnerabilityOut, status_code=status.HTTP_201_CREATED)
def create_vulnerability(payload: VulnerabilityCreate, db: Session = Depends(get_db), user: User = Depends(require_analysis)):
    if db.get(SoftwareComponent, payload.component_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Component not found")
    vuln = Vulnerability(**payload.model_dump())
    db.add(vuln)
    db.commit()
    audit(db, user.email, "vulnerability.create", "Vulnerability", vuln.id, vuln.cve_id)
    return vuln


@router.patch("/vulnerabilities/{vuln_id}", response_model=VulnerabilityOut)
def update_vulnerability(vuln_id: int, payload: VulnerabilityUpdate, db: Session = Depends(get_db), user: User = Depends(require_analysis)):
    vuln = db.get(Vulnerability, vuln_id)
    if vuln is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vulnerability not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(vuln, key, value)
    db.commit()
    audit(db, user.email, "vulnerability.update", "Vulnerability", vuln.id, vuln.cve_id)
    return vuln


@router.get("/vulnerabilities/{vuln_id}/trace")
def vulnerability_trace(vuln_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """CVE → Component → ECU → Vehicle (+ security context)."""
    vuln = db.get(Vulnerability, vuln_id)
    if vuln is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vulnerability not found")
    comp = vuln.component
    ecu = comp.ecu if comp else None
    vehicle = ecu.vehicle if ecu else None
    return {
        "vulnerability": VulnerabilityOut.model_validate(vuln).model_dump(),
        "component": ComponentOut.model_validate(comp).model_dump() if comp else None,
        "ecu": {"id": ecu.id, "name": ecu.name, "criticality": ecu.criticality} if ecu else None,
        "vehicle": {"id": vehicle.id, "name": vehicle.name} if vehicle else None,
    }


# ---------- SBOM ----------
@router.post("/sbom/import", response_model=SbomOut, status_code=status.HTTP_201_CREATED)
def import_sbom(payload: SbomImportRequest, db: Session = Depends(get_db), user: User = Depends(require_analysis)):
    if payload.vehicle_id is not None and db.get(Vehicle, payload.vehicle_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vehicle not found")
    if payload.ecu_id is not None and db.get(ECU, payload.ecu_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ECU not found")
    try:
        doc = parse_sbom(payload.content, payload.format)
    except SbomParseError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"SBOM parse error: {exc}") from exc
    sbom = SBOM(
        vehicle_id=payload.vehicle_id,
        ecu_id=payload.ecu_id,
        format=doc.format,
        file_name=payload.file_name[:255],
        version=doc.version,
        component_count=len(doc.entries),
    )
    db.add(sbom)
    db.flush()
    for entry in doc.entries:
        db.add(SbomComponent(
            sbom_id=sbom.id,
            name=entry.name,
            version=entry.version,
            purl=entry.purl,
            license=entry.license,
            hash=entry.hash,
            component_type=entry.component_type,
        ))
    db.commit()
    audit(db, user.email, "sbom.import", "SBOM", sbom.id, f"{doc.format} {payload.file_name} ({len(doc.entries)} components)")
    return sbom


@router.get("/sbom", response_model=list[SbomOut])
def list_sboms(ecu_id: int | None = None, vehicle_id: int | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    q = select(SBOM)
    if ecu_id:
        q = q.where(SBOM.ecu_id == ecu_id)
    if vehicle_id:
        q = q.where(SBOM.vehicle_id == vehicle_id)
    return list(db.scalars(q))


@router.get("/sbom/{sbom_id}")
def get_sbom(sbom_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    sbom = db.get(SBOM, sbom_id)
    if sbom is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "SBOM not found")
    return {
        "sbom": SbomOut.model_validate(sbom).model_dump(),
        "components": [
            {"id": c.id, "name": c.name, "version": c.version, "purl": c.purl,
             "license": c.license, "hash": c.hash, "component_type": c.component_type}
            for c in sbom.components
        ],
    }
