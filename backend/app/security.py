"""Authentication (JWT + bcrypt) and RBAC dependencies. No secrets in code."""
from __future__ import annotations

import datetime as dt

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .config import get_settings
from .database import get_db
from .models import AuditLog, Role, User, UserStatus

bearer_scheme = HTTPBearer(auto_error=False)

WRITE_ROLES = {
    Role.ADMIN,
    Role.CYBERSECURITY_ENGINEER,
    Role.ARCHITECT,
    Role.TESTER,
}
ANALYSIS_ROLES = {Role.ADMIN, Role.CYBERSECURITY_ENGINEER, Role.ARCHITECT}
ADMIN_ROLES = {Role.ADMIN}
SUPPLIER_ROLES = {Role.SUPPLIER, Role.ADMIN, Role.CYBERSECURITY_ENGINEER}
REVIEW_ROLES = {Role.ADMIN, Role.CYBERSECURITY_ENGINEER}


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user: User) -> str:
    settings = get_settings()
    now = dt.datetime.now(dt.timezone.utc)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "org": user.organization_id,
        "iat": now,
        "exp": now + dt.timedelta(minutes=settings.JWT_TTL_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token") from exc


def extract_token(request: Request, credentials: HTTPAuthorizationCredentials | None) -> str | None:
    """
    Token sources, in order. Hosted preview proxies may strip the standard
    `Authorization` header, so the client also sends `X-Acg-Token`, the login
    endpoint sets an `acg_token` cookie, and (outside production) a `?token=`
    query fallback is accepted. See docs/security.md.
    """
    if credentials is not None and credentials.credentials:
        return credentials.credentials
    token = request.headers.get("x-acg-token")
    if token:
        return token
    token = request.cookies.get("acg_token")
    if token:
        return token
    if get_settings().ENVIRONMENT != "production":
        token = request.query_params.get("token") or request.query_params.get("access_token")
        if token:
            return token
    return None


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = extract_token(request, credentials)
    if token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    payload = decode_token(token)
    user = db.get(User, int(payload["sub"]))
    if user is None or user.status != UserStatus.ACTIVE:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")
    return user


def set_auth_cookie(response, token: str) -> None:
    """Store the JWT in a SameSite=Lax cookie so auth survives header-stripping proxies.

    SameSite=Lax blocks the cookie on cross-site state-changing requests, which
    provides CSRF protection for cookie-based auth (see docs/security.md).
    """
    settings = get_settings()
    response.set_cookie(
        key="acg_token",
        value=token,
        max_age=settings.JWT_TTL_MINUTES * 60,
        httponly=True,
        samesite="lax",
        secure=settings.ENVIRONMENT == "production",
        path="/",
    )


def clear_auth_cookie(response) -> None:
    response.delete_cookie("acg_token", path="/")


def require_roles(*roles: Role):
    allowed = set(roles)

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed and Role.ADMIN not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"Requires role: {', '.join(r.value for r in allowed)}")
        if user.role == Role.ADMIN:
            return user
        if user.role not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient role")
        return user

    return checker


# Convenience composites
require_admin = require_roles(*ADMIN_ROLES)
require_write = require_roles(*WRITE_ROLES)
require_analysis = require_roles(*ANALYSIS_ROLES)
require_supplier_access = require_roles(*SUPPLIER_ROLES)
require_reviewer = require_roles(*REVIEW_ROLES)


def audit(db: Session, actor: str, action: str, entity_type: str = "", entity_id: int | None = None, detail: str = "") -> None:
    db.add(AuditLog(actor=actor, action=action, entity_type=entity_type, entity_id=entity_id, detail=detail))
    db.commit()


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"
