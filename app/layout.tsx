import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SentinelX AI",
  description: "Enterprise Multi-Tenant Secrets & Certificate Lifecycle Platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body>{children}</body>
    </html>
  );
}
