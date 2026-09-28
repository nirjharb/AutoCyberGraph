"""Supplier portal: submissions + OEM review workflow (org-scoped)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Supplier, SupplierSubmission, User, utcnow
from ..schemas import (
    SubmissionCreate,
    SubmissionOut,
    SubmissionReview,
    SupplierCreate,
    SupplierOut,
)
from ..security import (
    audit,
    get_current_user,
    require_reviewer,
    require_supplier_access,
    require_write,
)

router = APIRouter(prefix="/api/suppliers", tags=["suppliers"])


@router.get("", response_model=list[SupplierOut])
def list_suppliers(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return list(db.scalars(select(Supplier)))


@router.post("", response_model=SupplierOut, status_code=status.HTTP_201_CREATED)
def create_supplier(payload: SupplierCreate, db: Session = Depends(get_db), user: User = Depends(require_write)):
    supplier = Supplier(**payload.model_dump())
    db.add(supplier)
    db.commit()
    audit(db, user.email, "supplier.create", "Supplier", supplier.id, supplier.name)
    return supplier


@router.get("/submissions", response_model=list[SubmissionOut])
def list_submissions(
    supplier_id: int | None = None,
    status_filter: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(SupplierSubmission)
    if supplier_id:
        q = q.where(SupplierSubmission.supplier_id == supplier_id)
    rows = list(db.scalars(q))
    # Organization-level authorization: suppliers only see their own submissions
    if user.role.value == "SUPPLIER":
        own_supplier_ids = [s.id for s in db.scalars(select(Supplier).where(Supplier.organization_id == user.organization_id))]
        rows = [r for r in rows if r.supplier_id in own_supplier_ids]
    if status_filter:
        rows = [r for r in rows if r.status.value == status_filter.upper()]
    return rows


@router.post("/submissions", response_model=SubmissionOut, status_code=status.HTTP_201_CREATED)
def create_submission(payload: SubmissionCreate, db: Session = Depends(get_db), user: User = Depends(require_supplier_access)):
    supplier = db.get(Supplier, payload.supplier_id)
    if supplier is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Supplier not found")
    if user.role.value == "SUPPLIER" and supplier.organization_id != user.organization_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Suppliers can only submit for their own organization")
    submission = SupplierSubmission(**payload.model_dump(), created_by=user.email)
    db.add(submission)
    db.commit()
    audit(db, user.email, "submission.create", "SupplierSubmission", submission.id, submission.title)
    return submission


@router.post("/submissions/{submission_id}/review", response_model=SubmissionOut)
def review_submission(submission_id: int, payload: SubmissionReview, db: Session = Depends(get_db), user: User = Depends(require_reviewer)):
    submission = db.get(SupplierSubmission, submission_id)
    if submission is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Submission not found")
    submission.status = payload.status
    submission.review_notes = payload.review_notes
    submission.reviewed_at = utcnow()
    db.commit()
    audit(db, user.email, f"submission.{payload.status.value.lower()}", "SupplierSubmission", submission.id, submission.title)
    return submission
