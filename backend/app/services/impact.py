"""
Change Impact Engine — the core differentiator.

Traverses the traceability graph from the changed entity and returns affected
cybersecurity artifacts with per-object reasons derived from actual graph paths.
No arbitrary guessing: an object is affected iff it is reachable in the graph.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..graph import SqlGraphService, resolve_entity_type
from ..models import (
    ECU,
    TARA,
    Change,
    ChangeType,
    ImpactLevel,
    Severity,
    Vulnerability,
)

# Which traversed types matter for the report buckets
REPORT_BUCKETS = {
    "ECU": "ecus",
    "SoftwareComponent": "software_components",
    "Asset": "assets",
    "Threat": "threats",
    "TARA": "tara",
    "CybersecurityRequirement": "requirements",
    "Control": "controls",
    "AutosarMechanism": "autosar_mechanisms",
    "TestCase": "tests",
    "TestResult": "test_results",
    "Evidence": "evidence",
    "Release": "releases",
    "Vulnerability": "vulnerabilities",
    "SBOM": "sboms",
    "SbomComponent": "sbom_components",
    "Vehicle": "vehicles",
    "Network": "networks",
}

CHANGE_WEIGHT = {
    ChangeType.CRYPTO_LIBRARY_CHANGE: 3,
    ChangeType.VULNERABILITY: 3,
    ChangeType.AUTOSAR_CONFIG_CHANGE: 2,
    ChangeType.NETWORK_MESSAGE_CHANGE: 2,
    ChangeType.SOFTWARE_CHANGE: 2,
    ChangeType.ECU_CHANGE: 2,
    ChangeType.REQUIREMENT_CHANGE: 2,
    ChangeType.TARA_CHANGE: 2,
    ChangeType.SBOM_CHANGE: 1,
}


def compute_impact(db: Session, change: Change) -> dict:
    entity_type = resolve_entity_type(change.entity_type)
    graph = SqlGraphService(db)
    nodes = graph.bfs(entity_type, change.entity_id, max_depth=6)

    affected: dict[str, list[dict]] = {}
    for node in nodes:
        bucket = REPORT_BUCKETS.get(node.entity_type)
        if not bucket:
            continue
        affected.setdefault(bucket, []).append(
            {
                "entity_type": node.entity_type,
                "entity_id": node.entity_id,
                "label": node.label,
                "depth": node.depth,
                "reason": node.reason or "connected in traceability graph",
                "path": node.via,
            }
        )

    summary = {bucket: len(items) for bucket, items in affected.items()}
    impact_level = _score(change, affected, db)
    rationale = _rationale(change, affected, impact_level)
    actions = _recommend(change, affected, impact_level)

    report = [
        {"bucket": bucket, "count": len(items), "items": items[:50]}
        for bucket, items in sorted(affected.items())
    ]
    return {
        "impact_level": impact_level,
        "affected": affected,
        "summary": summary,
        "recommended_actions": actions,
        "rationale": rationale,
        "report": report,
    }


def _score(change: Change, affected: dict[str, list[dict]], db: Session) -> ImpactLevel:
    score = CHANGE_WEIGHT.get(change.change_type, 1)

    # Elevate for high-risk TARA reachability
    for item in affected.get("tara", []):
        tara = db.get(TARA, item["entity_id"])
        if tara and tara.risk_level in ("HIGH", "CRITICAL"):
            score += 1
            break

    # Elevate for open critical/high vulnerabilities in reachability
    for item in affected.get("vulnerabilities", []):
        vuln = db.get(Vulnerability, item["entity_id"])
        if vuln and vuln.status == "OPEN" and vuln.severity in (Severity.CRITICAL, Severity.HIGH):
            score += 2
            break

    # Releases in scope make it more serious
    if affected.get("releases"):
        score += 1
    # Safety-relevant ECU (criticality)
    for item in affected.get("ecus", []):
        ecu = db.get(ECU, item["entity_id"])
        if ecu and ecu.criticality == "HIGH":
            score += 1
            break

    if score >= 8:
        return ImpactLevel.CRITICAL
    if score >= 5:
        return ImpactLevel.HIGH
    if score >= 3:
        return ImpactLevel.MEDIUM
    return ImpactLevel.LOW


def _rationale(change: Change, affected: dict[str, list[dict]], level: ImpactLevel) -> list[str]:
    lines = [
        f"Change type {change.change_type.value} starts at {change.entity_type}:{change.entity_id}.",
        "Affected objects are exactly those reachable via traceability graph relationships; "
        "each object's reason field shows the graph path used.",
    ]
    lines.append(
        "Reachable: "
        + ", ".join(f"{count} {bucket}" for bucket, count in sorted(affected.items()))
        + "."
    )
    lines.append(f"Impact level {level.value} derived from change weight, risk/TARA levels, open vulnerabilities, ECU criticality and release exposure.")
    return lines


def _recommend(change: Change, affected: dict[str, list[dict]], level: ImpactLevel) -> list[str]:
    actions: list[str] = []
    if affected.get("tara"):
        actions.append("Re-review affected TARA scenarios and confirm risk levels are still valid.")
    if affected.get("requirements"):
        actions.append("Confirm affected cybersecurity requirements remain correct and re-approve if content changed.")
    if affected.get("tests"):
        actions.append("Re-execute affected test cases (especially security tests) on the changed configuration.")
    if affected.get("autosar_mechanisms"):
        actions.append("Verify AUTOSAR security mechanism configurations (e.g. SecOC freshness, CSM keys) against the change.")
    if affected.get("vulnerabilities"):
        actions.append("Re-assess vulnerabilities on the changed component; update remediation status.")
    if affected.get("evidence"):
        actions.append("Regenerate or re-validate evidence artifacts that were produced on the previous configuration.")
    if affected.get("releases"):
        actions.append("Run the Cybersecurity Release Gate for affected releases before approval.")
    if affected.get("sboms") or affected.get("software_components"):
        actions.append("Publish an updated SBOM and reconcile component versions/hashes.")
    if level in (ImpactLevel.CRITICAL, ImpactLevel.HIGH):
        actions.append("Treat as a security-relevant change: record a security impact assessment (R156-style workflow).")
    return actions
