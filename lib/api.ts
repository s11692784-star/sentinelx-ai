const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Tokens = { access_token: string; refresh_token: string };

function authHeaders(token?: string, tenantId?: string): HeadersInit {
  const h: Record<string, string> = { "Content-Type": "application/json" };
  if (token) h.Authorization = `Bearer ${token}`;
  if (tenantId) h["X-Tenant-Id"] = tenantId;
  return h;
}

async function parse(res: Response) {
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail || err));
  }
  return res.json();
}

export const api = {
  signup(body: Record<string, string>) {
    return fetch(`${API_URL}/api/v1/auth/signup`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(body),
    }).then(parse);
  },
  login(email: string, password: string, totp_code?: string) {
    return fetch(`${API_URL}/api/v1/auth/login`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ email, password, totp_code }),
    }).then(parse) as Promise<Tokens & { expires_in: number }>;
  },
  me(token: string) {
    return fetch(`${API_URL}/api/v1/auth/me`, { headers: authHeaders(token) }).then(parse);
  },
  dashboard(token: string, tenantId: string) {
    return fetch(`${API_URL}/api/v1/dashboard`, { headers: authHeaders(token, tenantId) }).then(parse);
  },
  findings(token: string, tenantId: string) {
    return fetch(`${API_URL}/api/v1/findings`, { headers: authHeaders(token, tenantId) }).then(parse);
  },
  certificates(token: string, tenantId: string) {
    return fetch(`${API_URL}/api/v1/certificates`, { headers: authHeaders(token, tenantId) }).then(parse);
  },
  scan(token: string, tenantId: string, body: Record<string, unknown>) {
    return fetch(`${API_URL}/api/v1/scans`, {
      method: "POST",
      headers: authHeaders(token, tenantId),
      body: JSON.stringify(body),
    }).then(parse);
  },
  remediate(token: string, tenantId: string, body: Record<string, unknown>) {
    return fetch(`${API_URL}/api/v1/remediation`, {
      method: "POST",
      headers: authHeaders(token, tenantId),
      body: JSON.stringify(body),
    }).then(parse);
  },
  chat(token: string, tenantId: string, message: string, gemini_api_key?: string) {
    return fetch(`${API_URL}/api/v1/ai/chat`, {
      method: "POST",
      headers: authHeaders(token, tenantId),
      body: JSON.stringify({ message, gemini_api_key }),
    }).then(parse);
  },
  compliance(token: string, tenantId: string, framework: string) {
    return fetch(`${API_URL}/api/v1/compliance/reports`, {
      method: "POST",
      headers: authHeaders(token, tenantId),
      body: JSON.stringify({ framework }),
    }).then(parse);
  },
  listCompliance(token: string, tenantId: string) {
    return fetch(`${API_URL}/api/v1/compliance/reports`, { headers: authHeaders(token, tenantId) }).then(parse);
  },
  threatIntel(token: string, tenantId: string) {
    return fetch(`${API_URL}/api/v1/threat-intel`, { headers: authHeaders(token, tenantId) }).then(parse);
  },
  auditLogs(token: string, tenantId: string) {
    return fetch(`${API_URL}/api/v1/audit-logs`, { headers: authHeaders(token, tenantId) }).then(parse);
  },
  repositories(token: string, tenantId: string) {
    return fetch(`${API_URL}/api/v1/organizations/${tenantId}/repositories`, {
      headers: authHeaders(token, tenantId),
    }).then(parse);
  },
  getSecuritySettings(token: string, tenantId: string) {
    return fetch(`${API_URL}/api/v1/settings/security`, { headers: authHeaders(token, tenantId) }).then(parse);
  },
  updateSecuritySettings(token: string, tenantId: string, body: Record<string, unknown>) {
    return fetch(`${API_URL}/api/v1/settings/security`, {
      method: "PUT",
      headers: authHeaders(token, tenantId),
      body: JSON.stringify(body),
    }).then(parse);
  },
  securityPosture(token: string, tenantId: string) {
    return fetch(`${API_URL}/api/v1/settings/security-posture`, { headers: authHeaders(token, tenantId) }).then(parse);
  },
  changePassword(token: string, current_password: string, new_password: string) {
    return fetch(`${API_URL}/api/v1/settings/change-password`, {
      method: "POST",
      headers: authHeaders(token),
      body: JSON.stringify({ current_password, new_password }),
    }).then(parse);
  },
};

export { API_URL };
