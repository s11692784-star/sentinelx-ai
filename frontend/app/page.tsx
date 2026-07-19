import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen px-6 py-16 md:px-12">
      <div className="mx-auto max-w-6xl">
        <div className="inline-flex items-center gap-2 rounded-full border border-cyan-400/30 bg-cyan-400/10 px-3 py-1 text-xs text-cyan-200">
          Enterprise DevSecOps · Multi-Tenant · Explainable AI
        </div>
        <h1 className="mt-6 max-w-3xl text-4xl font-semibold tracking-tight text-white md:text-6xl">
          SentinelX AI
          <span className="block bg-gradient-to-r from-cyan-300 to-indigo-300 bg-clip-text text-transparent">
            Secrets & Certificate Command Center
          </span>
        </h1>
        <p className="mt-6 max-w-2xl text-lg text-slate-300">
          Discover exposed credentials, score business risk with explainable AI, rotate secrets,
          monitor TLS expiry, and prove compliance — across every tenant, repo, and cloud.
        </p>
        <div className="mt-10 flex flex-wrap gap-4">
          <Link
            href="/login"
            className="rounded-xl bg-cyan-400 px-5 py-3 text-sm font-semibold text-ink-950 hover:bg-cyan-300"
          >
            Open Console
          </Link>
          <Link
            href="/signup"
            className="rounded-xl border border-white/15 bg-white/5 px-5 py-3 text-sm font-semibold text-white hover:bg-white/10"
          >
            Start Free Tenant
          </Link>
          <Link
            href="/dashboard"
            className="rounded-xl border border-cyan-400/20 px-5 py-3 text-sm font-semibold text-cyan-100 hover:bg-cyan-400/10"
          >
            Go to Dashboard
          </Link>
        </div>
        <div className="mt-16 grid gap-4 md:grid-cols-3">
          {[
            ["Secret Discovery", "GitHub, GitLab, Docker, Terraform, K8s, .env, logs"],
            ["Certificate Lifecycle", "Expiry prediction, renew workflows, alerting"],
            ["AI Risk Engine", "MITRE mapping, fix plans, compliance evidence"],
          ].map(([t, d]) => (
            <div key={t} className="glass glow-border p-5">
              <h3 className="text-base font-semibold text-white">{t}</h3>
              <p className="mt-2 text-sm text-slate-400">{d}</p>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
