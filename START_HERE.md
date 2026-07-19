# Start Here

## Local

```bash
chmod +x start-backend.sh start-frontend.sh
./start-backend.sh
./start-frontend.sh
```

- UI: http://localhost:3000  
- API: http://localhost:8000/docs  
- Login: `admin@sentinelx.demo` / `DemoPass12345!`

## Vercel

Next.js is at the **repo root**. Do **not** set Root Directory to `frontend`.

Import GitHub repo → Root Directory blank → set:

```
NEXT_PUBLIC_API_URL=https://your-api-host
```

See [DEPLOY.md](./DEPLOY.md).
