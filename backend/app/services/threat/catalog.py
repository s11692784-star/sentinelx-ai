from __future__ import annotations

from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compliance import ThreatIntelEntry

SEED: List[dict] = [
    {
        "source": "MITRE ATT&CK",
        "title": "Unsecured Credentials: Credentials In Files",
        "description": "Adversaries search compromised systems for credentials stored in cleartext files, config repos, and CI variables.",
        "mitre_id": "T1552.001",
        "cve_id": None,
        "owasp": "A07:2021",
        "severity": "high",
        "known_exploits": ["Git history secret dorking", "CI log scraping"],
        "references": ["https://attack.mitre.org/techniques/T1552/001/"],
    },
    {
        "source": "MITRE ATT&CK",
        "title": "Valid Accounts: Cloud Accounts",
        "description": "Stolen cloud API keys enable persistence and lateral movement across tenants and subscriptions.",
        "mitre_id": "T1078.004",
        "cve_id": None,
        "owasp": "A01:2021",
        "severity": "critical",
        "known_exploits": ["AWS key abuse for crypto mining"],
        "references": ["https://attack.mitre.org/techniques/T1078/004/"],
    },
    {
        "source": "NVD",
        "title": "Hard-coded credentials weakness",
        "description": "CWE-798 hard-coded credentials remain a top root cause in breached applications and IaC modules.",
        "mitre_id": "T1552",
        "cve_id": "CWE-798",
        "owasp": "A07:2021",
        "severity": "high",
        "known_exploits": ["Default password botnets"],
        "references": ["https://cwe.mitre.org/data/definitions/798.html"],
    },
    {
        "source": "OWASP",
        "title": "Cryptographic Failures",
        "description": "Expired or weak TLS certificates degrade transport security and enable downgrade or interception risks.",
        "mitre_id": "T1557",
        "cve_id": None,
        "owasp": "A02:2021",
        "severity": "medium",
        "known_exploits": ["Expired cert outages", "MITM on stale ciphers"],
        "references": ["https://owasp.org/Top10/A02_2021-Cryptographic_Failures/"],
    },
    {
        "source": "ExploitDB-style",
        "title": "JWT token theft and replay",
        "description": "Long-lived JWTs committed to repos or logs can be replayed to impersonate users and services.",
        "mitre_id": "T1528",
        "cve_id": "CWE-522",
        "owasp": "A07:2021",
        "severity": "high",
        "known_exploits": ["Token replay against APIs"],
        "references": ["https://attack.mitre.org/techniques/T1528/"],
    },
]


async def ensure_seed(db: AsyncSession) -> int:
    q = await db.execute(select(ThreatIntelEntry).limit(1))
    if q.scalar_one_or_none():
        return 0
    for row in SEED:
        db.add(ThreatIntelEntry(organization_id=None, **row))
    await db.flush()
    return len(SEED)
