/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#0b0d10",
        surface: "#14171c",
        primary: "#3d8bfd",
        text: "#e6e8eb",
        muted: "#8a9099",
        border: "#242832",
        success: "#3fb950",
        warning: "#d29922",
        error: "#f85149",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "SFMono-Regular", "monospace"],
      },
    },
  },
  plugins: [],
};
