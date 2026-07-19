from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "SentinelX AI"
    app_env: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # Default: SQLite for zero-deps local demo. Override with Postgres URL in production.
    database_url: str = "sqlite+aiosqlite:///./sentinelx.db"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    jwt_secret: str = "DEV_ONLY_REPLACE_WITH_STRONG_JWT_SECRET_VALUE_32CHARS"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14

    aes_master_key: str = "DEV_ONLY_REPLACE_WITH_OPENSSL_RAND_HEX_32_BYTES_KEY_VALUE_00"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    gemini_api_key: str = ""
    rate_limit_per_minute: int = 120
    frontend_url: str = "http://localhost:3000"
    session_cookie_secure: bool = False
    force_https: bool = False
    allow_demo_seed: bool = True
    password_min_length: int = 10
    max_login_attempts: int = 8
    login_lockout_minutes: int = 15

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production" or (not self.debug and self.app_env.lower() != "development")

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def validate_production_secrets(self) -> None:
        if not self.is_production:
            return
        weak = {
            "DEV_ONLY_REPLACE_WITH_STRONG_JWT_SECRET_VALUE_32CHARS",
            "dev-secret",
            "dev-secret-change-me",
            "test-secret-key-for-ci-only",
        }
        if self.jwt_secret in weak or len(self.jwt_secret) < 32:
            raise RuntimeError("JWT_SECRET must be a strong random value (>=32 chars) in production")
        if len(self.aes_master_key) < 32:
            raise RuntimeError("AES_MASTER_KEY must be set to a strong key in production")
        if "*" in self.cors_origins:
            raise RuntimeError("CORS_ORIGINS must not be wildcard in production")


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    # Coerce common string bools from cloud hosts
    if isinstance(s.debug, str):  # type: ignore[unreachable]
        pass
    return s


settings = get_settings()
