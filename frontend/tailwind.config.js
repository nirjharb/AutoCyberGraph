/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#0a0e14",
          900: "#0f1722",
          850: "#13202e",
          800: "#182938",
          700: "#22394c",
        },
        accent: {
          DEFAULT: "#22d3ee",
          dim: "#0e7490",
          glow: "#67e8f9",
        },
        risk: {
          critical: "#f43f5e",
          high: "#fb923c",
          medium: "#facc15",
          low: "#34d399",
        },
      },
      fontFamily: {
        display: ["'Segoe UI'", "system-ui", "-apple-system", "sans-serif"],
        mono: ["'JetBrains Mono'", "'Fira Code'", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
