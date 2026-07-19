"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/layout/PageHeader";
import { ErrorBanner, LoadingState } from "@/components/layout/LoadingState";
import { useTenantSession } from "@/hooks/useTenantSession";

export default function AIAssistantPage() {
  const { accessToken, tenantId, ready, error: sessionError } = useTenantSession();
  const [message, setMessage] = useState(
    "Explain our top certificate risks and how to remediate them for SOC2."
  );
  const [geminiKey, setGeminiKey] = useState("");
  const [messages, setMessages] = useState<
    { role: string; content: string; reasoning?: string; citations?: string[] }[]
  >([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function send() {
    if (!accessToken || !tenantId || !message.trim()) return;
    setBusy(true);
    setError("");
    const userMsg = message;
    setMessages((m) => [...m, { role: "user", content: userMsg }]);
    setMessage("");
    try {
      const res = await api.chat(accessToken, tenantId, userMsg, geminiKey || undefined);
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: res.reply,
          reasoning: res.reasoning,
          citations: res.citations,
        },
      ]);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Error";
      setError(msg);
      setMessages((m) => [...m, { role: "assistant", content: msg }]);
    } finally {
      setBusy(false);
    }
  }

  if (sessionError) return <div className="p-4"><ErrorBanner message={sessionError} /></div>;
  if (!ready) return <LoadingState label="Connecting AI assistant…" />;

  return (
    <div className="flex h-[calc(100vh-2rem)] flex-col gap-4 p-4">
      <PageHeader
        title="AI Security Assistant"
        subtitle="Gemini BYOK · explainable answers grounded in tenant findings"
      />
      {error ? <ErrorBanner message={error} /> : null}
      <input
        className="rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm"
        placeholder="Optional Gemini API key (BYOK)"
        value={geminiKey}
        onChange={(e) => setGeminiKey(e.target.value)}
      />
      <div className="glass glow-border flex-1 space-y-3 overflow-auto p-4">
        {messages.length === 0 ? (
          <div className="text-sm text-slate-500">
            Ask about findings, certificates, remediation plans, or compliance narratives.
          </div>
        ) : null}
        {messages.map((m, i) => (
          <div
            key={i}
            className={`max-w-3xl rounded-2xl px-4 py-3 text-sm ${
              m.role === "user"
                ? "ml-auto bg-cyan-400/10 text-cyan-50"
                : "bg-white/5 text-slate-200"
            }`}
          >
            <div className="whitespace-pre-wrap">{m.content}</div>
            {m.reasoning ? (
              <div className="mt-2 border-t border-white/10 pt-2 text-xs text-slate-400">
                Reasoning: {m.reasoning}
              </div>
            ) : null}
            {m.citations?.length ? (
              <div className="mt-2 text-[11px] text-slate-500">
                Citations: {m.citations.join(" · ")}
              </div>
            ) : null}
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <textarea
          className="min-h-[80px] flex-1 rounded-xl border border-white/10 bg-black/30 p-3 text-sm"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
        />
        <button
          disabled={busy}
          onClick={send}
          className="rounded-xl bg-cyan-400 px-5 text-sm font-semibold text-ink-950 disabled:opacity-60"
        >
          {busy ? "…" : "Send"}
        </button>
      </div>
    </div>
  );
}
