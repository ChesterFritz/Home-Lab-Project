import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import tailwindcss from "@tailwindcss/vite";

// Builds into ../app, which server.py serves at "/". The classic UI stays at /classic/.
// `npm run dev` proxies the API to a running server.py (MM_DEV_API, default the Pi).
const api = process.env.MM_DEV_API || "http://192.168.18.28:8888";
export default defineConfig({
  base: "/",
  plugins: [svelte(), tailwindcss()],
  build: { outDir: "../app", emptyOutDir: true, assetsDir: "assets", chunkSizeWarningLimit: 300 },
  server: { proxy: { "/api": api, "/moneyBook": api } },
});
