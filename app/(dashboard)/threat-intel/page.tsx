"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/Badge";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState, ErrorBanner, LoadingState } from "@/components/layout/LoadingState";
import { useTenantSession } from "@/hooks/useTenantSession";

export default function ThreatIntelPage() {
  const { accessToken, tenantId, ready, error: sessionError } = useTenantSession();
  const [rows, setRows] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [q, setQ] = useState("");

  useEffect(() => {
    if (!ready || !accessToken || !tenantId) return;
    setLoading(true);
    api
      .threatIntel(accessToken, tenantId)
      .then(setRows)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [ready, accessToken, tenantId]);

  const filtered = useMemo(() => {
    if (!q) return rows;
    const needle = q.toLowerCase();
    return rows.filter((r) =>
      `${r.title} ${r.description} ${r.mitre_id} ${r.cve_id} ${r.owasp}`.toLowerCase().includes(needle)
    );
  }, [rows, q]);

  if (sessionError) return <div className="p-4"><ErrorBanner message={sessionError} /></div>;
  if (!ready) return <LoadingState label="Loading threat intelligence…" />;

  return (
    <div className="space-y-6 p-4">
      <PageHeader
        title="Threat Intelligence"
        subtitle="MITRE ATT&CK · CVE/CWE · OWASP mapping · known exploits"
        actions={
          <input
            className="rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm"
            placeholder="Search intel…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        }
      />
      {error ? <ErrorBanner message={error} /> : null}
      {loading ? (
        <LoadingState />
      ) : filtered.length === 0 ? (
        <EmptyState title="No threat intel entries" />
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {filtered.map((r) => (
            <div key={r.id} className="glass glow-border p-4">
              <div className="flex items-center justify-between gap-2">
                <div className="font-medium text-white">{r.title}</div>
                <Badge severity={r.severity}>{r.severity}</Badge>
              </div>
              <p className="mt-2 text-sm text-slate-400">{r.description}</p>
              <div className="mt-3 flex flex-wrap gap-2 text-xs text-cyan-200/80">
                {r.mitre_id ? (
                  <span className="rounded-full border border-white/10 px-2 py-0.5">{r.mitre_id}</span>
                ) : null}
                {r.cve_id ? (
                  <span className="rounded-full border border-white/10 px-2 py-0.5">{r.cve_id}</span>
                ) : null}
                {r.owasp ? (
                  <span className="rounded-full border border-white/10 px-2 py-0.5">{r.owasp}</span>
                ) : null}
              </div>
              {(r.known_exploits || []).length ? (
                <div className="mt-3 text-xs text-slate-500">
                  Exploits: {(r.known_exploits || []).join(" · ")}
                </div>
              ) : null}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
