"use client";

import { useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/Badge";
import { StatCard } from "@/components/ui/StatCard";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState, ErrorBanner, LoadingState } from "@/components/layout/LoadingState";
import { useTenantSession } from "@/hooks/useTenantSession";

export default function DashboardPage() {
  const { accessToken, tenantId, ready, error: sessionError } = useTenantSession();
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!ready || !accessToken || !tenantId) return;
    setLoading(true);
    api
      .dashboard(accessToken, tenantId)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [ready, accessToken, tenantId]);

  if (sessionError || error) {
    return (
      <div className="space-y-4 p-4">
        <PageHeader title="Security Command Center" />
        <ErrorBanner message={sessionError || error} />
      </div>
    );
  }

  if (!ready || loading || !data) {
    return <LoadingState label="Loading security posture…" />;
  }

  const sevData = Object.entries(data.severity_breakdown || {}).map(([name, value]) => ({
    name,
    value,
  }));

  return (
    <div className="space-y-6 p-2 md:p-4">
      <PageHeader
        title="Security Command Center"
        subtitle="Live multi-tenant posture, risk heatmap, and attack graph"
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <StatCard label="Security Score" value={data.security_score} hint="Higher is better" />
        <StatCard label="Open Findings" value={data.open_findings} />
        <StatCard label="Critical" value={data.critical_findings} />
        <StatCard label="Expiring Certs" value={data.expiring_certificates} hint="≤ 30 days" />
        <StatCard label="Repositories" value={data.repositories} />
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <div className="glass glow-border p-4 xl:col-span-2">
          <h2 className="mb-4 text-sm font-medium text-slate-300">Open findings trend</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.trend || []}>
                <defs>
                  <linearGradient id="c" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#22d3ee" stopOpacity={0.5} />
                    <stop offset="100%" stopColor="#22d3ee" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="date" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
                <Tooltip contentStyle={{ background: "#0b1220", border: "1px solid #1f2937" }} />
                <Area type="monotone" dataKey="open_findings" stroke="#22d3ee" fill="url(#c)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="glass glow-border p-4">
          <h2 className="mb-4 text-sm font-medium text-slate-300">Severity breakdown</h2>
          <div className="h-64">
            {sevData.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={sevData}>
                  <CartesianGrid stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                  <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: "#0b1220", border: "1px solid #1f2937" }} />
                  <Bar dataKey="value" fill="#818cf8" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState title="No open findings" body="Run a scan to populate severity data." />
            )}
          </div>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="glass glow-border p-4">
          <h2 className="mb-3 text-sm font-medium text-slate-300">Risk heatmap</h2>
          <div className="space-y-2">
            {(data.risk_heatmap || []).length ? (
              (data.risk_heatmap || []).map((r: any) => (
                <div
                  key={r.id}
                  className="flex items-center justify-between rounded-xl border border-white/5 bg-black/20 px-3 py-2 text-sm"
                >
                  <div>
                    <div className="font-medium text-white">{r.type}</div>
                    <div className="text-xs text-slate-500">{r.file}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge severity={r.severity}>{r.severity}</Badge>
                    <span className="text-cyan-300">{r.risk}</span>
                  </div>
                </div>
              ))
            ) : (
              <EmptyState title="Heatmap empty" body="No scored findings yet." />
            )}
          </div>
        </div>
        <div className="glass glow-border p-4">
          <h2 className="mb-3 text-sm font-medium text-slate-300">Attack graph</h2>
          <div className="flex flex-wrap gap-2">
            {(data.attack_graph?.nodes || []).map((n: any) => (
              <div
                key={n.id}
                className="rounded-xl border border-cyan-400/20 bg-cyan-400/5 px-3 py-2 text-xs text-cyan-100"
              >
                {n.label}
                {n.severity ? <span className="ml-2 text-rose-300">{n.severity}</span> : null}
              </div>
            ))}
          </div>
          <div className="mt-4 space-y-1 text-xs text-slate-500">
            {(data.attack_graph?.edges || []).slice(0, 12).map((e: any, i: number) => (
              <div key={i}>
                {e.source} → {e.target}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="glass glow-border p-4">
        <h2 className="mb-3 text-sm font-medium text-slate-300">Recent alerts</h2>
        <div className="grid gap-2 md:grid-cols-2">
          {(data.recent_alerts || []).length ? (
            (data.recent_alerts || []).map((a: any) => (
              <div key={a.id} className="rounded-xl border border-white/5 bg-black/20 p-3">
                <div className="flex items-center justify-between gap-2">
                  <div className="font-medium text-white">{a.title}</div>
                  <Badge severity={a.severity}>{a.severity}</Badge>
                </div>
                <p className="mt-1 line-clamp-2 text-xs text-slate-400">{a.body}</p>
              </div>
            ))
          ) : (
            <EmptyState title="No alerts" body="Critical findings will appear here." />
          )}
        </div>
      </div>
    </div>
  );
}
