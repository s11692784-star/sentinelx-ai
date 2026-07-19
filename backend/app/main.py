from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.deps import enforce_rate_limit
from app.db.session import Base, engine
import app.models  # noqa: F401  ensure models registered


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.validate_production_secrets()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Enterprise Multi-Tenant Secrets & Certificate Lifecycle Platform",
    lifespan=lifespan,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Tenant-Id", "X-Request-Id"],
    expose_headers=["X-Request-Id"],
    max_age=600,
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    if settings.force_https:
        proto = request.headers.get("x-forwarded-proto", request.url.scheme)
        if proto != "https" and request.url.path not in {"/health", "/ready"}:
            url = request.url.replace(scheme="https")
            return Response(status_code=308, headers={"Location": str(url)})

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "same-site"
    response.headers["X-Request-Id"] = request.headers.get("x-request-id", "sx")
    if settings.is_production or settings.session_cookie_secure:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    # Hide server fingerprint
    if "server" in response.headers:
        del response.headers["server"]
    return response


@app.get("/health")
async def health():
    return {"status": "ok", "service": settings.app_name, "env": settings.app_env}


@app.get("/ready")
async def ready():
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"ready": True}


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "status": "online",
        "api": settings.api_v1_prefix,
        "docs": None if settings.is_production else "/docs",
    }


app.include_router(api_router, prefix=settings.api_v1_prefix, dependencies=[Depends(enforce_rate_limit)])
