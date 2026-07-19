"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState, ErrorBanner, LoadingState } from "@/components/layout/LoadingState";
import { useTenantSession } from "@/hooks/useTenantSession";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function RepositoriesPage() {
  const { accessToken, tenantId, ready, error: sessionError } = useTenantSession();
  const [repos, setRepos] = useState<any[]>([]);
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    name: "",
    url: "https://github.com/example/app",
    provider: "github",
    project_id: "",
  });
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    if (!accessToken || !tenantId) return;
    setLoading(true);
    try {
      const [r, p] = await Promise.all([
        api.repositories(accessToken, tenantId),
        fetch(`${API_URL}/api/v1/organizations/${tenantId}/projects`, {
          headers: { Authorization: `Bearer ${accessToken}`, "X-Tenant-Id": tenantId },
        }).then((res) => (res.ok ? res.json() : [])),
      ]);
      setRepos(r);
      setProjects(p);
      if (!form.project_id && p[0]?.id) setForm((f) => ({ ...f, project_id: p[0].id }));
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load repositories");
    } finally {
      setLoading(false);
    }
  }, [accessToken, tenantId]);

  useEffect(() => {
    if (ready) load();
  }, [ready, load]);

  async function createProject() {
    if (!accessToken || !tenantId) return;
    const res = await fetch(`${API_URL}/api/v1/organizations/${tenantId}/projects`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
        "X-Tenant-Id": tenantId,
      },
      body: JSON.stringify({ name: "Default Project", environment: "production" }),
    });
    if (!res.ok) throw new Error("Could not create project");
    const project = await res.json();
    setProjects((prev) => [...prev, project]);
    setForm((f) => ({ ...f, project_id: project.id }));
    return project.id as string;
  }

  async function addRepo() {
    if (!accessToken || !tenantId) return;
    setBusy(true);
    setError("");
    try {
      let projectId = form.project_id;
      if (!projectId) projectId = await createProject();
      const res = await fetch(`${API_URL}/api/v1/organizations/${tenantId}/repositories`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
          "X-Tenant-Id": tenantId,
        },
        body: JSON.stringify({
          project_id: projectId,
          name: form.name || "new-repo",
          provider: form.provider,
          url: form.url,
          default_branch: "main",
        }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || "Create failed");
      setForm((f) => ({ ...f, name: "" }));
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Create failed");
    } finally {
      setBusy(false);
    }
  }

  if (sessionError) return <div className="p-4"><ErrorBanner message={sessionError} /></div>;
  if (!ready) return <LoadingState label="Loading repositories…" />;

  return (
    <div className="space-y-6 p-4">
      <PageHeader
        title="Repositories & Cloud Sources"
        subtitle="GitHub, GitLab, Bitbucket and connected project inventories"
      />
      {error ? <ErrorBanner message={error} /> : null}

      <div className="glass glow-border grid gap-3 p-4 md:grid-cols-4">
        <input
          className="rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm"
          placeholder="Repository name"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
        />
        <input
          className="rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm md:col-span-2"
          placeholder="URL"
          value={form.url}
          onChange={(e) => setForm({ ...form, url: e.target.value })}
        />
        <button
          disabled={busy}
          onClick={addRepo}
          className="rounded-xl bg-cyan-400 px-4 py-2 text-sm font-semibold text-ink-950 disabled:opacity-60"
        >
          {busy ? "Adding…" : "Add repository"}
        </button>
      </div>

      {loading ? (
        <LoadingState />
      ) : repos.length === 0 ? (
        <EmptyState title="No repositories yet" body="Add a repository or run the seed script." />
      ) : (
        <div className="overflow-hidden rounded-2xl border border-white/10">
          <table className="min-w-full text-sm">
            <thead className="bg-white/5 text-xs uppercase text-slate-400">
              <tr>
                <th className="px-4 py-3 text-left">Name</th>
                <th className="px-4 py-3 text-left">Provider</th>
                <th className="px-4 py-3 text-left">URL</th>
                <th className="px-4 py-3 text-left">Risk</th>
              </tr>
            </thead>
            <tbody>
              {repos.map((r) => (
                <tr key={r.id} className="border-t border-white/5">
                  <td className="px-4 py-3 text-white">{r.name}</td>
                  <td className="px-4 py-3">{r.provider}</td>
                  <td className="px-4 py-3 text-cyan-300">{r.url}</td>
                  <td className="px-4 py-3">{r.risk_score}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
