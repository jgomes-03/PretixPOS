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
      input: {
        app: path.resolve(__dirname, 'src/main.tsx'),
        selfservice: path.resolve(__dirname, 'src/selfservice.tsx'),
      },
      output: {
        entryFileNames: (chunkInfo) => {
          if (chunkInfo.name === 'app') return 'betterpos-app.js';
          if (chunkInfo.name === 'selfservice') return 'betterpos-selfservice.js';
          return 'chunks/[name]-[hash].js';
        },
        chunkFileNames: 'chunks/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]'
      }
    }
  }
});
