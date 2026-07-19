"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAuth } from "@/store/auth";

const links = [
  ["Dashboard", "/dashboard"],
  ["Secrets", "/secrets"],
  ["Certificates", "/certificates"],
  ["Repositories", "/repositories"],
  ["Remediation", "/remediation"],
  ["AI Assistant", "/ai-assistant"],
  ["Threat Intel", "/threat-intel"],
  ["Compliance", "/compliance"],
  ["Audit Logs", "/audit"],
  ["Organizations", "/organizations"],
  ["Settings", "/settings"],
];

export function Sidebar() {
  const pathname = usePathname();
  const logout = useAuth((s) => s.logout);
  const email = useAuth((s) => s.email);
  const tenantId = useAuth((s) => s.tenantId);

  return (
    <aside className="glass glow-border sticky top-4 flex h-[calc(100vh-2rem)] w-64 shrink-0 flex-col p-4">
      <div className="mb-6 px-2">
        <div className="text-xs uppercase tracking-[0.2em] text-cyan-300/80">SentinelX</div>
        <div className="text-lg font-semibold text-white">Security OS</div>
        <div className="mt-2 truncate text-[11px] text-slate-500">{email || "signed in"}</div>
        {tenantId ? (
          <div className="truncate font-mono text-[10px] text-slate-600">tenant {tenantId.slice(0, 8)}…</div>
        ) : null}
      </div>
      <nav className="flex flex-1 flex-col gap-1 overflow-y-auto">
        {links.map(([label, href]) => {
          const active = pathname === href || pathname?.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "rounded-xl px-3 py-2 text-sm text-slate-300 transition hover:bg-white/5 hover:text-white",
                active && "border border-cyan-400/20 bg-cyan-400/10 text-cyan-200"
              )}
            >
              {label}
            </Link>
          );
        })}
      </nav>
      <button
        onClick={() => {
          logout();
          window.location.href = "/login";
        }}
        className="mt-4 rounded-xl border border-white/10 px-3 py-2 text-left text-sm text-slate-400 hover:text-white"
      >
        Sign out
      </button>
    </aside>
  );
}
