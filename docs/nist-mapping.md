# NIST SP 800-53 Mapping

> NIST SP 800-53 is a **security-control catalog**, not an automotive
> regulation. AutoCyberGraph uses it as a **mapping layer** for cybersecurity
> requirements and evidence. This is not an official NIST product and the
> standard's text is not reproduced. See the official NIST publication for the
> complete catalog: https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final

## Represented categories

| Family | Focus |
|--------|-------|
| AC | Access Control |
| AU | Audit and Accountability |
| CM | Configuration Management |
| IA | Identification and Authentication |
| IR | Incident Response |
| RA | Risk Assessment |
| SA | System and Services Acquisition |
| SC | System and Communications Protection |
| SI | System and Information Integrity |
| SR | Supply Chain Risk Management |

The demo dataset includes representative controls (AC-2, AC-3, AU-2, AU-6,
CM-2, CM-7, IA-2, IA-5, IR-4, RA-5, SA-10, SC-8, SC-13, SI-2, SR-3, SR-4) —
enough to demonstrate mappings, deliberately **not** the full catalog.

## Supported mappings

```
Control → Requirement   (RequirementControlLink)
Control → Evidence      (ControlEvidenceLink)
Control → Test          (ControlTestLink)
```

Plus the generic `ComplianceMapping` table for cross-standard annotations.

## Future: machine-readable catalogs

The `Control` schema (`standard_id`, `control_id`, `title`, `description`,
`category`) is designed so an **OSCAL-style catalog importer** can populate
controls in bulk. The architecture reserves this as a clean import module —
see `DECISIONS.md` and the roadmap in the README.

## API

- `GET /api/controls?standard_key=NIST80053&category=AC`
- `GET /api/controls/{id}/mappings` — linked requirements
- `POST /api/requirements/{id}/controls` — requirement ↔ control mapping
