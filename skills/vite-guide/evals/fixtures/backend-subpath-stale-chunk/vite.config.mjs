import { defineConfig } from 'vite';

export default defineConfig({
  base: '/',
  build: {
    assetsDir: 'assets',
    rollupOptions: {
      output: {
        chunkFileNames: 'assets/[name]-[hash].js'
      }
    }
  }
});
