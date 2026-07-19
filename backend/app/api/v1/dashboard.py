from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_tenant_id, require_membership
from app.db.session import get_db
from app.models.user import User
from app.schemas.security_ops import DashboardOut
from app.services.dashboard import build_dashboard

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardOut)
async def dashboard(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_id),
):
    membership = await require_membership(user=user, tenant_id=tenant_id, db=db)
    return await build_dashboard(db, membership.organization_id)
