/*
 * For licensing see accompanying LICENSE file.
 * Copyright (C) 2025 Apple Inc. All Rights Reserved.
 */

import { defineConfig } from "vite";
import anywidget from "@anywidget/vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";

export default defineConfig({
  plugins: [
    svelte({ hot: false }),
    anywidget(),
  ],
  server: {
    hmr: {
      overlay: false,
    },
  },
  build: {
    outDir: "policy_projector/static",
    emptyOutDir: false,
    lib: {
      entry: {
        index: "widget/index.js",
      },
      formats: ["es"],
    },
    rollupOptions: {
      output: {
        assetFileNames: "index.[ext]",
      },
    }
  },
});
