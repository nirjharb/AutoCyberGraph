"""Dashboard metrics — every metric is computed from live application data."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    ECU,
    TARA,
    Asset,
    Change,
    CybersecurityRequirement,
    Evidence,
    Release,
    SupplierSubmission,
    TestCase,
    User,
    Vehicle,
    Vulnerability,
)
from ..security import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    vehicles = list(db.scalars(select(Vehicle)))
    ecus = list(db.scalars(select(ECU)))
    taras = list(db.scalars(select(TARA)))
    reqs = list(db.scalars(select(CybersecurityRequirement)))
    vulns = list(db.scalars(select(Vulnerability)))
    tests = list(db.scalars(select(TestCase)))
    releases = list(db.scalars(select(Release)))
    changes = list(db.scalars(select(Change).order_by(Change.created_at.desc())))
    submissions = list(db.scalars(select(SupplierSubmission)))

    open_vulns = [v for v in vulns if v.status == "OPEN"]
    critical_vulns = [v for v in open_vulns if v.severity.value in ("CRITICAL", "HIGH")]
    failed_tests = [t for t in tests if t.status == "FAILED"]
    missing_evidence = [r for r in reqs if not list(db.scalars(select(Evidence).where(Evidence.requirement_id == r.id)))]
    pending_reviews = (
        [t for t in taras if t.status == "DRAFT"]
        + [r for r in reqs if r.status in ("DRAFT", "IN_REVIEW")]
        + [s for s in submissions if s.status.value in ("SUBMITTED", "IN_REVIEW")]
    )
    risk_distribution = {
        level: len([t for t in taras if t.risk_level == level])
        for level in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    }
    test_status_counts = {
        s: len([t for t in tests if t.status == s])
        for s in ("PASSED", "FAILED", "NOT_RUN", "BLOCKED")
    }
    vuln_severity_counts = {
        s: len([v for v in open_vulns if v.severity.value == s])
        for s in ("CRITICAL", "HIGH", "MEDIUM", "LOW")
    }
    release_readiness = [
        {"id": r.id, "version": r.version, "ecu_id": r.ecu_id, "status": r.status, "gate_result": r.gate_result}
        for r in releases
    ]

    return {
        "counts": {
            "vehicles": len(vehicles),
            "ecus": len(ecus),
            "assets": len(list(db.scalars(select(Asset)))),
            "tara_scenarios": len(taras),
            "requirements": len(reqs),
            "open_vulnerabilities": len(open_vulns),
            "critical_vulnerabilities": len(critical_vulns),
            "failed_tests": len(failed_tests),
            "evidence_items": len(list(db.scalars(select(Evidence)))),
            "missing_evidence": len(missing_evidence),
            "pending_reviews": len(pending_reviews),
            "releases": len(releases),
            "changes": len(changes),
        },
        "risk_distribution": risk_distribution,
        "test_status_counts": test_status_counts,
        "vuln_severity_counts": vuln_severity_counts,
        "recent_changes": [
            {"id": c.id, "entity_type": c.entity_type, "entity_id": c.entity_id,
             "change_type": c.change_type.value, "description": c.description,
             "created_at": c.created_at.isoformat() if c.created_at else None,
             "impact_level": c.impact_level}
            for c in changes[:8]
        ],
        "release_readiness": release_readiness,
        "critical_vulnerability_list": [
            {"id": v.id, "cve_id": v.cve_id, "severity": v.severity.value, "cvss_score": v.cvss_score,
             "component_id": v.component_id, "status": v.status}
            for v in critical_vulns
        ],
        "failed_test_list": [
            {"id": t.id, "name": t.name, "requirement_id": t.requirement_id}
            for t in failed_tests
        ],
        "missing_evidence_list": [
            {"id": r.id, "requirement_id": r.requirement_id, "title": r.title}
            for r in missing_evidence
        ],
    }
