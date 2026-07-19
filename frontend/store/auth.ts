"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

type AuthState = {
  accessToken: string | null;
  refreshToken: string | null;
  tenantId: string | null;
  email: string | null;
  hasHydrated: boolean;
  setHasHydrated: (value: boolean) => void;
  setSession: (p: {
    accessToken: string;
    refreshToken: string;
    tenantId?: string | null;
    email?: string | null;
  }) => void;
  setTenant: (id: string) => void;
  logout: () => void;
};

const STORAGE_KEY = "sentinelx-auth";

export const useAuth = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      tenantId: null,
      email: null,
      hasHydrated: false,
      setHasHydrated: (hasHydrated) => set({ hasHydrated }),
      setSession: ({ accessToken, refreshToken, tenantId, email }) =>
        set((s) => {
          const next = {
            accessToken,
            refreshToken,
            tenantId: tenantId !== undefined && tenantId !== null ? String(tenantId) : s.tenantId,
            email: email ?? s.email,
          };
          // Synchronously mirror to localStorage so hard navigations never lose the session.
          try {
            const payload = {
              state: {
                accessToken: next.accessToken,
                refreshToken: next.refreshToken,
                tenantId: next.tenantId,
                email: next.email,
              },
              version: 0,
            };
            localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
          } catch {
            /* ignore quota / private mode */
          }
          return next;
        }),
      setTenant: (tenantId) => {
        const id = String(tenantId);
        set({ tenantId: id });
        try {
          const raw = localStorage.getItem(STORAGE_KEY);
          if (raw) {
            const parsed = JSON.parse(raw);
            parsed.state = { ...(parsed.state || {}), tenantId: id };
            localStorage.setItem(STORAGE_KEY, JSON.stringify(parsed));
          }
        } catch {
          /* ignore */
        }
      },
      logout: () => {
        try {
          localStorage.removeItem(STORAGE_KEY);
        } catch {
          /* ignore */
        }
        set({ accessToken: null, refreshToken: null, tenantId: null, email: null });
      },
    }),
    {
      name: STORAGE_KEY,
      storage: createJSONStorage(() => localStorage),
      partialize: (s) => ({
        accessToken: s.accessToken,
        refreshToken: s.refreshToken,
        tenantId: s.tenantId,
        email: s.email,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
    }
  )
);

/** Read session without waiting for React — used right after login. */
export function readPersistedAuth(): {
  accessToken: string | null;
  refreshToken: string | null;
  tenantId: string | null;
  email: string | null;
} {
  if (typeof window === "undefined") {
    return { accessToken: null, refreshToken: null, tenantId: null, email: null };
  }
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { accessToken: null, refreshToken: null, tenantId: null, email: null };
    const parsed = JSON.parse(raw);
    const st = parsed.state || parsed;
    return {
      accessToken: st.accessToken ?? null,
      refreshToken: st.refreshToken ?? null,
      tenantId: st.tenantId ?? null,
      email: st.email ?? null,
    };
  } catch {
    return { accessToken: null, refreshToken: null, tenantId: null, email: null };
  }
}
