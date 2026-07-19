from __future__ import annotations

from typing import Annotated, AsyncGenerator, Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import Membership, User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise ValueError("wrong token type")
        user_id = payload.get("sub")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    result = await db.execute(
        select(User).options(selectinload(User.memberships)).where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or missing")
    return user


async def get_tenant_id(
    x_tenant_id: Annotated[Optional[str], Header(alias="X-Tenant-Id")] = None,
) -> Optional[UUID]:
    if not x_tenant_id:
        return None
    try:
        return UUID(x_tenant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid X-Tenant-Id")


async def require_membership(
    user: Annotated[User, Depends(get_current_user)],
    tenant_id: Annotated[Optional[UUID], Depends(get_tenant_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    roles: Optional[set[str]] = None,
) -> Membership:
    if tenant_id is None:
        # fallback to primary org
        if not user.memberships:
            raise HTTPException(status_code=403, detail="No organization membership")
        membership = sorted(user.memberships, key=lambda m: m.created_at)[0]
        return membership

    result = await db.execute(
        select(Membership).where(
            Membership.user_id == user.id,
            Membership.organization_id == tenant_id,
            Membership.is_active.is_(True),
        )
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    if roles and membership.role not in roles:
        raise HTTPException(status_code=403, detail=f"Requires one of roles: {', '.join(roles)}")
    return membership


class RateLimiter:
    """Simple in-memory rate limiter fallback; Redis preferred in prod path."""

    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = {}

    async def check(self, key: str, limit: int, window_seconds: int = 60) -> None:
        import time

        now = time.time()
        bucket = self._hits.setdefault(key, [])
        self._hits[key] = [t for t in bucket if now - t < window_seconds]
        if len(self._hits[key]) >= limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        self._hits[key].append(now)


rate_limiter = RateLimiter()


async def enforce_rate_limit(request: Request) -> None:
    from app.core.config import settings

    client = request.client.host if request.client else "unknown"
    await rate_limiter.check(f"ip:{client}", settings.rate_limit_per_minute)
