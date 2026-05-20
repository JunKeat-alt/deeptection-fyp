/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        // Display: Fraunces (modern serif with optical sizes)
        display: ['"Fraunces"', '"Iowan Old Style"', 'Georgia', 'serif'],
        // Body: Plus Jakarta Sans — geometric humanist sans
        sans: ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      colors: {
        ink: {
          DEFAULT: "#0B0F14",
          soft: "#1A212A",
          muted: "#4A5764",
          subtle: "#8A97A3",
        },
        paper: {
          DEFAULT: "#FAF8F4",
          raised: "#FFFFFF",
          sunken: "#F2EEE7",
        },
        accent: {
          DEFAULT: "#2E5FFF",
          muted: "#B7C6F4",
        },
        verdict: {
          real: "#2F8F6B",      // sage green
          realBg: "#E8F4EE",
          fake: "#C94F3D",      // coral
          fakeBg: "#FBEBE7",
          uncertain: "#C08A2E", // warm amber
          uncertainBg: "#FAF1DD",
        },
      },
      boxShadow: {
        soft: "0 1px 2px rgba(11,15,20,0.04), 0 8px 24px rgba(11,15,20,0.06)",
        ring: "0 0 0 1px rgba(11,15,20,0.08)",
        card: "0 2px 6px rgba(11,15,20,0.04), 0 24px 48px -12px rgba(11,15,20,0.10)",
      },
      borderRadius: {
        xl2: "1.25rem",
      },
      backgroundImage: {
        "grain":
          "radial-gradient(rgba(11,15,20,0.035) 1px, transparent 1px)",
        "hero-glow":
          "radial-gradient(60% 50% at 50% 0%, rgba(46,95,255,0.08), transparent 60%)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "shimmer": {
          "0%": { backgroundPosition: "-400px 0" },
          "100%": { backgroundPosition: "400px 0" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.5s ease-out both",
        "shimmer": "shimmer 2s linear infinite",
      },
    },
  },
  plugins: [],
};
