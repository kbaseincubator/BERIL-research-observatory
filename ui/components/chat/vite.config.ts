import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "node:path";

/**
 * Build output goes directly into the FastAPI app's static dir so the Jinja
 * template can reference it via `/static/chat/chat.js`.
 *
 * The output is ES-module only. The Jinja template loads it with
 * `<script type="module" src="/static/chat/chat.js">`.
 */
export default defineConfig({
  plugins: [react()],
  // React's dev/prod branch reads `process.env.NODE_ENV`. In app builds Vite
  // replaces this automatically; in library mode it does not, so the
  // reference survives into the bundle and throws `ReferenceError: process
  // is not defined` in the browser. Replace it with a literal at build time.
  define: {
    "process.env.NODE_ENV": JSON.stringify("production"),
  },
  build: {
    outDir: resolve(__dirname, "../../app/static/chat"),
    emptyOutDir: true,
    sourcemap: true,
    lib: {
      entry: resolve(__dirname, "src/main.tsx"),
      formats: ["es"],
      fileName: () => "chat.js",
    },
    rollupOptions: {
      // React is bundled so the script is self-contained — no import map
      // or CDN coordination needed on the Jinja side.
      external: [],
      output: {
        assetFileNames: "chat.[ext]",
      },
    },
  },
  server: {
    // Standalone preview (`npm run dev`) opens src/main.tsx against index.html.
    port: 5173,
    strictPort: false,
  },
});
