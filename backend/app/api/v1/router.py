from fastapi import APIRouter

from app.api.v1 import ai, auth, certificates, compliance, dashboard, organizations, remediation, scans, settings

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(organizations.router)
api_router.include_router(scans.router)
api_router.include_router(certificates.router)
api_router.include_router(remediation.router)
api_router.include_router(ai.router)
api_router.include_router(compliance.router)
api_router.include_router(dashboard.router)
api_router.include_router(settings.router)
