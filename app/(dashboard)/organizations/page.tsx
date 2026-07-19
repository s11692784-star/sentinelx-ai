"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/store/auth";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState, ErrorBanner, LoadingState } from "@/components/layout/LoadingState";
import { useTenantSession } from "@/hooks/useTenantSession";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function OrganizationsPage() {
  const { accessToken, ready, error: sessionError } = useTenantSession();
  const tenantId = useAuth((s) => s.tenantId);
  const setTenant = useAuth((s) => s.setTenant);
  const [orgs, setOrgs] = useState<any[]>([]);
  const [name, setName] = useState("");
  const [inviteEmail, setInviteEmail] = useState("");
  const [role, setRole] = useState("developer");
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!accessToken) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/organizations`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (!res.ok) throw new Error("Failed to load organizations");
      const data = await res.json();
      setOrgs(data);
      if (!tenantId && data[0]?.id) setTenant(String(data[0].id));
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load organizations");
    } finally {
      setLoading(false);
    }
  }, [accessToken, tenantId, setTenant]);

  useEffect(() => {
    if (ready || accessToken) load();
  }, [ready, accessToken, load]);

  async function createOrg() {
    if (!accessToken || !name.trim()) return;
    setError("");
    const res = await fetch(`${API_URL}/api/v1/organizations`, {
      method: "POST",
      headers: { Authorization: `Bearer ${accessToken}`, "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    if (!res.ok) {
      setError((await res.json().catch(() => ({}))).detail || "Create failed");
      return;
    }
    const org = await res.json();
    setName("");
    setTenant(String(org.id));
    await load();
    setMsg(`Created ${org.name}`);
  }

  async function invite() {
    if (!accessToken || !tenantId || !inviteEmail) return;
    const res = await fetch(`${API_URL}/api/v1/organizations/${tenantId}/invitations`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
        "X-Tenant-Id": tenantId,
      },
      body: JSON.stringify({ email: inviteEmail, role }),
    });
    const data = await res.json().catch(() => ({}));
    setMsg(res.ok ? `Invited ${inviteEmail} as ${role}` : JSON.stringify(data.detail || data));
  }

  if (sessionError) return <div className="p-4"><ErrorBanner message={sessionError} /></div>;
  if (!accessToken) return <LoadingState />;

  return (
    <div className="space-y-6 p-4">
      <PageHeader
        title="Organization Management"
        subtitle="Tenant isolation · RBAC roles · member invitations"
      />
      {error ? <ErrorBanner message={error} /> : null}
      {msg ? <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-200">{msg}</div> : null}

      <div className="grid gap-4 md:grid-cols-2">
        <div className="glass glow-border space-y-3 p-4">
          <h2 className="text-sm text-slate-300">Your tenants</h2>
          {loading ? (
            <LoadingState />
          ) : orgs.length === 0 ? (
            <EmptyState title="No organizations" body="Create one to continue." />
          ) : (
            orgs.map((o) => (
              <button
                key={o.id}
                onClick={() => setTenant(String(o.id))}
                className={`flex w-full items-center justify-between rounded-xl border px-3 py-2 text-left text-sm ${
                  tenantId === o.id
                    ? "border-cyan-400/40 bg-cyan-400/10"
                    : "border-white/10 bg-black/20"
                }`}
              >
                <span>{o.name}</span>
                <span className="text-xs text-slate-500">{o.plan}</span>
              </button>
            ))
          )}
        </div>
        <div className="space-y-4">
          <div className="glass glow-border space-y-2 p-4">
            <h2 className="text-sm text-slate-300">Create organization</h2>
            <input
              className="w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Acme Corp"
            />
            <button onClick={createOrg} className="rounded-xl bg-cyan-400 px-4 py-2 text-sm font-semibold text-ink-950">
              Create
            </button>
          </div>
          <div className="glass glow-border space-y-2 p-4">
            <h2 className="text-sm text-slate-300">Invite member to active tenant</h2>
            <input
              className="w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              placeholder="analyst@company.com"
            />
            <select
              className="w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm"
              value={role}
              onChange={(e) => setRole(e.target.value)}
            >
              {["admin", "security_analyst", "developer", "auditor", "viewer"].map((r) => (
                <option key={r}>{r}</option>
              ))}
            </select>
            <button onClick={invite} className="rounded-xl border border-cyan-400/30 px-4 py-2 text-sm text-cyan-200">
              Send invite
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
