"""Seed demo tenant with sample findings and certificates."""
from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.db.session import AsyncSessionLocal, Base, engine
from app.models import *  # noqa: F401,F403
from app.services.auth.service import signup
from app.services.discovery.engine import score_finding, scan_text
from app.models.secrets import CertificateAsset, SecretFinding
from app.models.organization import Project, Repository
from app.services.certificates.lifecycle import certificate_risk, days_until
from app.services.threat.catalog import ensure_seed


SAMPLE = Path(__file__).resolve().parents[2] / "sample_data" / "leaky_config.env"


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        user, org, otp = await signup(
            db,
            email="admin@sentinelx.demo",
            password="DemoPass12345!",
            full_name="Avery Admin",
            org_name="Nimbus Financial",
        )
        print("OTP", otp)
        project = Project(organization_id=org.id, name="Payments Platform", slug="payments-platform", description="Core payments", environment="production")
        db.add(project)
        await db.flush()
        repo = Repository(
            project_id=project.id,
            organization_id=org.id,
            name="payments-api",
            provider="github",
            url="https://github.com/nimbus/payments-api",
            default_branch="main",
            risk_score=78,
        )
        db.add(repo)
        content = SAMPLE.read_text() if SAMPLE.exists() else "AWS_ACCESS_KEY_ID=AKIAEXAMPLEKEY00000\n"
        for raw in scan_text(content, "configs/production.env"):
            scored = score_finding(raw)
            db.add(
                SecretFinding(
                    organization_id=org.id,
                    repository_id=repo.id,
                    secret_type=raw.secret_type,
                    title=raw.title,
                    file_path=raw.file_path,
                    line_number=raw.line_number,
                    tags=raw.tags,
                    severity=scored["severity"],
                    risk_score=scored["risk_score"],
                    likelihood=scored["likelihood"],
                    business_impact=scored["business_impact"],
                    confidence=scored["confidence"],
                    ai_reasoning=scored["ai_reasoning"],
                    mitre_techniques=scored["mitre_techniques"],
                    cve_references=scored["cve_references"],
                    suggested_fix=scored["suggested_fix"],
                    estimated_fix_minutes=scored["estimated_fix_minutes"],
                    owasp_category=scored["owasp_category"],
                    value_encrypted=scored["value_encrypted"],
                    value_fingerprint=scored["value_fingerprint"],
                    snippet_redacted=scored["snippet_redacted"],
                )
            )
        now = datetime.now(timezone.utc)
        for cn, days, issuer in [
            ("api.nimbus.bank", 12, "Let's Encrypt"),
            ("admin.nimbus.bank", 45, "DigiCert"),
            ("internal-ca.nimbus.local", 5, "Nimbus Internal CA"),
        ]:
            not_after = now + timedelta(days=days)
            db.add(
                CertificateAsset(
                    organization_id=org.id,
                    common_name=cn,
                    sans=[cn],
                    issuer=issuer,
                    serial_number=f"SN-{days:04d}",
                    cert_type="tls" if "local" not in cn else "internal",
                    not_before=now - timedelta(days=60),
                    not_after=not_after,
                    days_remaining=days_until(not_after),
                    risk_score=certificate_risk(days),
                    fingerprint_sha256=f"{'ab'*32}",
                    source="seed",
                    auto_renew=cn.startswith("api"),
                )
            )
        await ensure_seed(db)
        await db.commit()
        print("Seeded org", org.id, "user admin@sentinelx.demo / DemoPass12345!")


if __name__ == "__main__":
    asyncio.run(main())
