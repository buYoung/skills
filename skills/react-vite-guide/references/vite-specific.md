# Vite-Specific Patterns

Configuration, conventions, and optimization patterns specific to Vite + React 19 SPA projects.

---

## 1. Project Setup

### 1.1 Recommended Vite Config

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    target: 'esnext',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
        },
      },
    },
  },
})
```

- **`@vitejs/plugin-react-swc`** — faster than Babel plugin, suitable for most projects
- **`@vitejs/plugin-react`** — required when Babel plugins are needed (e.g., React Compiler, styled-components)

### 1.2 React Compiler with Vite

```typescript
// vite.config.ts — with React Compiler (Babel plugin required)
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const ReactCompilerConfig = { /* compiler options */ }

export default defineConfig({
  plugins: [
    react({
      babel: {
        plugins: [
          ['babel-plugin-react-compiler', ReactCompilerConfig],
        ],
      },
    }),
  ],
})
```

React Compiler eliminates the need for manual `memo()`, `useMemo()`, and `useCallback()` in most cases.

---

## 2. Environment Variables

### 2.1 Usage

Vite exposes env variables on `import.meta.env` (not `process.env`).

```typescript
// Only variables prefixed with VITE_ are exposed to client code
const apiUrl = import.meta.env.VITE_API_URL
const mode = import.meta.env.MODE        // 'development' | 'production'
const isDev = import.meta.env.DEV         // boolean
const isProd = import.meta.env.PROD       // boolean
```

### 2.2 Type Safety

```typescript
// src/vite-env.d.ts
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_APP_TITLE: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
```

### 2.3 Known Constraints

```typescript
// ❌ process.env is not available in Vite client code
const url = process.env.REACT_APP_API_URL

// ❌ Non-VITE_ prefixed vars are not exposed
const secret = import.meta.env.SECRET_KEY // undefined

// ✅ VITE_ prefix exposes the variable to client code
const url = import.meta.env.VITE_API_URL
```

---

## 3. Code Splitting

### 3.1 Route-Based Splitting

```tsx
import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'

const Home = lazy(() => import('./pages/Home'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Settings = lazy(() => import('./pages/Settings'))

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<PageSkeleton />}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}
```

### 3.2 Named Exports with React.lazy

`React.lazy` expects a default export. For named exports:

```tsx
// ✅ Re-export as default
const MonacoEditor = lazy(() =>
  import('./MonacoEditor').then(mod => ({ default: mod.MonacoEditor }))
)
```

### 3.3 Manual Chunks

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('react') || id.includes('react-dom')) {
              return 'vendor-react'
            }
            if (id.includes('@radix-ui') || id.includes('@headlessui')) {
              return 'vendor-ui'
            }
            return 'vendor'
          }
        },
      },
    },
  },
})
```

---

## 4. Path Aliases

### 4.1 Vite Config

```typescript
// vite.config.ts
resolve: {
  alias: {
    '@': path.resolve(__dirname, './src'),
    '@components': path.resolve(__dirname, './src/components'),
    '@hooks': path.resolve(__dirname, './src/hooks'),
    '@utils': path.resolve(__dirname, './src/utils'),
  },
}
```

### 4.2 TypeScript Config

```json
// tsconfig.json (or tsconfig.app.json)
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@components/*": ["./src/components/*"],
      "@hooks/*": ["./src/hooks/*"],
      "@utils/*": ["./src/utils/*"]
    }
  }
}
```

Both configurations are kept in sync. Vite resolves at build time; TypeScript resolves for type checking.

---

## 5. CSS Integration

### 5.1 CSS Modules

```tsx
// Button.module.css is automatically scoped
import styles from './Button.module.css'

function Button({ children }: { children: React.ReactNode }) {
  return <button className={styles.primary}>{children}</button>
}
```

### 5.2 Tailwind CSS v4

```typescript
// vite.config.ts
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
})
```

```css
/* src/index.css */
@import 'tailwindcss';
```

### 5.3 Global CSS

```tsx
// src/main.tsx
import './index.css'
import { createRoot } from 'react-dom/client'
import App from './App'

createRoot(document.getElementById('root')!).render(<App />)
```

---

## 6. Static Assets

### 6.1 Importing Assets

```tsx
// Vite handles asset imports with hashed filenames
import logoUrl from './assets/logo.svg'

function Logo() {
  return <img src={logoUrl} alt="Logo" width={120} height={40} />
}
```

### 6.2 Public Directory

Files in `public/` are served at root path and not processed by Vite:

```tsx
// public/favicon.ico → /favicon.ico
<link rel="icon" href="/favicon.ico" />
```

### 6.3 SVG as Component

```typescript
// Using vite-plugin-svgr
import { defineConfig } from 'vite'
import svgr from 'vite-plugin-svgr'

export default defineConfig({
  plugins: [react(), svgr()],
})
```

```tsx
import Logo from './assets/logo.svg?react'

function Header() {
  return <Logo className="h-8 w-8" aria-hidden="true" />
}
```

---

## 7. Development Patterns

### 7.1 Proxy API Requests

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:3001',
        changeOrigin: true,
      },
    },
  },
})
```

### 7.2 HTTPS in Development

```typescript
// vite.config.ts
import basicSsl from '@vitejs/plugin-basic-ssl'

export default defineConfig({
  plugins: [react(), basicSsl()],
})
```

---

## 8. Build Optimization

### 8.1 Analyze Bundle Size

```bash
# Install rollup-plugin-visualizer
npx vite build --mode analyze

# Or add to vite.config.ts
import { visualizer } from 'rollup-plugin-visualizer'

export default defineConfig({
  plugins: [
    react(),
    visualizer({ open: true, gzipSize: true }),
  ],
})
```

### 8.2 Preload Critical Assets

```html
<!-- index.html -->
<head>
  <link rel="preconnect" href="https://api.example.com" />
  <link rel="preload" href="/fonts/inter.woff2" as="font" type="font/woff2" crossorigin />
</head>
```

### 8.3 Compression

```typescript
// vite.config.ts
import compression from 'vite-plugin-compression'

export default defineConfig({
  plugins: [
    react(),
    compression({ algorithm: 'gzip' }),
    compression({ algorithm: 'brotliCompress' }),
  ],
})
```

---

## References

1. [https://vite.dev/guide/](https://vite.dev/guide/)
2. [https://vite.dev/config/](https://vite.dev/config/)
3. [https://vite.dev/guide/env-and-mode](https://vite.dev/guide/env-and-mode)
4. [https://react.dev/learn/react-compiler](https://react.dev/learn/react-compiler)
5. [https://tailwindcss.com/docs/installation/vite](https://tailwindcss.com/docs/installation/vite)
