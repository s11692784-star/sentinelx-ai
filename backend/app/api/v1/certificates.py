from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_tenant_id, require_membership
from app.db.session import get_db
from app.models.secrets import CertificateAsset
from app.models.user import User
from app.schemas.security_ops import CertificateCreate, CertificateOut
from app.services.certificates.lifecycle import certificate_risk, days_until, renew_recommendation

router = APIRouter(prefix="/certificates", tags=["Certificates"])


@router.get("", response_model=list[CertificateOut])
async def list_certs(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_id),
):
    membership = await require_membership(user=user, tenant_id=tenant_id, db=db)
    q = await db.execute(
        select(CertificateAsset)
        .where(CertificateAsset.organization_id == membership.organization_id)
        .order_by(CertificateAsset.days_remaining.asc())
    )
    return list(q.scalars().all())


@router.post("", response_model=CertificateOut)
async def create_cert(
    payload: CertificateCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_id),
):
    membership = await require_membership(user=user, tenant_id=tenant_id, db=db, roles={"admin", "security_analyst", "developer"})
    remaining = days_until(payload.not_after)
    cert = CertificateAsset(
        organization_id=membership.organization_id,
        common_name=payload.common_name,
        sans=payload.sans,
        issuer=payload.issuer,
        serial_number=payload.serial_number,
        cert_type=payload.cert_type,
        not_before=payload.not_before,
        not_after=payload.not_after,
        days_remaining=remaining,
        risk_score=certificate_risk(remaining, payload.cert_type, payload.auto_renew),
        auto_renew=payload.auto_renew,
        renew_status=renew_recommendation(remaining),
        fingerprint_sha256=payload.fingerprint_sha256,
        source=payload.source,
    )
    db.add(cert)
    await db.flush()
    return cert


@router.post("/{cert_id}/renew", response_model=CertificateOut)
async def renew_cert(
    cert_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_id),
):
    membership = await require_membership(user=user, tenant_id=tenant_id, db=db, roles={"admin", "security_analyst"})
    q = await db.execute(
        select(CertificateAsset).where(
            CertificateAsset.id == cert_id,
            CertificateAsset.organization_id == membership.organization_id,
        )
    )
    cert = q.scalar_one_or_none()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    # simulate renew +90d
    from datetime import timedelta

    cert.not_before = datetime.now(timezone.utc)
    cert.not_after = datetime.now(timezone.utc) + timedelta(days=90)
    cert.days_remaining = 90
    cert.risk_score = certificate_risk(90, cert.cert_type, cert.auto_renew)
    cert.renew_status = "renewed"
    cert.alert_sent = False
    await db.flush()
    return cert
