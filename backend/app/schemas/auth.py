from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    full_name: str = Field(min_length=2, max_length=200)
    organization_name: str = Field(min_length=2, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    otp_code: Optional[str] = None
    totp_code: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp_code: str
    new_password: str = Field(min_length=10, max_length=128)


class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp_code: str
    purpose: str = "signup"


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    is_active: bool
    is_email_verified: bool
    totp_enabled: bool
    last_login_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class MembershipOut(BaseModel):
    id: UUID
    organization_id: UUID
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


class MeResponse(BaseModel):
    user: UserOut
    memberships: List[MembershipOut]
