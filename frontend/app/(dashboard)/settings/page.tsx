"use client";

import { useEffect, useState } from "react";
import { api, API_URL } from "@/lib/api";
import { useAuth } from "@/store/auth";
import { PageHeader } from "@/components/layout/PageHeader";
import { ErrorBanner, LoadingState } from "@/components/layout/LoadingState";
import { useTenantSession } from "@/hooks/useTenantSession";
import { Badge } from "@/components/ui/Badge";

type SecuritySettings = {
  mfa_required: boolean;
  session_timeout_minutes: number;
  password_min_length: number;
  allow_api_keys: boolean;
  ip_allowlist_enabled: boolean;
  ip_allowlist: string[];
  notify_on_critical: boolean;
  notify_on_cert_expiry: boolean;
  cert_expiry_days: number;
  audit_retention_days: number;
  gemini_byok_enabled: boolean;
};

const defaultSettings: SecuritySettings = {
  mfa_required: false,
  session_timeout_minutes: 30,
  password_min_length: 10,
  allow_api_keys: true,
  ip_allowlist_enabled: false,
  ip_allowlist: [],
  notify_on_critical: true,
  notify_on_cert_expiry: true,
  cert_expiry_days: 30,
  audit_retention_days: 365,
  gemini_byok_enabled: true,
};

export default function SettingsPage() {
  const { accessToken, tenantId, ready, error: sessionError } = useTenantSession();
  const email = useAuth((s) => s.email);
  const [settings, setSettings] = useState<SecuritySettings>(defaultSettings);
  const [ipText, setIpText] = useState("");
  const [posture, setPosture] = useState<any>(null);
  const [secret, setSecret] = useState("");
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [pwd, setPwd] = useState({ current: "", next: "", confirm: "" });

  useEffect(() => {
    if (!ready || !accessToken || !tenantId) return;
    setLoading(true);
    Promise.all([
      api.getSecuritySettings(accessToken, tenantId),
      api.securityPosture(accessToken, tenantId),
    ])
      .then(([s, p]) => {
        setSettings({ ...defaultSettings, ...s });
        setIpText((s.ip_allowlist || []).join("\n"));
        setPosture(p);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [ready, accessToken, tenantId]);

  async function saveSettings() {
    if (!accessToken || !tenantId) return;
    setBusy(true);
    setError("");
    try {
      const body = {
        ...settings,
        ip_allowlist: ipText
          .split(/[\n,]/)
          .map((s) => s.trim())
          .filter(Boolean),
      };
      const saved = await api.updateSecuritySettings(accessToken, tenantId, body);
      setSettings({ ...defaultSettings, ...saved });
      setPosture(await api.securityPosture(accessToken, tenantId));
      setMsg("Security settings saved");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setBusy(false);
    }
  }

  async function enable2fa() {
    if (!accessToken) return;
    setBusy(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/2fa/enable`, {
        method: "POST",
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to enable 2FA");
      setSecret(data.totp_secret || "");
      setMsg(data.message || "2FA enabled");
      if (tenantId) setPosture(await api.securityPosture(accessToken, tenantId));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  async function changePassword() {
    if (!accessToken) return;
    if (pwd.next !== pwd.confirm) {
      setError("New passwords do not match");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await api.changePassword(accessToken, pwd.current, pwd.next);
      setMsg("Password changed");
      setPwd({ current: "", next: "", confirm: "" });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Password change failed");
    } finally {
      setBusy(false);
    }
  }

  if (sessionError) return <div className="p-4"><ErrorBanner message={sessionError} /></div>;
  if (!ready || loading) return <LoadingState label="Loading security settings…" />;

  return (
    <div className="space-y-6 p-4">
      <PageHeader title="Settings & Security" subtitle="Account, tenant policies, alerts, and posture" />
      {error ? <ErrorBanner message={error} /> : null}
      {msg ? (
        <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-200">
          {msg}
        </div>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="glass glow-border space-y-3 p-4">
          <div className="text-sm text-slate-400">Signed in as</div>
          <div className="text-white">{email || "—"}</div>
          <div className="text-xs text-slate-500">Active tenant</div>
          <div className="break-all font-mono text-xs text-cyan-200">{tenantId}</div>
          <div className="text-xs text-slate-500">API endpoint</div>
          <div className="break-all font-mono text-xs text-slate-300">{API_URL}</div>
        </div>

        <div className="glass glow-border space-y-3 p-4 lg:col-span-2">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-medium text-white">Security posture</h2>
            <div className="text-2xl font-semibold text-cyan-300">{posture?.score ?? "—"}</div>
          </div>
          <div className="grid gap-2 md:grid-cols-2">
            {(posture?.checks || []).map((c: any) => (
              <div key={c.id} className="flex items-center justify-between rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-xs">
                <span className="text-slate-300">{c.label}</span>
                <Badge severity={c.ok ? "medium" : "critical"}>{c.ok ? "pass" : "gap"}</Badge>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="glass glow-border space-y-4 p-4">
          <h2 className="text-sm font-medium text-white">Tenant security policy</h2>

          {([
            ["mfa_required", "Require MFA for all members"],
            ["allow_api_keys", "Allow personal API keys"],
            ["ip_allowlist_enabled", "Enable IP allowlist"],
            ["notify_on_critical", "Alert on critical findings"],
            ["notify_on_cert_expiry", "Alert on certificate expiry"],
            ["gemini_byok_enabled", "Allow Gemini BYOK in AI assistant"],
          ] as const).map(([key, label]) => (
            <label key={key} className="flex items-center justify-between gap-3 text-sm text-slate-300">
              <span>{label}</span>
              <input
                type="checkbox"
                checked={Boolean((settings as any)[key])}
                onChange={(e) => setSettings({ ...settings, [key]: e.target.checked })}
                className="h-4 w-4 accent-cyan-400"
              />
            </label>
          ))}

          <div className="grid gap-3 sm:grid-cols-2">
            <label className="text-xs text-slate-400">
              Session timeout (min)
              <input
                type="number"
                className="mt-1 w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
                value={settings.session_timeout_minutes}
                onChange={(e) => setSettings({ ...settings, session_timeout_minutes: Number(e.target.value) })}
              />
            </label>
            <label className="text-xs text-slate-400">
              Password min length
              <input
                type="number"
                className="mt-1 w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
                value={settings.password_min_length}
                onChange={(e) => setSettings({ ...settings, password_min_length: Number(e.target.value) })}
              />
            </label>
            <label className="text-xs text-slate-400">
              Cert alert window (days)
              <input
                type="number"
                className="mt-1 w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
                value={settings.cert_expiry_days}
                onChange={(e) => setSettings({ ...settings, cert_expiry_days: Number(e.target.value) })}
              />
            </label>
            <label className="text-xs text-slate-400">
              Audit retention (days)
              <input
                type="number"
                className="mt-1 w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
                value={settings.audit_retention_days}
                onChange={(e) => setSettings({ ...settings, audit_retention_days: Number(e.target.value) })}
              />
            </label>
          </div>

          <label className="block text-xs text-slate-400">
            IP allowlist (one per line)
            <textarea
              className="mt-1 h-24 w-full rounded-xl border border-white/10 bg-black/30 p-3 font-mono text-xs text-white"
              value={ipText}
              onChange={(e) => setIpText(e.target.value)}
              placeholder="203.0.113.10"
            />
          </label>

          <button
            disabled={busy}
            onClick={saveSettings}
            className="rounded-xl bg-cyan-400 px-4 py-2 text-sm font-semibold text-ink-950 disabled:opacity-60"
          >
            {busy ? "Saving…" : "Save security settings"}
          </button>
        </div>

        <div className="space-y-4">
          <div className="glass glow-border space-y-3 p-4">
            <h2 className="text-sm font-medium text-white">Two-factor authentication</h2>
            <p className="text-xs text-slate-400">
              Enable TOTP-backed 2FA. In development, login accepts code <code>000000</code>.
            </p>
            <button
              disabled={busy || !accessToken}
              onClick={enable2fa}
              className="rounded-xl border border-cyan-400/30 px-4 py-2 text-sm text-cyan-200 disabled:opacity-60"
            >
              Enable 2FA
            </button>
            {secret ? (
              <div className="rounded-xl border border-white/10 bg-black/30 p-3 font-mono text-xs">
                TOTP secret: {secret}
              </div>
            ) : null}
          </div>

          <div className="glass glow-border space-y-3 p-4">
            <h2 className="text-sm font-medium text-white">Change password</h2>
            <input
              type="password"
              placeholder="Current password"
              className="w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm"
              value={pwd.current}
              onChange={(e) => setPwd({ ...pwd, current: e.target.value })}
            />
            <input
              type="password"
              placeholder="New password"
              className="w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm"
              value={pwd.next}
              onChange={(e) => setPwd({ ...pwd, next: e.target.value })}
            />
            <input
              type="password"
              placeholder="Confirm new password"
              className="w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm"
              value={pwd.confirm}
              onChange={(e) => setPwd({ ...pwd, confirm: e.target.value })}
            />
            <button
              disabled={busy}
              onClick={changePassword}
              className="rounded-xl bg-cyan-400 px-4 py-2 text-sm font-semibold text-ink-950 disabled:opacity-60"
            >
              Update password
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
