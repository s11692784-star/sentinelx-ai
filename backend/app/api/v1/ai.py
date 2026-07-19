from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_tenant_id, require_membership
from app.db.session import get_db
from app.models.compliance import AIConversation
from app.models.secrets import CertificateAsset, SecretFinding
from app.models.user import User
from app.schemas.security_ops import AIChatRequest, AIChatResponse
from app.services.ai.gemini import GeminiClient
from app.services.audit import write_audit

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


@router.post("/chat", response_model=AIChatResponse)
async def chat(
    payload: AIChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_id),
):
    membership = await require_membership(user=user, tenant_id=tenant_id, db=db)

    # gather lightweight tenant context
    fq = await db.execute(
        select(SecretFinding)
        .where(SecretFinding.organization_id == membership.organization_id, SecretFinding.status == "open")
        .order_by(SecretFinding.risk_score.desc())
        .limit(5)
    )
    findings = [
        {"type": f.secret_type, "severity": f.severity, "risk": f.risk_score, "file": f.file_path}
        for f in fq.scalars().all()
    ]
    cq = await db.execute(
        select(CertificateAsset)
        .where(CertificateAsset.organization_id == membership.organization_id)
        .order_by(CertificateAsset.days_remaining.asc())
        .limit(5)
    )
    certs = [{"cn": c.common_name, "days": c.days_remaining, "risk": c.risk_score} for c in cq.scalars().all()]
    context = f"Open findings: {findings}. Certificates: {certs}."

    conv = None
    if payload.conversation_id:
        q = await db.execute(
            select(AIConversation).where(
                AIConversation.id == payload.conversation_id,
                AIConversation.organization_id == membership.organization_id,
                AIConversation.user_id == user.id,
            )
        )
        conv = q.scalar_one_or_none()
    if not conv:
        conv = AIConversation(
            organization_id=membership.organization_id,
            user_id=user.id,
            title=payload.message[:80],
            messages=[],
        )
        db.add(conv)
        await db.flush()

    client = GeminiClient(api_key=payload.gemini_api_key)
    result = client.generate(payload.message, context=context)
    messages = list(conv.messages or [])
    messages.append({"role": "user", "content": payload.message})
    messages.append({"role": "assistant", "content": result["reply"], "reasoning": result["reasoning"]})
    conv.messages = messages
    await write_audit(
        db,
        action="ai.chat",
        resource_type="ai_conversation",
        resource_id=str(conv.id),
        organization_id=membership.organization_id,
        actor_id=user.id,
        actor_email=user.email,
    )
    await db.flush()
    return AIChatResponse(
        conversation_id=conv.id,
        reply=result["reply"],
        reasoning=result["reasoning"],
        citations=result.get("citations") or [],
    )
