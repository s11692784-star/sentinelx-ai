from __future__ import annotations

import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.security import encrypt_secret
from app.db.session import get_db
from app.models.organization import CloudAccount, Invitation, Organization, Project, Repository
from app.models.user import Membership, User
from app.schemas.org import (
    CloudAccountCreate,
    CloudAccountOut,
    InvitationOut,
    InviteMemberRequest,
    OrganizationCreate,
    OrganizationOut,
    ProjectCreate,
    ProjectOut,
    RepositoryCreate,
    RepositoryOut,
)
from app.services.audit import write_audit

router = APIRouter(prefix="/organizations", tags=["Organizations"])


async def _membership(db, user, org_id: str, roles: set[str] | None = None):
    from uuid import UUID

    tid = UUID(org_id)
    result = await db.execute(
        select(Membership).where(
            Membership.user_id == user.id,
            Membership.organization_id == tid,
            Membership.is_active.is_(True),
        )
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    if roles and membership.role not in roles:
        raise HTTPException(status_code=403, detail=f"Requires one of roles: {', '.join(roles)}")
    return membership


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") + "-" + secrets.token_hex(2)


@router.get("", response_model=list[OrganizationOut])
async def list_orgs(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    org_ids = [m.organization_id for m in user.memberships if m.is_active]
    if not org_ids:
        return []
    q = await db.execute(select(Organization).where(Organization.id.in_(org_ids)))
    return list(q.scalars().all())


@router.post("", response_model=OrganizationOut)
async def create_org(payload: OrganizationCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    org = Organization(name=payload.name, slug=_slugify(payload.name), plan=payload.plan)
    db.add(org)
    await db.flush()
    db.add(Membership(user_id=user.id, organization_id=org.id, role="admin"))
    await write_audit(db, action="org.create", resource_type="organization", resource_id=str(org.id), organization_id=org.id, actor_id=user.id, actor_email=user.email)
    await db.flush()
    return org


@router.post("/{org_id}/invitations", response_model=InvitationOut)
async def invite_member(
    org_id: str,
    payload: InviteMemberRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    membership = await _membership(db, user, org_id, roles={"admin"})
    token = secrets.token_urlsafe(24)
    inv = Invitation(
        organization_id=membership.organization_id,
        email=payload.email.lower(),
        role=payload.role,
        token_hash=hashlib.sha256(token.encode()).hexdigest(),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        invited_by=user.id,
    )
    db.add(inv)
    await write_audit(db, action="org.invite", resource_type="invitation", organization_id=membership.organization_id, actor_id=user.id, details={"email": payload.email, "role": payload.role})
    await db.flush()
    return inv


@router.get("/{org_id}/projects", response_model=list[ProjectOut])
async def list_projects(org_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    membership = await _membership(db, user, org_id)
    q = await db.execute(select(Project).where(Project.organization_id == membership.organization_id))
    return list(q.scalars().all())


@router.post("/{org_id}/projects", response_model=ProjectOut)
async def create_project(org_id: str, payload: ProjectCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    membership = await _membership(db, user, org_id, roles={"admin", "security_analyst", "developer"})
    project = Project(
        organization_id=membership.organization_id,
        name=payload.name,
        slug=_slugify(payload.name)[:80],
        description=payload.description,
        environment=payload.environment,
    )
    db.add(project)
    await db.flush()
    return project


@router.post("/{org_id}/repositories", response_model=RepositoryOut)
async def create_repo(org_id: str, payload: RepositoryCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    membership = await _membership(db, user, org_id, roles={"admin", "security_analyst", "developer"})
    repo = Repository(
        project_id=payload.project_id,
        organization_id=membership.organization_id,
        name=payload.name,
        provider=payload.provider,
        url=payload.url,
        default_branch=payload.default_branch,
    )
    db.add(repo)
    await db.flush()
    return repo


@router.get("/{org_id}/repositories", response_model=list[RepositoryOut])
async def list_repos(org_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    membership = await _membership(db, user, org_id)
    q = await db.execute(select(Repository).where(Repository.organization_id == membership.organization_id))
    return list(q.scalars().all())


@router.post("/{org_id}/cloud-accounts", response_model=CloudAccountOut)
async def add_cloud(org_id: str, payload: CloudAccountCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    membership = await _membership(db, user, org_id, roles={"admin"})
    acc = CloudAccount(
        organization_id=membership.organization_id,
        provider=payload.provider,
        account_label=payload.account_label,
        external_id=payload.external_id,
        credentials_enc=encrypt_secret(payload.credentials) if payload.credentials else None,
    )
    db.add(acc)
    await db.flush()
    return acc


@router.get("/{org_id}/cloud-accounts", response_model=list[CloudAccountOut])
async def list_cloud(org_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    membership = await _membership(db, user, org_id)
    q = await db.execute(select(CloudAccount).where(CloudAccount.organization_id == membership.organization_id))
    return list(q.scalars().all())
