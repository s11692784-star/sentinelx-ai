"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/Badge";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState, ErrorBanner, LoadingState } from "@/components/layout/LoadingState";
import { useTenantSession } from "@/hooks/useTenantSession";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function CertificatesPage() {
  const { accessToken, tenantId, ready, error: sessionError } = useTenantSession();
  const [certs, setCerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("all");
  const [busyId, setBusyId] = useState("");

  const load = useCallback(async () => {
    if (!accessToken || !tenantId) return;
    setLoading(true);
    try {
      setCerts(await api.certificates(accessToken, tenantId));
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load certificates");
    } finally {
      setLoading(false);
    }
  }, [accessToken, tenantId]);

  useEffect(() => {
    if (ready) load();
  }, [ready, load]);

  async function renew(id: string) {
    if (!accessToken || !tenantId) return;
    setBusyId(id);
    try {
      const res = await fetch(`${API_URL}/api/v1/certificates/${id}/renew`, {
        method: "POST",
        headers: { Authorization: `Bearer ${accessToken}`, "X-Tenant-Id": tenantId },
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || "Renew failed");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Renew failed");
    } finally {
      setBusyId("");
    }
  }

  const rows = useMemo(() => {
    return certs.filter((c) => {
      if (filter === "expiring") return c.days_remaining <= 30;
      if (filter === "critical") return c.days_remaining <= 14;
      return true;
    });
  }, [certs, filter]);

  if (sessionError) return <div className="p-4"><ErrorBanner message={sessionError} /></div>;
  if (!ready) return <LoadingState label="Loading certificate inventory…" />;

  return (
    <div className="space-y-6 p-4">
      <PageHeader
        title="Certificate Lifecycle"
        subtitle="Monitor TLS/SSL and internal certificates, predict expiry, trigger renew workflows"
        actions={
          <>
            <select
              className="rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            >
              <option value="all">All certificates</option>
              <option value="expiring">Expiring ≤30d</option>
              <option value="critical">Critical ≤14d</option>
            </select>
            <button onClick={load} className="rounded-xl border border-white/10 px-3 py-2 text-sm">
              Refresh
            </button>
          </>
        }
      />

      {error ? <ErrorBanner message={error} /> : null}

      {loading ? (
        <LoadingState />
      ) : rows.length === 0 ? (
        <EmptyState title="No certificates" body="Seed data or register certificates via API." />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {rows.map((c) => (
            <div key={c.id} className="glass glow-border p-4">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="font-medium text-white">{c.common_name}</div>
                  <div className="text-xs text-slate-500">{c.issuer}</div>
                </div>
                <Badge
                  severity={
                    c.days_remaining <= 14 ? "critical" : c.days_remaining <= 30 ? "high" : "medium"
                  }
                >
                  {c.days_remaining}d
                </Badge>
              </div>
              <div className="mt-4 grid grid-cols-2 gap-2 text-xs text-slate-400">
                <div>Type: {c.cert_type}</div>
                <div>
                  Risk: <span className="text-cyan-300">{c.risk_score}</span>
                </div>
                <div>Auto-renew: {c.auto_renew ? "yes" : "no"}</div>
                <div>Status: {c.renew_status}</div>
                <div className="col-span-2 truncate">Serial: {c.serial_number}</div>
              </div>
              <button
                disabled={busyId === c.id}
                onClick={() => renew(c.id)}
                className="mt-4 rounded-lg border border-cyan-400/30 px-3 py-1.5 text-xs text-cyan-200 disabled:opacity-50"
              >
                {busyId === c.id ? "Renewing…" : "Run renew workflow"}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
