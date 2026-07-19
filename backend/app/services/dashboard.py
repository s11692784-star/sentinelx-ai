from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compliance import Notification
from app.models.organization import Repository
from app.models.secrets import CertificateAsset, SecretFinding
from app.schemas.security_ops import DashboardOut


async def build_dashboard(db: AsyncSession, organization_id: UUID) -> DashboardOut:
    findings_q = await db.execute(select(SecretFinding).where(SecretFinding.organization_id == organization_id))
    findings = list(findings_q.scalars().all())
    open_findings = [f for f in findings if f.status == "open"]
    critical = [f for f in open_findings if f.severity == "critical"]

    certs_q = await db.execute(select(CertificateAsset).where(CertificateAsset.organization_id == organization_id))
    certs = list(certs_q.scalars().all())
    expiring = [c for c in certs if c.days_remaining <= 30]

    repo_q = await db.execute(select(func.count()).select_from(Repository).where(Repository.organization_id == organization_id))
    repo_count = int(repo_q.scalar() or 0)

    # security score
    if not findings and not certs:
        score = 92.0
    else:
        avg_risk = sum(f.risk_score for f in open_findings) / max(1, len(open_findings))
        cert_pen = min(30, 2 * len(expiring))
        score = max(5.0, round(100 - avg_risk * 0.55 - len(critical) * 4 - cert_pen * 0.4, 1))

    sev = Counter(f.severity for f in open_findings)
    heatmap = []
    for f in sorted(open_findings, key=lambda x: x.risk_score, reverse=True)[:20]:
        heatmap.append(
            {
                "id": str(f.id),
                "type": f.secret_type,
                "severity": f.severity,
                "risk": f.risk_score,
                "file": f.file_path,
            }
        )

    now = datetime.now(timezone.utc)
    trend = []
    for i in range(13, -1, -1):
        day = (now - timedelta(days=i)).date()
        count = sum(1 for f in findings if f.created_at and f.created_at.date() <= day and f.status == "open")
        trend.append({"date": day.isoformat(), "open_findings": count})

    nodes = [{"id": "org", "label": "Organization", "type": "org"}]
    edges = []
    for ridx, repo_name in enumerate({(f.file_path or "repo").split("/")[0] for f in open_findings} or {"app"}):
        rid = f"repo-{ridx}"
        nodes.append({"id": rid, "label": repo_name, "type": "repository"})
        edges.append({"source": "org", "target": rid})
    for f in open_findings[:12]:
        fid = str(f.id)[:8]
        nodes.append({"id": fid, "label": f.secret_type, "type": "finding", "severity": f.severity})
        edges.append({"source": nodes[1]["id"] if len(nodes) > 1 else "org", "target": fid})

    alerts_q = await db.execute(
        select(Notification)
        .where(Notification.organization_id == organization_id)
        .order_by(Notification.created_at.desc())
        .limit(8)
    )
    alerts = [
        {"id": str(n.id), "title": n.title, "severity": n.severity, "body": n.body, "created_at": n.created_at.isoformat()}
        for n in alerts_q.scalars().all()
    ]
    if not alerts:
        for f in critical[:5]:
            alerts.append(
                {
                    "id": str(f.id),
                    "title": f.title,
                    "severity": f.severity,
                    "body": f.suggested_fix or "",
                    "created_at": f.created_at.isoformat() if f.created_at else now.isoformat(),
                }
            )

    return DashboardOut(
        security_score=score,
        open_findings=len(open_findings),
        critical_findings=len(critical),
        expiring_certificates=len(expiring),
        repositories=repo_count,
        recent_alerts=alerts,
        risk_heatmap=heatmap,
        trend=trend,
        attack_graph={"nodes": nodes, "edges": edges},
        severity_breakdown=dict(sev),
    )
