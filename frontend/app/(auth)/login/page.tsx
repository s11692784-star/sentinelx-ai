"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { readPersistedAuth, useAuth } from "@/store/auth";

function LoginForm() {
  const router = useRouter();
  const search = useSearchParams();
  const setSession = useAuth((s) => s.setSession);
  const existing = useAuth((s) => s.accessToken);
  const hasHydrated = useAuth((s) => s.hasHydrated);

  const [email, setEmail] = useState("admin@sentinelx.demo");
  const [password, setPassword] = useState("DemoPass12345!");
  const [totp, setTotp] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const nextPath = search.get("next") || "/dashboard";

  useEffect(() => {
    if (!hasHydrated) return;
    const token = existing || readPersistedAuth().accessToken;
    if (token) router.replace(nextPath);
  }, [hasHydrated, existing, router, nextPath]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const tokens = await api.login(email, password, totp || undefined);
      if (!tokens?.access_token) {
        throw new Error("Login succeeded but no access token was returned");
      }

      let tenantId: string | undefined;
      try {
        const me = await api.me(tokens.access_token);
        const org = me?.memberships?.[0]?.organization_id;
        if (org) tenantId = String(org);
      } catch {
        // still allow entry; dashboard can recover tenant later
      }

      setSession({
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token || "",
        tenantId: tenantId ?? null,
        email,
      });

      // Confirm persistence before navigation (fixes blank bounce).
      const check = readPersistedAuth();
      if (!check.accessToken) {
        localStorage.setItem(
          "sentinelx-auth",
          JSON.stringify({
            state: {
              accessToken: tokens.access_token,
              refreshToken: tokens.refresh_token || "",
              tenantId: tenantId ?? null,
              email,
            },
            version: 0,
          })
        );
      }

      router.replace(nextPath);
      // Fallback hard navigation if client router stalls
      setTimeout(() => {
        if (window.location.pathname.includes("/login")) {
          window.location.assign(nextPath);
        }
      }, 250);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <form onSubmit={onSubmit} className="glass glow-border w-full max-w-md p-8">
        <div className="mb-1 text-xs uppercase tracking-[0.2em] text-cyan-300/80">SentinelX AI</div>
        <h1 className="text-2xl font-semibold text-white">Sign in</h1>
        <p className="mt-2 text-sm text-slate-400">Multi-tenant secrets & certificate console</p>

        <label className="mt-6 block text-xs text-slate-400">Email</label>
        <input
          className="mt-1 w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 outline-none focus:border-cyan-400/50"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          autoComplete="username"
          required
        />

        <label className="mt-4 block text-xs text-slate-400">Password</label>
        <input
          type="password"
          className="mt-1 w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 outline-none focus:border-cyan-400/50"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
          required
        />

        <label className="mt-4 block text-xs text-slate-400">2FA code (optional)</label>
        <input
          className="mt-1 w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 outline-none focus:border-cyan-400/50"
          value={totp}
          onChange={(e) => setTotp(e.target.value)}
          placeholder="000000 in dev"
        />

        {error ? (
          <div className="mt-3 rounded-xl border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-300">
            {error}
          </div>
        ) : null}

        <button
          disabled={loading}
          className="mt-6 w-full rounded-xl bg-cyan-400 py-2.5 text-sm font-semibold text-ink-950 hover:bg-cyan-300 disabled:opacity-60"
        >
          {loading ? "Authenticating…" : "Continue to dashboard"}
        </button>

        <div className="mt-4 flex justify-between text-xs text-slate-400">
          <Link href="/forgot-password" className="hover:text-cyan-300">
            Forgot password
          </Link>
          <Link href="/signup" className="hover:text-cyan-300">
            Create tenant
          </Link>
        </div>

        <p className="mt-6 text-[11px] leading-relaxed text-slate-500">
          Demo: admin@sentinelx.demo / DemoPass12345! — API must be running on :8000
        </p>
      </form>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center text-slate-400">Loading…</div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
