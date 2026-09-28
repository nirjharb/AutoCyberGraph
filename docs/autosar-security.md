# AUTOSAR Security

> AutoCyberGraph represents AUTOSAR security mechanisms as a **reference
> catalog and mapping layer**. It is not an official AUTOSAR tool and does not
> implement or configure AUTOSAR software.

## Mechanism catalog

| Mechanism | Category |
|-----------|----------|
| SecOC (Secure Onboard Communication) | Communication protection |
| Crypto Service Manager (CSM) | Cryptography |
| Crypto Interface (CryIf) | Cryptography |
| Crypto Driver (CDD) | Cryptography |
| HSM | Hardware security |
| Secure Boot | Platform security |
| Secure Diagnostics | Diagnostics security |
| Key Management | Key handling |
| Authentication | Access control |
| Freshness | Replay protection |
| Cryptographic services | Cryptography |

## Mapping: requirement → mechanism

Example from the demo dataset:

```
CS-REQ-001 "Authenticated vehicle dynamics messages"
        ↓
AUTOSAR SecOC
        ↓
Authentication + Freshness
        ↓
Gateway ECU (MechanismImplementation)
        ↓
Verification Test TC-SECOC-001
```

- Links are created via `POST /api/requirements/{id}/mechanisms`
- Implementations (`MechanismImplementation`) record *which ECU* realizes a
  mechanism and with what status (`IMPLEMENTED`, `IN_PROGRESS`, …)
- The release gate checks that every requirement in scope has at least one
  AUTOSAR mechanism mapping

## API

- `GET /api/autosar/mechanisms` — catalog
- `GET /api/autosar/mechanisms/{id}` — mapped requirements + ECU implementations
- `POST /api/requirements/{id}/mechanisms` — create mapping
