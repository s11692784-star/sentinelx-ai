"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState, ErrorBanner, LoadingState } from "@/components/layout/LoadingState";
import { useTenantSession } from "@/hooks/useTenantSession";

export default function AuditPage() {
  const { accessToken, tenantId, ready, error: sessionError } = useTenantSession();
  const [rows, setRows] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [q, setQ] = useState("");

  useEffect(() => {
    if (!ready || !accessToken || !tenantId) return;
    setLoading(true);
    api
      .auditLogs(accessToken, tenantId)
      .then(setRows)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [ready, accessToken, tenantId]);

  const filtered = useMemo(() => {
    if (!q) return rows;
    const needle = q.toLowerCase();
    return rows.filter((r) =>
      `${r.action} ${r.actor_email} ${r.resource_type} ${r.resource_id}`.toLowerCase().includes(needle)
    );
  }, [rows, q]);

  if (sessionError) return <div className="p-4"><ErrorBanner message={sessionError} /></div>;
  if (!ready) return <LoadingState label="Loading audit trail…" />;

  return (
    <div className="space-y-6 p-4">
      <PageHeader
        title="Immutable Audit Logs"
        subtitle="Hash-chained evidence trail for every security action"
        actions={
          <input
            className="rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm"
            placeholder="Filter actions…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        }
      />
      {error ? <ErrorBanner message={error} /> : null}
      {loading ? (
        <LoadingState />
      ) : filtered.length === 0 ? (
        <EmptyState title="No audit events" body="Actions like login, scan, and remediation will appear here." />
      ) : (
        <div className="space-y-2">
          {filtered.map((r) => (
            <div key={r.id} className="rounded-xl border border-white/10 bg-black/20 px-4 py-3 text-sm">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="font-medium text-white">{r.action}</div>
                <div className="text-xs text-slate-500">{r.created_at}</div>
              </div>
              <div className="mt-1 text-xs text-slate-400">
                {r.actor_email} · {r.resource_type} · {r.resource_id}
              </div>
              <div className="mt-2 font-mono text-[10px] text-slate-500">
                hash {r.integrity_hash?.slice(0, 24)}… prev {r.prev_hash?.slice(0, 16) || "genesis"}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
