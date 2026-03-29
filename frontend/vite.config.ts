import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: path.resolve(__dirname, '../pretix_betterpos/static/pretixplugins/pretix_betterpos/dist'),
    emptyOutDir: true,
    sourcemap: false,
    manifest: false,
    rollupOptions: {
      input: path.resolve(__dirname, 'src/main.tsx'),
      output: {
        entryFileNames: 'betterpos-app.js',
        chunkFileNames: 'chunks/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]'
      }
    }
  }
});
