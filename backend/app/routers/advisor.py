"""CyberAdvisor — grounded Q&A over project data."""
from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models import User
from ..schemas import AdvisorAnswer, AdvisorQuestion
from ..security import get_current_user
from ..services.cyberadvisor import get_advisor_backend

router = APIRouter(prefix="/api/advisor", tags=["advisor"])
limiter = Limiter(key_func=get_remote_address)
settings = get_settings()


@router.post("/ask", response_model=AdvisorAnswer)
@limiter.limit(settings.RATE_LIMIT_ADVISOR)
def ask(request: Request, payload: AdvisorQuestion, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    backend = get_advisor_backend()
    response = backend.answer(payload.question, db)
    return AdvisorAnswer(
        question=payload.question,
        intent=response.intent,
        answer=response.answer,
        data=response.data,
        grounded=response.grounded,
        links=response.links,
    )
