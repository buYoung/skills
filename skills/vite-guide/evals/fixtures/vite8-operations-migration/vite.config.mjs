import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { auditPlugin } from './build/auditPlugin.mjs';

export default defineConfig({
  base: '/ops/',
  plugins: [react(), auditPlugin()],
  server: {
    forwardConsole: true
  },
  optimizeDeps: {
    exclude: ['react-dom/client'],
    esbuildOptions: {
      target: 'es2020'
    }
  },
  build: {
    target: 'es2020',
    minify: 'esbuild',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-runtime': ['react', 'react-dom'],
          vendor: ['zod', 'date-fns']
        }
      }
    }
  }
});
