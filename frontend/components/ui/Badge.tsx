import { cn, severityColor } from "@/lib/utils";

export function Badge({ children, severity }: { children: React.ReactNode; severity?: string }) {
  return (
    <span className={cn("inline-flex rounded-full border px-2.5 py-0.5 text-xs font-medium", severity ? severityColor(severity) : "border-white/10 text-slate-300")}>
      {children}
    </span>
  );
}
