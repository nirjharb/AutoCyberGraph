# AutoCyberGraph — Release Notes

## v0.1.0 — MVP (2026-09-28)

**Connect Automotive Cybersecurity Risk to Reality.**

### What was built

AutoCyberGraph — an open-source automotive cybersecurity digital thread /
evidence graph platform. Full-stack monorepo: React + Vite frontend, FastAPI +
SQLAlchemy backend, SQLite/PostgreSQL, JWT + RBAC, Docker + CI, documentation
and a realistic demo dataset.

### Major features

- **Traceability spine** — Vehicle → ECU → Software → Asset → Threat → TARA →
  Goal → Requirement → Control → AUTOSAR Mechanism → Test → Evidence → Release
  → standards mappings (18 entity types, typed graph edges)
- **Change Impact Engine** *(core differentiator)* — graph traversal from any
  change; every affected artifact carries the relationship path that made it
  affected; impact levels + recommended actions
- **Cybersecurity Release Gate** — 8 deterministic checks → PASS / REVIEW /
  HOLD with reasons (no vanity scores)
- **TARA workflow** — configurable risk matrix (documented as an application
  implementation, not a certification methodology)
- **Requirement traceability** — checklist with missing-link detection
- **Evidence graph** — interactive Cytoscape visualization with click-through
- **SBOM & vulnerability engine** — CycloneDX + SPDX import, CVE → Component →
  ECU → Vehicle traceability
- **Standards mapping layers** — ISO/SAE 21434, UNECE R155, R156, NIST SP 800-53
  (representative controls), AUTOSAR security mechanism catalog
- **Supplier portal** — submissions + OEM review workflow with org-scoped
  authorization
- **CyberAdvisor** — DB-grounded Q&A; replies *"Insufficient evidence in the
  project database."* when the data cannot answer; never invents compliance
  conclusions
- **Security** — bcrypt + JWT, 7-role RBAC, audit logging, rate limiting,
  security headers, threat model (`docs/security.md`)
- **Demo dataset** — Demo EV Platform (5 ECUs, 12 assets, 10 threats, 12 TARA,
  16 requirements, 12 tests, 4 CVEs, 3 releases) including the flagship
  *Gateway ECU crypto library v2.4 → v2.5* change scenario

### Testing

- 34 backend tests (auth, RBAC, risk calculation, traceability, impact engine,
  vulnerability mapping, release gate, SBOM, CyberAdvisor, security baselines)
  including the flagship *Change → Impact → Release Gate* integration test
- 8 frontend tests (login, dashboard, traceability display, change-impact
  display, release-gate display)
- CI: lint + tests + build + dependency audit + Docker build (Python 3.11–3.13)

### Demo instructions

```bash
bash scripts/dev.sh     # http://localhost:8000
# sign in: engineer@autocybergraph.io / ChangeMe123!
```

Follow the 3-minute demo flow in the README.

### Known limitations

- Graph traversal computed in the service layer (Neo4j adapter is a roadmap
  item; the protocol is already defined)
- SPDX parsing is document/package level (CycloneDX is the robust path)
- Evidence stores file references, not blobs (storage backend is pluggable)
- CyberAdvisor MVP is a deterministic query engine (LLM adapter interface exists)
- Refresh-token rotation and multi-tenant row isolation are roadmap items
- Risk matrix is an application method — configurable, not normative

### Roadmap (v0.2.0)

Neo4j backend · NIST OSCAL catalog import · object-storage evidence backends ·
refresh-token rotation · LLM CyberAdvisor adapter · richer R156 update workflow.

---

**Disclaimer:** AutoCyberGraph is an engineering and evidence-management
platform. It does not provide legal, regulatory, certification, or compliance
advice. ISO/SAE 21434, UNECE R155, UNECE R156, NIST SP 800-53 and AUTOSAR
security are represented as reference/mapping concepts only.
