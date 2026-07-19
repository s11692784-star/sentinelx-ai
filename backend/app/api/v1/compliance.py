from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_tenant_id, require_membership
from app.db.session import get_db
from app.models.compliance import AuditLog, ComplianceReport, ThreatIntelEntry
from app.models.user import User
from app.schemas.security_ops import ComplianceGenerateRequest, ComplianceReportOut, ThreatIntelOut
from app.services.compliance.engine import generate_report
from app.services.threat.catalog import ensure_seed

router = APIRouter(tags=["Compliance & Threat Intel"])


@router.post("/compliance/reports", response_model=ComplianceReportOut)
async def create_report(
    payload: ComplianceGenerateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_id),
):
    membership = await require_membership(user=user, tenant_id=tenant_id, db=db, roles={"admin", "security_analyst", "auditor"})
    try:
        report = await generate_report(db, organization_id=membership.organization_id, framework=payload.framework, generated_by=user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return report


@router.get("/compliance/reports", response_model=list[ComplianceReportOut])
async def list_reports(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_id),
):
    membership = await require_membership(user=user, tenant_id=tenant_id, db=db)
    q = await db.execute(
        select(ComplianceReport)
        .where(ComplianceReport.organization_id == membership.organization_id)
        .order_by(ComplianceReport.created_at.desc())
    )
    return list(q.scalars().all())


@router.get("/threat-intel", response_model=list[ThreatIntelOut])
async def threat_intel(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_id),
):
    await require_membership(user=user, tenant_id=tenant_id, db=db)
    await ensure_seed(db)
    q = await db.execute(select(ThreatIntelEntry).order_by(ThreatIntelEntry.severity.desc()).limit(100))
    return list(q.scalars().all())


@router.get("/audit-logs")
async def audit_logs(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_id),
):
    membership = await require_membership(user=user, tenant_id=tenant_id, db=db, roles={"admin", "security_analyst", "auditor"})
    q = await db.execute(
        select(AuditLog)
        .where(AuditLog.organization_id == membership.organization_id)
        .order_by(AuditLog.created_at.desc())
        .limit(200)
    )
    rows = q.scalars().all()
    return [
        {
            "id": str(r.id),
            "action": r.action,
            "resource_type": r.resource_type,
            "resource_id": r.resource_id,
            "actor_email": r.actor_email,
            "details": r.details,
            "integrity_hash": r.integrity_hash,
            "prev_hash": r.prev_hash,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
