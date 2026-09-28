"""
Cybersecurity Release Gate.

Deterministic checks over the release scope (ECU → vehicle). The result is
PASS / REVIEW / HOLD with individual checks and human-readable reasons —
deliberately NOT a composite "security score".
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (
    SBOM,
    TARA,
    Change,
    CybersecurityRequirement,
    Evidence,
    EvidenceStatus,
    Release,
    ReleaseGateResult,
    RequirementMechanismLink,
    Severity,
    TestCase,
    TestResult,
    TestStatus,
    Vulnerability,
)
from ..schemas import GateCheck, GateEvaluation

BLOCKING = "BLOCKING"
WARNING = "WARNING"


def evaluate_release(db: Session, release: Release) -> GateEvaluation:
    checks: list[GateCheck] = []
    reasons: list[str] = []

    ecu = release.ecu

    # ---- Scope: artifacts connected to this ECU -------------------------
    assets = list(ecu.assets) if ecu else []
    asset_ids = [a.id for a in assets]
    taras = list(db.scalars(select(TARA).where(TARA.asset_id.in_(asset_ids)))) if asset_ids else []
    tara_ids = [t.id for t in taras]
    reqs = list(db.scalars(select(CybersecurityRequirement).where(CybersecurityRequirement.tara_id.in_(tara_ids)))) if tara_ids else []
    req_ids = [r.id for r in reqs]
    tests = list(db.scalars(select(TestCase).where(TestCase.requirement_id.in_(req_ids)))) if req_ids else []
    test_ids = [t.id for t in tests]
    results = list(db.scalars(select(TestResult).where(TestResult.test_case_id.in_(test_ids)))) if test_ids else []
    components = list(ecu.components) if ecu else []
    comp_ids = [c.id for c in components]
    vulns = list(db.scalars(select(Vulnerability).where(Vulnerability.component_id.in_(comp_ids)))) if comp_ids else []
    sboms = list(db.scalars(select(SBOM).where(SBOM.ecu_id == release.ecu_id)))
    evidences = []
    if req_ids or test_ids:
        q = select(Evidence).where(
            (Evidence.requirement_id.in_(req_ids))
            | (Evidence.release_id == release.id)
            | (Evidence.tara_id.in_(tara_ids))
        )
        evidences = list(db.scalars(q))

    # ---- 1. TARA reviewed ----------------------------------------------
    unreviewed = [t for t in taras if t.status not in ("REVIEWED", "APPROVED")]
    ok = bool(taras) and not unreviewed
    checks.append(GateCheck(
        key="tara_reviewed",
        label="TARA reviewed",
        passed=ok,
        severity=BLOCKING if not taras else WARNING,
        detail=(
            f"{len(taras)} TARA scenario(s) in scope, all reviewed/approved."
            if ok else
            (f"No TARA scenarios found for ECU {ecu.name if ecu else '?'}."
             if not taras else
             f"{len(unreviewed)} TARA scenario(s) not reviewed: "
             + ", ".join(t.reference for t in unreviewed[:5]))
        ),
    ))
    if not ok:
        reasons.append("TARA not fully reviewed for this ECU.")

    # ---- 2. Requirements traced ----------------------------------------
    untraced = []
    for r in reqs:
        has_test = any(t.requirement_id == r.id for t in tests)
        has_ev = bool(db.scalars(select(Evidence).where(Evidence.requirement_id == r.id).limit(1)))
        if not (has_test and has_ev):
            untraced.append(r)
    ok = bool(reqs) and not untraced
    checks.append(GateCheck(
        key="requirements_traced",
        label="Requirements traced (test + evidence)",
        passed=ok,
        severity=BLOCKING if not reqs else WARNING,
        detail=(
            f"All {len(reqs)} requirement(s) have tests and evidence."
            if ok else
            ("No cybersecurity requirements derived for this ECU's TARA scope."
             if not reqs else
             f"{len(untraced)} requirement(s) missing test and/or evidence: "
             + ", ".join(r.requirement_id for r in untraced[:5]))
        ),
    ))
    if not ok:
        reasons.append("Requirements are not fully traced to tests and evidence.")

    # ---- 3. Tests completed --------------------------------------------
    latest_by_test: dict[int, TestResult] = {}
    for tr in sorted(results, key=lambda r: r.executed_at or dt.datetime.min):
        latest_by_test[tr.test_case_id] = tr
    not_run = [t for t in tests if t.id not in latest_by_test]
    failed_latest = [tr for tr in latest_by_test.values() if tr.result == TestStatus.FAILED]
    ok = bool(tests) and not not_run and not failed_latest
    checks.append(GateCheck(
        key="tests_completed",
        label="Tests completed and passing",
        passed=ok,
        severity=BLOCKING if failed_latest else WARNING,
        detail=(
            f"All {len(tests)} test case(s) executed, latest results passing."
            if ok else
            f"{len(failed_latest)} failing, {len(not_run)} not executed (of {len(tests)} test cases)."
        ),
    ))
    if failed_latest:
        reasons.append(f"{len(failed_latest)} test case(s) failing.")
    elif not_run:
        reasons.append(f"{len(not_run)} test case(s) not executed.")

    # ---- 4. Critical vulnerabilities resolved --------------------------
    open_critical = [v for v in vulns if v.status == "OPEN" and v.severity in (Severity.CRITICAL, Severity.HIGH)]
    open_all = [v for v in vulns if v.status == "OPEN"]
    ok = not open_critical
    checks.append(GateCheck(
        key="vulns_resolved",
        label="Critical/high vulnerabilities resolved",
        passed=ok,
        severity=BLOCKING,
        detail=(
            f"No open critical/high vulnerabilities ({len(open_all)} open total)."
            if ok else
            f"{len(open_critical)} open critical/high vulnerability(ies): "
            + ", ".join(v.cve_id for v in open_critical[:5])
        ),
    ))
    if not ok:
        reasons.append(f"Open critical/high vulnerabilities: {', '.join(v.cve_id for v in open_critical[:5])}.")

    # ---- 5. SBOM available ---------------------------------------------
    ok = bool(sboms)
    checks.append(GateCheck(
        key="sbom_available",
        label="SBOM available",
        passed=ok,
        severity=BLOCKING,
        detail=(f"{len(sboms)} SBOM document(s) registered for this ECU." if ok else "No SBOM registered for this ECU."),
    ))
    if not ok:
        reasons.append("No SBOM registered for this ECU.")

    # ---- 6. AUTOSAR security mappings present --------------------------
    mech_links = []
    if req_ids:
        mech_links = list(db.scalars(select(RequirementMechanismLink).where(
            RequirementMechanismLink.requirement_id.in_(req_ids))))
    ok = bool(reqs) and len({lnk.requirement_id for lnk in mech_links}) == len(reqs)
    checks.append(GateCheck(
        key="autosar_mappings",
        label="AUTOSAR security mappings present",
        passed=ok,
        severity=WARNING,
        detail=(
            f"All {len(reqs)} requirement(s) mapped to AUTOSAR security mechanisms."
            if ok else
            f"{len(reqs) - len({lnk.requirement_id for lnk in mech_links})} requirement(s) without AUTOSAR mechanism mapping."
        ),
    ))
    if not ok:
        reasons.append("Some requirements lack AUTOSAR security mechanism mappings.")

    # ---- 7. Required evidence available --------------------------------
    approved_ev = [e for e in evidences if e.status == EvidenceStatus.APPROVED]
    ok = bool(evidences) and len(approved_ev) >= max(1, len(reqs) // 2)
    checks.append(GateCheck(
        key="evidence_available",
        label="Required evidence available",
        passed=ok,
        severity=WARNING,
        detail=(
            f"{len(evidences)} evidence item(s), {len(approved_ev)} approved."
            if evidences else "No evidence recorded for this release scope."
        ),
    ))
    if not ok:
        reasons.append("Insufficient approved evidence for the release scope.")

    # ---- 8. Security impact analysis complete --------------------------
    scope_comp_ids = set(comp_ids)
    unanalysed = []
    for ch in db.scalars(select(Change)):
        if ch.analyzed_at is None:
            if ch.entity_type in ("SoftwareComponent", "Component") and ch.entity_id in scope_comp_ids:
                unanalysed.append(ch)
            elif ch.entity_type == "ECU" and ecu and ch.entity_id == ecu.id:
                unanalysed.append(ch)
    ok = not unanalysed
    checks.append(GateCheck(
        key="security_impact",
        label="Security-impact analysis complete",
        passed=ok,
        severity=BLOCKING,
        detail=(
            "All recorded changes have a completed impact analysis."
            if ok else
            f"{len(unanalysed)} change(s) without impact analysis: #"
            + ", ".join(str(c.id) for c in unanalysed[:5])
        ),
    ))
    if not ok:
        reasons.append(f"{len(unanalysed)} change(s) missing change-impact analysis.")

    # ---- Result aggregation --------------------------------------------
    blocking_failed = [c for c in checks if not c.passed and c.severity == BLOCKING]
    warning_failed = [c for c in checks if not c.passed and c.severity == WARNING]
    if blocking_failed:
        result = ReleaseGateResult.HOLD
    elif warning_failed:
        result = ReleaseGateResult.REVIEW
    else:
        result = ReleaseGateResult.PASS

    return GateEvaluation(
        release_id=release.id,
        result=result,
        checks=checks,
        reasons=reasons or ["All cybersecurity release gate checks passed."],
    )
