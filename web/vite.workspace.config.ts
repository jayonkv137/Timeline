import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
// Single entry on purpose: scripts/package-workspace.py inlines exactly one JS and one CSS file.
// The design-system gallery (design-system.html) is served by the dev server: npm run workspace → /design-system.html
export default defineConfig({plugins:[react()],build:{outDir:'dist-workspace',rollupOptions:{input:'workspace.html'}}});
