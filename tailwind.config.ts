import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#05070f",
          900: "#0a0f1e",
          800: "#11182b",
          700: "#1a243b",
        },
        cyan: {
          glow: "#22d3ee",
        },
        danger: "#f43f5e",
        ok: "#34d399",
      },
      boxShadow: {
        glass: "0 8px 32px rgba(0,0,0,0.45)",
      },
      backgroundImage: {
        grid: "radial-gradient(rgba(34,211,238,0.08) 1px, transparent 1px)",
      },
    },
  },
  plugins: [],
};
export default config;
