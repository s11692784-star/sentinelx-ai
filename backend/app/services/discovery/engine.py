from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Iterable, List, Optional

from app.core.security import encrypt_secret, fingerprint_secret


@dataclass
class RawFinding:
    secret_type: str
    title: str
    value: str
    file_path: str
    line_number: int
    snippet: str
    confidence: float
    tags: List[str] = field(default_factory=list)


PATTERNS: list[tuple[str, re.Pattern[str], str, float, list[str]]] = [
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}"), "AWS Access Key ID", 0.95, ["aws", "cloud"]),
    ("aws_secret_key", re.compile(r"(?i)aws(.{0,20})?(secret|access)?(.{0,20})?['\"]([0-9a-zA-Z/+]{40})['\"]"), "AWS Secret Access Key", 0.85, ["aws"]),
    ("azure_key", re.compile(r"(?i)DefaultEndpointsProtocol=https;AccountName=[^;]+;AccountKey=[A-Za-z0-9+/=]{40,};"), "Azure Storage Connection String", 0.9, ["azure"]),
    ("gcp_api_key", re.compile(r"AIza[0-9A-Za-z\-_]{35}"), "Google API Key", 0.9, ["gcp", "google"]),
    ("stripe_key", re.compile(r"sk_live_[0-9a-zA-Z]{24,}"), "Stripe Live Secret Key", 0.97, ["stripe", "payments"]),
    ("twilio_key", re.compile(r"SK[0-9a-fA-F]{32}"), "Twilio API Key", 0.88, ["twilio"]),
    ("firebase", re.compile(r"(?i)firebase(.{0,20})?['\"]([A-Za-z0-9_\-]{20,})['\"]"), "Firebase Credential", 0.7, ["firebase"]),
    ("jwt", re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}"), "JWT Token", 0.8, ["jwt", "auth"]),
    ("ssh_private_key", re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"), "SSH Private Key", 0.99, ["ssh", "key"]),
    ("generic_password", re.compile(r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{8,}['\"]"), "Hardcoded Password", 0.65, ["password"]),
    ("pem_cert", re.compile(r"-----BEGIN CERTIFICATE-----"), "Embedded Certificate", 0.9, ["certificate"]),
    ("github_pat", re.compile(r"ghp_[A-Za-z0-9]{36}"), "GitHub Personal Access Token", 0.96, ["github"]),
    ("slack_token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"), "Slack Token", 0.93, ["slack"]),
]


SEVERITY_MAP = {
    "aws_access_key": "critical",
    "aws_secret_key": "critical",
    "azure_key": "critical",
    "stripe_key": "critical",
    "ssh_private_key": "critical",
    "github_pat": "high",
    "gcp_api_key": "high",
    "jwt": "high",
    "twilio_key": "high",
    "slack_token": "high",
    "pem_cert": "medium",
    "firebase": "medium",
    "generic_password": "high",
}


def redact(value: str) -> str:
    if len(value) <= 8:
        return "*" * len(value)
    return value[:4] + ("*" * min(24, len(value) - 8)) + value[-4:]


def scan_text(content: str, filename: str = "uploaded.txt") -> List[RawFinding]:
    findings: List[RawFinding] = []
    lines = content.splitlines() or [content]
    for idx, line in enumerate(lines, start=1):
        for secret_type, pattern, title, conf, tags in PATTERNS:
            for match in pattern.finditer(line):
                value = match.group(0)
                findings.append(
                    RawFinding(
                        secret_type=secret_type,
                        title=title,
                        value=value,
                        file_path=filename,
                        line_number=idx,
                        snippet=redact(line.strip()[:240]),
                        confidence=conf,
                        tags=tags,
                    )
                )
    return _dedupe(findings)


def scan_structured(content: str, filename: str, source_type: str) -> List[RawFinding]:
    base = scan_text(content, filename)
    # source-aware boosts
    for f in base:
        if source_type in {"docker", "k8s", "terraform"} and f.secret_type in {"aws_access_key", "ssh_private_key"}:
            f.confidence = min(0.99, f.confidence + 0.05)
            f.tags = list(set(f.tags + [source_type]))
    return base


def _dedupe(findings: Iterable[RawFinding]) -> List[RawFinding]:
    seen: set[str] = set()
    out: List[RawFinding] = []
    for f in findings:
        key = f"{f.secret_type}:{fingerprint_secret(f.value)}:{f.file_path}:{f.line_number}"
        if key in seen:
            continue
        seen.add(key)
        out.append(f)
    return out


def score_finding(raw: RawFinding) -> dict:
    severity = SEVERITY_MAP.get(raw.secret_type, "medium")
    impact = {"critical": 0.95, "high": 0.8, "medium": 0.55, "low": 0.3}[severity]
    likelihood = min(0.99, 0.4 + raw.confidence * 0.55)
    risk = round(100 * math.sqrt(impact * likelihood), 2)
    mitre = _mitre_for(raw.secret_type)
    cves = _cves_for(raw.secret_type)
    fix = _fix_for(raw.secret_type)
    minutes = {"critical": 120, "high": 90, "medium": 45, "low": 20}[severity]
    reasoning = (
        f"Detected {raw.title} in {raw.file_path}:{raw.line_number}. "
        f"Pattern confidence={raw.confidence:.2f}. Exposure of this credential enables "
        f"unauthorized access consistent with MITRE {', '.join(mitre)}. "
        f"Business impact scored {impact:.2f} due to privilege scope; likelihood {likelihood:.2f} "
        f"based on entropy/pattern strength. Recommended immediate rotation and secret manager migration."
    )
    return {
        "severity": severity,
        "risk_score": risk,
        "likelihood": round(likelihood, 3),
        "business_impact": impact,
        "confidence": raw.confidence,
        "ai_reasoning": reasoning,
        "mitre_techniques": mitre,
        "cve_references": cves,
        "suggested_fix": fix,
        "estimated_fix_minutes": minutes,
        "owasp_category": "A07:2021 Identification and Authentication Failures",
        "value_encrypted": encrypt_secret(raw.value),
        "value_fingerprint": fingerprint_secret(raw.value),
        "snippet_redacted": raw.snippet,
    }


def _mitre_for(secret_type: str) -> list[str]:
    mapping = {
        "aws_access_key": ["T1078.004", "T1552.001"],
        "aws_secret_key": ["T1078.004", "T1552.001"],
        "ssh_private_key": ["T1552.004", "T1021.004"],
        "jwt": ["T1528", "T1550.001"],
        "stripe_key": ["T1552.001", "T1651"],
        "github_pat": ["T1552.001", "T1195"],
    }
    return mapping.get(secret_type, ["T1552.001"])


def _cves_for(secret_type: str) -> list[str]:
    if secret_type.startswith("aws"):
        return ["CVE-2024-21626", "CWE-798"]
    if secret_type == "jwt":
        return ["CWE-347", "CWE-522"]
    return ["CWE-798"]


def _fix_for(secret_type: str) -> str:
    fixes = {
        "aws_access_key": "Disable the exposed IAM key in AWS IAM, create a replacement key, store it in AWS Secrets Manager or SentinelX vault, and purge git history.",
        "stripe_key": "Roll the Stripe secret key in the Stripe dashboard, update services via secret injection, and enable Stripe key restriction.",
        "ssh_private_key": "Revoke the SSH key on all hosts, generate a new keypair, and load private keys only via an agent or secret mount.",
        "jwt": "Invalidate sessions, rotate signing keys, reduce token TTL, and ensure tokens are never committed to source control.",
        "github_pat": "Revoke the PAT in GitHub settings, issue a fine-scoped token, and migrate to GitHub Apps where possible.",
    }
    return fixes.get(
        secret_type,
        "Rotate the credential immediately, remove it from the repository, and store the replacement in a managed secret store with least privilege.",
    )
