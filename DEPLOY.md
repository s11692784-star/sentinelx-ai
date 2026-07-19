# Deploy SentinelX AI

## Architecture

| Layer | Platform | Path |
|-------|----------|------|
| Frontend (Next.js) | **Vercel** | repo **root** (`package.json` + `app/`) |
| Backend (FastAPI) | **Render / Railway / Fly** | `/backend` |
| Database | Neon / Supabase / Render Postgres | `DATABASE_URL` |

---

## Vercel (frontend) — fixed layout

The Next.js app is at the **repository root** (not in `/frontend`).

### Dashboard import

1. [vercel.com/new](https://vercel.com/new) → import `s11692784-star/sentinelx-ai`
2. **Root Directory:** leave **empty** / `.` (repo root)
3. Framework: **Next.js** (auto-detected from root `package.json`)
4. Build: default `next build` / `npm run build`
5. Install: default `npm install`
6. Output Directory: **leave blank**
7. Environment variable:

```
NEXT_PUBLIC_API_URL=https://YOUR-API-HOST
```

8. Deploy

### If you previously set Root Directory to `frontend`

1. Settings → General → Root Directory → **Edit** → clear it (use repo root)
2. Save → Redeploy latest `main`

### CLI

```bash
git clone https://github.com/s11692784-star/sentinelx-ai.git
cd sentinelx-ai
npx vercel
npx vercel --prod
```

---

## API (Render example)

1. Web Service → repo `s11692784-star/sentinelx-ai`
2. **Root Directory:** `backend`
3. Build: `pip install -r requirements.txt`
4. Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Env:

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

Seed (optional):

```bash
python scripts/seed.py
# admin@sentinelx.demo / DemoPass12345!
```

---

## Local

```bash
./start-backend.sh    # :8000
./start-frontend.sh   # :3000  (npm install + next dev at repo root)
```

---

## Post-deploy

- [ ] Vercel log shows Next.js 15.5.x and build success
- [ ] Login page loads
- [ ] API CORS includes Vercel domain
- [ ] Strong JWT_SECRET + AES_MASTER_KEY on API
