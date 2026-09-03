import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        "deep-graphite": "#0B0F14",
        "dark-slate": "#111820",
        "slate-panel": "#151D26",
        "subtle-slate": "#26313D",
        "almost-white": "#E6EDF3",
        "muted-gray": "#8B98A7",
        "electric-blue": "#4C8DFF",
        "bright-blue": "#6BA1FF",
        success: "#3CCB7F",
        warning: "#F2B84B",
        error: "#F05D6C",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "ui-monospace", "monospace"],
      },
      animation: {
        "fade-in": "fadeIn 0.3s ease-out",
        "slide-up": "slideUp 0.35s ease-out",
        "pulse-dot": "pulseDot 1.4s infinite ease-in-out",
        "glow": "glow 2s ease-in-out infinite alternate",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulseDot: {
          "0%, 80%, 100%": { transform: "scale(0.6)", opacity: "0.4" },
          "40%": { transform: "scale(1)", opacity: "1" },
        },
        glow: {
          "0%": { boxShadow: "0 0 5px rgba(76,141,255,0.2), 0 0 10px rgba(76,141,255,0.1)" },
          "100%": { boxShadow: "0 0 10px rgba(76,141,255,0.4), 0 0 20px rgba(76,141,255,0.2)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
