# SentinelX AI

**Enterprise Multi-Tenant Secrets & Certificate Lifecycle Platform**

Hackathon-ready commercial SaaS foundation for discovering, classifying, rotating, and governing secrets & certificates with explainable AI.

[![CI](https://img.shields.io/badge/CI-GitHub%20Actions-black)](#)
[![Frontend](https://img.shields.io/badge/Frontend-Vercel%20ready-black)](./DEPLOY.md)
[![API](https://img.shields.io/badge/API-FastAPI-009688)](./backend)

## Quick links

- **Deploy guide:** [DEPLOY.md](./DEPLOY.md)
- **Local start:** [START_HERE.md](./START_HERE.md)
- **Architecture:** [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)
- **API notes:** [docs/API.md](./docs/API.md)

## Stack

- **Frontend:** Next.js 14 · TypeScript · Tailwind · Recharts · Zustand → **Vercel**
- **Backend:** FastAPI · SQLAlchemy · PostgreSQL/SQLite · JWT · AES-GCM → **Render/Railway**
- **AI:** Gemini BYOK + explainable offline engine

## Features

1. Authentication (OTP, 2FA, JWT, RBAC)  
2. Multi-tenant organizations  
3. Secret discovery engine  
4. Certificate lifecycle  
5. AI risk scoring (MITRE / CVE / fix ETA)  
6. AI security assistant  
7. Auto remediation  
8. Threat intelligence  
9. Compliance reports (ISO/SOC2/PCI/HIPAA/GDPR)  
10. Command-center dashboard  
11. **Security settings & posture** (MFA policy, IP allowlist, alerts, password change)

## Local demo

```bash
chmod +x start-backend.sh start-frontend.sh
./start-backend.sh    # http://localhost:8000
./start-frontend.sh   # http://localhost:3000
```

Login: `admin@sentinelx.demo` / `DemoPass12345!`

## Production deploy (summary)

1. Push this repo to GitHub  
2. Deploy `/backend` to Render/Railway with Postgres + secrets  
3. Deploy `/frontend` to Vercel with `NEXT_PUBLIC_API_URL`  
4. Set API `CORS_ORIGINS` to your Vercel domain  

Full steps: **[DEPLOY.md](./DEPLOY.md)**

## Security

- Secrets encrypted with AES-256-GCM (never plaintext at rest)
- JWT access + rotating refresh tokens
- RBAC roles + tenant header isolation
- Rate limiting, security headers, CSP (frontend)
- Production secret validation; OpenAPI disabled in prod
- Immutable hash-chained audit logs

## License

MIT — see [LICENSE](./LICENSE)
