import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}", "./store/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "var(--vb-primary)",
        secondary: "var(--vb-secondary)",
        tertiary: "var(--vb-tertiary)",
        background: "var(--vb-background)",
        surface: "var(--vb-surface)",
        raised: "var(--vb-surface-raised)",
        ink: "var(--vb-text-primary)",
        muted: "var(--vb-text-secondary)",
        faint: "var(--vb-text-tertiary)",
        border: {
          subtle: "var(--vb-border-subtle)",
          medium: "var(--vb-border-medium)",
          strong: "var(--vb-border-strong)"
        },
        success: "var(--vb-success)",
        warning: "var(--vb-warning)",
        error: "var(--vb-error)",
        paper: "var(--vb-background)",
        coral: "var(--vb-secondary)",
        amber: "var(--vb-warning)",
        steel: "var(--vb-text-secondary)",
        mint: "var(--vb-success)"
      },
      fontFamily: {
        display: ["Archivo Black", "Impact", "Arial Black", "sans-serif"],
        sans: ["Work Sans", "-apple-system", "Segoe UI", "Helvetica", "sans-serif"],
        mono: ["Space Mono", "Courier New", "Consolas", "monospace"]
      },
      fontSize: {
        display: ["56px", { lineHeight: "1.05", letterSpacing: "-0.03em", fontWeight: "400" }],
        headline: ["38px", { lineHeight: "1.1", letterSpacing: "-0.02em", fontWeight: "400" }],
        subhead: ["24px", { lineHeight: "1.2", letterSpacing: "-0.01em", fontWeight: "400" }],
        body: ["16px", { lineHeight: "1.7" }],
        caption: ["12px", { lineHeight: "1.5", letterSpacing: "0.01em", fontWeight: "500" }],
        overline: ["11px", { lineHeight: "1.4", letterSpacing: "0.12em", fontWeight: "700" }]
      },
      borderRadius: {
        none: "0",
        sm: "0",
        DEFAULT: "0",
        md: "0",
        lg: "0",
        xl: "0"
      },
      boxShadow: {
        sm: "none",
        DEFAULT: "none",
        md: "none",
        lg: "none",
        xl: "none",
        focus: "0 0 0 2px var(--vb-background), 0 0 0 4px var(--vb-primary)"
      },
      transitionTimingFunction: {
        editorial: "cubic-bezier(0.2, 0, 0, 1)"
      }
    }
  },
  plugins: []
};

export default config;
