"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/Badge";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState, ErrorBanner, LoadingState } from "@/components/layout/LoadingState";
import { useTenantSession } from "@/hooks/useTenantSession";

const SAMPLE = `AWS_ACCESS_KEY_ID=AKIAEXAMPLEKEY000000
STRIPE_SECRET_KEY=sk_test_51Habcdefghijklmnopqrstuvwx
GITHUB_TOKEN=ghp_exampleexampleexampleexample000001
-----BEGIN OPENSSH PRIVATE KEY-----`;

export default function SecretsPage() {
  const { accessToken, tenantId, ready, error: sessionError } = useTenantSession();
  const [findings, setFindings] = useState<any[]>([]);
  const [content, setContent] = useState(SAMPLE);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [q, setQ] = useState("");
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<any>(null);

  const load = useCallback(async () => {
    if (!accessToken || !tenantId) return;
    setLoading(true);
    try {
      setFindings(await api.findings(accessToken, tenantId));
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load findings");
    } finally {
      setLoading(false);
    }
  }, [accessToken, tenantId]);

  useEffect(() => {
    if (ready) load();
  }, [ready, load]);

  async function runScan() {
    if (!accessToken || !tenantId) return;
    setBusy(true);
    setError("");
    try {
      await api.scan(accessToken, tenantId, {
        source_type: "env",
        filename: "manual-scan.env",
        content,
      });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Scan failed");
    } finally {
      setBusy(false);
    }
  }

  async function rotate(id: string) {
    if (!accessToken || !tenantId) return;
    try {
      await api.remediate(accessToken, tenantId, { finding_id: id, action_type: "rotate" });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Remediation failed");
    }
  }

  const rows = useMemo(() => {
    return findings.filter((f) => {
      if (filter !== "all" && f.severity !== filter) return false;
      if (!q) return true;
      const hay = `${f.title} ${f.secret_type} ${f.file_path} ${f.snippet_redacted}`.toLowerCase();
      return hay.includes(q.toLowerCase());
    });
  }, [findings, filter, q]);

  if (sessionError) return <div className="p-4"><ErrorBanner message={sessionError} /></div>;
  if (!ready) return <LoadingState label="Preparing secrets workspace…" />;

  return (
    <div className="space-y-6 p-2 md:p-4">
      <PageHeader
        title="Secret Discovery"
        subtitle="Scan repos, configs, containers, and IaC for exposed credentials"
      />

      {error ? <ErrorBanner message={error} /> : null}

      <div className="glass glow-border p-4">
        <div className="mb-2 text-xs uppercase tracking-wide text-slate-400">Scan payload</div>
        <textarea
          className="h-36 w-full rounded-xl border border-white/10 bg-black/30 p-3 font-mono text-xs outline-none focus:border-cyan-400/40"
          value={content}
          onChange={(e) => setContent(e.target.value)}
        />
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <button
            disabled={busy}
            onClick={runScan}
            className="rounded-xl bg-cyan-400 px-4 py-2 text-sm font-semibold text-ink-950 disabled:opacity-60"
          >
            {busy ? "Scanning…" : "Run AI-assisted scan"}
          </button>
          <select
            className="rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          >
            <option value="all">All severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <input
            className="min-w-[200px] flex-1 rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm"
            placeholder="Search findings…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <button onClick={load} className="rounded-xl border border-white/10 px-3 py-2 text-sm text-slate-300">
            Refresh
          </button>
        </div>
      </div>

      {loading ? (
        <LoadingState label="Loading findings…" />
      ) : rows.length === 0 ? (
        <EmptyState title="No findings yet" body="Paste a leaky config above and run a scan." />
      ) : (
        <div className="grid gap-4 xl:grid-cols-3">
          <div className="overflow-x-auto rounded-2xl border border-white/10 xl:col-span-2">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-white/5 text-xs uppercase text-slate-400">
                <tr>
                  <th className="px-4 py-3">Finding</th>
                  <th className="px-4 py-3">Location</th>
                  <th className="px-4 py-3">Risk</th>
                  <th className="px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((f) => (
                  <tr
                    key={f.id}
                    className="cursor-pointer border-t border-white/5 align-top hover:bg-white/[0.03]"
                    onClick={() => setSelected(f)}
                  >
                    <td className="px-4 py-3">
                      <div className="font-medium text-white">{f.title}</div>
                      <div className="mt-1 flex flex-wrap gap-2">
                        <Badge severity={f.severity}>{f.severity}</Badge>
                        <Badge>{f.status}</Badge>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-400">
                      {f.file_path}:{f.line_number}
                      <div className="mt-1 font-mono">{f.snippet_redacted}</div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-cyan-300">{f.risk_score}</div>
                      <div className="text-xs text-slate-500">conf {f.confidence}</div>
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          rotate(f.id);
                        }}
                        className="rounded-lg border border-cyan-400/30 px-2 py-1 text-xs text-cyan-200"
                      >
                        Rotate
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="glass glow-border p-4">
            <h2 className="text-sm font-medium text-slate-300">Finding detail</h2>
            {selected ? (
              <div className="mt-3 space-y-3 text-sm">
                <div className="text-lg font-medium text-white">{selected.title}</div>
                <div className="flex flex-wrap gap-2">
                  <Badge severity={selected.severity}>{selected.severity}</Badge>
                  <Badge>{selected.secret_type}</Badge>
                </div>
                <div className="text-xs text-slate-400">
                  MITRE: {(selected.mitre_techniques || []).join(", ") || "—"}
                </div>
                <div className="text-xs text-slate-400">
                  CVE/CWE: {(selected.cve_references || []).join(", ") || "—"}
                </div>
                <div className="rounded-xl border border-white/10 bg-black/20 p-3 text-xs text-slate-300">
                  {selected.ai_reasoning}
                </div>
                <div className="text-xs text-emerald-300">{selected.suggested_fix}</div>
                <div className="text-xs text-slate-500">
                  ETA ~{selected.estimated_fix_minutes || "?"} minutes · OWASP {selected.owasp_category}
                </div>
              </div>
            ) : (
              <p className="mt-3 text-sm text-slate-500">Select a finding to inspect AI reasoning.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
