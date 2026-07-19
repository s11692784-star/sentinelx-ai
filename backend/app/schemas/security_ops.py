from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ScanRequest(BaseModel):
    source_type: str = Field(description="github|gitlab|bitbucket|docker|terraform|env|yaml|json|xml|k8s|zip|logs|docs|upload")
    repository_id: Optional[UUID] = None
    content: Optional[str] = None
    filename: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class ScanJobOut(BaseModel):
    id: UUID
    source_type: str
    status: str
    progress: int
    findings_count: int
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    error_message: Optional[str]

    model_config = {"from_attributes": True}


class SecretFindingOut(BaseModel):
    id: UUID
    secret_type: str
    severity: str
    title: str
    file_path: Optional[str]
    line_number: Optional[int]
    snippet_redacted: str
    status: str
    risk_score: float
    likelihood: float
    business_impact: float
    confidence: float
    ai_reasoning: Optional[str]
    mitre_techniques: list
    cve_references: list
    suggested_fix: Optional[str]
    estimated_fix_minutes: Optional[int]
    owasp_category: Optional[str]
    tags: list
    created_at: datetime

    model_config = {"from_attributes": True}


class CertificateCreate(BaseModel):
    common_name: str
    issuer: str
    serial_number: str
    cert_type: str = "tls"
    not_before: datetime
    not_after: datetime
    sans: List[str] = Field(default_factory=list)
    fingerprint_sha256: str
    auto_renew: bool = False
    source: str = "manual"


class CertificateOut(BaseModel):
    id: UUID
    common_name: str
    issuer: str
    serial_number: str
    cert_type: str
    not_before: datetime
    not_after: datetime
    days_remaining: int
    risk_score: float
    auto_renew: bool
    renew_status: str
    sans: list
    fingerprint_sha256: str
    source: str
    alert_sent: bool

    model_config = {"from_attributes": True}


class RemediationRequest(BaseModel):
    finding_id: UUID
    action_type: str = Field(description="rotate|pr|k8s|docker|terraform|slack")
    options: Dict[str, Any] = Field(default_factory=dict)


class RemediationOut(BaseModel):
    id: UUID
    finding_id: Optional[UUID]
    action_type: str
    status: str
    payload: dict
    result: dict
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class AIChatRequest(BaseModel):
    message: str
    conversation_id: Optional[UUID] = None
    gemini_api_key: Optional[str] = Field(default=None, description="BYOK Gemini key")


class AIChatResponse(BaseModel):
    conversation_id: UUID
    reply: str
    reasoning: str
    citations: List[str] = Field(default_factory=list)


class ComplianceGenerateRequest(BaseModel):
    framework: str = Field(pattern="^(ISO27001|SOC2|PCI_DSS|HIPAA|GDPR)$")


class ComplianceReportOut(BaseModel):
    id: UUID
    framework: str
    score: float
    status: str
    controls: list
    gaps: list
    summary: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ThreatIntelOut(BaseModel):
    id: UUID
    source: str
    title: str
    description: str
    mitre_id: Optional[str]
    cve_id: Optional[str]
    owasp: Optional[str]
    severity: str
    known_exploits: list
    references: list

    model_config = {"from_attributes": True}


class DashboardOut(BaseModel):
    security_score: float
    open_findings: int
    critical_findings: int
    expiring_certificates: int
    repositories: int
    recent_alerts: List[dict]
    risk_heatmap: List[dict]
    trend: List[dict]
    attack_graph: dict
    severity_breakdown: dict
