"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState, ErrorBanner, LoadingState } from "@/components/layout/LoadingState";
import { useTenantSession } from "@/hooks/useTenantSession";

const FRAMEWORKS = ["ISO27001", "SOC2", "PCI_DSS", "HIPAA", "GDPR"];

export default function CompliancePage() {
  const { accessToken, tenantId, ready, error: sessionError } = useTenantSession();
  const [reports, setReports] = useState<any[]>([]);
  const [framework, setFramework] = useState("SOC2");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!accessToken || !tenantId) return;
    setLoading(true);
    try {
      setReports(await api.listCompliance(accessToken, tenantId));
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load reports");
    } finally {
      setLoading(false);
    }
  }, [accessToken, tenantId]);

  useEffect(() => {
    if (ready) load();
  }, [ready, load]);

  async function generate() {
    if (!accessToken || !tenantId) return;
    setBusy(true);
    setError("");
    try {
      await api.compliance(accessToken, tenantId, framework);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Report generation failed");
    } finally {
      setBusy(false);
    }
  }

  if (sessionError) return <div className="p-4"><ErrorBanner message={sessionError} /></div>;
  if (!ready) return <LoadingState label="Loading compliance workspace…" />;

  return (
    <div className="space-y-6 p-4">
      <PageHeader
        title="Compliance Reporting"
        subtitle="Map live secret/certificate risk into framework control scores"
      />
      {error ? <ErrorBanner message={error} /> : null}

      <div className="glass glow-border flex flex-wrap items-center gap-3 p-4">
        <select
          className="rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm"
          value={framework}
          onChange={(e) => setFramework(e.target.value)}
        >
          {FRAMEWORKS.map((f) => (
            <option key={f}>{f}</option>
          ))}
        </select>
        <button
          disabled={busy}
          onClick={generate}
          className="rounded-xl bg-cyan-400 px-4 py-2 text-sm font-semibold text-ink-950 disabled:opacity-60"
        >
          {busy ? "Generating…" : "Generate report"}
        </button>
        <button onClick={load} className="rounded-xl border border-white/10 px-3 py-2 text-sm">
          Refresh
        </button>
      </div>

      {loading ? (
        <LoadingState />
      ) : reports.length === 0 ? (
        <EmptyState title="No reports yet" body="Generate a SOC2 or ISO27001 report to begin." />
      ) : (
        <div className="space-y-4">
          {reports.map((r) => (
            <div key={r.id} className="glass glow-border p-4">
              <div className="flex items-center justify-between">
                <div className="text-lg font-medium text-white">{r.framework}</div>
                <div className="text-2xl font-semibold text-cyan-300">{r.score}</div>
              </div>
              <p className="mt-2 text-sm text-slate-400">{r.summary}</p>
              <div className="mt-4 grid gap-2 md:grid-cols-2">
                {(r.controls || []).map((c: any) => (
                  <div key={c.id} className="rounded-xl border border-white/5 bg-black/20 px-3 py-2 text-xs">
                    <div className="flex justify-between gap-2">
                      <span>
                        {c.id} · {c.name}
                      </span>
                      <span className={c.status === "pass" ? "text-emerald-300" : "text-rose-300"}>
                        {c.status} {c.score}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
              {(r.gaps || []).length ? (
                <div className="mt-4 space-y-2">
                  <div className="text-xs uppercase tracking-wide text-slate-500">Gaps</div>
                  {(r.gaps || []).map((g: any, i: number) => (
                    <div key={i} className="rounded-xl border border-amber-500/20 bg-amber-500/5 px-3 py-2 text-xs text-amber-100">
                      <strong>{g.control}</strong>: {g.issue} — {g.recommendation}
                    </div>
                  ))}
                </div>
              ) : null}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
