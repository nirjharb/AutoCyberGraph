"""Vehicle architecture: vehicles, ECUs, networks, ECU security context."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    ECU,
    TARA,
    Asset,
    AutosarMechanism,
    CybersecurityRequirement,
    MechanismImplementation,
    Network,
    Release,
    SoftwareComponent,
    User,
    Vehicle,
    Vulnerability,
)
from ..schemas import (
    ECUCreate,
    ECUOut,
    NetworkCreate,
    NetworkOut,
    VehicleCreate,
    VehicleOut,
)
from ..security import audit, get_current_user, require_write

router = APIRouter(prefix="/api", tags=["architecture"])


# ---------- Vehicles ----------
@router.get("/vehicles", response_model=list[VehicleOut])
def list_vehicles(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return list(db.scalars(select(Vehicle)))


@router.post("/vehicles", response_model=VehicleOut, status_code=status.HTTP_201_CREATED)
def create_vehicle(payload: VehicleCreate, db: Session = Depends(get_db), user: User = Depends(require_write)):
    vehicle = Vehicle(**payload.model_dump())
    db.add(vehicle)
    db.commit()
    audit(db, user.email, "vehicle.create", "Vehicle", vehicle.id, vehicle.name)
    return vehicle


@router.get("/vehicles/{vehicle_id}", response_model=VehicleOut)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    vehicle = db.get(Vehicle, vehicle_id)
    if vehicle is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vehicle not found")
    return vehicle


@router.get("/vehicles/{vehicle_id}/architecture")
def vehicle_architecture(vehicle_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    vehicle = db.get(Vehicle, vehicle_id)
    if vehicle is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vehicle not found")
    ecus = list(db.scalars(select(ECU).where(ECU.vehicle_id == vehicle_id)))
    networks = list(db.scalars(select(Network).where(Network.vehicle_id == vehicle_id)))
    return {
        "vehicle": VehicleOut.model_validate(vehicle).model_dump(),
        "ecus": [ECUOut.model_validate(e).model_dump() for e in ecus],
        "networks": [NetworkOut.model_validate(n).model_dump() for n in networks],
    }


# ---------- ECUs ----------
@router.get("/ecus", response_model=list[ECUOut])
def list_ecus(vehicle_id: int | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    q = select(ECU)
    if vehicle_id:
        q = q.where(ECU.vehicle_id == vehicle_id)
    return list(db.scalars(q))


@router.post("/ecus", response_model=ECUOut, status_code=status.HTTP_201_CREATED)
def create_ecu(payload: ECUCreate, db: Session = Depends(get_db), user: User = Depends(require_write)):
    if db.get(Vehicle, payload.vehicle_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vehicle not found")
    ecu = ECU(**payload.model_dump())
    db.add(ecu)
    db.commit()
    audit(db, user.email, "ecu.create", "ECU", ecu.id, ecu.name)
    return ecu


@router.get("/ecus/{ecu_id}", response_model=ECUOut)
def get_ecu(ecu_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    ecu = db.get(ECU, ecu_id)
    if ecu is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ECU not found")
    return ecu


@router.get("/ecus/{ecu_id}/security-context")
def ecu_security_context(ecu_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Everything security-relevant about one ECU — used by the demo workflow."""
    ecu = db.get(ECU, ecu_id)
    if ecu is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ECU not found")
    assets = list(db.scalars(select(Asset).where(Asset.ecu_id == ecu_id)))
    asset_ids = [a.id for a in assets]
    taras = list(db.scalars(select(TARA).where(TARA.asset_id.in_(asset_ids)))) if asset_ids else []
    tara_ids = [t.id for t in taras]
    reqs = list(db.scalars(select(CybersecurityRequirement).where(CybersecurityRequirement.tara_id.in_(tara_ids)))) if tara_ids else []
    components = list(db.scalars(select(SoftwareComponent).where(SoftwareComponent.ecu_id == ecu_id)))
    comp_ids = [c.id for c in components]
    vulns = list(db.scalars(select(Vulnerability).where(Vulnerability.component_id.in_(comp_ids)))) if comp_ids else []
    releases = list(db.scalars(select(Release).where(Release.ecu_id == ecu_id)))
    impls = list(db.scalars(select(MechanismImplementation).where(MechanismImplementation.ecu_id == ecu_id)))
    mechanisms = []
    for impl in impls:
        mech = db.get(AutosarMechanism, impl.mechanism_id)
        if mech:
            mechanisms.append({"id": mech.id, "name": mech.name, "category": mech.category,
                               "status": impl.status, "notes": impl.notes})
    return {
        "ecu": ECUOut.model_validate(ecu).model_dump(),
        "vehicle": VehicleOut.model_validate(ecu.vehicle).model_dump(),
        "assets": [{"id": a.id, "name": a.name, "type": a.type, "criticality": a.criticality} for a in assets],
        "taras": [{"id": t.id, "reference": t.reference, "risk_level": t.risk_level,
                   "cybersecurity_goal": t.cybersecurity_goal, "status": t.status} for t in taras],
        "requirements": [{"id": r.id, "requirement_id": r.requirement_id, "title": r.title,
                          "status": r.status, "priority": r.priority} for r in reqs],
        "components": [{"id": c.id, "name": c.name, "version": c.version, "supplier": c.supplier} for c in components],
        "vulnerabilities": [{"id": v.id, "cve_id": v.cve_id, "severity": v.severity.value,
                             "status": v.status, "cvss_score": v.cvss_score} for v in vulns],
        "releases": [{"id": r.id, "version": r.version, "status": r.status, "gate_result": r.gate_result} for r in releases],
        "autosar_mechanisms": mechanisms,
    }


# ---------- Networks ----------
@router.get("/networks", response_model=list[NetworkOut])
def list_networks(vehicle_id: int | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    q = select(Network)
    if vehicle_id:
        q = q.where(Network.vehicle_id == vehicle_id)
    return list(db.scalars(q))


@router.post("/networks", response_model=NetworkOut, status_code=status.HTTP_201_CREATED)
def create_network(payload: NetworkCreate, db: Session = Depends(get_db), user: User = Depends(require_write)):
    if db.get(Vehicle, payload.vehicle_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vehicle not found")
    network = Network(**payload.model_dump())
    db.add(network)
    db.commit()
    audit(db, user.email, "network.create", "Network", network.id, network.name)
    return network
