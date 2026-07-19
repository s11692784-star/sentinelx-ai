# API Documentation

Base URL: `http://localhost:8000`  
OpenAPI: `/docs` · ReDoc: `/redoc`

## Auth
All protected routes require:
```
Authorization: Bearer <access_token>
X-Tenant-Id: <organization_uuid>   # required for tenant-scoped routes
```

### POST /api/v1/auth/signup
```json
{"email":"a@b.com","password":"longpassword1","full_name":"Ada","organization_name":"Ada Labs"}
```

### POST /api/v1/auth/login
```json
{"email":"a@b.com","password":"longpassword1","totp_code":"000000"}
```

### POST /api/v1/scans
```json
{"source_type":"env","filename":"prod.env","content":"AWS_ACCESS_KEY_ID=AKIA..."}
```

### POST /api/v1/remediation
```json
{"finding_id":"<uuid>","action_type":"rotate"}
```

### POST /api/v1/ai/chat
```json
{"message":"Summarize critical risks","gemini_api_key":"optional-byok"}
```

### POST /api/v1/compliance/reports
```json
{"framework":"SOC2"}
```
