from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from app.core.config import settings


SYSTEM_PROMPT = """You are SentinelX AI, an enterprise security copilot specializing in secrets management,
certificate lifecycle, threat intelligence, and compliance (ISO27001, SOC2, PCI DSS, HIPAA, GDPR).
Always explain your reasoning clearly. Prefer actionable remediation steps. Never request or echo full secret values.
"""


class GeminiClient:
    """Gemini BYOK client with deterministic offline fallback for demos without a key."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = (api_key or settings.gemini_api_key or "").strip()

    def available(self) -> bool:
        return bool(self.api_key)

    def generate(self, prompt: str, context: Optional[str] = None) -> Dict[str, Any]:
        if self.api_key:
            try:
                return self._call_gemini(prompt, context)
            except Exception as exc:  # noqa: BLE001
                offline = self._offline(prompt, context)
                offline["reasoning"] += f" (Gemini error fallback: {exc})"
                return offline
        return self._offline(prompt, context)

    def _call_gemini(self, prompt: str, context: Optional[str]) -> Dict[str, Any]:
        import google.generativeai as genai

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        full = f"{SYSTEM_PROMPT}\n\nContext:\n{context or 'None'}\n\nUser:\n{prompt}\n\nRespond with JSON keys: reply, reasoning, citations (array)."
        response = model.generate_content(full)
        text = response.text or ""
        parsed = _extract_json(text)
        if parsed:
            return {
                "reply": parsed.get("reply") or text,
                "reasoning": parsed.get("reasoning") or "Model provided structured answer.",
                "citations": parsed.get("citations") or [],
            }
        return {
            "reply": text,
            "reasoning": "Gemini returned free-form text; structured fields inferred by SentinelX.",
            "citations": ["gemini-1.5-flash"],
        }

    def _offline(self, prompt: str, context: Optional[str]) -> Dict[str, Any]:
        lower = prompt.lower()
        if "certificate" in lower or "tls" in lower or "ssl" in lower:
            reply = (
                "Certificate risk is driven by remaining validity, key algorithm strength, and public exposure. "
                "Renew certificates under 30 days remaining, enforce auto-renew workflows, and monitor SAN drift."
            )
            reasoning = (
                "Matched certificate lifecycle intent. Applied industry baselines: 30/14/7 day alert thresholds, "
                "prefer ECDSA/RSA-2048+, require CT log visibility for public certs."
            )
        elif "compliance" in lower or "soc2" in lower or "iso" in lower or "gdpr" in lower:
            reply = (
                "Map open secret findings to control failures (access control, crypto, logging). "
                "Generate evidence packs from immutable audit logs and rotation history for auditors."
            )
            reasoning = (
                "Compliance frameworks share control families around secret storage (A.8/CC6), encryption (A.10/CC6.1), "
                "and monitoring (A.12/CC7). SentinelX correlates findings to those families."
            )
        elif "rotate" in lower or "remediat" in lower:
            reply = (
                "Recommended remediation: 1) revoke exposed credential, 2) issue replacement via manager, "
                "3) open PR replacing hardcoded values with references, 4) verify pipelines, 5) close finding."
            )
            reasoning = (
                "Remediation order minimizes dwell time of attacker-usable secrets while preserving service availability "
                "through dual-running old/new secrets when providers support it."
            )
        else:
            reply = (
                "I can explain findings, prioritize risk, draft remediation PRs, summarize certificate posture, "
                "and produce compliance narratives. Provide a finding ID, repo, or framework name for deeper analysis."
            )
            reasoning = (
                "General security-assistant pathway. No specialized intent keyword dominated classification; "
                "returned capability overview grounded in SentinelX modules."
            )
        if context:
            reply += f"\n\nContext considered: {context[:500]}"
        return {
            "reply": reply,
            "reasoning": reasoning + " Offline explainable engine used because no Gemini API key was provided (BYOK).",
            "citations": ["sentinelx-risk-model-v1", "mitre-attack", "owasp-asvs-4.0"],
        }

    def enrich_finding(self, finding: dict) -> dict:
        prompt = (
            f"Enrich secret finding type={finding.get('secret_type')} severity={finding.get('severity')} "
            f"file={finding.get('file_path')}. Provide business impact narrative and fix plan."
        )
        result = self.generate(prompt, context=json.dumps(finding)[:2000])
        finding = dict(finding)
        finding["ai_reasoning"] = result["reasoning"] + " | " + result["reply"]
        return finding


def _extract_json(text: str) -> Optional[dict]:
    fence = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    raw = fence.group(1) if fence else None
    if not raw:
        brace = re.search(r"\{.*\}", text, re.DOTALL)
        raw = brace.group(0) if brace else None
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None
