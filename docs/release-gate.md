# Cybersecurity Release Gate

> Deliberately **not** a "security score". A release receives a deterministic
> verdict and the exact list of failed checks that produced it.

## Verdicts

| Result | Meaning |
|--------|---------|
| `PASS` | All checks passed |
| `REVIEW` | No blocking failure; advisory checks need human review |
| `HOLD`  | At least one **BLOCKING** check failed — do not release |

## Checks

| Key | Severity | What it verifies |
|-----|----------|------------------|
| `tara_reviewed` | BLOCKING / WARNING | All TARA scenarios in scope are REVIEWED/APPROVED |
| `requirements_traced` | BLOCKING / WARNING | Every requirement has a test **and** evidence |
| `tests_completed` | BLOCKING (failing) / WARNING | Latest results exist and pass |
| `vulns_resolved` | BLOCKING | No OPEN CRITICAL/HIGH vulnerability in scope |
| `sbom_available` | BLOCKING | An SBOM exists for the release's ECU |
| `autosar_mappings` | WARNING | Every requirement has an AUTOSAR mechanism mapping |
| `evidence_available` | WARNING | Sufficient approved evidence in scope |
| `security_impact` | BLOCKING | Every change in scope has a completed impact analysis |

Scope = the release's ECU → its assets → TARA → requirements → tests; its
components → vulnerabilities; its SBOMs and releases.

## Why reasons, not scores

A weighted score hides *what* is wrong. AutoCyberGraph returns, per check:

```json
{
  "key": "vulns_resolved",
  "label": "Critical/high vulnerabilities resolved",
  "passed": false,
  "severity": "BLOCKING",
  "detail": "1 open critical/high vulnerability(ies): CVE-2025-55555"
}
```

plus a human-readable `reasons` list. Teams act on the failing check — the
number would not tell them what to do.

## State effects

Evaluating a gate persists `gate_result`, `gate_reasons` and
`gate_evaluated_at` on the release. `PASS` promotes `PLANNED/IN_VALIDATION` to
`APPROVED`; `HOLD` sets the release to `BLOCKED`.

## API

- `POST /api/releases/{id}/evaluate`
- `GET /api/releases` (includes last gate result per release)
