from __future__ import annotations

from datetime import datetime, timezone
from math import exp
from typing import Optional


def days_until(not_after: datetime, now: Optional[datetime] = None) -> int:
    now = now or datetime.now(timezone.utc)
    if not_after.tzinfo is None:
        not_after = not_after.replace(tzinfo=timezone.utc)
    return int((not_after - now).total_seconds() // 86400)


def certificate_risk(days_remaining: int, cert_type: str = "tls", auto_renew: bool = False) -> float:
    """Higher score = higher risk. Exponential urgency under 30 days."""
    base = 100 * exp(-max(days_remaining, 0) / 45.0)
    if cert_type in {"tls", "ssl"}:
        base *= 1.1
    if days_remaining < 0:
        base = 100.0
    if auto_renew and days_remaining > 7:
        base *= 0.7
    return round(min(100.0, base), 2)


def renew_recommendation(days_remaining: int) -> str:
    if days_remaining < 0:
        return "expired_immediate_reissue"
    if days_remaining <= 7:
        return "emergency_renew"
    if days_remaining <= 30:
        return "schedule_renew"
    return "monitor"
