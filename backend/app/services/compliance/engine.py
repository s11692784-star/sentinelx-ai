from __future__ import annotations

from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compliance import ComplianceReport
from app.models.secrets import CertificateAsset, SecretFinding
from app.services.audit import write_audit

FRAMEWORKS: Dict[str, List[Dict[str, Any]]] = {
    "ISO27001": [
        {"id": "A.8.2", "name": "Information classification", "weight": 1.0},
        {"id": "A.8.3", "name": "Media handling / secret storage", "weight": 1.2},
        {"id": "A.9.2", "name": "User access management", "weight": 1.1},
        {"id": "A.10.1", "name": "Cryptographic controls", "weight": 1.3},
        {"id": "A.12.4", "name": "Logging and monitoring", "weight": 1.0},
    ],
    "SOC2": [
        {"id": "CC6.1", "name": "Logical access security", "weight": 1.2},
        {"id": "CC6.6", "name": "Encryption in transit/at rest", "weight": 1.2},
        {"id": "CC7.2", "name": "Monitor security events", "weight": 1.0},
        {"id": "CC8.1", "name": "Change management", "weight": 0.9},
    ],
    "PCI_DSS": [
        {"id": "3.5", "name": "Protect secret keys", "weight": 1.4},
        {"id": "8.3", "name": "Strong authentication", "weight": 1.1},
        {"id": "10.2", "name": "Audit trails", "weight": 1.0},
    ],
    "HIPAA": [
        {"id": "164.312(a)", "name": "Access control", "weight": 1.2},
        {"id": "164.312(b)", "name": "Audit controls", "weight": 1.0},
        {"id": "164.312(e)", "name": "Transmission security", "weight": 1.1},
    ],
    "GDPR": [
        {"id": "Art.32", "name": "Security of processing", "weight": 1.3},
        {"id": "Art.33", "name": "Breach notification readiness", "weight": 1.0},
        {"id": "Art.25", "name": "Data protection by design", "weight": 1.1},
    ],
}


async def generate_report(
    db: AsyncSession,
    *,
    organization_id: UUID,
    framework: str,
    generated_by: UUID | None,
) -> ComplianceReport:
    if framework not in FRAMEWORKS:
        raise ValueError("Unsupported framework")

    open_q = await db.execute(
        select(func.count()).select_from(SecretFinding).where(
            SecretFinding.organization_id == organization_id,
            SecretFinding.status == "open",
        )
    )
    open_findings = int(open_q.scalar() or 0)
    crit_q = await db.execute(
        select(func.count()).select_from(SecretFinding).where(
            SecretFinding.organization_id == organization_id,
            SecretFinding.severity == "critical",
            SecretFinding.status == "open",
        )
    )
    critical = int(crit_q.scalar() or 0)
    exp_q = await db.execute(
        select(func.count()).select_from(CertificateAsset).where(
            CertificateAsset.organization_id == organization_id,
            CertificateAsset.days_remaining <= 30,
        )
    )
    expiring = int(exp_q.scalar() or 0)

    controls = []
    gaps = []
    total_w = 0.0
    score_w = 0.0
    for ctrl in FRAMEWORKS[framework]:
        total_w += ctrl["weight"]
        # degrade score with open risk
        penalty = min(0.85, 0.08 * open_findings + 0.12 * critical + 0.05 * expiring)
        ctrl_score = max(15.0, 100.0 * (1.0 - penalty))
        status = "pass" if ctrl_score >= 75 else "gap"
        item = {**ctrl, "score": round(ctrl_score, 1), "status": status}
        controls.append(item)
        score_w += ctrl_score * ctrl["weight"]
        if status == "gap":
            gaps.append(
                {
                    "control": ctrl["id"],
                    "issue": "Elevated secret/certificate risk reduces control effectiveness",
                    "recommendation": "Close critical findings, enforce rotation SLAs, enable cert auto-renew",
                }
            )

    score = round(score_w / total_w, 1) if total_w else 0.0
    summary = (
        f"{framework} posture score {score}/100 based on {open_findings} open findings "
        f"({critical} critical) and {expiring} certificates nearing expiry. "
        f"{len(gaps)} control gaps require remediation evidence."
    )
    report = ComplianceReport(
        organization_id=organization_id,
        framework=framework,
        score=score,
        status="generated",
        controls=controls,
        gaps=gaps,
        summary=summary,
        generated_by=generated_by,
    )
    db.add(report)
    await write_audit(
        db,
        action="compliance.report_generated",
        resource_type="compliance_report",
        organization_id=organization_id,
        actor_id=generated_by,
        details={"framework": framework, "score": score},
    )
    await db.flush()
    return report
