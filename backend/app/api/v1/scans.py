from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_membership
from app.db.session import get_db
from app.models.compliance import Notification
from app.models.secrets import ScanJob, SecretFinding
from app.models.user import User
from app.schemas.security_ops import ScanJobOut, ScanRequest, SecretFindingOut
from app.services.audit import write_audit
from app.services.discovery.engine import score_finding, scan_structured, scan_text
from app.services.ai.gemini import GeminiClient

router = APIRouter(tags=["Secret Discovery"])


@router.post("/scans", response_model=ScanJobOut)
async def start_scan(
    payload: ScanRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID | None = Depends(__import__("app.core.deps", fromlist=["get_tenant_id"]).get_tenant_id),
):
    membership = await require_membership(user=user, tenant_id=tenant_id, db=db, roles={"admin", "security_analyst", "developer"})
    job = ScanJob(
        organization_id=membership.organization_id,
        repository_id=payload.repository_id,
        initiated_by=user.id,
        source_type=payload.source_type,
        status="running",
        progress=10,
        started_at=datetime.now(timezone.utc),
        meta=payload.meta or {},
    )
    db.add(job)
    await db.flush()

    content = payload.content or ""
    filename = payload.filename or f"scan.{payload.source_type}"
    raws = scan_structured(content, filename, payload.source_type) if content else []
    gemini = GeminiClient()
    count = 0
    for raw in raws:
        scored = score_finding(raw)
        scored = gemini.enrich_finding({**scored, "secret_type": raw.secret_type, "severity": scored["severity"], "file_path": raw.file_path})
        finding = SecretFinding(
            organization_id=membership.organization_id,
            scan_job_id=job.id,
            repository_id=payload.repository_id,
            secret_type=raw.secret_type,
            title=raw.title,
            file_path=raw.file_path,
            line_number=raw.line_number,
            tags=raw.tags,
            **{k: scored[k] for k in [
                "severity", "risk_score", "likelihood", "business_impact", "confidence", "ai_reasoning",
                "mitre_techniques", "cve_references", "suggested_fix", "estimated_fix_minutes",
                "owasp_category", "value_encrypted", "value_fingerprint", "snippet_redacted",
            ]},
        )
        db.add(finding)
        count += 1
        if scored["severity"] in {"critical", "high"}:
            db.add(
                Notification(
                    organization_id=membership.organization_id,
                    user_id=user.id,
                    title=f"{scored['severity'].upper()}: {raw.title}",
                    body=scored.get("suggested_fix") or "Remediate exposed secret",
                    severity=scored["severity"],
                    meta={"finding_type": raw.secret_type},
                )
            )

    job.progress = 100
    job.status = "completed"
    job.findings_count = count
    job.finished_at = datetime.now(timezone.utc)
    await write_audit(
        db,
        action="scan.completed",
        resource_type="scan_job",
        resource_id=str(job.id),
        organization_id=membership.organization_id,
        actor_id=user.id,
        actor_email=user.email,
        details={"findings": count, "source_type": payload.source_type},
    )
    await db.flush()
    return job


@router.post("/scans/upload", response_model=ScanJobOut)
async def upload_scan(
    source_type: str = Form("upload"),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID | None = Depends(__import__("app.core.deps", fromlist=["get_tenant_id"]).get_tenant_id),
):
    data = await file.read()
    try:
        text = data.decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Unable to read file") from exc
    return await start_scan(
        ScanRequest(source_type=source_type, content=text, filename=file.filename or "upload.txt"),
        user=user,
        db=db,
        tenant_id=tenant_id,
    )


@router.get("/scans", response_model=list[ScanJobOut])
async def list_scans(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID | None = Depends(__import__("app.core.deps", fromlist=["get_tenant_id"]).get_tenant_id),
):
    membership = await require_membership(user=user, tenant_id=tenant_id, db=db)
    q = await db.execute(
        select(ScanJob).where(ScanJob.organization_id == membership.organization_id).order_by(ScanJob.created_at.desc()).limit(100)
    )
    return list(q.scalars().all())


@router.get("/findings", response_model=list[SecretFindingOut])
async def list_findings(
    status: str | None = None,
    severity: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID | None = Depends(__import__("app.core.deps", fromlist=["get_tenant_id"]).get_tenant_id),
):
    membership = await require_membership(user=user, tenant_id=tenant_id, db=db)
    stmt = select(SecretFinding).where(SecretFinding.organization_id == membership.organization_id)
    if status:
        stmt = stmt.where(SecretFinding.status == status)
    if severity:
        stmt = stmt.where(SecretFinding.severity == severity)
    stmt = stmt.order_by(SecretFinding.risk_score.desc()).limit(500)
    q = await db.execute(stmt)
    return list(q.scalars().all())


@router.get("/findings/{finding_id}", response_model=SecretFindingOut)
async def get_finding(
    finding_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID | None = Depends(__import__("app.core.deps", fromlist=["get_tenant_id"]).get_tenant_id),
):
    membership = await require_membership(user=user, tenant_id=tenant_id, db=db)
    q = await db.execute(
        select(SecretFinding).where(
            SecretFinding.id == finding_id,
            SecretFinding.organization_id == membership.organization_id,
        )
    )
    finding = q.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding
