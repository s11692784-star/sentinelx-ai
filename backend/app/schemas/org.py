from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    plan: str = "enterprise"


class OrganizationOut(BaseModel):
    id: UUID
    name: str
    slug: str
    plan: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class InviteMemberRequest(BaseModel):
    email: EmailStr
    role: str = Field(pattern="^(admin|security_analyst|developer|auditor|viewer)$")


class InvitationOut(BaseModel):
    id: UUID
    email: EmailStr
    role: str
    expires_at: datetime
    accepted_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    environment: str = "production"


class ProjectOut(BaseModel):
    id: UUID
    name: str
    slug: str
    description: Optional[str]
    environment: str
    organization_id: UUID

    model_config = {"from_attributes": True}


class RepositoryCreate(BaseModel):
    project_id: UUID
    name: str
    provider: str = "github"
    url: str
    default_branch: str = "main"


class RepositoryOut(BaseModel):
    id: UUID
    name: str
    provider: str
    url: str
    default_branch: str
    risk_score: float
    last_scanned_at: Optional[datetime]
    project_id: UUID
    organization_id: UUID

    model_config = {"from_attributes": True}


class CloudAccountCreate(BaseModel):
    provider: str
    account_label: str
    external_id: str
    credentials: Optional[str] = None


class CloudAccountOut(BaseModel):
    id: UUID
    provider: str
    account_label: str
    external_id: str
    status: str

    model_config = {"from_attributes": True}
