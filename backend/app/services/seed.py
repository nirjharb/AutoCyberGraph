"""
Demo dataset — Demo EV Platform.

Idempotent: running twice does not duplicate data (ADR-010).
Includes the flagship change scenario:
    Gateway ECU — Crypto library v2.4 → v2.5 (CRYPTO_LIBRARY_CHANGE)
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models as m
from ..security import hash_password
from .risk import calculate_risk


def seed_demo_data(db: Session) -> dict:
    existing = db.scalars(select(m.Vehicle).where(m.Vehicle.name == "Demo EV Platform")).first()
    if existing:
        return {"status": "already-seeded", "vehicle_id": existing.id}

    # ------------------------------------------------------------------ orgs & users
    oem = m.Organization(name="Apex Mobility (Demo OEM)", type="OEM")
    supplier_org = m.Organization(name="Bosch-like Tier1 (Demo)", type="SUPPLIER")
    db.add_all([oem, supplier_org])
    db.flush()

    users = [
        ("Alice Admin", "admin@autocybergraph.io", "ADMIN", "ChangeMe123!"),
        ("Eric Engineer", "engineer@autocybergraph.io", "CYBERSECURITY_ENGINEER", "ChangeMe123!"),
        ("Ava Architect", "architect@autocybergraph.io", "ARCHITECT", "ChangeMe123!"),
        ("Tina Tester", "tester@autocybergraph.io", "TESTER", "ChangeMe123!"),
        ("Sam Supplier", "supplier@autocybergraph.io", "SUPPLIER", "ChangeMe123!"),
        ("Oscar Auditor", "auditor@autocybergraph.io", "AUDITOR", "ChangeMe123!"),
        ("Vera Viewer", "viewer@autocybergraph.io", "VIEWER", "ChangeMe123!"),
    ]
    for name, email, role, pwd in users:
        org = supplier_org if role == "SUPPLIER" else oem
        db.add(m.User(
            organization_id=org.id, name=name, email=email,
            password_hash=hash_password(pwd), role=m.Role(role), status=m.UserStatus.ACTIVE,
        ))

    # ------------------------------------------------------------------ vehicle & ECUs
    vehicle = m.Vehicle(
        name="Demo EV Platform",
        model="AX-EV 2026",
        platform="EVA-2",
        version="1.0",
        description="Reference electric vehicle platform for AutoCyberGraph demonstrations.",
    )
    db.add(vehicle)
    db.flush()

    ecu_defs = [
        ("Gateway ECU", "Central Gateway", "Continental (demo)", "HIGH", "GW-1000", "2.4.0"),
        ("ADAS ECU", "Driver Assistance", "Aptiv (demo)", "HIGH", "AD-2200", "5.1.0"),
        ("Infotainment ECU", "Infotainment", "Harman (demo)", "MEDIUM", "IVI-3300", "4.7.2"),
        ("Telematics ECU", "Telematics / Connectivity", "LG (demo)", "HIGH", "TCU-4400", "3.3.1"),
        ("Battery Management ECU", "Battery Management", "CATL (demo)", "HIGH", "BMS-5500", "1.9.0"),
    ]
    ecus: dict[str, m.ECU] = {}
    for name, ecu_type, supplier, criticality, hw, sw in ecu_defs:
        ecu = m.ECU(
            vehicle_id=vehicle.id, name=name, ecu_type=ecu_type, supplier=supplier,
            hardware_version=hw, software_version=sw, criticality=criticality, status="ACTIVE",
        )
        db.add(ecu)
        ecus[name] = ecu
    db.flush()

    db.add_all([
        m.Network(vehicle_id=vehicle.id, name="Vehicle CAN", network_type="CAN",
                  description="Body/chassis CAN bus", ecu_ids=[ecus["Gateway ECU"].id, ecus["Battery Management ECU"].id]),
        m.Network(vehicle_id=vehicle.id, name="Powertrain CAN-FD", network_type="CAN-FD",
                  description="High-speed powertrain bus", ecu_ids=[ecus["Gateway ECU"].id, ecus["ADAS ECU"].id, ecus["Battery Management ECU"].id]),
        m.Network(vehicle_id=vehicle.id, name="Automotive Ethernet Backbone", network_type="Automotive Ethernet",
                  description="100BASE-T1 backbone", ecu_ids=[ecus["Gateway ECU"].id, ecus["ADAS ECU"].id, ecus["Infotainment ECU"].id, ecus["Telematics ECU"].id]),
        m.Network(vehicle_id=vehicle.id, name="SOME/IP Service Network", network_type="SOME/IP",
                  description="Service-oriented middleware over Ethernet", ecu_ids=[ecus["ADAS ECU"].id, ecus["Infotainment ECU"].id, ecus["Telematics ECU"].id]),
    ])

    # ------------------------------------------------------------------ standards & controls
    std_21434 = m.Standard(key="ISO21434", name="ISO/SAE 21434",
                           description="Road vehicles — Cybersecurity engineering (reference concepts only).",
                           reference_url="https://www.iso.org/standard/70918.html")
    std_r155 = m.Standard(key="R155", name="UNECE R155",
                          description="Cyber security and cyber security management system (reference concepts only).",
                          reference_url="https://unece.org/transport/vehicle-regulations")
    std_r156 = m.Standard(key="R156", name="UNECE R156",
                          description="Software update and software update management system (reference concepts only).",
                          reference_url="https://unece.org/transport/vehicle-regulations")
    std_nist = m.Standard(key="NIST80053", name="NIST SP 800-53",
                          description="Security and privacy controls catalog (mapping layer only).",
                          reference_url="https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final")
    std_autosar = m.Standard(key="AUTOSAR", name="AUTOSAR Security",
                             description="AUTOSAR automotive security mechanisms (reference concepts only).",
                             reference_url="https://www.autosar.org/standards")
    db.add_all([std_21434, std_r155, std_r156, std_nist, std_autosar])
    db.flush()

    nist_controls = [
        ("AC-2", "Account Management", "AC", "Identify and manage system accounts."),
        ("AC-3", "Access Enforcement", "AC", "Enforce approved authorizations for access."),
        ("AU-2", "Event Logging", "AU", "Identify events for logging."),
        ("AU-6", "Audit Record Review", "AU", "Review and analyze audit records."),
        ("CM-2", "Baseline Configuration", "CM", "Maintain a baseline configuration."),
        ("CM-7", "Least Functionality", "CM", "Restrict system functions to necessary ones."),
        ("IA-2", "Identification and Authentication", "IA", "Uniquely identify and authenticate users/devices."),
        ("IA-5", "Authenticator Management", "IA", "Manage authenticators (keys, certificates)."),
        ("IR-4", "Incident Handling", "IR", "Implement incident handling capability."),
        ("RA-5", "Vulnerability Monitoring", "RA", "Monitor and scan for vulnerabilities."),
        ("SA-10", "Developer Configuration Management", "SA", "Developer configuration management controls."),
        ("SC-8", "Transmission Confidentiality and Integrity", "SC", "Protect transmitted information."),
        ("SC-13", "Cryptographic Protection", "SC", "Employ cryptographic mechanisms."),
        ("SI-2", "Flaw Remediation", "SI", "Identify, report and correct system flaws."),
        ("SR-3", "Supply Chain Controls", "SR", "Apply supply chain risk management controls."),
        ("SR-4", "Provenance", "SR", "Document and maintain system component provenance."),
    ]
    controls: dict[str, m.Control] = {}
    for cid, title, cat, desc in nist_controls:
        c = m.Control(standard_id=std_nist.id, control_id=cid, title=title, category=cat, description=desc)
        db.add(c)
        controls[cid] = c

    r155_controls = [
        ("R155-7.2.2.2", "CSMS processes", "PROCESS", "Processes for managing cybersecurity risks."),
        ("R155-7.2.2.3", "Risk assessment and management", "PROCESS", "Vehicle type risk assessment and treatment."),
        ("R155-7.2.2.4", "Security by design", "PROCESS", "Cybersecurity by design considerations."),
        ("R155-7.2.2.5", "Post-production monitoring", "PROCESS", "Monitoring, detection and response."),
    ]
    for cid, title, cat, desc in r155_controls:
        db.add(m.Control(standard_id=std_r155.id, control_id=cid, title=title, category=cat, description=desc))

    r156_controls = [
        ("R156-7.1.1", "SUMS processes", "PROCESS", "Software update management system requirements."),
        ("R156-7.2.1", "Update integrity and authenticity", "PROCESS", "Verify integrity and authenticity of updates."),
        ("R156-7.2.2", "Security impact assessment", "PROCESS", "Assess security impact of software updates."),
        ("R156-7.2.3", "Safe update execution", "PROCESS", "Execute updates without compromising safety."),
    ]
    for cid, title, cat, desc in r156_controls:
        db.add(m.Control(standard_id=std_r156.id, control_id=cid, title=title, category=cat, description=desc))

    # 21434 engineering concepts (mapping layer — not a reproduction of the standard)
    concepts = [
        ("21434-ITEM", "Item definition", "CONCEPT"),
        ("21434-ASSET", "Asset identification", "CONCEPT"),
        ("21434-TARA", "Threat analysis and risk assessment", "CONCEPT"),
        ("21434-GOAL", "Cybersecurity goal", "CONCEPT"),
        ("21434-REQ", "Cybersecurity requirement", "CONCEPT"),
        ("21434-VERIF", "Verification", "CONCEPT"),
        ("21434-VALID", "Validation", "CONCEPT"),
        ("21434-CASE", "Cybersecurity case", "CONCEPT"),
        ("21434-EVID", "Evidence", "CONCEPT"),
    ]
    for cid, title, cat in concepts:
        db.add(m.Control(standard_id=std_21434.id, control_id=cid, title=title, category=cat,
                         description="Engineering concept reference for traceability mapping."))

    # ------------------------------------------------------------------ AUTOSAR mechanisms
    mech_defs = [
        ("SecOC", "Communication protection", "Secure Onboard Communication: authenticity + freshness for messages."),
        ("Crypto Service Manager", "Cryptography", "Central AUTOSAR service for cryptographic operations."),
        ("Crypto Interface", "Cryptography", "Interface abstraction to crypto drivers."),
        ("Crypto Driver", "Cryptography", "Low-level cryptographic driver implementations."),
        ("HSM", "Hardware security", "Hardware Security Module key storage and crypto acceleration."),
        ("Secure Boot", "Platform security", "Verify software integrity at startup."),
        ("Secure Diagnostics", "Diagnostics security", "Authenticate and authorize diagnostic access."),
        ("Key Management", "Key handling", "Key provisioning, storage, rotation and revocation."),
        ("Authentication", "Access control", "Entity authentication for services and messages."),
        ("Freshness", "Replay protection", "Freshness value management (counters/timestamps)."),
        ("Cryptographic services", "Cryptography", "Signature, MAC, encryption, hashing services."),
    ]
    mechs: dict[str, m.AutosarMechanism] = {}
    for name, cat, desc in mech_defs:
        mech = m.AutosarMechanism(name=name, category=cat, description=desc)
        db.add(mech)
        mechs[name] = mech
    db.flush()

    # Mechanism implementations on ECUs
    db.add_all([
        m.MechanismImplementation(mechanism_id=mechs["SecOC"].id, ecu_id=ecus["Gateway ECU"].id, status="IMPLEMENTED", notes="SecOC on CAN + Ethernet PDUs"),
        m.MechanismImplementation(mechanism_id=mechs["HSM"].id, ecu_id=ecus["Gateway ECU"].id, status="IMPLEMENTED", notes="SHE+ HSM"),
        m.MechanismImplementation(mechanism_id=mechs["Secure Boot"].id, ecu_id=ecus["Gateway ECU"].id, status="IMPLEMENTED"),
        m.MechanismImplementation(mechanism_id=mechs["Crypto Service Manager"].id, ecu_id=ecus["Gateway ECU"].id, status="IMPLEMENTED", notes="CSM v2.4 with mbedTLS backend"),
        m.MechanismImplementation(mechanism_id=mechs["Secure Boot"].id, ecu_id=ecus["ADAS ECU"].id, status="IMPLEMENTED"),
        m.MechanismImplementation(mechanism_id=mechs["Authentication"].id, ecu_id=ecus["ADAS ECU"].id, status="IMPLEMENTED"),
        m.MechanismImplementation(mechanism_id=mechs["Secure Diagnostics"].id, ecu_id=ecus["Telematics ECU"].id, status="IMPLEMENTED"),
        m.MechanismImplementation(mechanism_id=mechs["Key Management"].id, ecu_id=ecus["Telematics ECU"].id, status="IN_PROGRESS"),
        m.MechanismImplementation(mechanism_id=mechs["Secure Boot"].id, ecu_id=ecus["Battery Management ECU"].id, status="IMPLEMENTED"),
    ])

    # ------------------------------------------------------------------ assets (12)
    asset_defs = [
        ("Vehicle speed messages", "DATA", "HIGH", "Authenticated speed and dynamics signals on CAN-FD.", "Gateway ECU"),
        ("OTA update package", "DATA", "HIGH", "Signed software update payload for all ECUs.", "Telematics ECU"),
        ("Driver authentication token", "DATA", "HIGH", "Digital key / driver identity token.", "Telematics ECU"),
        ("ADAS object list", "DATA", "HIGH", "Fused object list consumed by control functions.", "ADAS ECU"),
        ("Brake-by-wire command", "FUNCTION", "HIGH", "Deceleration request from ADAS.", "ADAS ECU"),
        ("Infotainment user profile", "DATA", "MEDIUM", "Driver profile and preferences.", "Infotainment ECU"),
        ("CAN diagnostic session", "COMMUNICATION", "MEDIUM", "UDS diagnostic channel.", "Gateway ECU"),
        ("Battery state data", "DATA", "HIGH", "SOC/SOH and cell balancing data.", "Battery Management ECU"),
        ("Charging control interface", "FUNCTION", "HIGH", "External charging communication.", "Battery Management ECU"),
        ("Telematics cloud link", "COMMUNICATION", "MEDIUM", "Backend connectivity channel.", "Telematics ECU"),
        ("Firmware image store", "DATA", "HIGH", "Flash-resident firmware images.", "Gateway ECU"),
        ("V2X broadcast messages", "COMMUNICATION", "MEDIUM", "Vehicle-to-everything broadcasts.", "Telematics ECU"),
    ]
    assets: dict[str, m.Asset] = {}
    for name, atype, crit, desc, ecu_name in asset_defs:
        a = m.Asset(ecu_id=ecus[ecu_name].id, name=name, type=atype, criticality=crit, description=desc)
        db.add(a)
        assets[name] = a
    db.flush()

    # ------------------------------------------------------------------ threats (10)
    threat_defs = [
        ("Spoofed vehicle speed messages", "SPOOFING", "Compromised ECU on CAN-FD", "Vehicle speed messages"),
        ("Replay of control commands", "REPLAY", "Bus eavesdropping + injection", "Brake-by-wire command"),
        ("Tampered OTA update package", "TAMPERING", "Malicious server / MITM", "OTA update package"),
        ("Stolen driver token", "INFORMATION_DISCLOSURE", "Cloud credential theft", "Driver authentication token"),
        ("Malicious infotainment app", "TAMPERING", "Sideloading", "Infotainment user profile"),
        ("Diagnostic session abuse", "PRIVILEGE_ESCALATION", "OBD port access", "CAN diagnostic session"),
        ("Battery data falsification", "SPOOFING", "Internal sensor compromise", "Battery state data"),
        ("Charging interface attack", "DENIAL_OF_SERVICE", "Malicious EVSE", "Charging control interface"),
        ("Cloud link hijack", "REPUDIATION", "Backend compromise", "Telematics cloud link"),
        ("Malicious firmware image", "TAMPERING", "Supply chain insertion", "Firmware image store"),
    ]
    for name, ttype, vector, asset_name in threat_defs:
        db.add(m.Threat(asset_id=assets[asset_name].id, name=name,
                        description=f"Threat scenario: {name}.", threat_type=ttype, attack_vector=vector))
    db.flush()

    # ------------------------------------------------------------------ TARA (12)
    tara_defs = [
        ("Vehicle speed messages", "Loss of vehicle dynamics integrity", "Attacker injects false speed data over CAN-FD",
         "SEVERE", "HIGH", "Prevent spoofing of safety-relevant dynamics messages", "APPROVED"),
        ("Brake-by-wire command", "Unauthorized deceleration", "Replayed brake commands via bus injection",
         "SEVERE", "MEDIUM", "Guarantee authenticity and freshness of brake commands", "APPROVED"),
        ("OTA update package", "Malicious software installation", "Attacker replaces update payload in transit",
         "SEVERE", "MEDIUM", "Ensure update authenticity and integrity end-to-end", "REVIEWED"),
        ("Driver authentication token", "Vehicle theft", "Stolen digital key token reused",
         "MAJOR", "HIGH", "Protect driver tokens against theft and replay", "REVIEWED"),
        ("Firmware image store", "Persistent ECU compromise", "Malicious firmware written to flash",
         "SEVERE", "MEDIUM", "Only execute authenticated firmware images", "APPROVED"),
        ("CAN diagnostic session", "Unauthorized reprogramming", "Unauthenticated UDS session access",
         "MAJOR", "HIGH", "Authenticate and authorize diagnostic operations", "REVIEWED"),
        ("Battery state data", "Battery damage", "Falsified SOC data causes overcharge",
         "SEVERE", "MEDIUM", "Protect battery telemetry integrity", "DRAFT"),
        ("Charging control interface", "Charging disruption", "Malicious EVSE floods charging bus",
         "MODERATE", "HIGH", "Resist denial of service on charging interface", "DRAFT"),
        ("Infotainment user profile", "Privacy violation", "Malicious app exfiltrates profile data",
         "MODERATE", "HIGH", "Contain infotainment app privileges", "REVIEWED"),
        ("Telematics cloud link", "Loss of remote services", "Backend channel hijacked",
         "MAJOR", "MEDIUM", "Mutual authentication with backend", "REVIEWED"),
        ("ADAS object list", "Perception spoofing", "Injected objects in fused list",
         "SEVERE", "MEDIUM", "Protect perception data integrity", "DRAFT"),
        ("V2X broadcast messages", "False V2X information", "Broadcast of misleading V2X frames",
         "MAJOR", "MEDIUM", "Authenticate V2X broadcasts", "DRAFT"),
    ]
    taras: list[m.TARA] = []
    tara_count = len(list(db.scalars(select(m.TARA)))) + 1
    for i, (asset_name, damage, threat_scenario, impact, feasibility, goal, tstatus) in enumerate(tara_defs, start=tara_count):
        risk, il, fl, _ = calculate_risk(impact, feasibility)
        tara = m.TARA(
            asset_id=assets[asset_name].id,
            reference=f"TARA-{i:03d}",
            damage_scenario=damage,
            threat_scenario=threat_scenario,
            impact=impact, impact_level=il,
            attack_feasibility=feasibility, feasibility_level=fl,
            risk_level=risk,
            cybersecurity_goal=goal,
            status=tstatus,
            reviewed_at=dt.datetime.now(dt.timezone.utc) if tstatus in ("REVIEWED", "APPROVED") else None,
        )
        db.add(tara)
        taras.append(tara)
    db.flush()

    # ------------------------------------------------------------------ requirements (16)
    req_defs = [
        ("CS-REQ-001", "Authenticated vehicle dynamics messages", "Safety-relevant CAN-FD messages shall be authenticated.", "HIGH", "APPROVED", 0),
        ("CS-REQ-002", "Freshness for brake commands", "Brake commands shall include replay protection via freshness values.", "HIGH", "APPROVED", 1),
        ("CS-REQ-003", "Signed OTA packages", "Update packages shall be cryptographically signed and verified before installation.", "HIGH", "APPROVED", 2),
        ("CS-REQ-004", "Token binding", "Driver tokens shall be bound to the vehicle and session.", "HIGH", "REVIEWED", 3),
        ("CS-REQ-005", "Secure boot enforcement", "All ECUs shall verify firmware signatures before execution.", "HIGH", "APPROVED", 4),
        ("CS-REQ-006", "Authenticated diagnostics", "Diagnostic sessions above default level shall require authentication.", "HIGH", "REVIEWED", 5),
        ("CS-REQ-007", "Battery telemetry integrity", "Battery state data shall be integrity protected end-to-end.", "MEDIUM", "REVIEWED", 6),
        ("CS-REQ-008", "Charging DoS resilience", "Charging control shall remain available under malformed input.", "MEDIUM", "DRAFT", 7),
        ("CS-REQ-009", "Infotainment sandboxing", "Third-party apps shall run with least privilege.", "MEDIUM", "REVIEWED", 8),
        ("CS-REQ-010", "Backend mutual authentication", "Telematics shall mutually authenticate with backend services.", "HIGH", "REVIEWED", 9),
        ("CS-REQ-011", "Perception data protection", "ADAS object list consumers shall verify data origin.", "HIGH", "DRAFT", 10),
        ("CS-REQ-012", "V2X message authentication", "V2X broadcasts shall carry verifiable signatures.", "MEDIUM", "DRAFT", 11),
        ("CS-REQ-013", "Crypto library integrity", "The gateway crypto library shall be measured and verified at boot.", "HIGH", "APPROVED", 4),
        ("CS-REQ-014", "Key rotation support", "The key management solution shall support key rotation.", "MEDIUM", "REVIEWED", 3),
        ("CS-REQ-015", "Audit logging", "Security-relevant events shall be logged with timestamps.", "MEDIUM", "APPROVED", 5),
        ("CS-REQ-016", "Secure diagnostic locking", "Diagnostic unlocks shall time out automatically.", "MEDIUM", "REVIEWED", 5),
    ]
    reqs: dict[str, m.CybersecurityRequirement] = {}
    for rid, title, desc, prio, rstatus, t_idx in req_defs:
        req = m.CybersecurityRequirement(
            tara_id=taras[t_idx].id, requirement_id=rid, title=title,
            description=desc, priority=prio, status=rstatus,
        )
        db.add(req)
        reqs[rid] = req
    db.flush()

    # Requirement ↔ AUTOSAR mechanism mappings (12+)
    mech_links = [
        ("CS-REQ-001", "SecOC", "SecOC provides authenticity for CAN-FD PDUs"),
        ("CS-REQ-001", "Authentication", ""),
        ("CS-REQ-002", "SecOC", "Freshness value manager integrated with SecOC"),
        ("CS-REQ-002", "Freshness", ""),
        ("CS-REQ-003", "Cryptographic services", "Signature verification via CSM"),
        ("CS-REQ-003", "Secure Boot", ""),
        ("CS-REQ-004", "Authentication", ""),
        ("CS-REQ-004", "Key Management", ""),
        ("CS-REQ-005", "Secure Boot", ""),
        ("CS-REQ-005", "HSM", "Root of trust in HSM"),
        ("CS-REQ-006", "Secure Diagnostics", ""),
        ("CS-REQ-006", "Authentication", ""),
        ("CS-REQ-007", "SecOC", ""),
        ("CS-REQ-010", "Crypto Service Manager", ""),
        ("CS-REQ-010", "Authentication", ""),
        ("CS-REQ-013", "Secure Boot", "Crypto library hash measured at boot"),
        ("CS-REQ-013", "HSM", ""),
        ("CS-REQ-014", "Key Management", ""),
    ]
    for rid, mech_name, notes in mech_links:
        db.add(m.RequirementMechanismLink(requirement_id=reqs[rid].id, mechanism_id=mechs[mech_name].id, notes=notes))

    # Requirement ↔ NIST control mappings
    control_links = [
        ("CS-REQ-001", "SC-8"), ("CS-REQ-001", "SC-13"),
        ("CS-REQ-002", "SC-8"),
        ("CS-REQ-003", "SI-2"), ("CS-REQ-003", "SA-10"),
        ("CS-REQ-005", "CM-7"), ("CS-REQ-005", "IA-5"),
        ("CS-REQ-006", "AC-2"), ("CS-REQ-006", "IA-2"),
        ("CS-REQ-009", "AC-3"), ("CS-REQ-009", "CM-7"),
        ("CS-REQ-010", "IA-2"), ("CS-REQ-010", "SC-8"),
        ("CS-REQ-013", "CM-2"), ("CS-REQ-013", "SI-2"),
        ("CS-REQ-015", "AU-2"), ("CS-REQ-015", "AU-6"),
        ("CS-REQ-014", "IA-5"), ("CS-REQ-016", "AC-2"),
    ]
    for rid, cid in control_links:
        db.add(m.RequirementControlLink(requirement_id=reqs[rid].id, control_id=controls[cid].id))

    # ------------------------------------------------------------------ test cases (12) + results
    test_defs = [
        ("TC-SECOC-001", "SecOC message authentication verification", "Verify CAN-FD speed messages rejected when MAC invalid", "FUNCTIONAL", "PASSED", "CS-REQ-001"),
        ("TC-SECOC-002", "Freshness replay rejection", "Replay captured brake command; expect rejection", "PENETRATION", "PASSED", "CS-REQ-002"),
        ("TC-OTA-001", "OTA signature verification", "Install unsigned package; expect refusal", "FUNCTIONAL", "PASSED", "CS-REQ-003"),
        ("TC-OTA-002", "OTA rollback protection", "Attempt version rollback; expect refusal", "FUNCTIONAL", "FAILED", "CS-REQ-003"),
        ("TC-KEY-001", "Driver token binding check", "Use stolen token on another vehicle; expect refusal", "PENETRATION", "PASSED", "CS-REQ-004"),
        ("TC-BOOT-001", "Secure boot tamper detection", "Corrupt firmware image; expect boot refusal", "FUNCTIONAL", "PASSED", "CS-REQ-005"),
        ("TC-DIAG-001", "Diagnostic authentication enforcement", "Run reprogramming session without auth; expect denial", "FUNCTIONAL", "PASSED", "CS-REQ-006"),
        ("TC-DIAG-002", "Diagnostic unlock timeout", "Unlock then wait; verify lock returns", "FUNCTIONAL", "NOT_RUN", "CS-REQ-016"),
        ("TC-BMS-001", "Battery data integrity check", "Inject modified SOC frames; expect rejection", "FUZZ", "FAILED", "CS-REQ-007"),
        ("TC-INFO-001", "Infotainment sandbox escape attempt", "Malicious app attempts IPC escalation; expect containment", "PENETRATION", "PASSED", "CS-REQ-009"),
        ("TC-CLOUD-001", "Backend mutual TLS handshake", "Verify client cert required for cloud link", "CONFIG_REVIEW", "PASSED", "CS-REQ-010"),
        ("TC-CRYPTO-001", "Crypto library boot measurement", "Verify hash measurement of crypto library at boot", "CONFIG_REVIEW", "NOT_RUN", "CS-REQ-013"),
    ]
    tests: dict[str, m.TestCase] = {}
    for tid, name, desc, ttype, result_status, rid in test_defs:
        tc = m.TestCase(
            requirement_id=reqs[rid].id, name=name, description=desc,
            test_type=ttype, expected_result="Security behavior as specified in the requirement.",
            status=result_status,
        )
        db.add(tc)
        tests[tid] = tc
    db.flush()
    for tid, _, _, _, result_status, _ in test_defs:
        if result_status != "NOT_RUN":
            db.add(m.TestResult(
                test_case_id=tests[tid].id,
                result=m.TestStatus(result_status),
                tester="Tina Tester",
                notes=f"Executed in demo validation run ({result_status}).",
            ))

    # ------------------------------------------------------------------ evidence
    evidence_defs = [
        ("SecOC configuration report", "CONFIG", "APPROVED", "CS-REQ-001", "docs/evidence/secoc-config.pdf"),
        ("SecOC replay test report", "TEST_REPORT", "APPROVED", "CS-REQ-002", "docs/evidence/secoc-replay-test.pdf"),
        ("OTA signature verification report", "TEST_REPORT", "APPROVED", "CS-REQ-003", "docs/evidence/ota-sig-test.pdf"),
        ("Secure boot analysis", "ANALYSIS", "APPROVED", "CS-REQ-005", "docs/evidence/secure-boot-analysis.pdf"),
        ("Diagnostic security test report", "TEST_REPORT", "SUBMITTED", "CS-REQ-006", "docs/evidence/diag-auth-test.pdf"),
        ("Crypto library measurement log", "LOG", "DRAFT", "CS-REQ-013", "docs/evidence/crypto-measure.log"),
        ("TARA workshop minutes", "DOCUMENT", "APPROVED", None, "docs/evidence/tara-minutes.pdf"),
        ("R155 CSMS process description", "DOCUMENT", "APPROVED", None, "docs/evidence/r155-csms-process.pdf"),
        ("R156 update integrity procedure", "DOCUMENT", "APPROVED", None, "docs/evidence/r156-update-integrity.pdf"),
    ]
    for name, etype, estatus, rid, ref in evidence_defs:
        db.add(m.Evidence(
            name=name, type=etype, status=m.EvidenceStatus(estatus),
            description=f"Demo evidence item: {name}.", file_reference=ref,
            requirement_id=reqs[rid].id if rid else None,
        ))

    # ------------------------------------------------------------------ software components + vulnerabilities
    comp_defs = [
        ("mbedTLS crypto library", "2.4.0", "TrustedFirmware (demo)", "Gateway ECU"),
        ("SecOC module", "3.2.1", "Vector (demo)", "Gateway ECU"),
        ("OTA update agent", "1.8.0", "Excelfore (demo)", "Telematics ECU"),
        ("ADAS perception stack", "5.1.0", "Aptiv (demo)", "ADAS ECU"),
        ("Infotainment OS image", "4.7.2", "Harman (demo)", "Infotainment ECU"),
        ("BMS firmware", "1.9.0", "CATL (demo)", "Battery Management ECU"),
    ]
    comps: dict[str, m.SoftwareComponent] = {}
    for name, version, supplier, ecu_name in comp_defs:
        c = m.SoftwareComponent(ecu_id=ecus[ecu_name].id, name=name, version=version, supplier=supplier, hash="")
        db.add(c)
        comps[name] = c
    db.flush()

    vuln_defs = [
        ("CVE-2025-55555", 9.1, "CRITICAL", "mbedTLS crypto library",
         "Buffer overflow in TLS handshake parsing (demo data).", "OPEN",
         "Upgrade to crypto library v2.5.0 which includes the fix."),
        ("CVE-2025-44444", 7.5, "HIGH", "OTA update agent",
         "Improper signature verification under error conditions (demo data).", "OPEN",
         "Patch OTA agent to v1.8.2; enforce strict verification paths."),
        ("CVE-2025-33333", 5.3, "MEDIUM", "Infotainment OS image",
         "Local info leak in media service (demo data).", "IN_PROGRESS",
         "Apply vendor patch; restrict media service privileges."),
        ("CVE-2024-22222", 8.1, "HIGH", "SecOC module",
         "Freshness value desync allows limited replay window (demo data).", "RESOLVED",
         "Patched in SecOC module v3.2.1; counters re-synced."),
    ]
    for cve, score, sev, comp_name, desc, vstatus, remediation in vuln_defs:
        db.add(m.Vulnerability(
            component_id=comps[comp_name].id, cve_id=cve, cvss_score=score,
            severity=m.Severity(sev), description=desc, status=vstatus, remediation=remediation,
        ))

    # ------------------------------------------------------------------ SBOM (CycloneDX, Gateway ECU)
    import hashlib
    import json

    cyclonedx = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "components": [
            {"type": "library", "name": "mbedTLS crypto library", "version": "2.4.0", "purl": "pkg:generic/mbedtls@2.4.0",
             "licenses": [{"license": {"id": "Apache-2.0"}}],
             "hashes": [{"alg": "SHA-256", "content": hashlib.sha256(b"mbedtls-2.4.0").hexdigest()}]},
            {"type": "library", "name": "SecOC module", "version": "3.2.1", "purl": "pkg:generic/secoc@3.2.1",
             "licenses": [{"license": {"id": "Proprietary"}}]},
            {"type": "application", "name": "gateway-core", "version": "2.4.0", "purl": "pkg:generic/gateway-core@2.4.0"},
            {"type": "library", "name": "FreeRTOS", "version": "10.5.1", "purl": "pkg:generic/freertos@10.5.1",
             "licenses": [{"license": {"id": "MIT"}}]},
            {"type": "library", "name": "lwIP", "version": "2.1.3", "purl": "pkg:generic/lwip@2.1.3"},
        ],
    }
    from .sbom import parse_sbom

    doc = parse_sbom(json.dumps(cyclonedx), "CycloneDX")
    sbom = m.SBOM(
        vehicle_id=vehicle.id, ecu_id=ecus["Gateway ECU"].id,
        format=doc.format, file_name="gateway-ecu-sbom-cyclonedx.json",
        version="2.4.0", component_count=len(doc.entries),
    )
    db.add(sbom)
    db.flush()
    for entry in doc.entries:
        db.add(m.SbomComponent(
            sbom_id=sbom.id, name=entry.name, version=entry.version,
            purl=entry.purl, license=entry.license, hash=entry.hash,
            component_type=entry.component_type,
        ))

    # ------------------------------------------------------------------ releases (3)
    rel_gateway = m.Release(ecu_id=ecus["Gateway ECU"].id, version="2.4.0", release_type="PRODUCTION",
                            release_date=dt.date(2026, 6, 1), status="RELEASED")
    rel_adas = m.Release(ecu_id=ecus["ADAS ECU"].id, version="5.1.0", release_type="PRODUCTION",
                         release_date=dt.date(2026, 7, 15), status="IN_VALIDATION")
    rel_tcu = m.Release(ecu_id=ecus["Telematics ECU"].id, version="3.3.1", release_type="OTA",
                        release_date=dt.date(2026, 9, 1), status="PLANNED")
    db.add_all([rel_gateway, rel_adas, rel_tcu])
    db.flush()

    # ------------------------------------------------------------------ the flagship change
    db.add(m.Change(
        entity_type="SoftwareComponent",
        entity_id=comps["mbedTLS crypto library"].id,
        change_type=m.ChangeType.CRYPTO_LIBRARY_CHANGE,
        description="Gateway ECU crypto library v2.4 → v2.5 (mbedTLS 2.4.0 → 2.5.0) to remediate CVE-2025-55555 and harden TLS handshake parsing.",
        created_by="engineer@autocybergraph.io",
        security_assessment="Security impact assessment pending: signature algorithm compatibility, HSM key handle mapping, SecOC MAC derivation and boot measurement update must be re-verified before release.",
    ))

    # ------------------------------------------------------------------ supplier + submission
    supplier = m.Supplier(organization_id=supplier_org.id, name="Bosch-like Tier1 (Demo)",
                          type="TIER1", contact="security@tier1-demo.example")
    db.add(supplier)
    db.flush()
    db.add(m.SupplierSubmission(
        supplier_id=supplier.id, kind="SBOM",
        title="Gateway ECU SBOM v2.5.0 candidate",
        description="Updated CycloneDX SBOM for gateway-core v2.5.0 including mbedTLS 2.5.0.",
        payload={"file_name": "gateway-ecu-sbom-2.5.0.json", "format": "CycloneDX", "components": 6},
        status=m.SubmissionStatus.SUBMITTED,
        created_by="supplier@autocybergraph.io",
    ))
    db.add(m.SupplierSubmission(
        supplier_id=supplier.id, kind="TEST_RESULT",
        title="SecOC regression test results — gateway v2.5.0",
        description="Regression run of TC-SECOC-001/002 on release candidate.",
        payload={"tests": ["TC-SECOC-001", "TC-SECOC-002"], "result": "PASSED"},
        status=m.SubmissionStatus.SUBMITTED,
        created_by="supplier@autocybergraph.io",
    ))

    # ------------------------------------------------------------------ compliance mappings (sample)
    db.add_all([
        m.ComplianceMapping(source_entity="TARA", source_id=taras[0].id, standard="ISO/SAE 21434",
                            control_id="21434-TARA", mapping_type="concept", confidence="HIGH",
                            notes="TARA-001 represents the 21434 TARA concept for vehicle dynamics assets."),
        m.ComplianceMapping(source_entity="CybersecurityRequirement", source_id=reqs["CS-REQ-003"].id,
                            standard="UNECE R156", control_id="R156-7.2.1", mapping_type="trace", confidence="HIGH",
                            notes="Signed OTA packages support update integrity and authenticity."),
        m.ComplianceMapping(source_entity="CybersecurityRequirement", source_id=reqs["CS-REQ-003"].id,
                            standard="ISO/SAE 21434", control_id="21434-REQ", mapping_type="concept", confidence="MEDIUM",
                            notes="Cybersecurity requirement derived from TARA-003."),
        m.ComplianceMapping(source_entity="Evidence", source_id=1, standard="UNECE R155",
                            control_id="R155-7.2.2.2", mapping_type="evidence", confidence="MEDIUM",
                            notes="SecOC configuration report supports CSMS process evidence."),
        m.ComplianceMapping(source_entity="Release", source_id=rel_gateway.id, standard="UNECE R156",
                            control_id="R156-7.2.2", mapping_type="process", confidence="MEDIUM",
                            notes="Release 2.4.0 went through the software update security impact workflow."),
    ])

    db.commit()
    return {
        "status": "seeded",
        "vehicle_id": vehicle.id,
        "ecus": len(ecu_defs),
        "assets": len(asset_defs),
        "threats": len(threat_defs),
        "taras": len(tara_defs),
        "requirements": len(req_defs),
        "tests": len(test_defs),
        "releases": 3,
    }
