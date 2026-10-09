import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
// Single entry on purpose: scripts/package-workspace.py inlines exactly one JS and one CSS file.
// The design-system gallery (design-system.html) is served by the dev server: npm run workspace → /design-system.html
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8765',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist-workspace',
    rollupOptions: {
      input: 'workspace.html',
    },
  },
});

