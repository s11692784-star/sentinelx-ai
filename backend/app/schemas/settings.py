from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class SecuritySettingsOut(BaseModel):
    mfa_required: bool = False
    session_timeout_minutes: int = 30
    password_min_length: int = 10
    allow_api_keys: bool = True
    ip_allowlist_enabled: bool = False
    ip_allowlist: List[str] = Field(default_factory=list)
    notify_on_critical: bool = True
    notify_on_cert_expiry: bool = True
    cert_expiry_days: int = 30
    audit_retention_days: int = 365
    gemini_byok_enabled: bool = True


class SecuritySettingsUpdate(BaseModel):
    mfa_required: Optional[bool] = None
    session_timeout_minutes: Optional[int] = Field(default=None, ge=5, le=1440)
    password_min_length: Optional[int] = Field(default=None, ge=8, le=128)
    allow_api_keys: Optional[bool] = None
    ip_allowlist_enabled: Optional[bool] = None
    ip_allowlist: Optional[List[str]] = None
    notify_on_critical: Optional[bool] = None
    notify_on_cert_expiry: Optional[bool] = None
    cert_expiry_days: Optional[int] = Field(default=None, ge=1, le=365)
    audit_retention_days: Optional[int] = Field(default=None, ge=30, le=3650)
    gemini_byok_enabled: Optional[bool] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=10, max_length=128)
