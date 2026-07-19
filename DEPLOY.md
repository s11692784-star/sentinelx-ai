# Deploy SentinelX AI (Vercel + API + GitHub)

## Architecture for production

| Layer | Platform | Notes |
|-------|----------|-------|
| Frontend | **Vercel** | Next.js App Router in `/frontend` |
| Backend API | **Render / Railway / Fly.io** | FastAPI in `/backend` |
| Database | **Neon / Supabase / Render Postgres** | `DATABASE_URL` |
| Secrets | Platform env vars | Never commit `.env` |

> Vercel hosts the UI only. The Python API must run on a Python host.

---

## 1) Push to GitHub

```bash
git clone <your-repo-url>
# or use the repo already created for you
cd sentinelx-ai
```

If starting from the archive:

```bash
tar -xzf sentinelx-ai.tar.gz
cd sentinelx-ai
git init
git add .
git commit -m "Initial SentinelX AI commit"
git branch -M main
git remote add origin https://github.com/<you>/sentinelx-ai.git
git push -u origin main
```

---

## 2) Deploy API (Render example)

1. New **Web Service** → connect GitHub repo  
2. **Root Directory:** `backend`  
3. **Build:** `pip install -r requirements.txt`  
4. **Start:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`  
5. Set env vars:

```
APP_ENV=production
DEBUG=false
DATABASE_URL=postgresql+asyncpg://...
JWT_SECRET=<openssl rand -hex 32>
AES_MASTER_KEY=<openssl rand -hex 32>
CORS_ORIGINS=https://your-app.vercel.app
FRONTEND_URL=https://your-app.vercel.app
ALLOW_DEMO_SEED=false
```

6. Note your API URL, e.g. `https://sentinelx-api.onrender.com`

Seed once (optional demo):

```bash
# from a one-off shell with same env
python scripts/seed.py
```

---

## 3) Deploy frontend on Vercel

1. [vercel.com/new](https://vercel.com/new) → import GitHub repo  
2. **Root Directory:** `frontend`  
3. Framework: Next.js (auto)  
4. Environment variable:

```
NEXT_PUBLIC_API_URL=https://sentinelx-api.onrender.com
```

5. Deploy  

CLI alternative:

```bash
cd frontend
npx vercel
# set NEXT_PUBLIC_API_URL in project settings
npx vercel --prod
```

---

## 4) Post-deploy checklist

- [ ] Open Vercel URL → Login works  
- [ ] Browser network calls hit your API host (not localhost)  
- [ ] CORS_ORIGINS includes exact Vercel domain (and `*.vercel.app` preview if needed)  
- [ ] JWT_SECRET / AES_MASTER_KEY are unique strong values  
- [ ] Production docs disabled (`/docs` returns 404)  
- [ ] Settings → Security posture shows checks  

---

## 5) Local development

```bash
./start-backend.sh   # :8000
./start-frontend.sh  # :3000
```

---

## Security defaults enabled

- AES-256-GCM secret encryption  
- JWT + refresh tokens  
- RBAC + tenant isolation (`X-Tenant-Id`)  
- Rate limiting  
- Security headers (HSTS, CSP on frontend, COOP/CORP on API)  
- Production secret validation  
- OpenAPI disabled in production  
- Hash-chained audit logs  
- Tenant security policy UI (MFA, IP allowlist, alerts, retention)  
