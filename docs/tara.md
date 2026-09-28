# TARA Module

> **Important:** The risk calculation implemented in AutoCyberGraph is an
> **application implementation of a risk method**. It is **not** an official
> ISO/SAE 21434 certification methodology and must not be presented as one.
> The method is configurable per organization.

## Workflow

1. **Select an asset** (assets live on ECUs; ECUs belong to vehicles)
2. **Create a damage scenario** — what harm occurs when the asset is compromised?
3. **Create a threat scenario** — how could the damage be caused?
4. **Define impact** — `NEGLIGIBLE | MINOR | MODERATE | MAJOR | SEVERE`
5. **Define attack feasibility** — `VERY_LOW | LOW | MEDIUM | HIGH | VERY_HIGH`
6. **Calculate risk** — computed automatically (see below)
7. **Define the cybersecurity goal** — what must be prevented/ensured?
8. **Derive cybersecurity requirements** — linked back to the TARA entry

Status lifecycle: `DRAFT → REVIEWED → APPROVED` (review/approval timestamps are recorded).

## Risk calculation

Implemented in `backend/app/services/risk.py`:

```
score = (impact_level + 1) × (feasibility_level + 1)      # range 1..25

CRITICAL   score ≥ 20
HIGH       score ≥ 12
MEDIUM     score ≥ 6
LOW        otherwise
```

Label → level maps (`IMPACT_LEVELS`, `FEASIBILITY_LEVELS`) and thresholds
(`THRESHOLDS`) are plain data structures — organizations can adapt them to
their own risk methodology without code changes elsewhere.

### Why this shape?

- Deterministic and unit-tested
- Monotonic: more impact or more feasibility never lowers risk
- Configurable without claiming normative conformance to any standard

## Mapping to ISO/SAE 21434 concepts

AutoCyberGraph represents the *concepts* of item definition, asset, TARA,
cybersecurity goal, cybersecurity requirement, verification, validation,
cybersecurity case and evidence as traceability objects and mapping rows
(`ComplianceMapping`, `mapping_type="concept"`). The standard itself is never
reproduced.

## API

- `GET /api/tara` — list (filter by `asset_id`, `risk_level`)
- `POST /api/tara` — create (risk calculated server-side)
- `GET /api/tara/{id}` / `PATCH /api/tara/{id}` — detail / update (risk recalculated on impact/feasibility change)
- `GET /api/tara/{id}/requirements` — derived requirements + goal
