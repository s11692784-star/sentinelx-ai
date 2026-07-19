from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_tenant_id, require_membership
from app.core.security import hash_password, verify_password
from app.db.session import get_db
from app.models.organization import Organization
from app.models.user import User
from app.schemas.settings import ChangePasswordRequest, SecuritySettingsOut, SecuritySettingsUpdate
from app.services.audit import write_audit

router = APIRouter(prefix="/settings", tags=["Settings & Security"])

DEFAULTS = SecuritySettingsOut().model_dump()


def _merge_settings(raw: dict | None) -> dict:
    data = dict(DEFAULTS)
    if raw:
        data.update({k: v for k, v in raw.items() if k in DEFAULTS})
    return data


@router.get("/security", response_model=SecuritySettingsOut)
async def get_security_settings(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_id),
):
    membership = await require_membership(user=user, tenant_id=tenant_id, db=db)
    q = await db.execute(select(Organization).where(Organization.id == membership.organization_id))
    org = q.scalar_one()
    return SecuritySettingsOut(**_merge_settings(org.settings or {}))


@router.put("/security", response_model=SecuritySettingsOut)
async def update_security_settings(
    payload: SecuritySettingsUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_id),
):
    membership = await require_membership(
        user=user, tenant_id=tenant_id, db=db, roles={"admin", "security_analyst"}
    )
    q = await db.execute(select(Organization).where(Organization.id == membership.organization_id))
    org = q.scalar_one()
    current = _merge_settings(org.settings or {})
    updates = payload.model_dump(exclude_unset=True)
    current.update(updates)
    org.settings = current
    await write_audit(
        db,
        action="settings.security_updated",
        resource_type="organization",
        resource_id=str(org.id),
        organization_id=org.id,
        actor_id=user.id,
        actor_email=user.email,
        details={"keys": list(updates.keys())},
    )
    await db.flush()
    return SecuritySettingsOut(**current)


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(payload.new_password) < 10:
        raise HTTPException(status_code=400, detail="Password must be at least 10 characters")
    user.hashed_password = hash_password(payload.new_password)
    await write_audit(
        db,
        action="user.password_changed",
        resource_type="user",
        resource_id=str(user.id),
        actor_id=user.id,
        actor_email=user.email,
    )
    await db.flush()
    return {"message": "Password updated successfully"}


@router.get("/security-posture")
async def security_posture(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_id),
):
    membership = await require_membership(user=user, tenant_id=tenant_id, db=db)
    q = await db.execute(select(Organization).where(Organization.id == membership.organization_id))
    org = q.scalar_one()
    cfg = _merge_settings(org.settings or {})
    checks = [
        {"id": "mfa", "label": "MFA required for tenant", "ok": bool(cfg.get("mfa_required")), "severity": "high"},
        {"id": "user_2fa", "label": "Your account has 2FA enabled", "ok": bool(user.totp_enabled), "severity": "high"},
        {"id": "session", "label": "Session timeout ≤ 60 minutes", "ok": int(cfg.get("session_timeout_minutes", 30)) <= 60, "severity": "medium"},
        {"id": "password_policy", "label": "Password min length ≥ 10", "ok": int(cfg.get("password_min_length", 10)) >= 10, "severity": "medium"},
        {"id": "cert_alerts", "label": "Certificate expiry alerts enabled", "ok": bool(cfg.get("notify_on_cert_expiry", True)), "severity": "medium"},
        {"id": "critical_alerts", "label": "Critical finding alerts enabled", "ok": bool(cfg.get("notify_on_critical", True)), "severity": "medium"},
        {"id": "audit_retention", "label": "Audit retention ≥ 90 days", "ok": int(cfg.get("audit_retention_days", 365)) >= 90, "severity": "low"},
    ]
    score = round(100 * sum(1 for c in checks if c["ok"]) / max(1, len(checks)), 1)
    return {"score": score, "checks": checks, "settings": cfg}
