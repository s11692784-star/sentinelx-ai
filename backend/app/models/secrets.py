from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class ScanJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "scan_jobs"

    organization_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    repository_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True, index=True)
    initiated_by: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)
    source_type: Mapped[str] = mapped_column(String(50))  # github|gitlab|upload|k8s|docker|terraform
    status: Mapped[str] = mapped_column(String(50), default="queued")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    findings_count: Mapped[int] = mapped_column(Integer, default=0)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    findings: Mapped[List["SecretFinding"]] = relationship(back_populates="scan_job", cascade="all, delete-orphan")


class SecretFinding(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "secret_findings"

    organization_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    scan_job_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("scan_jobs.id", ondelete="SET NULL"), nullable=True
    )
    repository_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True, index=True)
    secret_type: Mapped[str] = mapped_column(String(80), index=True)
    severity: Mapped[str] = mapped_column(String(20), default="high")
    title: Mapped[str] = mapped_column(String(300))
    file_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    line_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    snippet_redacted: Mapped[str] = mapped_column(Text)
    value_fingerprint: Mapped[str] = mapped_column(String(128), index=True)
    value_encrypted: Mapped[str] = mapped_column(Text)  # AES-GCM, never plaintext
    status: Mapped[str] = mapped_column(String(40), default="open")  # open|rotating|resolved|false_positive
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    likelihood: Mapped[float] = mapped_column(Float, default=0.0)
    business_impact: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    ai_reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mitre_techniques: Mapped[list] = mapped_column(JSON, default=list)
    cve_references: Mapped[list] = mapped_column(JSON, default=list)
    suggested_fix: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estimated_fix_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    owasp_category: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    tags: Mapped[list] = mapped_column(JSON, default=list)

    scan_job: Mapped[Optional[ScanJob]] = relationship(back_populates="findings")


class CertificateAsset(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "certificates"

    organization_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    common_name: Mapped[str] = mapped_column(String(300), index=True)
    sans: Mapped[list] = mapped_column(JSON, default=list)
    issuer: Mapped[str] = mapped_column(String(300))
    serial_number: Mapped[str] = mapped_column(String(128))
    cert_type: Mapped[str] = mapped_column(String(40), default="tls")  # tls|ssl|internal|client
    not_before: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    not_after: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    days_remaining: Mapped[int] = mapped_column(Integer, default=0)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False)
    renew_status: Mapped[str] = mapped_column(String(40), default="idle")
    fingerprint_sha256: Mapped[str] = mapped_column(String(128), index=True)
    source: Mapped[str] = mapped_column(String(80), default="scan")
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    alert_sent: Mapped[bool] = mapped_column(Boolean, default=False)


class RemediationAction(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "remediation_actions"

    organization_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    finding_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True, index=True)
    action_type: Mapped[str] = mapped_column(String(80))  # rotate|pr|k8s|docker|terraform|slack
    status: Mapped[str] = mapped_column(String(40), default="pending")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    initiated_by: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
