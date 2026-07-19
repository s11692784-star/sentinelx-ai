#!/usr/bin/env bash
set -euo pipefail
API=${API:-http://localhost:8000/api/v1}
echo "== Signup / Login =="
curl -s -X POST "$API/auth/login" -H 'Content-Type: application/json' \
  -d '{"email":"admin@sentinelx.demo","password":"DemoPass12345!"}' | tee /tmp/sx_login.json
TOKEN=$(python3 -c "import json;print(json.load(open('/tmp/sx_login.json'))['access_token'])")
ORG=$(curl -s "$API/auth/me" -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json;print(json.load(sys.stdin)['memberships'][0]['organization_id'])")
echo "ORG=$ORG"
echo "== Scan sample =="
curl -s -X POST "$API/scans" -H "Authorization: Bearer $TOKEN" -H "X-Tenant-Id: $ORG" -H 'Content-Type: application/json' \
  -d "{\"source_type\":\"env\",\"filename\":\"demo.env\",\"content\":$(python3 -c 'import json,pathlib;print(json.dumps(pathlib.Path("sample_data/leaky_config.env").read_text()))')}" 
echo
echo "== Dashboard =="
curl -s "$API/dashboard" -H "Authorization: Bearer $TOKEN" -H "X-Tenant-Id: $ORG" | python3 -m json.tool | head -n 40
