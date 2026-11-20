import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import tailwindcss from "@tailwindcss/vite";

// Builds straight into ../static, which install.sh copies to the Pi.
// `npm run dev` proxies the API to the real Pi so you can develop against live data.
export default defineConfig({
  base: "./",
  plugins: [svelte(), tailwindcss()],
  build: { outDir: "../static", emptyOutDir: true, assetsDir: "assets", chunkSizeWarningLimit: 200, assetsInlineLimit: 0 },
  server: { proxy: { "/api": "http://192.168.18.28:8090" } },
});
