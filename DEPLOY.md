# Deploy SentinelX AI (Vercel + API + GitHub)

## Architecture

| Layer | Platform | Notes |
|-------|----------|-------|
| Frontend | **Vercel** | Next.js lives in **`/frontend`** |
| Backend API | **Render / Railway / Fly.io** | FastAPI in `/backend` |
| Database | **Neon / Supabase / Render Postgres** | `DATABASE_URL` |

> Vercel hosts the UI only. The Python API must run on a Python host.

---

## Fix: "No Next.js version detected"

This monorepo has **no** `package.json` with `next` at the repo root.
Next.js is only inside **`frontend/`**.

### In the Vercel dashboard (required)

1. Open your project → **Settings → General**
2. **Root Directory** → click **Edit** → set to:

```
frontend
```

3. Framework Preset: **Next.js** (auto after Root Directory is set)
4. Build Command: leave default (`next build` or `npm run build`)
5. Install Command: leave default (`npm install`)
6. Output Directory: leave **empty** (Next.js handles this)
7. Save → **Deployments → Redeploy**

### Do NOT

- Import the monorepo with Root Directory = `.` (repo root)
- Keep a root `vercel.json` that sets `"framework": "nextjs"` without a root `package.json`
- Set Output Directory to `frontend/.next` manually

### CLI (alternative)

```bash
git clone https://github.com/s11692784-star/sentinelx-ai.git
cd sentinelx-ai/frontend
npx vercel
# link project, then:
npx vercel --prod
```

When using CLI from `frontend/`, Vercel detects Next.js correctly.

---

## 1) GitHub

Repo: https://github.com/s11692784-star/sentinelx-ai

```bash
git clone https://github.com/s11692784-star/sentinelx-ai.git
cd sentinelx-ai
```

---

## 2) Deploy API (Render example)

1. New **Web Service** → connect GitHub repo  
2. **Root Directory:** `backend`  
3. **Build:** `pip install -r requirements.txt`  
4. **Start:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`  
5. Env vars:

```
APP_ENV=production
DEBUG=false
DATABASE_URL=postgresql+asyncpg://...
JWT_SECRET=<openssl rand -hex 32>
AES_MASTER_KEY=<openssl rand -hex 32>
CORS_ORIGINS=https://YOUR-APP.vercel.app
FRONTEND_URL=https://YOUR-APP.vercel.app
ALLOW_DEMO_SEED=false
```

6. API URL example: `https://sentinelx-api.onrender.com`

Optional seed (one-off shell):

```bash
python scripts/seed.py
```

Demo login after seed:

```
admin@sentinelx.demo
DemoPass12345!
```

---

## 3) Deploy frontend on Vercel

1. [vercel.com/new](https://vercel.com/new) → import `s11692784-star/sentinelx-ai`
2. **IMPORTANT — Root Directory: `frontend`**
3. Environment variable:

```
NEXT_PUBLIC_API_URL=https://sentinelx-api.onrender.com
```

(no trailing slash)

4. Deploy

### Vercel project settings checklist

| Setting | Value |
|---------|--------|
| Root Directory | `frontend` |
| Framework | Next.js |
| Build Command | `npm run build` (default) |
| Install Command | `npm install` (default) |
| Output Directory | *(blank)* |
| Node.js Version | 20.x |

---

## 4) Post-deploy checklist

- [ ] Vercel build log shows `Next.js 15.x` and succeeds
- [ ] Site loads; login page opens
- [ ] Browser Network tab calls your API host (not localhost)
- [ ] API `CORS_ORIGINS` includes exact Vercel domain
- [ ] JWT_SECRET / AES_MASTER_KEY are strong unique values
- [ ] Production `/docs` is disabled on API

---

## 5) Local development

```bash
./start-backend.sh   # :8000
./start-frontend.sh  # :3000
```

---

## Security defaults

- AES-256-GCM secret encryption  
- JWT + refresh tokens  
- RBAC + tenant isolation (`X-Tenant-Id`)  
- Rate limiting + security headers  
- Production secret validation; OpenAPI off in prod  
- Hash-chained audit logs  
- Settings UI: MFA policy, IP allowlist, alerts, password change  
