# API Reference

Interactive documentation is served by the running application:

- **Swagger UI:** `/api/docs`
- **ReDoc:** `/api/redoc`
- **OpenAPI JSON:** `/openapi.json`

All endpoints (except `/api/health`, `/api/meta` and the frontend) require
`Authorization: Bearer <JWT>` from `POST /api/auth/login`.

## Endpoint overview

### Auth
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | Register (roles below ADMIN) |
| POST | `/api/auth/login` | Obtain JWT |
| GET | `/api/auth/me` | Current user |
| GET | `/api/auth/users` | List users (ADMIN) |

### Vehicle architecture
| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/api/vehicles` | List / create vehicles |
| GET | `/api/vehicles/{id}` | Vehicle detail |
| GET | `/api/vehicles/{id}/architecture` | ECUs + networks |
| GET/POST | `/api/ecus` | List / create ECUs |
| GET | `/api/ecus/{id}` | ECU detail |
| GET | `/api/ecus/{id}/security-context` | Full security context |
| GET/POST | `/api/networks` | In-vehicle networks |

### Analysis (assets, threats, TARA)
| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/api/assets` | Assets |
| GET/POST | `/api/threats` | Threats |
| GET/POST | `/api/tara` | TARA scenarios |
| GET/PATCH | `/api/tara/{id}` | TARA detail / update |
| GET | `/api/tara/{id}/requirements` | Derived requirements |

### Requirements & traceability
| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/api/requirements` | List (`?missing=evidence\|tests`) / create |
| GET/PATCH | `/api/requirements/{id}` | Detail / update |
| GET | `/api/requirements/{id}/traceability` | Traceability + checklist |
| POST | `/api/requirements/{id}/mechanisms` | AUTOSAR mapping |
| POST | `/api/requirements/{id}/controls` | Control mapping |

### Standards
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/standards` | Catalog (21434, R155, R156, NIST, AUTOSAR) |
| GET | `/api/controls` | Controls (`?standard_key=&category=`) |
| GET | `/api/controls/{id}/mappings` | Control ↔ requirement mappings |
| GET | `/api/autosar/mechanisms` | AUTOSAR mechanism catalog |
| GET | `/api/autosar/mechanisms/{id}` | Mechanism detail |
| GET/POST | `/api/mappings` | Compliance mapping layer |

### Supply chain
| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/api/components` | Software components |
| GET/PATCH | `/api/components/{id}` | Component detail / update |
| GET/POST | `/api/vulnerabilities` | Vulnerabilities |
| GET | `/api/vulnerabilities/{id}/trace` | CVE → vehicle trace |
| POST | `/api/sbom/import` | CycloneDX / SPDX import |
| GET | `/api/sbom` · `/api/sbom/{id}` | SBOM documents |

### Quality
| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/api/tests` | Test cases |
| POST | `/api/tests/{id}/results` | Record result |
| GET/POST | `/api/evidence` | Evidence items |
| GET | `/api/evidence-graph` | Graph subgraph for visualization |

### Releases & changes
| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/api/releases` | Releases |
| POST | `/api/releases/{id}/evaluate` | **Cybersecurity Release Gate** |
| GET/POST | `/api/changes` | Change records |
| POST | `/api/changes/{id}/impact` | **Change Impact Engine** |

### Suppliers, advisor, admin
| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/api/suppliers` · `/api/suppliers/submissions` | Supplier portal |
| POST | `/api/suppliers/submissions/{id}/review` | Review workflow |
| POST | `/api/advisor/ask` | CyberAdvisor Q&A |
| GET | `/api/dashboard` | Dashboard metrics |
| GET | `/api/health` · `/api/meta` | Health / metadata |
| GET | `/api/audit` | Audit log (ADMIN) |
| POST | `/api/admin/seed` | Seed demo data (ADMIN) |

## Error handling

- `400` invalid input / SBOM parse errors
- `401` missing/invalid credentials
- `403` role or organization scope violation
- `404` unknown entity
- `409` conflicts (duplicate email/requirement id)
- `422` schema validation
- `429` rate limit
