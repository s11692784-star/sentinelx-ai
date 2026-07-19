from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MeResponse,
    MembershipOut,
    OTPVerifyRequest,
    RefreshRequest,
    ResetPasswordRequest,
    SignupRequest,
    TokenResponse,
    UserOut,
)
from app.services.auth import service as auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=dict)
async def signup(payload: SignupRequest, db: AsyncSession = Depends(get_db)):
    try:
        user, org, otp = await auth_service.signup(
            db, payload.email, payload.password, payload.full_name, payload.organization_name
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "user": UserOut.model_validate(user),
        "organization_id": str(org.id),
        "organization_slug": org.slug,
        "otp_demo": otp if settings.debug else None,
        "message": "Signup successful. Verify email with OTP.",
    }


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        user, access, refresh = await auth_service.login(db, payload.email, payload.password, payload.totp_code)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        access, refresh_token = await auth_service.refresh_tokens(db, payload.refresh_token)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return TokenResponse(
        access_token=access,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    otp = await auth_service.create_otp(db, payload.email, "reset")
    return {"message": "If the account exists, an OTP was issued.", "otp_demo": otp if settings.debug else None}


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    try:
        await auth_service.reset_password(db, payload.email, payload.otp_code, payload.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"message": "Password updated"}


@router.post("/verify-otp")
async def verify_otp(payload: OTPVerifyRequest, db: AsyncSession = Depends(get_db)):
    ok = await auth_service.verify_otp(db, payload.email, payload.otp_code, payload.purpose)
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    return {"verified": True}


@router.post("/2fa/enable")
async def enable_2fa(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    secret = await auth_service.enable_2fa(db, user)
    return {"totp_secret": secret, "message": "2FA enabled. In development use code 000000."}


@router.get("/me", response_model=MeResponse)
async def me(user: User = Depends(get_current_user)):
    return MeResponse(
        user=UserOut.model_validate(user),
        memberships=[MembershipOut.model_validate(m) for m in user.memberships],
    )
