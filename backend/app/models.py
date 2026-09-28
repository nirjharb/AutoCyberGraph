"""
AutoCyberGraph domain model.

Traceability spine:
  Vehicle → ECU → Software Component → Asset → Threat → TARA → Cybersecurity Goal
  → Requirement → Control → AUTOSAR Mechanism → Test Case → Test Result
  → Evidence → Release → Compliance Mapping (R155 / R156 / 21434 / NIST)

All models are portable across SQLite and PostgreSQL (see DECISIONS.md ADR-001).
"""
from __future__ import annotations

import datetime as dt
import enum

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class Role(str, enum.Enum):
    ADMIN = "ADMIN"
    CYBERSECURITY_ENGINEER = "CYBERSECURITY_ENGINEER"
    ARCHITECT = "ARCHITECT"
    TESTER = "TESTER"
    SUPPLIER = "SUPPLIER"
    AUDITOR = "AUDITOR"
    VIEWER = "VIEWER"


class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PENDING = "PENDING"


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Severity(str, enum.Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TestStatus(str, enum.Enum):
    NOT_RUN = "NOT_RUN"
    PASSED = "PASSED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class EvidenceStatus(str, enum.Enum):
    MISSING = "MISSING"
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ChangeType(str, enum.Enum):
    SOFTWARE_CHANGE = "SOFTWARE_CHANGE"
    AUTOSAR_CONFIG_CHANGE = "AUTOSAR_CONFIG_CHANGE"
    ECU_CHANGE = "ECU_CHANGE"
    NETWORK_MESSAGE_CHANGE = "NETWORK_MESSAGE_CHANGE"
    CRYPTO_LIBRARY_CHANGE = "CRYPTO_LIBRARY_CHANGE"
    REQUIREMENT_CHANGE = "REQUIREMENT_CHANGE"
    TARA_CHANGE = "TARA_CHANGE"
    VULNERABILITY = "VULNERABILITY"
    SBOM_CHANGE = "SBOM_CHANGE"


class ImpactLevel(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ReleaseGateResult(str, enum.Enum):
    PASS = "PASS"
    REVIEW = "REVIEW"
    HOLD = "HOLD"


class SubmissionStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"


# --------------------------------------------------------------------------- #
# Organization & Users
# --------------------------------------------------------------------------- #
class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    type: Mapped[str] = mapped_column(String(80), default="OEM")  # OEM | SUPPLIER | LAB | OTHER
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)

    users: Mapped[list["User"]] = relationship(back_populates="organization")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.VIEWER)
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.ACTIVE)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)

    organization: Mapped[Organization] = relationship(back_populates="users")


# --------------------------------------------------------------------------- #
# Vehicle architecture
# --------------------------------------------------------------------------- #
class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    model: Mapped[str] = mapped_column(String(200), default="")
    platform: Mapped[str] = mapped_column(String(200), default="")
    version: Mapped[str] = mapped_column(String(80), default="1.0")
    description: Mapped[str] = mapped_column(Text, default="")

    ecus: Mapped[list["ECU"]] = relationship(back_populates="vehicle", cascade="all, delete-orphan")
    networks: Mapped[list["Network"]] = relationship(back_populates="vehicle", cascade="all, delete-orphan")
    sboms: Mapped[list["SBOM"]] = relationship(back_populates="vehicle", cascade="all, delete-orphan")


class ECU(Base):
    __tablename__ = "ecus"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    ecu_type: Mapped[str] = mapped_column(String(120), default="")
    supplier: Mapped[str] = mapped_column(String(200), default="")
    hardware_version: Mapped[str] = mapped_column(String(80), default="")
    software_version: Mapped[str] = mapped_column(String(80), default="")
    criticality: Mapped[str] = mapped_column(String(40), default="MEDIUM")
    status: Mapped[str] = mapped_column(String(40), default="ACTIVE")

    vehicle: Mapped[Vehicle] = relationship(back_populates="ecus")
    assets: Mapped[list["Asset"]] = relationship(back_populates="ecu", cascade="all, delete-orphan")
    components: Mapped[list["SoftwareComponent"]] = relationship(back_populates="ecu", cascade="all, delete-orphan")
    releases: Mapped[list["Release"]] = relationship(back_populates="ecu", cascade="all, delete-orphan")
    sboms: Mapped[list["SBOM"]] = relationship(back_populates="ecu", cascade="all, delete-orphan")


class Network(Base):
    __tablename__ = "networks"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    network_type: Mapped[str] = mapped_column(String(80))  # CAN | CAN-FD | Automotive Ethernet | SOME/IP
    description: Mapped[str] = mapped_column(Text, default="")
    # ECUs attached to this network, stored as a JSON list of ECU ids (simple MVP model)
    ecu_ids: Mapped[list] = mapped_column(JSON, default=list)

    vehicle: Mapped[Vehicle] = relationship(back_populates="networks")


# --------------------------------------------------------------------------- #
# Assets, threats, TARA
# --------------------------------------------------------------------------- #
class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    ecu_id: Mapped[int] = mapped_column(ForeignKey("ecus.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(120), default="")  # DATA | FUNCTION | COMMUNICATION | ...
    criticality: Mapped[str] = mapped_column(String(40), default="MEDIUM")
    description: Mapped[str] = mapped_column(Text, default="")

    ecu: Mapped[ECU] = relationship(back_populates="assets")
    threats: Mapped[list["Threat"]] = relationship(back_populates="asset", cascade="all, delete-orphan")
    taras: Mapped[list["TARA"]] = relationship(back_populates="asset", cascade="all, delete-orphan")


class Threat(Base):
    __tablename__ = "threats"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    threat_type: Mapped[str] = mapped_column(String(120), default="")  # SPOOFING | TAMPERING | ...
    attack_vector: Mapped[str] = mapped_column(String(200), default="")

    asset: Mapped[Asset] = relationship(back_populates="threats")
    taras: Mapped[list["TARA"]] = relationship(back_populates="threat", cascade="all, delete-orphan")


class TARA(Base):
    __tablename__ = "taras"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    threat_id: Mapped[int | None] = mapped_column(ForeignKey("threats.id"), nullable=True, index=True)
    reference: Mapped[str] = mapped_column(String(80), unique=True)  # e.g. TARA-001
    damage_scenario: Mapped[str] = mapped_column(Text)
    threat_scenario: Mapped[str] = mapped_column(Text)
    impact: Mapped[str] = mapped_column(String(40))  # SEVERE | MAJOR | MODERATE | MINOR
    impact_level: Mapped[int] = mapped_column(Integer, default=2)  # 0..4, configurable
    attack_feasibility: Mapped[str] = mapped_column(String(40))  # HIGH | MEDIUM | LOW | VERY_LOW
    feasibility_level: Mapped[int] = mapped_column(Integer, default=2)  # 0..4
    risk_level: Mapped[str] = mapped_column(String(20), default="MEDIUM")
    cybersecurity_goal: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="DRAFT")  # DRAFT | REVIEWED | APPROVED
    reviewed_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)

    asset: Mapped[Asset] = relationship(back_populates="taras")
    threat: Mapped[Threat | None] = relationship(back_populates="taras")
    requirements: Mapped[list["CybersecurityRequirement"]] = relationship(back_populates="tara")


# --------------------------------------------------------------------------- #
# Requirements, standards, controls, AUTOSAR
# --------------------------------------------------------------------------- #
class CybersecurityRequirement(Base):
    __tablename__ = "cybersecurity_requirements"

    id: Mapped[int] = mapped_column(primary_key=True)
    tara_id: Mapped[int | None] = mapped_column(ForeignKey("taras.id"), nullable=True, index=True)
    requirement_id: Mapped[str] = mapped_column(String(80), unique=True)  # CS-REQ-001
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, default="")
    priority: Mapped[str] = mapped_column(String(20), default="MEDIUM")
    status: Mapped[str] = mapped_column(String(30), default="DRAFT")  # DRAFT | IN_REVIEW | APPROVED

    tara: Mapped[TARA | None] = relationship(back_populates="requirements")
    test_cases: Mapped[list["TestCase"]] = relationship(back_populates="requirement", cascade="all, delete-orphan")
    mechanisms: Mapped[list["RequirementMechanismLink"]] = relationship(back_populates="requirement", cascade="all, delete-orphan")
    controls: Mapped[list["RequirementControlLink"]] = relationship(back_populates="requirement", cascade="all, delete-orphan")


class Standard(Base):
    __tablename__ = "standards"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(60), unique=True)  # ISO21434 | R155 | R156 | NIST80053 | AUTOSAR
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    reference_url: Mapped[str] = mapped_column(String(500), default="")

    controls: Mapped[list["Control"]] = relationship(back_populates="standard", cascade="all, delete-orphan")


class Control(Base):
    __tablename__ = "controls"

    id: Mapped[int] = mapped_column(primary_key=True)
    standard_id: Mapped[int] = mapped_column(ForeignKey("standards.id"), index=True)
    control_id: Mapped[str] = mapped_column(String(80))  # e.g. AC-2, R155-7.2.2.2
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(120), default="")  # AC | AU | CM | ... | PROCESS

    standard: Mapped[Standard] = relationship(back_populates="controls")


class AutosarMechanism(Base):
    __tablename__ = "autosar_mechanisms"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)  # SecOC, CSM, HSM, ...
    category: Mapped[str] = mapped_column(String(120), default="")
    description: Mapped[str] = mapped_column(Text, default="")


class RequirementMechanismLink(Base):
    __tablename__ = "requirement_mechanism_links"
    __table_args__ = (UniqueConstraint("requirement_id", "mechanism_id", name="uq_req_mech"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    requirement_id: Mapped[int] = mapped_column(ForeignKey("cybersecurity_requirements.id"), index=True)
    mechanism_id: Mapped[int] = mapped_column(ForeignKey("autosar_mechanisms.id"), index=True)
    notes: Mapped[str] = mapped_column(Text, default="")

    requirement: Mapped[CybersecurityRequirement] = relationship(back_populates="mechanisms")
    mechanism: Mapped[AutosarMechanism] = relationship()


class RequirementControlLink(Base):
    __tablename__ = "requirement_control_links"
    __table_args__ = (UniqueConstraint("requirement_id", "control_id", name="uq_req_ctl"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    requirement_id: Mapped[int] = mapped_column(ForeignKey("cybersecurity_requirements.id"), index=True)
    control_id: Mapped[int] = mapped_column(ForeignKey("controls.id"), index=True)
    notes: Mapped[str] = mapped_column(Text, default="")

    requirement: Mapped[CybersecurityRequirement] = relationship(back_populates="controls")
    control: Mapped[Control] = relationship()


class ControlEvidenceLink(Base):
    __tablename__ = "control_evidence_links"
    __table_args__ = (UniqueConstraint("control_id", "evidence_id", name="uq_ctl_ev"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    control_id: Mapped[int] = mapped_column(ForeignKey("controls.id"), index=True)
    evidence_id: Mapped[int] = mapped_column(ForeignKey("evidences.id"), index=True)

    control: Mapped[Control] = relationship()
    evidence: Mapped["Evidence"] = relationship()


class ControlTestLink(Base):
    __tablename__ = "control_test_links"
    __table_args__ = (UniqueConstraint("control_id", "test_case_id", name="uq_ctl_test"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    control_id: Mapped[int] = mapped_column(ForeignKey("controls.id"), index=True)
    test_case_id: Mapped[int] = mapped_column(ForeignKey("test_cases.id"), index=True)

    control: Mapped[Control] = relationship()
    test_case: Mapped["TestCase"] = relationship()


class MechanismImplementation(Base):
    """An AUTOSAR security mechanism realized on a concrete ECU."""

    __tablename__ = "mechanism_implementations"
    __table_args__ = (UniqueConstraint("mechanism_id", "ecu_id", name="uq_mech_ecu"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    mechanism_id: Mapped[int] = mapped_column(ForeignKey("autosar_mechanisms.id"), index=True)
    ecu_id: Mapped[int] = mapped_column(ForeignKey("ecus.id"), index=True)
    status: Mapped[str] = mapped_column(String(40), default="IMPLEMENTED")
    notes: Mapped[str] = mapped_column(Text, default="")

    mechanism: Mapped[AutosarMechanism] = relationship()
    ecu: Mapped[ECU] = relationship()


# --------------------------------------------------------------------------- #
# Software, SBOM, vulnerabilities
# --------------------------------------------------------------------------- #
class SoftwareComponent(Base):
    __tablename__ = "software_components"

    id: Mapped[int] = mapped_column(primary_key=True)
    ecu_id: Mapped[int] = mapped_column(ForeignKey("ecus.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    version: Mapped[str] = mapped_column(String(80), default="1.0")
    supplier: Mapped[str] = mapped_column(String(200), default="")
    hash: Mapped[str] = mapped_column(String(128), default="")

    ecu: Mapped[ECU] = relationship(back_populates="components")
    vulnerabilities: Mapped[list["Vulnerability"]] = relationship(back_populates="component", cascade="all, delete-orphan")


class Vulnerability(Base):
    __tablename__ = "vulnerabilities"

    id: Mapped[int] = mapped_column(primary_key=True)
    component_id: Mapped[int] = mapped_column(ForeignKey("software_components.id"), index=True)
    cve_id: Mapped[str] = mapped_column(String(40), index=True)
    cvss_score: Mapped[float] = mapped_column(Float, default=0.0)
    severity: Mapped[Severity] = mapped_column(Enum(Severity), default=Severity.MEDIUM)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="OPEN")  # OPEN | IN_PROGRESS | RESOLVED | ACCEPTED | FALSE_POSITIVE
    remediation: Mapped[str] = mapped_column(Text, default="")
    published_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)

    component: Mapped[SoftwareComponent] = relationship(back_populates="vulnerabilities")


class SBOM(Base):
    __tablename__ = "sboms"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int | None] = mapped_column(ForeignKey("vehicles.id"), nullable=True, index=True)
    ecu_id: Mapped[int | None] = mapped_column(ForeignKey("ecus.id"), nullable=True, index=True)
    format: Mapped[str] = mapped_column(String(30))  # CycloneDX | SPDX
    file_name: Mapped[str] = mapped_column(String(255))
    version: Mapped[str] = mapped_column(String(80), default="")
    uploaded_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)
    component_count: Mapped[int] = mapped_column(Integer, default=0)

    vehicle: Mapped[Vehicle | None] = relationship(back_populates="sboms")
    ecu: Mapped[ECU | None] = relationship(back_populates="sboms")
    components: Mapped[list["SbomComponent"]] = relationship(back_populates="sbom", cascade="all, delete-orphan")


class SbomComponent(Base):
    __tablename__ = "sbom_components"

    id: Mapped[int] = mapped_column(primary_key=True)
    sbom_id: Mapped[int] = mapped_column(ForeignKey("sboms.id"), index=True)
    name: Mapped[str] = mapped_column(String(300))
    version: Mapped[str] = mapped_column(String(120), default="")
    purl: Mapped[str] = mapped_column(String(500), default="")
    license: Mapped[str] = mapped_column(String(120), default="")
    hash: Mapped[str] = mapped_column(String(255), default="")
    component_type: Mapped[str] = mapped_column(String(80), default="")

    sbom: Mapped[SBOM] = relationship(back_populates="components")


# --------------------------------------------------------------------------- #
# Tests & evidence
# --------------------------------------------------------------------------- #
class TestCase(Base):
    __tablename__ = "test_cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    requirement_id: Mapped[int | None] = mapped_column(ForeignKey("cybersecurity_requirements.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, default="")
    test_type: Mapped[str] = mapped_column(String(80), default="FUNCTIONAL")  # FUNCTIONAL | FUZZ | PENETRATION | STATIC | CONFIG_REVIEW
    expected_result: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="NOT_RUN")

    requirement: Mapped[CybersecurityRequirement | None] = relationship(back_populates="test_cases")
    results: Mapped[list["TestResult"]] = relationship(back_populates="test_case", cascade="all, delete-orphan")


class TestResult(Base):
    __tablename__ = "test_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    test_case_id: Mapped[int] = mapped_column(ForeignKey("test_cases.id"), index=True)
    result: Mapped[TestStatus] = mapped_column(Enum(TestStatus), default=TestStatus.NOT_RUN)
    executed_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)
    tester: Mapped[str] = mapped_column(String(200), default="")
    notes: Mapped[str] = mapped_column(Text, default="")

    test_case: Mapped[TestCase] = relationship(back_populates="results")


class Evidence(Base):
    __tablename__ = "evidences"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(300))
    type: Mapped[str] = mapped_column(String(120), default="DOCUMENT")  # DOCUMENT | TEST_REPORT | CONFIG | LOG | SBOM | ANALYSIS
    description: Mapped[str] = mapped_column(Text, default="")
    file_reference: Mapped[str] = mapped_column(String(500), default="")
    status: Mapped[str] = mapped_column(Enum(EvidenceStatus), default=EvidenceStatus.DRAFT)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)
    # Core traceability hooks (nullable — an evidence item links where it belongs)
    requirement_id: Mapped[int | None] = mapped_column(ForeignKey("cybersecurity_requirements.id"), nullable=True, index=True)
    test_result_id: Mapped[int | None] = mapped_column(ForeignKey("test_results.id"), nullable=True, index=True)
    release_id: Mapped[int | None] = mapped_column(ForeignKey("releases.id"), nullable=True, index=True)
    tara_id: Mapped[int | None] = mapped_column(ForeignKey("taras.id"), nullable=True, index=True)


# --------------------------------------------------------------------------- #
# Release & change
# --------------------------------------------------------------------------- #
class Release(Base):
    __tablename__ = "releases"

    id: Mapped[int] = mapped_column(primary_key=True)
    ecu_id: Mapped[int] = mapped_column(ForeignKey("ecus.id"), index=True)
    version: Mapped[str] = mapped_column(String(80))
    release_type: Mapped[str] = mapped_column(String(60), default="PRODUCTION")  # PRODUCTION | PATCH | OTA | DEVELOPMENT
    release_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="PLANNED")  # PLANNED | IN_VALIDATION | APPROVED | RELEASED | BLOCKED
    gate_result: Mapped[str | None] = mapped_column(String(20), nullable=True)
    gate_reasons: Mapped[list] = mapped_column(JSON, default=list)
    gate_evaluated_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)

    ecu: Mapped[ECU] = relationship(back_populates="releases")


class Change(Base):
    __tablename__ = "changes"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(80))  # e.g. SoftwareComponent, ECU, Requirement, TARA, ...
    entity_id: Mapped[int] = mapped_column(Integer)
    change_type: Mapped[ChangeType] = mapped_column(Enum(ChangeType))
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)
    created_by: Mapped[str] = mapped_column(String(200), default="")
    impact_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    impact_report: Mapped[list] = mapped_column(JSON, default=list)
    impact_summary: Mapped[dict] = mapped_column(JSON, default=dict)
    analyzed_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    security_assessment: Mapped[str] = mapped_column(Text, default="")  # R156 security impact assessment


class ComplianceMapping(Base):
    """Generic standards mapping layer (R155 / R156 / 21434 / NIST / AUTOSAR)."""

    __tablename__ = "compliance_mappings"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_entity: Mapped[str] = mapped_column(String(80))
    source_id: Mapped[int] = mapped_column(Integer)
    standard: Mapped[str] = mapped_column(String(120))  # ISO/SAE 21434 | UNECE R155 | UNECE R156 | NIST SP 800-53 | AUTOSAR Security
    control_id: Mapped[str] = mapped_column(String(80))
    target_entity: Mapped[str] = mapped_column(String(80), default="")
    target_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mapping_type: Mapped[str] = mapped_column(String(60), default="trace")  # trace | evidence | concept | process
    confidence: Mapped[str] = mapped_column(String(20), default="MEDIUM")  # HIGH | MEDIUM | LOW
    notes: Mapped[str] = mapped_column(Text, default="")


# --------------------------------------------------------------------------- #
# Supplier portal
# --------------------------------------------------------------------------- #
class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(120), default="TIER1")
    contact: Mapped[str] = mapped_column(String(255), default="")


class SupplierSubmission(Base):
    __tablename__ = "supplier_submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), index=True)
    kind: Mapped[str] = mapped_column(String(80))  # ECU_INFO | SOFTWARE_VERSION | SBOM | REQUIREMENT | TARA_EVIDENCE | TEST_RESULT | VULNERABILITY | SECURITY_DOC
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, default="")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(Enum(SubmissionStatus), default=SubmissionStatus.SUBMITTED)
    review_notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)
    reviewed_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[str] = mapped_column(String(200), default="")

    supplier: Mapped[Supplier] = relationship()


# --------------------------------------------------------------------------- #
# Audit
# --------------------------------------------------------------------------- #
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor: Mapped[str] = mapped_column(String(200))
    action: Mapped[str] = mapped_column(String(120))
    entity_type: Mapped[str] = mapped_column(String(80), default="")
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)
