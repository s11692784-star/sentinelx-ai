"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("admin@sentinelx.demo");
  const [otp, setOtp] = useState("");
  const [password, setPassword] = useState("");
  const [info, setInfo] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function requestOtp(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Request failed");
      setInfo(`OTP issued${data.otp_demo ? `: ${data.otp_demo}` : ""}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setBusy(false);
    }
  }

  async function reset(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, otp_code: otp, new_password: password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Reset failed");
      setInfo(data.message || "Password updated. You can sign in now.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Reset failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <div className="glass glow-border w-full max-w-md space-y-6 p-8">
        <div>
          <div className="text-xs uppercase tracking-[0.2em] text-cyan-300/80">SentinelX AI</div>
          <h1 className="mt-1 text-2xl font-semibold">Reset password</h1>
        </div>
        {error ? (
          <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-300">
            {error}
          </div>
        ) : null}
        {info ? <p className="text-sm text-emerald-300">{info}</p> : null}
        <form onSubmit={requestOtp} className="space-y-3">
          <input
            className="w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <button
            disabled={busy}
            className="w-full rounded-xl border border-cyan-400/30 py-2 text-sm text-cyan-200 disabled:opacity-60"
          >
            Send OTP
          </button>
        </form>
        <form onSubmit={reset} className="space-y-3">
          <input
            className="w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2"
            placeholder="OTP"
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
            required
          />
          <input
            type="password"
            className="w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2"
            placeholder="New password (min 10 chars)"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={10}
            required
          />
          <button
            disabled={busy}
            className="w-full rounded-xl bg-cyan-400 py-2 text-sm font-semibold text-ink-950 disabled:opacity-60"
          >
            Update password
          </button>
        </form>
        <Link href="/login" className="text-xs text-slate-400 hover:text-cyan-300">
          Back to login
        </Link>
      </div>
    </main>
  );
}
