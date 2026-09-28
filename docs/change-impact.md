# Change Impact Engine

> The core differentiator of AutoCyberGraph.

## Why it exists

A software component, ECU, AUTOSAR configuration, network message, crypto
library, requirement, TARA entry or vulnerability **will** change during a
vehicle program. The question is never *if* cybersecurity artifacts are
affected — it is *which ones*, and *why*.

## How it works

1. **Record a change** (`POST /api/changes`) with:
   - `entity_type` + `entity_id` — what changed (e.g. `SoftwareComponent:1`)
   - `change_type` — `SOFTWARE_CHANGE`, `CRYPTO_LIBRARY_CHANGE`, `AUTOSAR_CONFIG_CHANGE`,
     `ECU_CHANGE`, `NETWORK_MESSAGE_CHANGE`, `REQUIREMENT_CHANGE`, `TARA_CHANGE`,
     `VULNERABILITY`, `SBOM_CHANGE`
   - `description` and optional R156-style `security_assessment`
2. **Run impact analysis** (`POST /api/changes/{id}/impact`):
   - BFS traversal of the traceability graph from the changed entity
     (`GraphService.bfs`, both directions, depth-bounded)
   - Affected artifacts are **exactly the reachable objects** — no guesses
   - Every object carries the **graph path** that made it affected
3. **Report**:
   - `impact_level`: `CRITICAL | HIGH | MEDIUM | LOW`
   - Counts per bucket (requirements, TARA, tests, controls, mechanisms,
     evidence, releases, vulnerabilities, SBOM, ECU, vehicle…)
   - `rationale` explaining the scoring
   - `recommended_actions` derived from *what* is affected

## Impact level scoring

Score composition (see `services/impact.py`):

- Change-type weight (crypto change / vulnerability > config change > SBOM change)
- +1 for reachable HIGH/CRITICAL-risk TARA
- +2 for reachable open CRITICAL/HIGH vulnerabilities
- +1 for reachable releases
- +1 for HIGH-criticality ECU in scope

Thresholds: `≥8 CRITICAL · ≥5 HIGH · ≥3 MEDIUM · else LOW`.

## Example: Gateway ECU crypto library v2.4 → v2.5

```
Change: CRYPTO_LIBRARY_CHANGE on SoftwareComponent (mbedTLS 2.4.0)

Affected (from the demo dataset):
  16 requirements · 12 TARA scenarios · 12 tests · 12 controls
  9 AUTOSAR mechanisms · 6 evidence items · 4 vulnerabilities
  3 releases · 1 SBOM · 5 components · 1 vehicle · …

Sample reason (per object):
  "CybersecurityRequirement:CS-REQ-001 → [TARA derives cybersecurity requirement]"

Recommended actions include re-reviewing TARA, re-running security tests,
re-verifying AUTOSAR configurations, publishing an updated SBOM and running
the Cybersecurity Release Gate.
```

## Honesty constraints

- An object is affected **iff** it is reachable in the recorded relationships —
  the engine never fabricates impact
- Each reason names the actual relationship (`ECU runs software component`,
  `Requirement verified by test`, …)
- If the graph has no path between the change and an artifact, the artifact is
  not reported

## API

- `POST /api/changes` — record a change
- `GET /api/changes` — list (newest first)
- `POST /api/changes/{id}/impact` — run and persist the analysis
