import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// `npm run build` writes console/dist, which the API serves at http://127.0.0.1:8000/ (one command, one address).
// `npm run dev` serves on http://localhost:5173 and calls the API on :8000 (allowed by the API's CORS list).
export default defineConfig({
  plugins: [react()],
  base: "/",
  build: { outDir: "dist", emptyOutDir: true, assetsInlineLimit: 0 },
  server: { port: 5173, strictPort: true },
});
