from __future__ import annotations

import hashlib
import json
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compliance import AuditLog


async def write_audit(
    db: AsyncSession,
    *,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    organization_id: Optional[UUID] = None,
    actor_id: Optional[UUID] = None,
    actor_email: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
) -> AuditLog:
    prev_hash = None
    q = await db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(1))
    last = q.scalar_one_or_none()
    if last:
        prev_hash = last.integrity_hash

    payload = {
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "organization_id": str(organization_id) if organization_id else None,
        "actor_id": str(actor_id) if actor_id else None,
        "details": details or {},
        "prev_hash": prev_hash,
    }
    integrity = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    entry = AuditLog(
        organization_id=organization_id,
        actor_id=actor_id,
        actor_email=actor_email,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details or {},
        integrity_hash=integrity,
        prev_hash=prev_hash,
    )
    db.add(entry)
    await db.flush()
    return entry
