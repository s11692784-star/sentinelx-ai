from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_tenant_id, require_membership
from app.db.session import get_db
from app.models.secrets import RemediationAction
from app.models.user import User
from app.schemas.security_ops import RemediationOut, RemediationRequest
from app.services.remediation.actions import execute_remediation

router = APIRouter(prefix="/remediation", tags=["Auto Remediation"])


@router.post("", response_model=RemediationOut)
async def remediate(
    payload: RemediationRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_id),
):
    membership = await require_membership(user=user, tenant_id=tenant_id, db=db, roles={"admin", "security_analyst", "developer"})
    try:
        action = await execute_remediation(
            db,
            organization_id=membership.organization_id,
            finding_id=payload.finding_id,
            action_type=payload.action_type,
            initiated_by=user.id,
            options=payload.options,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return action


@router.get("", response_model=list[RemediationOut])
async def list_actions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_id),
):
    membership = await require_membership(user=user, tenant_id=tenant_id, db=db)
    q = await db.execute(
        select(RemediationAction)
        .where(RemediationAction.organization_id == membership.organization_id)
        .order_by(RemediationAction.created_at.desc())
        .limit(200)
    )
    return list(q.scalars().all())
