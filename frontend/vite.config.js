import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server proxies /api/* → http://localhost:5000
// Prod build writes to dist/ which the Flask app (or any static host) serves.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:5000",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: false,
    chunkSizeWarningLimit: 1024,
  },
});
