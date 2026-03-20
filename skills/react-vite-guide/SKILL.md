---
name: react-vite-guide
description:
  React 19 + Vite SPA development guidelines. Use PROACTIVELY when writing,
  reviewing, or refactoring any React component — even if the user doesn't
  explicitly ask for best practices. Covers composition patterns (compound
  components, boolean prop elimination, state lifting, context providers),
  performance optimization (React.lazy, Suspense, code splitting, useMemo,
  useCallback, memo, re-render prevention, bundle size reduction), and web
  interface best practices (accessibility, ARIA, forms, animation, dark mode).
  Triggers on any work involving useState, useEffect, useRef, useMemo,
  useCallback, useTransition, useContext, use(), React.lazy, Suspense, SWR,
  React Router, Vite config, import.meta.env, manualChunks, rollupOptions,
  Tailwind CSS, CSS Modules, or barrel file imports. Also triggers on
  performance debugging, re-render issues, bundle analysis, code splitting
  decisions, component architecture discussions, state management patterns,
  or new feature development in React + Vite projects.
license: MIT
---

# React 19 + Vite Guide

Comprehensive guidelines for building React 19 SPA applications with Vite. Combines composition patterns, performance optimization, and web interface best practices into a single reference optimized for AI agent workflows.

## Tech Stack

- **React 19** — `use()`, ref as prop, React Compiler support
- **Vite** — `React.lazy()` + dynamic `import()`, env variables, HMR
- **TypeScript** — strict mode recommended
- **Pure SPA (CSR)** — no SSR, no hydration concerns

## Capability Index

### 1. Composition Patterns (references/composition-patterns.md)

Component architecture and state management patterns for scalable React apps.

| Priority | Category | Impact |
|----------|----------|--------|
| 1 | Component Architecture | HIGH |
| 2 | State Management | MEDIUM |
| 3 | Implementation Patterns | MEDIUM |
| 4 | React 19 APIs | MEDIUM |

Key topics:
- Boolean prop proliferation vs composition alternatives
- Compound components with shared context
- State management decoupled from UI via providers
- Generic context interfaces (state/actions/meta)
- State lifted into providers for sibling access
- Explicit component variants vs boolean modes
- Children vs render props
- React 19: `use()` replaces `useContext()`, ref as regular prop

### 2. Performance Optimization (references/performance-optimization.md)

Performance optimization patterns adapted for Vite + React 19 SPA. Next.js-specific patterns removed; Vite equivalents provided.

| Priority | Category | Impact |
|----------|----------|--------|
| 1 | Async Optimization | CRITICAL |
| 2 | Bundle Size | CRITICAL |
| 3 | Client-Side Data Fetching | MEDIUM-HIGH |
| 4 | Re-render Optimization | MEDIUM |
| 5 | Rendering Performance | MEDIUM |
| 6 | JavaScript Performance | LOW-MEDIUM |
| 7 | Advanced Patterns | LOW |

Key topics:
- `Promise.all()` and dependency-based parallelization
- `React.lazy()` + `Suspense` for code splitting (Vite)
- Barrel file import cost and direct imports
- Hover/focus preloading for perceived speed
- SWR for client-side data deduplication
- Functional `setState`, lazy state initialization
- `useTransition` for non-urgent updates
- `content-visibility: auto` for long lists
- `useRef` for transient values
- Module-level caching patterns

### 3. Web Interface (references/web-interface.md)

UI/UX patterns for accessibility, forms, animation, performance, and content quality.

| Category | Focus |
|----------|-------|
| Accessibility | ARIA, semantic HTML, keyboard handlers |
| Focus States | `focus-visible`, no bare `outline-none` |
| Forms | `autocomplete`, correct `type`, paste allowed |
| Animation | `prefers-reduced-motion`, compositor-only props |
| Typography | Ellipsis, curly quotes, `tabular-nums` |
| Content Handling | Truncation, empty states, long content |
| Images | Explicit dimensions, lazy loading |
| Performance | Virtualization, no layout reads in render |
| Navigation & State | URL reflects state, deep-linkable UI |
| Touch & Interaction | `touch-action`, `overscroll-behavior` |
| Dark Mode | `color-scheme`, `theme-color` meta |
| Locale & i18n | `Intl.DateTimeFormat`, `Intl.NumberFormat` |

### 4. Vite-Specific Patterns (references/vite-specific.md)

Vite-specific configuration, conventions, and optimization patterns.

Key topics:
- Dynamic imports and code splitting with Vite
- Environment variables (`import.meta.env`)
- Vite plugin ecosystem (React SWC/Babel)
- Build optimization (`manualChunks`, `rollupOptions`)
- Alias and path resolution
- CSS Modules / Tailwind CSS integration

