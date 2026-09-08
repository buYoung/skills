# Runtime package contracts

- `@fixture/banner@1.0.0` exports: `{ "custom": "./custom.js", "node": "./node.js", "default": "./default.js" }`. All branches are valid Node ESM; only custom returns the required release label. The host installs this package in production. Keep it external.
- `@fixture/theme@1.0.0` imports CSS. It needs Vite transforms in SSR and client builds. Keep it non-external; do not make every dependency non-external.
- The existing `host.mjs` is host-owned and not included in this isolated fixture. Package scripts are the supported place to set Node conditions for dev and production launch. Adapter and fixture validation do not require creating the host.
