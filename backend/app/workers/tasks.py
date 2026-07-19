from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.compliance import Notification
from app.models.secrets import CertificateAsset
from app.services.certificates.lifecycle import certificate_risk, days_until
from app.workers.celery_app import celery_app


async def _sweep() -> int:
    async with AsyncSessionLocal() as db:
        q = await db.execute(select(CertificateAsset))
        certs = list(q.scalars().all())
        alerts = 0
        for cert in certs:
            cert.days_remaining = days_until(cert.not_after)
            cert.risk_score = certificate_risk(cert.days_remaining, cert.cert_type, cert.auto_renew)
            if cert.days_remaining <= 30 and not cert.alert_sent:
                db.add(
                    Notification(
                        organization_id=cert.organization_id,
                        channel="in_app",
                        title=f"Certificate expiring: {cert.common_name}",
                        body=f"{cert.days_remaining} days remaining. Issuer={cert.issuer}",
                        severity="high" if cert.days_remaining <= 14 else "medium",
                        meta={"certificate_id": str(cert.id)},
                    )
                )
                cert.alert_sent = True
                alerts += 1
        await db.commit()
        return alerts


@celery_app.task(name="app.workers.tasks.sweep_certificate_expiry")
def sweep_certificate_expiry() -> dict:
    count = asyncio.get_event_loop().run_until_complete(_sweep()) if False else asyncio.run(_sweep())
    return {"alerts": count, "ran_at": datetime.now(timezone.utc).isoformat()}
