"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { readPersistedAuth, useAuth } from "@/store/auth";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const token = useAuth((s) => s.accessToken);
  const tenantId = useAuth((s) => s.tenantId);
  const hasHydrated = useAuth((s) => s.hasHydrated);
  const setSession = useAuth((s) => s.setSession);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // Recover session if zustand rehydrate lagged behind navigation.
    if (!token) {
      const persisted = readPersistedAuth();
      if (persisted.accessToken) {
        setSession({
          accessToken: persisted.accessToken,
          refreshToken: persisted.refreshToken || "",
          tenantId: persisted.tenantId,
          email: persisted.email,
        });
        setReady(true);
        return;
      }
    }
    if (hasHydrated || token) {
      setReady(true);
    }
  }, [hasHydrated, token, setSession]);

  useEffect(() => {
    if (!ready) return;
    const effective = token || readPersistedAuth().accessToken;
    if (!effective) {
      router.replace(`/login?next=${encodeURIComponent(pathname || "/dashboard")}`);
    }
  }, [ready, token, router, pathname]);

  if (!ready || !(token || readPersistedAuth().accessToken)) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="glass glow-border px-8 py-6 text-center">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-cyan-400 border-t-transparent" />
          <p className="mt-3 text-sm text-slate-300">Loading secure console…</p>
          {!tenantId && token ? (
            <p className="mt-1 text-xs text-amber-300">Resolving tenant membership…</p>
          ) : null}
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen gap-4 p-4">
      <Sidebar />
      <main className="min-w-0 flex-1 overflow-auto">{children}</main>
    </div>
  );
}
