#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/backend"
python3 -m venv .venv 2>/dev/null || true
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt
export DATABASE_URL="${DATABASE_URL:-sqlite+aiosqlite:///./sentinelx.db}"
export AES_MASTER_KEY="${AES_MASTER_KEY:-DEV_ONLY_REPLACE_WITH_OPENSSL_RAND_HEX_32_BYTES_KEY_VALUE_00}"
export JWT_SECRET="${JWT_SECRET:-dev-secret-change-me}"
export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:3000,http://127.0.0.1:3000}"
export PYTHONPATH=.
python scripts/seed.py || true
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
