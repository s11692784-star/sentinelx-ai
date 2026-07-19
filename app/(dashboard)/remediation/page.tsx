"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState, ErrorBanner, LoadingState } from "@/components/layout/LoadingState";
import { useTenantSession } from "@/hooks/useTenantSession";
import { Badge } from "@/components/ui/Badge";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function RemediationPage() {
  const { accessToken, tenantId, ready, error: sessionError } = useTenantSession();
  const [findings, setFindings] = useState<any[]>([]);
  const [actions, setActions] = useState<any[]>([]);
  const [selected, setSelected] = useState("");
  const [type, setType] = useState("pr");
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    if (!accessToken || !tenantId) return;
    setLoading(true);
    try {
      const [f, a] = await Promise.all([
        api.findings(accessToken, tenantId),
        fetch(`${API_URL}/api/v1/remediation`, {
          headers: { Authorization: `Bearer ${accessToken}`, "X-Tenant-Id": tenantId },
        }).then(async (r) => (r.ok ? r.json() : [])),
      ]);
      setFindings(f);
      setActions(a);
      if (!selected && f[0]?.id) setSelected(f[0].id);
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load remediation data");
    } finally {
      setLoading(false);
    }
  }, [accessToken, tenantId, selected]);

  useEffect(() => {
    if (ready) load();
  }, [ready, load]);

  async function run() {
    if (!accessToken || !tenantId || !selected) return;
    setBusy(true);
    setError("");
    try {
      const res = await api.remediate(accessToken, tenantId, {
        finding_id: selected,
        action_type: type,
      });
      setResult(res);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Remediation failed");
    } finally {
      setBusy(false);
    }
  }

  if (sessionError) return <div className="p-4"><ErrorBanner message={sessionError} /></div>;
  if (!ready) return <LoadingState label="Loading remediation workspace…" />;

  return (
    <div className="space-y-6 p-4">
      <PageHeader
        title="Auto Remediation"
        subtitle="Rotate secrets, open PRs, update K8s/Docker/Terraform, notify Slack"
      />
      {error ? <ErrorBanner message={error} /> : null}

      <div className="glass glow-border grid gap-4 p-4 md:grid-cols-3">
        <select
          className="rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm"
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
        >
          <option value="">Select finding</option>
          {findings.map((f) => (
            <option key={f.id} value={f.id}>
              {f.title} ({f.severity})
            </option>
          ))}
        </select>
        <select
          className="rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm"
          value={type}
          onChange={(e) => setType(e.target.value)}
        >
          {["rotate", "pr", "k8s", "docker", "terraform", "slack"].map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        <button
          disabled={busy || !selected}
          onClick={run}
          className="rounded-xl bg-cyan-400 px-4 py-2 text-sm font-semibold text-ink-950 disabled:opacity-60"
        >
          {busy ? "Executing…" : "Execute"}
        </button>
      </div>

      {result ? (
        <pre className="glass overflow-auto p-4 text-xs text-emerald-200">
          {JSON.stringify(result, null, 2)}
        </pre>
      ) : null}

      {loading ? (
        <LoadingState />
      ) : actions.length === 0 ? (
        <EmptyState title="No remediation actions yet" body="Execute an action above to populate history." />
      ) : (
        <div className="space-y-2">
          <h2 className="text-sm text-slate-400">Recent actions</h2>
          {actions.map((a) => (
            <div key={a.id} className="rounded-xl border border-white/10 bg-black/20 px-4 py-3 text-sm">
              <div className="flex flex-wrap items-center gap-2">
                <div className="font-medium text-white">{a.action_type}</div>
                <Badge>{a.status}</Badge>
              </div>
              <pre className="mt-2 overflow-auto text-xs text-slate-400">
                {JSON.stringify(a.result, null, 2)}
              </pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
