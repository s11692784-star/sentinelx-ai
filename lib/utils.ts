import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function severityColor(sev: string) {
  switch (sev) {
    case "critical":
      return "text-rose-400 bg-rose-500/10 border-rose-500/30";
    case "high":
      return "text-orange-300 bg-orange-500/10 border-orange-500/30";
    case "medium":
      return "text-amber-300 bg-amber-500/10 border-amber-500/30";
    default:
      return "text-sky-300 bg-sky-500/10 border-sky-500/30";
  }
}
