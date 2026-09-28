# AutoCyberGraph — Project Plan

**Tagline:** Connect Automotive Cybersecurity Risk to Reality.

**Category:** Automotive Cybersecurity Digital Thread / Evidence Graph

**Status:** MVP (v0.1.0) — implemented, tested, documented, deployment-ready.

> **Disclaimer:** AutoCyberGraph is an engineering and evidence-management platform.
> It does not provide legal, regulatory, certification, or compliance advice.

---

## 1. Vision

AutoCyberGraph connects automotive cybersecurity engineering, risk, implementation,
testing, vulnerabilities, software changes, and compliance evidence into one
traceable system:

```
Vehicle → ECU → Software → Asset → Threat → TARA → Cybersecurity Goal
→ Requirement → Security Control → AUTOSAR Security Mechanism → Test
→ Vulnerability → Evidence → Release → R155 / R156 / ISO 21434 / NIST mapping
```

**Key differentiator:** *Change Impact Analysis* across the entire lifecycle. When a
software component, ECU, AUTOSAR configuration, network message, crypto library,
requirement or vulnerability changes, the engine identifies affected cybersecurity
artifacts and evidence — and **explains why** via actual graph paths.

## 2. Scope

### In scope (MVP v0.1.0)
- Authentication (JWT) + RBAC (7 roles) + organization-scoped authorization
- Full domain model (18 entity types) with relationship/traceability graph
- Dashboard with live metrics (every metric links to real data)
- Vehicle architecture view (ECUs + networks)
- TARA workflow with configurable risk calculation (Low/Medium/High/Critical)
- Requirement traceability with missing-link detection
- Standards mapping layers: ISO/SAE 21434, UNECE R155, UNECE R156, NIST SP 800-53, AUTOSAR security
- SBOM import (CycloneDX robust, SPDX JSON basic) + vulnerability engine (CVE/CVSS)
- **Change Impact Engine** (graph traversal with reasoned explanations)
- **Cybersecurity Release Gate** (PASS / REVIEW / HOLD with reasons — no vanity score)
- Evidence graph (interactive, navigable)
- Supplier portal (submit / review / approve / reject with org-level authorization)
- CyberAdvisor (DB-grounded question answering; refuses to invent conclusions)
- Realistic demo dataset incl. `Crypto library v2.4 → v2.5` change scenario
- Public landing page, docs, CI, Docker, deployment preparation

### Out of scope (documented future work)
- Neo4j-backed graph store (abstraction layer is in place: `app/graph.py`)
- Machine-readable control catalog import (NIST OSCAL) — API designed for it
- Full text of any standard (we reference, never reproduce)
- LLM-backed CyberAdvisor (adapter interface present; rule engine is the MVP)
- Real file blob storage (evidence `file_reference` is a URI/ref; storage config documented)

## 3. Delivery Phases

| Phase | Content | Status |
|-------|---------|--------|
| 1 | Project setup, auth, database, core entities, dashboard, demo data | ✅ |
| 2 | Vehicle architecture, ECU, asset, TARA, requirements | ✅ |
| 3 | Traceability graph, standards mapping, AUTOSAR security | ✅ |
| 4 | SBOM, vulnerabilities, Change Impact Engine | ✅ |
| 5 | Release Gate, evidence management, supplier portal | ✅ |
| 6 | CyberAdvisor | ✅ |
| 7 | Testing, security hardening, documentation, deployment prep | ✅ |

## 4. Development Loop

`PLAN → BUILD → RUN → TEST → FIX → REFACTOR → DOCUMENT → DEPLOY → VERIFY`

Engineering rules:
- Simplest reliable approach wins; decision recorded in `DECISIONS.md`.
- No placeholder buttons, fake metrics, fake AI responses or fake compliance claims.
- Every dashboard metric links to real application data.
- Tests cover: auth, RBAC, TARA risk calculation, traceability, change-impact engine,
  vulnerability mapping, release gate, SBOM import, and the end-to-end
  *Change → Impact → Release Gate* integration path.

## 5. Milestones

1. **v0.1.0 — MVP** (this release): all success criteria in the build brief.
2. **v0.2.0 (roadmap)**: Neo4j adapter, OSCAL catalog import, file storage backends,
   richer supplier workflows, LLM CyberAdvisor adapter, i18n.

## 6. Quality Bar

Optimized for: working workflows, clean UX, traceability, correctness, security,
maintainability, demonstrability. See `README.md` for the 3-minute demo script.
