"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/store/auth";

export default function SignupPage() {
  const router = useRouter();
  const setSession = useAuth((s) => s.setSession);
  const [form, setForm] = useState({
    email: "",
    password: "",
    full_name: "",
    organization_name: "",
  });
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setMsg("");
    setLoading(true);
    try {
      const res = await api.signup(form);
      setMsg(`Tenant ready${res.otp_demo ? ` · OTP ${res.otp_demo}` : ""}. Signing you in…`);

      const tokens = await api.login(form.email, form.password);
      let tenantId = res.organization_id ? String(res.organization_id) : undefined;
      try {
        const me = await api.me(tokens.access_token);
        tenantId = me?.memberships?.[0]?.organization_id
          ? String(me.memberships[0].organization_id)
          : tenantId;
      } catch {
        /* optional */
      }

      setSession({
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token || "",
        tenantId: tenantId ?? null,
        email: form.email,
      });
      router.replace("/dashboard");
      setTimeout(() => {
        if (window.location.pathname.includes("/signup")) window.location.assign("/dashboard");
      }, 250);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Signup failed");
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <form onSubmit={onSubmit} className="glass glow-border w-full max-w-md space-y-3 p-8">
        <div className="text-xs uppercase tracking-[0.2em] text-cyan-300/80">SentinelX AI</div>
        <h1 className="text-2xl font-semibold text-white">Create organization</h1>
        <p className="text-sm text-slate-400">Spin up a multi-tenant workspace in seconds</p>

        {(["full_name", "email", "password", "organization_name"] as const).map((k) => (
          <div key={k}>
            <label className="text-xs uppercase tracking-wide text-slate-400">
              {k.replaceAll("_", " ")}
            </label>
            <input
              type={k === "password" ? "password" : k === "email" ? "email" : "text"}
              className="mt-1 w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 outline-none focus:border-cyan-400/50"
              value={form[k]}
              onChange={(e) => setForm({ ...form, [k]: e.target.value })}
              required
              minLength={k === "password" ? 10 : 2}
            />
          </div>
        ))}

        {error ? (
          <p className="rounded-xl border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-300">
            {error}
          </p>
        ) : null}
        {msg ? <p className="text-sm text-emerald-300">{msg}</p> : null}

        <button
          disabled={loading}
          className="w-full rounded-xl bg-cyan-400 py-2.5 text-sm font-semibold text-ink-950 disabled:opacity-60"
        >
          {loading ? "Creating…" : "Create account & open console"}
        </button>
        <Link href="/login" className="block text-center text-xs text-slate-400 hover:text-cyan-300">
          Back to login
        </Link>
      </form>
    </main>
  );
}
