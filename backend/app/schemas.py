"""Pydantic v2 schemas for API request/response validation."""
from __future__ import annotations

import datetime as dt
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .models import (
    ChangeType,
    EvidenceStatus,
    ImpactLevel,
    ReleaseGateResult,
    Role,
    Severity,
    SubmissionStatus,
    TestStatus,
    UserStatus,
)


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Auth ----------
class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Role = Role.VIEWER
    organization_name: str = Field(default="Default Org", max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(ORMModel):
    id: int
    organization_id: int
    name: str
    email: EmailStr
    role: Role
    status: UserStatus
    created_at: dt.datetime


# ---------- Vehicle architecture ----------
class VehicleCreate(BaseModel):
    name: str
    model: str = ""
    platform: str = ""
    version: str = "1.0"
    description: str = ""


class VehicleOut(ORMModel):
    id: int
    name: str
    model: str
    platform: str
    version: str
    description: str


class ECUCreate(BaseModel):
    vehicle_id: int
    name: str
    ecu_type: str = ""
    supplier: str = ""
    hardware_version: str = ""
    software_version: str = ""
    criticality: str = "MEDIUM"
    status: str = "ACTIVE"


class ECUOut(ORMModel):
    id: int
    vehicle_id: int
    name: str
    ecu_type: str
    supplier: str
    hardware_version: str
    software_version: str
    criticality: str
    status: str


class NetworkCreate(BaseModel):
    vehicle_id: int
    name: str
    network_type: str
    description: str = ""
    ecu_ids: list[int] = []


class NetworkOut(ORMModel):
    id: int
    vehicle_id: int
    name: str
    network_type: str
    description: str
    ecu_ids: list[int]


# ---------- Assets / threats / TARA ----------
class AssetCreate(BaseModel):
    ecu_id: int
    name: str
    type: str = ""
    criticality: str = "MEDIUM"
    description: str = ""


class AssetOut(ORMModel):
    id: int
    ecu_id: int
    name: str
    type: str
    criticality: str
    description: str


class ThreatCreate(BaseModel):
    asset_id: int
    name: str
    description: str = ""
    threat_type: str = ""
    attack_vector: str = ""


class ThreatOut(ORMModel):
    id: int
    asset_id: int
    name: str
    description: str
    threat_type: str
    attack_vector: str


class TARACreate(BaseModel):
    asset_id: int
    threat_id: int | None = None
    damage_scenario: str
    threat_scenario: str
    impact: str = "MODERATE"
    attack_feasibility: str = "MEDIUM"
    cybersecurity_goal: str = ""
    status: str = "DRAFT"


class TARAUpdate(BaseModel):
    damage_scenario: str | None = None
    threat_scenario: str | None = None
    impact: str | None = None
    attack_feasibility: str | None = None
    cybersecurity_goal: str | None = None
    status: str | None = None


class TARAOut(ORMModel):
    id: int
    asset_id: int
    threat_id: int | None
    reference: str
    damage_scenario: str
    threat_scenario: str
    impact: str
    impact_level: int
    attack_feasibility: str
    feasibility_level: int
    risk_level: str
    cybersecurity_goal: str
    status: str
    reviewed_at: dt.datetime | None


# ---------- Requirements ----------
class RequirementCreate(BaseModel):
    tara_id: int | None = None
    requirement_id: str
    title: str
    description: str = ""
    priority: str = "MEDIUM"
    status: str = "DRAFT"


class RequirementUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: str | None = None
    status: str | None = None
    tara_id: int | None = None


class RequirementOut(ORMModel):
    id: int
    tara_id: int | None
    requirement_id: str
    title: str
    description: str
    priority: str
    status: str


# ---------- Standards / controls / AUTOSAR ----------
class StandardOut(ORMModel):
    id: int
    key: str
    name: str
    description: str
    reference_url: str


class ControlOut(ORMModel):
    id: int
    standard_id: int
    control_id: str
    title: str
    description: str
    category: str


class MechanismOut(ORMModel):
    id: int
    name: str
    category: str
    description: str


class MechanismLinkCreate(BaseModel):
    requirement_id: int
    mechanism_id: int
    notes: str = ""


class ControlLinkCreate(BaseModel):
    requirement_id: int
    control_id: int
    notes: str = ""


class ComplianceMappingCreate(BaseModel):
    source_entity: str
    source_id: int
    standard: str
    control_id: str
    target_entity: str = ""
    target_id: int | None = None
    mapping_type: str = "trace"
    confidence: str = "MEDIUM"
    notes: str = ""


class ComplianceMappingOut(ORMModel):
    id: int
    source_entity: str
    source_id: int
    standard: str
    control_id: str
    target_entity: str
    target_id: int | None
    mapping_type: str
    confidence: str
    notes: str


# ---------- Software / SBOM / vulnerabilities ----------
class ComponentCreate(BaseModel):
    ecu_id: int
    name: str
    version: str = "1.0"
    supplier: str = ""
    hash: str = ""


class ComponentUpdate(BaseModel):
    version: str | None = None
    supplier: str | None = None
    hash: str | None = None
    name: str | None = None


class ComponentOut(ORMModel):
    id: int
    ecu_id: int
    name: str
    version: str
    supplier: str
    hash: str


class VulnerabilityCreate(BaseModel):
    component_id: int
    cve_id: str
    cvss_score: float = 0.0
    severity: Severity = Severity.MEDIUM
    description: str = ""
    status: str = "OPEN"
    remediation: str = ""


class VulnerabilityUpdate(BaseModel):
    status: str | None = None
    remediation: str | None = None
    severity: Severity | None = None
    cvss_score: float | None = None


class VulnerabilityOut(ORMModel):
    id: int
    component_id: int
    cve_id: str
    cvss_score: float
    severity: Severity
    description: str
    status: str
    remediation: str
    published_at: dt.datetime | None


class SbomImportRequest(BaseModel):
    vehicle_id: int | None = None
    ecu_id: int | None = None
    format: str = "auto"  # auto | CycloneDX | SPDX
    file_name: str
    content: str  # raw SBOM text (JSON)


class SbomComponentOut(ORMModel):
    id: int
    name: str
    version: str
    purl: str
    license: str
    hash: str
    component_type: str


class SbomOut(ORMModel):
    id: int
    vehicle_id: int | None
    ecu_id: int | None
    format: str
    file_name: str
    version: str
    uploaded_at: dt.datetime
    component_count: int


# ---------- Tests / evidence ----------
class TestCaseCreate(BaseModel):
    requirement_id: int | None = None
    name: str
    description: str = ""
    test_type: str = "FUNCTIONAL"
    expected_result: str = ""
    status: str = "NOT_RUN"


class TestCaseOut(ORMModel):
    id: int
    requirement_id: int | None
    name: str
    description: str
    test_type: str
    expected_result: str
    status: str


class TestResultCreate(BaseModel):
    test_case_id: int
    result: TestStatus
    tester: str = ""
    notes: str = ""


class TestResultOut(ORMModel):
    id: int
    test_case_id: int
    result: TestStatus
    executed_at: dt.datetime
    tester: str
    notes: str


class EvidenceCreate(BaseModel):
    name: str
    type: str = "DOCUMENT"
    description: str = ""
    file_reference: str = ""
    status: EvidenceStatus = EvidenceStatus.DRAFT
    requirement_id: int | None = None
    test_result_id: int | None = None
    release_id: int | None = None
    tara_id: int | None = None


class EvidenceOut(ORMModel):
    id: int
    name: str
    type: str
    description: str
    file_reference: str
    status: EvidenceStatus
    created_at: dt.datetime
    requirement_id: int | None
    test_result_id: int | None
    release_id: int | None
    tara_id: int | None


# ---------- Release / change ----------
class ReleaseCreate(BaseModel):
    ecu_id: int
    version: str
    release_type: str = "PRODUCTION"
    release_date: dt.date | None = None
    status: str = "PLANNED"


class ReleaseOut(ORMModel):
    id: int
    ecu_id: int
    version: str
    release_type: str
    release_date: dt.date | None
    status: str
    gate_result: str | None
    gate_reasons: list[Any]
    gate_evaluated_at: dt.datetime | None


class GateCheck(BaseModel):
    key: str
    label: str
    passed: bool
    severity: str  # BLOCKING | WARNING
    detail: str


class GateEvaluation(BaseModel):
    release_id: int
    result: ReleaseGateResult
    checks: list[GateCheck]
    reasons: list[str]


class ChangeCreate(BaseModel):
    entity_type: str
    entity_id: int
    change_type: ChangeType
    description: str
    security_assessment: str = ""


class ChangeOut(ORMModel):
    id: int
    entity_type: str
    entity_id: int
    change_type: ChangeType
    description: str
    created_at: dt.datetime
    created_by: str
    impact_level: str | None
    impact_report: list[Any]
    impact_summary: dict
    analyzed_at: dt.datetime | None
    security_assessment: str


class AffectedObject(BaseModel):
    entity_type: str
    entity_id: int
    label: str
    depth: int
    reason: str
    path: list[str]


class ImpactReport(BaseModel):
    change_id: int
    impact_level: ImpactLevel
    affected: dict[str, list[AffectedObject]]
    summary: dict[str, int]
    recommended_actions: list[str]
    rationale: list[str]


# ---------- Supplier ----------
class SupplierCreate(BaseModel):
    organization_id: int
    name: str
    type: str = "TIER1"
    contact: str = ""


class SupplierOut(ORMModel):
    id: int
    organization_id: int
    name: str
    type: str
    contact: str


class SubmissionCreate(BaseModel):
    supplier_id: int
    kind: str
    title: str
    description: str = ""
    payload: dict = {}


class SubmissionReview(BaseModel):
    status: SubmissionStatus
    review_notes: str = ""


class SubmissionOut(ORMModel):
    id: int
    supplier_id: int
    kind: str
    title: str
    description: str
    payload: dict
    status: SubmissionStatus
    review_notes: str
    created_at: dt.datetime
    reviewed_at: dt.datetime | None
    created_by: str


# ---------- Advisor ----------
class AdvisorQuestion(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class AdvisorAnswer(BaseModel):
    question: str
    intent: str
    answer: str
    data: list[dict] | dict[str, list[dict]] = []
    grounded: bool = True
    links: list[dict] = []


class AuditOut(ORMModel):
    id: int
    actor: str
    action: str
    entity_type: str
    entity_id: int | None
    detail: str
    created_at: dt.datetime
