# Database Schema

PostgreSQL 16 with UUID PKs and JSONB metadata.

## Core tables
- `users`, `refresh_tokens`, `otp_challenges`
- `organizations`, `memberships`, `invitations`
- `projects`, `repositories`, `cloud_accounts`
- `scan_jobs`, `secret_findings`
- `certificates`, `remediation_actions`
- `audit_logs`, `notifications`
- `compliance_reports`, `threat_intel`, `ai_conversations`

## secret_findings (critical fields)
- `value_encrypted` — AES-GCM blob
- `value_fingerprint` — SHA-256 for dedupe (not reversible)
- `risk_score`, `likelihood`, `business_impact`, `confidence`
- `ai_reasoning`, `mitre_techniques`, `cve_references`, `suggested_fix`

## audit_logs integrity
```
integrity_hash = SHA256(json({action, resource, org, actor, details, prev_hash}))
```
