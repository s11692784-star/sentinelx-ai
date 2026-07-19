"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/store/auth";

/** Ensures access token + tenant id are available for tenant-scoped API calls. */
export function useTenantSession() {
  const accessToken = useAuth((s) => s.accessToken);
  const tenantId = useAuth((s) => s.tenantId);
  const setTenant = useAuth((s) => s.setTenant);
  const [resolving, setResolving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function ensure() {
      if (!accessToken) return;
      if (tenantId) {
        setError("");
        return;
      }
      setResolving(true);
      try {
        const me = await api.me(accessToken);
        const org = me?.memberships?.[0]?.organization_id;
        if (!org) {
          if (!cancelled) setError("No organization membership found for this user.");
          return;
        }
        setTenant(String(org));
        if (!cancelled) setError("");
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to resolve tenant");
      } finally {
        if (!cancelled) setResolving(false);
      }
    }
    ensure();
    return () => {
      cancelled = true;
    };
  }, [accessToken, tenantId, setTenant]);

  const ready = Boolean(accessToken && tenantId && !resolving);

  return {
    accessToken: accessToken || "",
    tenantId: tenantId || "",
    ready,
    resolving,
    error,
  };
}
