/*
 * For licensing see accompanying LICENSE file.
 * Copyright (C) 2025 Apple Inc. All Rights Reserved.
 */

import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vite";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [sveltekit(), tailwindcss()],
  server: {
    host: "0.0.0.0",
    port: 5174,
  },
  build: {
    target: "esnext", //browsers can handle the latest ES features
  },
  optimizeDeps: {
    exclude: ["embedding-atlas"],
  },
});
