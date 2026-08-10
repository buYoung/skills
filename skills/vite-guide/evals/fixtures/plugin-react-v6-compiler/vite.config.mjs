import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

function virtualFlagsPlugin() {
  const id = '\0virtual:release-flags';
  return {
    name: 'release-flags',
    resolveId(source) {
      return source === 'virtual:release-flags' ? id : null;
    },
    load(source) {
      return source === id ? 'export default { compiler: true }' : null;
    }
  };
}

export default defineConfig({
  plugins: [
    virtualFlagsPlugin(),
    react({
      babel: {
        plugins: [
          ['babel-plugin-react-compiler', { target: '19', compilationMode: 'annotation' }]
        ]
      }
    })
  ],
  server: {
    forwardConsole: true
  },
  build: {
    sourcemap: true
  }
});
