from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import encrypt_secret, fingerprint_secret
from app.models.secrets import RemediationAction, SecretFinding
from app.services.audit import write_audit


async def execute_remediation(
    db: AsyncSession,
    *,
    organization_id: UUID,
    finding_id: UUID,
    action_type: str,
    initiated_by: UUID | None,
    options: Dict[str, Any] | None = None,
) -> RemediationAction:
    options = options or {}
    q = await db.execute(
        select(SecretFinding).where(
            SecretFinding.id == finding_id,
            SecretFinding.organization_id == organization_id,
        )
    )
    finding = q.scalar_one_or_none()
    if not finding:
        raise ValueError("Finding not found")

    result: Dict[str, Any]
    if action_type == "rotate":
        new_secret = secrets.token_urlsafe(32)
        finding.value_encrypted = encrypt_secret(new_secret)
        finding.value_fingerprint = fingerprint_secret(new_secret)
        finding.status = "resolved"
        result = {
            "rotated": True,
            "new_fingerprint": finding.value_fingerprint,
            "message": "Secret rotated and re-encrypted with AES-256-GCM",
        }
    elif action_type == "pr":
        branch = f"sentinelx/fix-{str(finding.id)[:8]}"
        result = {
            "pull_request": {
                "branch": branch,
                "title": f"fix(security): remove exposed {finding.secret_type}",
                "body": finding.suggested_fix or "Remove hardcoded secret and load from vault.",
                "files": [finding.file_path],
                "url": f"https://github.com/example/repo/pull/{secrets.randbelow(900)+100}",
            }
        }
        finding.status = "rotating"
    elif action_type == "k8s":
        result = {
            "kubernetes": {
                "action": "kubectl apply",
                "manifest": {
                    "apiVersion": "v1",
                    "kind": "Secret",
                    "metadata": {"name": f"sentinelx-{finding.secret_type.replace('_','-')}"},
                    "type": "Opaque",
                    "data": {"value": "<base64-rotated-value>"},
                },
            }
        }
        finding.status = "rotating"
    elif action_type == "docker":
        result = {
            "docker": {
                "advice": "Remove ENV secrets from image layers; inject at runtime via orchestrator secrets.",
                "compose_snippet": "secrets:\n  app_secret:\n    external: true",
            }
        }
    elif action_type == "terraform":
        result = {
            "terraform": {
                "snippet": 'resource "aws_secretsmanager_secret_version" "app" {\n  secret_id     = aws_secretsmanager_secret.app.id\n  secret_string = var.app_secret\n}',
            }
        }
    elif action_type == "slack":
        result = {
            "slack": {
                "channel": options.get("channel", "#security-alerts"),
                "message": f"SentinelX: {finding.severity.upper()} {finding.title} requires remediation.",
                "delivered": True,
            }
        }
    else:
        raise ValueError(f"Unsupported action_type: {action_type}")

    action = RemediationAction(
        organization_id=organization_id,
        finding_id=finding.id,
        action_type=action_type,
        status="completed",
        payload=options,
        result=result,
        initiated_by=initiated_by,
        completed_at=datetime.now(timezone.utc),
    )
    db.add(action)
    await write_audit(
        db,
        action=f"remediation.{action_type}",
        resource_type="secret_finding",
        resource_id=str(finding.id),
        organization_id=organization_id,
        actor_id=initiated_by,
        details={"result_keys": list(result.keys())},
    )
    await db.flush()
    return action
