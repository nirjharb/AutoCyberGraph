"""
Graph abstraction layer.

`GraphService` exposes typed traversal over the traceability graph. The MVP
implementation derives adjacency from relational rows; a Neo4j-backed service can
implement the same protocol later without rewriting callers (see ARCHITECTURE.md).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models as m


@dataclass(frozen=True)
class Edge:
    source_type: str
    source_id: int
    target_type: str
    target_id: int
    kind: str
    description: str


@dataclass
class GraphNode:
    entity_type: str
    entity_id: int
    label: str
    depth: int
    via: list[str] = field(default_factory=list)  # edge kind chain
    reason: str = ""


class GraphProtocol(Protocol):
    def edges_from(self, entity_type: str, entity_id: int) -> list[Edge]: ...
    def bfs(self, entity_type: str, entity_id: int, max_depth: int = 6) -> list[GraphNode]: ...


def _label(obj, entity_type: str) -> str:
    for attr in ("reference", "requirement_id", "cve_id", "name", "title", "version"):
        value = getattr(obj, attr, None)
        if value:
            return f"{entity_type}:{value}"
    return f"{entity_type}:{getattr(obj, 'id', '?')}"


class SqlGraphService:
    """Adjacency derived from SQLAlchemy rows. Deterministic and DB-portable."""

    # (model, id_attr, [(edge_kind, description, target_model, target_fk_attr, direction)])
    # direction: "forward" means source row owns the FK pointing at target.
    FORWARD_SPECS = [
        ("Vehicle", "ecus", "Vehicle→ECU", "ECU", "vehicle_id"),
        ("Vehicle", "networks", "Vehicle→Network", "Network", "vehicle_id"),
        ("Vehicle", "sboms", "Vehicle→SBOM", "SBOM", "vehicle_id"),
        ("ECU", "assets", "ECU→Asset", "Asset", "ecu_id"),
        ("ECU", "components", "ECU→SoftwareComponent", "SoftwareComponent", "ecu_id"),
        ("ECU", "releases", "ECU→Release", "Release", "ecu_id"),
        ("ECU", "sboms", "ECU→SBOM", "SBOM", "ecu_id"),
        ("Asset", "threats", "Asset→Threat", "Threat", "asset_id"),
        ("Asset", "taras", "Asset→TARA", "TARA", "asset_id"),
        ("Threat", "taras", "Threat→TARA", "TARA", "threat_id"),
        ("TARA", "requirements", "TARA→Requirement", "CybersecurityRequirement", "tara_id"),
        ("CybersecurityRequirement", "test_cases", "Requirement→TestCase", "TestCase", "requirement_id"),
        ("TestCase", "results", "TestCase→TestResult", "TestResult", "test_case_id"),
        ("SoftwareComponent", "vulnerabilities", "Component→Vulnerability", "Vulnerability", "component_id"),
    ]

    def __init__(self, db: Session):
        self.db = db

    # -- raw edge assembly -------------------------------------------------
    def _all_edges(self) -> list[Edge]:
        edges: list[Edge] = []
        add = edges.append

        def rel_edges(source_type: str, source, targets: Iterable, kind: str, desc: str, target_type: str):
            for t in targets:
                add(Edge(source_type, source.id, target_type, t.id, kind, desc))

        # FK-based forward relationships
        for vehicle in self.db.scalars(select(m.Vehicle)):
            rel_edges("Vehicle", vehicle, vehicle.ecus, "contains", "Vehicle contains ECU", "ECU")
            rel_edges("Vehicle", vehicle, vehicle.networks, "contains", "Vehicle contains network", "Network")
            rel_edges("Vehicle", vehicle, vehicle.sboms, "documents", "Vehicle SBOM", "SBOM")
        for ecu in self.db.scalars(select(m.ECU)):
            rel_edges("ECU", ecu, ecu.assets, "contains", "ECU hosts asset", "Asset")
            rel_edges("ECU", ecu, ecu.components, "runs", "ECU runs software component", "SoftwareComponent")
            rel_edges("ECU", ecu, ecu.releases, "releases", "ECU software release", "Release")
            rel_edges("ECU", ecu, ecu.sboms, "documents", "ECU SBOM", "SBOM")
        for asset in self.db.scalars(select(m.Asset)):
            rel_edges("Asset", asset, asset.threats, "threatened_by", "Asset exposed to threat", "Threat")
            rel_edges("Asset", asset, asset.taras, "assessed_by", "Asset TARA assessment", "TARA")
        for threat in self.db.scalars(select(m.Threat)):
            rel_edges("Threat", threat, threat.taras, "analysed_in", "Threat analysed in TARA", "TARA")
        for tara in self.db.scalars(select(m.TARA)):
            rel_edges("TARA", tara, tara.requirements, "derives", "TARA derives cybersecurity requirement", "CybersecurityRequirement")
        for req in self.db.scalars(select(m.CybersecurityRequirement)):
            rel_edges("CybersecurityRequirement", req, req.test_cases, "verified_by", "Requirement verified by test", "TestCase")
            for link in req.mechanisms:
                add(Edge("CybersecurityRequirement", req.id, "AutosarMechanism", link.mechanism_id,
                         "mitigated_by", "Requirement mitigated by AUTOSAR mechanism"))
            for link in req.controls:
                add(Edge("CybersecurityRequirement", req.id, "Control", link.control_id,
                         "mapped_to_control", "Requirement mapped to security control"))
        for test in self.db.scalars(select(m.TestCase)):
            rel_edges("TestCase", test, test.results, "produces", "Test execution result", "TestResult")
        for comp in self.db.scalars(select(m.SoftwareComponent)):
            rel_edges("SoftwareComponent", comp, comp.vulnerabilities, "has_vuln", "Component vulnerability", "Vulnerability")
        # Evidence hooks
        for ev in self.db.scalars(select(m.Evidence)):
            if ev.requirement_id:
                add(Edge("Evidence", ev.id, "CybersecurityRequirement", ev.requirement_id,
                         "evidence_for", "Evidence supports requirement"))
            if ev.test_result_id:
                add(Edge("Evidence", ev.id, "TestResult", ev.test_result_id,
                         "evidence_for", "Evidence supports test result"))
            if ev.release_id:
                add(Edge("Evidence", ev.id, "Release", ev.release_id,
                         "evidence_for", "Evidence supports release"))
            if ev.tara_id:
                add(Edge("Evidence", ev.id, "TARA", ev.tara_id,
                         "evidence_for", "Evidence supports TARA"))
        # Link tables
        for link in self.db.scalars(select(m.ControlEvidenceLink)):
            add(Edge("Control", link.control_id, "Evidence", link.evidence_id,
                     "supported_by", "Control supported by evidence"))
        for link in self.db.scalars(select(m.ControlTestLink)):
            add(Edge("Control", link.control_id, "TestCase", link.test_case_id,
                     "tested_by", "Control tested by test case"))
        for impl in self.db.scalars(select(m.MechanismImplementation)):
            add(Edge("AutosarMechanism", impl.mechanism_id, "ECU", impl.ecu_id,
                     "implemented_on", "Mechanism implemented on ECU"))
        # SBOM contents
        for sbom in self.db.scalars(select(m.SBOM)):
            for comp in sbom.components:
                add(Edge("SBOM", sbom.id, "SbomComponent", comp.id,
                         "lists", "SBOM lists component"))
        # Compliance mappings (standards layer)
        for cm in self.db.scalars(select(m.ComplianceMapping)):
            target_type = cm.target_entity or ""
            if target_type and cm.target_id:
                add(Edge(cm.source_entity, cm.source_id, target_type, cm.target_id,
                         "mapped", f"Mapped to {cm.standard} {cm.control_id}"))
            else:
                add(Edge(cm.source_entity, cm.source_id, "ControlRef", f"{cm.standard}:{cm.control_id}".__hash__() % 10_000_000,
                         "mapped_standard", f"Mapped to {cm.standard} {cm.control_id}"))
        return edges

    def _edges_indexed(self) -> dict[tuple[str, int], list[Edge]]:
        index: dict[tuple[str, int], list[Edge]] = {}
        for e in self._all_edges():
            index.setdefault((e.source_type, e.source_id), []).append(e)
            index.setdefault((e.target_type, e.target_id), []).append(
                Edge(e.target_type, e.target_id, e.source_type, e.source_id, e.kind, e.description)
            )
        return index

    def edges_from(self, entity_type: str, entity_id: int) -> list[Edge]:
        return self._edges_indexed().get((entity_type, entity_id), [])

    def bfs(self, entity_type: str, entity_id: int, max_depth: int = 6) -> list[GraphNode]:
        index = self._edges_indexed()
        start_label = self._lookup_label(entity_type, entity_id)
        seen: dict[tuple[str, int], GraphNode] = {}
        queue: list[tuple[str, int, int, list[str], str]] = [(entity_type, entity_id, 0, [], "")]
        while queue:
            et, eid, depth, chain, reason = queue.pop(0)
            key = (et, eid)
            if key in seen:
                continue
            seen[key] = GraphNode(
                entity_type=et,
                entity_id=eid,
                label=self._lookup_label(et, eid) if depth > 0 else start_label,
                depth=depth,
                via=list(chain),
                reason=reason,
            )
            if depth >= max_depth:
                continue
            for edge in index.get(key, []):
                next_key = (edge.target_type, edge.target_id)
                if next_key in seen:
                    continue
                step = f"{edge.kind}"
                new_reason = (
                    f"{reason} → [{edge.description}]" if reason else f"[{edge.description}]"
                )
                queue.append((edge.target_type, edge.target_id, depth + 1, chain + [step], new_reason))
        nodes = [n for n in seen.values() if not (n.entity_type == entity_type and n.entity_id == entity_id)]
        nodes.sort(key=lambda n: (n.depth, n.entity_type, n.entity_id))
        return nodes

    def _lookup_label(self, entity_type: str, entity_id: int) -> str:
        model = TYPE_TO_MODEL.get(entity_type)
        if model is None:
            return f"{entity_type}:{entity_id}"
        if entity_type == "ControlRef":
            return f"ControlRef:{entity_id}"
        obj = self.db.get(model, entity_id)
        return _label(obj, entity_type) if obj else f"{entity_type}:{entity_id}"


TYPE_TO_MODEL = {
    "Vehicle": m.Vehicle,
    "ECU": m.ECU,
    "Network": m.Network,
    "Asset": m.Asset,
    "Threat": m.Threat,
    "TARA": m.TARA,
    "CybersecurityRequirement": m.CybersecurityRequirement,
    "Requirement": m.CybersecurityRequirement,
    "Control": m.Control,
    "AutosarMechanism": m.AutosarMechanism,
    "SoftwareComponent": m.SoftwareComponent,
    "Vulnerability": m.Vulnerability,
    "SBOM": m.SBOM,
    "SbomComponent": m.SbomComponent,
    "TestCase": m.TestCase,
    "TestResult": m.TestResult,
    "Evidence": m.Evidence,
    "Release": m.Release,
    "Change": m.Change,
    "ComplianceMapping": m.ComplianceMapping,
    "Supplier": m.Supplier,
    "SupplierSubmission": m.SupplierSubmission,
    "Standard": m.Standard,
}

# Aliases accepted from API clients
ENTITY_ALIASES = {
    "Requirement": "CybersecurityRequirement",
    "CybersecurityRequirement": "CybersecurityRequirement",
    "Mechanism": "AutosarMechanism",
    "AutosarMechanism": "AutosarMechanism",
    "Component": "SoftwareComponent",
    "SoftwareComponent": "SoftwareComponent",
    "Test": "TestCase",
    "TestCase": "TestCase",
    "TestResult": "TestResult",
    "Vulnerability": "Vulnerability",
    "Evidence": "Evidence",
    "Release": "Release",
    "ECU": "ECU",
    "Vehicle": "Vehicle",
    "Asset": "Asset",
    "Threat": "Threat",
    "TARA": "TARA",
    "Control": "Control",
    "SBOM": "SBOM",
    "Network": "Network",
}


def resolve_entity_type(entity_type: str) -> str:
    return ENTITY_ALIASES.get(entity_type, entity_type)


def get_graph_service(db: Session) -> SqlGraphService:
    return SqlGraphService(db)
