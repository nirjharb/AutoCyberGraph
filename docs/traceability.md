# Requirement Traceability

## The traceability spine

```
Requirement
   ↓
TARA
   ↓
Asset
   ↓
Threat
   ↓
Control
   ↓
AUTOSAR Mechanism
   ↓
Test
   ↓
Evidence
```

Every cybersecurity requirement exposes a **traceability checklist**:

```
Requirement CS-REQ-017

✓ TARA linked
✓ Asset linked
✓ AUTOSAR mechanism linked
✓ Test linked
✗ Evidence missing
```

Missing links are first-class data (`missing_links` in the API, red ✗ cards in
the UI) — not something a user has to compare documents to discover.

## How links are created

| Link | Created via |
|------|-------------|
| Requirement → TARA | `POST /api/requirements` (`tara_id`) |
| Requirement → Control | `POST /api/requirements/{id}/controls` |
| Requirement → AUTOSAR mechanism | `POST /api/requirements/{id}/mechanisms` |
| Requirement → Test | `POST /api/tests` (`requirement_id`) |
| Requirement → Evidence | `POST /api/evidence` (`requirement_id`) |
| TARA → Asset / Threat | TARA creation (`asset_id`, `threat_id`) |

## API

- `GET /api/requirements?missing=evidence` — requirements missing evidence
- `GET /api/requirements?missing=tests` — requirements missing tests
- `GET /api/requirements/{id}/traceability` — full detail + checklist + graph neighbors

## Evidence graph

`GET /api/evidence-graph?requirement_id=…` returns a Cytoscape-ready subgraph
(TARA → goal → requirement → control → mechanism → test → evidence) rendered on
the **Evidence Graph** page. Node clicks navigate to detail pages.
