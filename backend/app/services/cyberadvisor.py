"""
CyberAdvisor — AI assistant interface, grounded strictly in application data.

MVP backend: deterministic intent engine over live DB queries (ADR-007).
An `AdvisorBackend` protocol allows an LLM backend later (AI_API_KEY), but the
grounding contract is enforced around ANY backend:

- answers cite real entity IDs / links
- if the system cannot determine an answer from data:
      "Insufficient evidence in the project database."
- never invent compliance conclusions
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models as m

INSUFFICIENT = "Insufficient evidence in the project database."


@dataclass
class AdvisorResponse:
    intent: str
    answer: str
    data: list[dict] | dict = field(default_factory=list)
    links: list[dict] = field(default_factory=list)
    grounded: bool = True


class AdvisorBackend(Protocol):
    def answer(self, question: str, db: Session) -> AdvisorResponse: ...


def _find_by_name(db: Session, model, text: str, *name_cols):
    for col_name in name_cols:
        col = getattr(model, col_name)
        for obj in db.scalars(select(model).where(col.ilike(f"%{text}%"))):
            return obj
    return None


class RuleEngineBackend:
    """Deterministic query engine over the domain model."""

    def answer(self, question: str, db: Session) -> AdvisorResponse:
        q = question.lower().strip()
        handlers = [
            (self._is_missing_evidence, self._missing_evidence),
            (self._is_change_impact, self._change_impact),
            (self._is_vuln_scope, self._vuln_scope),
            (self._is_tara_for, self._tara_for),
            (self._is_mechanisms_for, self._mechanisms_for),
            (self._is_release_gate, self._release_gate),
            (self._is_critical_vulns, self._critical_vulns),
            (self._is_failed_tests, self._failed_tests),
            (self._is_missing_tests, self._missing_tests),
            (self._is_release_readiness, self._release_readiness),
            (self._is_trace_req, self._trace_req),
        ]
        for matcher, handler in handlers:
            if matcher(q):
                return handler(q, db)
        return AdvisorResponse(
            intent="unknown",
            answer=INSUFFICIENT + " I could not map this question to a supported query over the project data. "
            "Try asking about missing evidence, change impact, vulnerabilities, TARA scenarios, AUTOSAR mechanisms, "
            "release gates, failed tests, or release readiness.",
            grounded=True,
        )

    # -- intent matchers ---------------------------------------------------
    @staticmethod
    def _is_missing_evidence(q: str) -> bool:
        return ("missing evidence" in q or "without evidence" in q or "evidence missing" in q
                or ("evidence" in q and "which" in q and "requirement" in q))

    @staticmethod
    def _is_change_impact(q: str) -> bool:
        return ("what happens if" in q or "change impact" in q or "impact of" in q
                or ("changes" in q and ("if" in q or "impact" in q or "affected" in q))
                or "affected by" in q)

    @staticmethod
    def _is_vuln_scope(q: str) -> bool:
        return "vulnerabilit" in q and ("affect" in q or "which" in q)

    @staticmethod
    def _is_tara_for(q: str) -> bool:
        return "tara" in q and ("connected" in q or "which" in q or "for" in q or "scenario" in q)

    @staticmethod
    def _is_mechanisms_for(q: str) -> bool:
        return ("mechanism" in q or "secoc" in q or "autosar" in q) and ("mitigate" in q or "which" in q or "requirement" in q)

    @staticmethod
    def _is_release_gate(q: str) -> bool:
        return ("release gate" in q or "pass" in q or "gate" in q) and "release" in q

    @staticmethod
    def _is_critical_vulns(q: str) -> bool:
        return ("critical" in q and "vulnerabilit" in q) or "open vulnerabilit" in q

    @staticmethod
    def _is_failed_tests(q: str) -> bool:
        return "failed test" in q or "failing test" in q or ("test" in q and "fail" in q)

    @staticmethod
    def _is_missing_tests(q: str) -> bool:
        return "missing test" in q or ("requirement" in q and "test" in q and "missing" in q)

    @staticmethod
    def _is_release_readiness(q: str) -> bool:
        return "release readiness" in q or "ready for release" in q or "releases" in q and "ready" in q

    @staticmethod
    def _is_trace_req(q: str) -> bool:
        return "trace" in q or "cs-req" in q or "cs_req" in q

    # -- handlers ----------------------------------------------------------
    def _missing_evidence(self, q: str, db: Session) -> AdvisorResponse:
        reqs = list(db.scalars(select(m.CybersecurityRequirement)))
        missing = []
        for r in reqs:
            ev = db.scalars(select(m.Evidence).where(m.Evidence.requirement_id == r.id)).first()
            if ev is None:
                missing.append(r)
        if not reqs:
            return AdvisorResponse("missing_evidence", INSUFFICIENT)
        if not missing:
            return AdvisorResponse(
                "missing_evidence",
                f"All {len(reqs)} cybersecurity requirements have at least one linked evidence item.",
                data=[{"requirement": r.requirement_id, "title": r.title} for r in reqs],
                links=[{"type": "requirement", "id": r.id} for r in reqs],
            )
        return AdvisorResponse(
            "missing_evidence",
            f"{len(missing)} of {len(reqs)} cybersecurity requirements are missing evidence: "
            + ", ".join(r.requirement_id for r in missing),
            data=[{"requirement": r.requirement_id, "title": r.title, "id": r.id} for r in missing],
            links=[{"type": "requirement", "id": r.id} for r in missing],
        )

    def _change_impact(self, q: str, db: Session) -> AdvisorResponse:
        from .impact import compute_impact  # local import to avoid cycle

        entity, entity_type, entity_id = self._resolve_entity(q, db)
        if entity is None:
            return AdvisorResponse("change_impact", INSUFFICIENT)
        change = m.Change(
            entity_type=entity_type,
            entity_id=entity_id,
            change_type=m.ChangeType.SOFTWARE_CHANGE,
            description="CyAdvisor simulated change-impact query",
        )
        result = compute_impact(db, change)
        summary = result["summary"]
        parts = [f"{count} {bucket}" for bucket, count in sorted(summary.items())]
        label = getattr(entity, "name", None) or getattr(entity, "requirement_id", f"{entity_type}:{entity_id}")
        return AdvisorResponse(
            "change_impact",
            f"A change to {label} ({entity_type}:{entity_id}) can affect: "
            + (", ".join(parts) if parts else "nothing else in the current graph")
            + f". Impact level: {result['impact_level'].value}. Each affected object is listed with its graph path in the data.",
            data=result["affected"],
            links=[{"type": entity_type, "id": entity_id}],
        )

    def _vuln_scope(self, q: str, db: Session) -> AdvisorResponse:
        # "which vulnerabilities affect ADAS ECU" / "vulnerabilities in crypto"
        scope_obj = self._match_named(q, db, [m.ECU, m.SoftwareComponent, m.Vehicle])
        vulns = list(db.scalars(select(m.Vulnerability)))
        if scope_obj is not None and isinstance(scope_obj, m.ECU):
            comp_ids = [c.id for c in scope_obj.components]
            vulns = [v for v in vulns if v.component_id in comp_ids]
            scope_label = scope_obj.name
        elif scope_obj is not None and isinstance(scope_obj, m.SoftwareComponent):
            vulns = [v for v in vulns if v.component_id == scope_obj.id]
            scope_label = scope_obj.name
        elif scope_obj is not None and isinstance(scope_obj, m.Vehicle):
            comp_ids = [c.id for e in scope_obj.ecus for c in e.components]
            vulns = [v for v in vulns if v.component_id in comp_ids]
            scope_label = scope_obj.name
        else:
            scope_label = "the project"
        if not vulns:
            return AdvisorResponse("vuln_scope", f"No vulnerabilities recorded for {scope_label}." if scope_obj else INSUFFICIENT)
        return AdvisorResponse(
            "vuln_scope",
            f"{len(vulns)} vulnerability(ies) recorded for {scope_label}: "
            + ", ".join(f"{v.cve_id} ({v.severity.value}, {v.status})" for v in vulns),
            data=[{"id": v.id, "cve": v.cve_id, "severity": v.severity.value, "status": v.status,
                   "component_id": v.component_id} for v in vulns],
            links=[{"type": "Vulnerability", "id": v.id} for v in vulns],
        )

    def _tara_for(self, q: str, db: Session) -> AdvisorResponse:
        scope_obj = self._match_named(q, db, [m.ECU, m.Asset, m.Vehicle, m.Threat])
        taras = list(db.scalars(select(m.TARA)))
        label = "the project"
        if isinstance(scope_obj, m.Asset):
            taras = [t for t in taras if t.asset_id == scope_obj.id]
            label = scope_obj.name
        elif isinstance(scope_obj, m.ECU):
            asset_ids = [a.id for a in scope_obj.assets]
            taras = [t for t in taras if t.asset_id in asset_ids]
            label = scope_obj.name
        elif isinstance(scope_obj, m.Vehicle):
            asset_ids = [a.id for e in scope_obj.ecus for a in e.assets]
            taras = [t for t in taras if t.asset_id in asset_ids]
            label = scope_obj.name
        elif isinstance(scope_obj, m.Threat):
            taras = [t for t in taras if t.threat_id == scope_obj.id]
            label = scope_obj.name
        if not taras:
            return AdvisorResponse("tara_for", f"No TARA scenarios found for {label}." if scope_obj else INSUFFICIENT)
        return AdvisorResponse(
            "tara_for",
            f"{len(taras)} TARA scenario(s) connected to {label}: "
            + ", ".join(f"{t.reference} ({t.risk_level})" for t in taras),
            data=[{"id": t.id, "reference": t.reference, "risk_level": t.risk_level,
                   "cybersecurity_goal": t.cybersecurity_goal} for t in taras],
            links=[{"type": "TARA", "id": t.id} for t in taras],
        )

    def _mechanisms_for(self, q: str, db: Session) -> AdvisorResponse:
        req = self._match_named(q, db, [m.CybersecurityRequirement])
        if req is None:
            # try requirement id pattern CS-REQ-017
            match = re.search(r"(cs[-_ ]?req[-_ ]?\d+)", q, re.I)
            if match:
                rid = match.group(1).upper().replace("_", "-").replace(" ", "-")
                req = db.scalars(select(m.CybersecurityRequirement).where(m.CybersecurityRequirement.requirement_id == rid)).first()
        if req is None:
            mechs = list(db.scalars(select(m.AutosarMechanism)))
            return AdvisorResponse(
                "mechanisms_for",
                "Which requirement do you mean? The project has these AUTOSAR security mechanisms: "
                + ", ".join(x.name for x in mechs),
                data=[{"id": x.id, "name": x.name} for x in mechs],
                links=[{"type": "AutosarMechanism", "id": x.id} for x in mechs],
            )
        links = list(req.mechanisms)
        if not links:
            return AdvisorResponse(
                "mechanisms_for",
                f"No AUTOSAR security mechanism is currently mapped to {req.requirement_id} ({req.title}).",
                links=[{"type": "requirement", "id": req.id}],
            )
        names = [link.mechanism.name for link in links]
        return AdvisorResponse(
            "mechanisms_for",
            f"{req.requirement_id} is mitigated by: " + ", ".join(names) + ".",
            data=[{"mechanism": link.mechanism.name, "category": link.mechanism.category, "notes": link.notes} for link in links],
            links=[{"type": "requirement", "id": req.id}] + [{"type": "AutosarMechanism", "id": link.mechanism_id} for link in links],
        )

    def _release_gate(self, q: str, db: Session) -> AdvisorResponse:
        from .release_gate import evaluate_release

        releases = list(db.scalars(select(m.Release)))
        if not releases:
            return AdvisorResponse("release_gate", INSUFFICIENT)
        release = self._match_named(q, db, [m.Release]) or releases[-1]
        evaluation = evaluate_release(db, release)
        return AdvisorResponse(
            "release_gate",
            f"Release {release.version} (release #{release.id}) evaluates to {evaluation.result.value}: "
            + " ".join(evaluation.reasons)
            + " Blocking failures: "
            + ("; ".join(f"{c.label}: {c.detail}" for c in evaluation.checks if not c.passed and c.severity == "BLOCKING") or "none"),
            data=[c.model_dump() for c in evaluation.checks],
            links=[{"type": "Release", "id": release.id}],
        )

    def _critical_vulns(self, q: str, db: Session) -> AdvisorResponse:
        vulns = [v for v in db.scalars(select(m.Vulnerability))
                 if v.status == "OPEN" and v.severity in (m.Severity.CRITICAL, m.Severity.HIGH)]
        if not vulns:
            return AdvisorResponse("critical_vulns", "No open critical/high vulnerabilities are recorded in the project database.")
        return AdvisorResponse(
            "critical_vulns",
            f"{len(vulns)} open critical/high vulnerability(ies): "
            + ", ".join(f"{v.cve_id} (CVSS {v.cvss_score}, {v.severity.value})" for v in vulns),
            data=[{"id": v.id, "cve": v.cve_id, "cvss": v.cvss_score, "status": v.status} for v in vulns],
            links=[{"type": "Vulnerability", "id": v.id} for v in vulns],
        )

    def _failed_tests(self, q: str, db: Session) -> AdvisorResponse:
        failed = [t for t in db.scalars(select(m.TestCase)) if t.status == "FAILED"]
        latest_failed = [r for r in db.scalars(select(m.TestResult)) if r.result == m.TestStatus.FAILED]
        if not failed and not latest_failed:
            return AdvisorResponse("failed_tests", "No failed tests are recorded in the project database.")
        labels = [t.name for t in failed] or [f"test case #{r.test_case_id}" for r in latest_failed]
        return AdvisorResponse(
            "failed_tests",
            f"{len(labels)} failed test(s): " + ", ".join(labels[:10]),
            data=[{"id": t.id, "name": t.name, "requirement_id": t.requirement_id} for t in failed],
            links=[{"type": "TestCase", "id": t.id} for t in failed],
        )

    def _missing_tests(self, q: str, db: Session) -> AdvisorResponse:
        reqs = list(db.scalars(select(m.CybersecurityRequirement)))
        missing = [r for r in reqs if not r.test_cases]
        if not reqs:
            return AdvisorResponse("missing_tests", INSUFFICIENT)
        if not missing:
            return AdvisorResponse("missing_tests", f"All {len(reqs)} requirements have at least one test case.")
        return AdvisorResponse(
            "missing_tests",
            f"{len(missing)} requirement(s) have no test case: " + ", ".join(r.requirement_id for r in missing),
            data=[{"id": r.id, "requirement": r.requirement_id, "title": r.title} for r in missing],
            links=[{"type": "requirement", "id": r.id} for r in missing],
        )

    def _release_readiness(self, q: str, db: Session) -> AdvisorResponse:
        releases = list(db.scalars(select(m.Release)))
        if not releases:
            return AdvisorResponse("release_readiness", INSUFFICIENT)
        rows = [
            {"id": r.id, "version": r.version, "status": r.status, "gate_result": r.gate_result}
            for r in releases
        ]
        summary = "; ".join(f"#{r['id']} v{r['version']}: gate={r['gate_result'] or 'not evaluated'}" for r in rows)
        return AdvisorResponse("release_readiness", f"Release readiness overview: {summary}", data=rows,
                               links=[{"type": "Release", "id": r.id} for r in releases])

    def _trace_req(self, q: str, db: Session) -> AdvisorResponse:
        req = self._match_named(q, db, [m.CybersecurityRequirement])
        if req is None:
            match = re.search(r"(cs[-_ ]?req[-_ ]?\d+)", q, re.I)
            if match:
                rid = match.group(1).upper().replace("_", "-").replace(" ", "-")
                req = db.scalars(select(m.CybersecurityRequirement).where(m.CybersecurityRequirement.requirement_id == rid)).first()
        if req is None:
            return AdvisorResponse("trace_requirement", INSUFFICIENT)
        links = {
            "TARA": req.tara is not None,
            "Asset": req.tara is not None and req.tara.asset is not None,
            "AUTOSAR mechanism": len(req.mechanisms) > 0,
            "Control": len(req.controls) > 0,
            "Test": len(req.test_cases) > 0,
            "Evidence": db.scalars(select(m.Evidence).where(m.Evidence.requirement_id == req.id)).first() is not None,
        }
        missing = [k for k, v in links.items() if not v]
        status_line = ", ".join(("✓ " if v else "✗ ") + k for k, v in links.items())
        return AdvisorResponse(
            "trace_requirement",
            f"Traceability for {req.requirement_id} ({req.title}): {status_line}."
            + (f" Missing links: {', '.join(missing)}." if missing else " All links present."),
            data=[{"link": k, "present": v} for k, v in links.items()],
            links=[{"type": "requirement", "id": req.id}],
        )

    # -- helpers -----------------------------------------------------------
    def _match_named(self, q: str, db: Session, models: list) -> object | None:
        # Try each model's name/title/reference/requirement_id attributes against tokens
        tokens = [t for t in re.split(r"[^a-z0-9\-]+", q) if len(t) > 1]
        for model in models:
            cols = [c for c in ("name", "title", "reference", "requirement_id", "version") if hasattr(model, c)]
            for obj in db.scalars(select(model)):
                values = " ".join(str(getattr(obj, c, "") or "").lower() for c in cols)
                if values and any(tok in values for tok in tokens if len(tok) >= 3):
                    # prefer multi-word matches
                    for col in cols:
                        val = str(getattr(obj, col, "") or "").lower()
                        if val and val in q:
                            return obj
                    if model.__name__ in ("ECU", "Asset", "Release", "CybersecurityRequirement", "Threat"):
                        return obj
        return None

    def _resolve_entity(self, q: str, db: Session) -> tuple[object | None, str, int]:
        named = self._match_named(q, db, [m.SoftwareComponent, m.ECU, m.CybersecurityRequirement, m.TARA, m.Asset, m.Release])
        if named is None:
            return None, "", 0
        mapping = {
            m.SoftwareComponent: "SoftwareComponent",
            m.ECU: "ECU",
            m.CybersecurityRequirement: "CybersecurityRequirement",
            m.TARA: "TARA",
            m.Asset: "Asset",
            m.Release: "Release",
        }
        entity_type = mapping[type(named)]
        return named, entity_type, named.id


def get_advisor_backend() -> AdvisorBackend:
    # LLM backend adapter point (AI_API_KEY + AI_BACKEND="llm") — rules engine in MVP.
    return RuleEngineBackend()
