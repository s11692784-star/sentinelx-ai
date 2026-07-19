# SentinelX AI — Architecture

## Design principles
1. **Tenant-first isolation** — every sensitive query filters by `organization_id`.
2. **Secrets never plaintext** — AES-256-GCM before persistence; API returns redactions only.
3. **Explainable AI** — every risk decision carries reasoning, MITRE, and fix guidance.
4. **Immutable evidence** — audit log hash chain for compliance export.
5. **Async-ready** — Celery workers for certificate sweeps and future deep scans.

## Logical components
- **Edge UI** — Next.js 14 dark glassmorphism console
- **API gateway** — FastAPI, JWT, rate limit, CORS, security headers
- **Domain services** — discovery, certificates, remediation, compliance, AI
- **Data plane** — PostgreSQL 16 (JSONB for flexible intel/control payloads)
- **Control plane jobs** — Redis + Celery beat

## Data flow (secret scan)
1. Client submits content or upload with `X-Tenant-Id`
2. `ScanJob` created (`running`)
3. Pattern engine extracts candidates (entropy/pattern confidence)
4. Risk scorer computes impact × likelihood; AI enriches reasoning
5. Findings stored encrypted; high severity creates notifications
6. Audit event appended with integrity hash
7. Dashboard aggregates heatmap + attack graph

## Multi-tenancy
- Organizations own projects, repos, findings, certificates, reports
- Memberships bind users with RBAC role
- Optional ABAC JSON attributes on membership

## Threat model (summary)
| Threat | Control |
|--------|---------|
| Secret exfil via DB dump | AES-GCM at rest, key outside DB |
| Cross-tenant read | org_id filters + membership checks |
| Token theft | short access TTL + refresh rotation |
| Audit tampering | hash chain (`prev_hash` + payload hash) |
| Injection | SQLAlchemy binds, Pydantic validation |
