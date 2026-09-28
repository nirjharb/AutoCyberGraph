"""Auth + user management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models import Organization, Role, User, UserStatus
from ..schemas import LoginRequest, RegisterRequest, TokenResponse, UserOut
from ..security import (
    audit,
    create_access_token,
    get_current_user,
    hash_password,
    require_admin,
    set_auth_cookie,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)
settings = get_settings()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_AUTH)
def register(request: Request, response: Response, payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.scalars(select(User).where(User.email == payload.email)).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    org = db.scalars(select(Organization).where(Organization.name == payload.organization_name)).first()
    if org is None:
        org = Organization(name=payload.organization_name, type="OEM")
        db.add(org)
        db.flush()
    user = User(
        organization_id=org.id,
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role if payload.role != Role.ADMIN else Role.VIEWER,  # admin bootstrap is seed-only
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    db.commit()
    audit(db, user.email, "user.register", "User", user.id)
    token = create_access_token(user)
    set_auth_cookie(response, token)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.RATE_LIMIT_AUTH)
def login(request: Request, response: Response, payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalars(select(User).where(User.email == payload.email)).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is not active")
    audit(db, user.email, "user.login", "User", user.id)
    token = create_access_token(user)
    set_auth_cookie(response, token)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.get("/users", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return list(db.scalars(select(User)))
