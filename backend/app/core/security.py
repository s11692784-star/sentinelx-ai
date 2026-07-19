from __future__ import annotations

import base64
import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(data: Dict[str, Any], expires_delta: timedelta, token_type: str = "access") -> str:
    payload = data.copy()
    now = datetime.now(timezone.utc)
    payload.update({"exp": now + expires_delta, "iat": now, "type": token_type})
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str, extra: Optional[Dict[str, Any]] = None) -> str:
    data = {"sub": subject, **(extra or {})}
    return create_token(data, timedelta(minutes=settings.access_token_expire_minutes), "access")


def create_refresh_token(subject: str) -> str:
    return create_token({"sub": subject}, timedelta(days=settings.refresh_token_expire_days), "refresh")


def decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc


def generate_otp(length: int = 6) -> str:
    return "".join(str(secrets.randbelow(10)) for _ in range(length))


def generate_totp_secret() -> str:
    return base64.b32encode(os.urandom(20)).decode("utf-8")


def _aes_key() -> bytes:
    raw = settings.aes_master_key.encode("utf-8")
    if len(raw) == 64:
        try:
            return bytes.fromhex(settings.aes_master_key)
        except ValueError:
            pass
    return hashlib.sha256(raw).digest()


def encrypt_secret(plaintext: str) -> str:
    """AES-256-GCM encrypt. Returns base64(nonce + ciphertext + tag)."""
    if plaintext is None:
        raise ValueError("plaintext required")
    key = _aes_key()
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ct = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.b64encode(nonce + ct).decode("utf-8")


def decrypt_secret(token: str) -> str:
    raw = base64.b64decode(token.encode("utf-8"))
    nonce, ct = raw[:12], raw[12:]
    aesgcm = AESGCM(_aes_key())
    return aesgcm.decrypt(nonce, ct, None).decode("utf-8")


def fingerprint_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
