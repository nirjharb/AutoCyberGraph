# Supplier Management

## Model

- **Supplier** — an organization (`organization_id`) with type + contact
- **SupplierSubmission** — a submitted artifact with `kind`, title, description,
  JSON payload, status and review trail

## Submission kinds

`ECU_INFO` · `SOFTWARE_VERSION` · `SBOM` · `REQUIREMENT` · `TARA_EVIDENCE` ·
`TEST_RESULT` · `VULNERABILITY` · `SECURITY_DOC`

## Workflow

```
SUPPLIER                OEM
   │  create submission  │
   ├────────────────────►│
   │                     │  review:
   │◄────────────────────┤  APPROVED / REJECTED / CHANGES_REQUESTED
   │  (resubmit if       │
   │   changes requested)│
```

Status lifecycle: `SUBMITTED → IN_REVIEW → APPROVED | REJECTED | CHANGES_REQUESTED`.

## Authorization

- Suppliers can **only** create submissions for their own organization and can
  **only see their own** submissions (organization scoping enforced server-side)
- Review actions (`/review`) require the `ADMIN` or `CYBERSECURITY_ENGINEER` role
  — supplier accounts receive HTTP 403
- Every submission and review action is written to the audit log

## API

- `GET/POST /api/suppliers`
- `GET/POST /api/suppliers/submissions`
- `POST /api/suppliers/submissions/{id}/review`
