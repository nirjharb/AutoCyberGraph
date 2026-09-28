"""Test cases, test results, evidence management."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import CybersecurityRequirement, Evidence, TestCase, TestResult, User
from ..schemas import (
    EvidenceCreate,
    EvidenceOut,
    TestCaseCreate,
    TestCaseOut,
    TestResultCreate,
    TestResultOut,
)
from ..security import audit, get_current_user, require_write

router = APIRouter(prefix="/api", tags=["quality"])


# ---------- Test cases ----------
@router.get("/tests", response_model=list[TestCaseOut])
def list_tests(requirement_id: int | None = None, status_filter: str | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    q = select(TestCase)
    if requirement_id:
        q = q.where(TestCase.requirement_id == requirement_id)
    rows = list(db.scalars(q))
    if status_filter:
        rows = [t for t in rows if t.status == status_filter.upper()]
    return rows


@router.post("/tests", response_model=TestCaseOut, status_code=status.HTTP_201_CREATED)
def create_test(payload: TestCaseCreate, db: Session = Depends(get_db), user: User = Depends(require_write)):
    if payload.requirement_id is not None and db.get(CybersecurityRequirement, payload.requirement_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Requirement not found")
    test = TestCase(**payload.model_dump())
    db.add(test)
    db.commit()
    audit(db, user.email, "test.create", "TestCase", test.id, test.name)
    return test


@router.post("/tests/{test_id}/results", response_model=TestResultOut, status_code=status.HTTP_201_CREATED)
def record_result(test_id: int, payload: TestResultCreate, db: Session = Depends(get_db), user: User = Depends(require_write)):
    test = db.get(TestCase, test_id)
    if test is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Test case not found")
    result = TestResult(test_case_id=test_id, result=payload.result, tester=payload.tester or user.name, notes=payload.notes)
    test.status = payload.result.value
    db.add(result)
    db.commit()
    audit(db, user.email, "test.result", "TestCase", test_id, payload.result.value)
    return result


@router.get("/tests/{test_id}")
def get_test(test_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    test = db.get(TestCase, test_id)
    if test is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Test case not found")
    return {
        "test": TestCaseOut.model_validate(test).model_dump(),
        "requirement": ({"id": test.requirement.id, "requirement_id": test.requirement.requirement_id}
                        if test.requirement else None),
        "results": [TestResultOut.model_validate(r).model_dump() for r in test.results],
    }


# ---------- Evidence ----------
@router.get("/evidence", response_model=list[EvidenceOut])
def list_evidence(
    status_filter: str | None = None,
    requirement_id: int | None = None,
    release_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(Evidence)
    if requirement_id:
        q = q.where(Evidence.requirement_id == requirement_id)
    if release_id:
        q = q.where(Evidence.release_id == release_id)
    rows = list(db.scalars(q))
    if status_filter:
        rows = [e for e in rows if e.status.value == status_filter.upper()]
    return rows


@router.post("/evidence", response_model=EvidenceOut, status_code=status.HTTP_201_CREATED)
def create_evidence(payload: EvidenceCreate, db: Session = Depends(get_db), user: User = Depends(require_write)):
    evidence = Evidence(**payload.model_dump())
    db.add(evidence)
    db.commit()
    audit(db, user.email, "evidence.create", "Evidence", evidence.id, evidence.name)
    return evidence


@router.get("/evidence/{evidence_id}", response_model=EvidenceOut)
def get_evidence(evidence_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    evidence = db.get(Evidence, evidence_id)
    if evidence is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Evidence not found")
    return evidence


@router.patch("/evidence/{evidence_id}", response_model=EvidenceOut)
def update_evidence(evidence_id: int, payload: EvidenceCreate, db: Session = Depends(get_db), user: User = Depends(require_write)):
    evidence = db.get(Evidence, evidence_id)
    if evidence is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Evidence not found")
    for key, value in payload.model_dump().items():
        setattr(evidence, key, value)
    db.commit()
    audit(db, user.email, "evidence.update", "Evidence", evidence.id, evidence.name)
    return evidence


@router.get("/evidence-graph")
def evidence_graph(tara_id: int | None = None, requirement_id: int | None = None, release_id: int | None = None,
                   db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """
    Subgraph for the evidence graph visualization:
    TARA → Goal → Requirement → Control → Mechanism → Test → Evidence (→ Release).
    """
    from ..graph import SqlGraphService

    graph = SqlGraphService(db)
    start_type, start_id = None, None
    if requirement_id:
        start_type, start_id = "CybersecurityRequirement", requirement_id
    elif tara_id:
        start_type, start_id = "TARA", tara_id
    elif release_id:
        start_type, start_id = "Release", release_id
    if start_type is None:
        return {"nodes": [], "edges": []}

    nodes_map: dict[tuple[str, int], dict] = {}
    start_label = graph._lookup_label(start_type, start_id)
    nodes_map[(start_type, start_id)] = {"id": f"{start_type}:{start_id}", "label": start_label,
                                         "entity_type": start_type, "entity_id": start_id, "depth": 0}
    edges = []
    for node in graph.bfs(start_type, start_id, max_depth=4):
        key = (node.entity_type, node.entity_id)
        if key not in nodes_map:
            nodes_map[key] = {"id": f"{node.entity_type}:{node.entity_id}", "label": node.label,
                              "entity_type": node.entity_type, "entity_id": node.entity_id, "depth": node.depth}
        # link each node to the node it was reached from (true chain edges)
        parent = node.parent or (start_type, start_id)
        edges.append({"id": f"e{len(edges)}", "source": f"{parent[0]}:{parent[1]}",
                      "target": f"{node.entity_type}:{node.entity_id}", "label": node.via[-1] if node.via else ""})
    return {"nodes": list(nodes_map.values()), "edges": edges}
