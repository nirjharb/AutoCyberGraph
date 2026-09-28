"""
AutoCyberGraph — FastAPI application entrypoint.

Connect Automotive Cybersecurity Risk to Reality.

Disclaimer: AutoCyberGraph is an engineering and evidence-management platform.
It does not provide legal, regulatory, certification, or compliance advice.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .config import get_settings
from .database import Base, SessionLocal, engine
from .routers import (
    admin,
    advisor,
    analysis,
    auth,
    changes,
    dashboard,
    quality,
    releases,
    requirements,
    standards,
    suppliers,
    supply,
    vehicles,
)
from .services.seed import seed_demo_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("autocybergraph")

settings = get_settings()
limiter = Limiter(key_func=get_remote_address)

DESCRIPTION = """
AutoCyberGraph connects automotive cybersecurity engineering, risk, implementation,
testing, vulnerabilities, software changes, and compliance evidence into one traceable system.

**Disclaimer:** AutoCyberGraph is an engineering and evidence-management platform.
It does not provide legal, regulatory, certification, or compliance advice.
ISO/SAE 21434, UNECE R155, UNECE R156, NIST SP 800-53 and AUTOSAR security are represented
as reference/mapping concepts only.
"""


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    if settings.SEED_DEMO_ON_STARTUP:
        with SessionLocal() as db:
            result = seed_demo_data(db)
            logger.info("Demo seed on startup: %s", result)
    logger.info("AutoCyberGraph %s started (env=%s)", settings.APP_VERSION, settings.ENVIRONMENT)
    yield


app = FastAPI(
    title="AutoCyberGraph API",
    description=DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    contact={"name": "AutoCyberGraph", "url": "https://github.com/autocybergraph/autocybergraph"},
    license_info={"name": "Apache-2.0"},
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if settings.ENVIRONMENT == "production":
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=63072000; includeSubDomains"
        )
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; frame-ancestors 'none'",
        )
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# Routers
app.include_router(auth.router)
app.include_router(vehicles.router)
app.include_router(analysis.router)
app.include_router(requirements.router)
app.include_router(standards.router)
app.include_router(supply.router)
app.include_router(quality.router)
app.include_router(releases.router)
app.include_router(changes.router)
app.include_router(suppliers.router)
app.include_router(advisor.router)
app.include_router(dashboard.router)
app.include_router(admin.router)


@app.get("/api/meta")
def meta():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "tagline": "Connect Automotive Cybersecurity Risk to Reality.",
        "disclaimer": "AutoCyberGraph is an engineering and evidence-management platform. "
                      "It does not provide legal, regulatory, certification, or compliance advice.",
    }


# Serve built frontend when present (single-service deployment / demo)
_frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _frontend_dist.exists():
    from fastapi.responses import FileResponse

    _assets_dir = _frontend_dist / "assets"
    if _assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(_assets_dir)), name="frontend-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_catch_all(full_path: str):
        """Serve the SPA for client-side routes; keep /api and real files intact."""
        candidate = _frontend_dist / full_path
        if full_path and not full_path.startswith("api/") and candidate.is_file():
            return FileResponse(candidate)
        index = _frontend_dist / "index.html"
        return FileResponse(index)
