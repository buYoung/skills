# OPS-731: complete the bundler arrival

The console runs on the Node version declared in `package.json` and is deployed at `/ops/`. The organization authorized stable Vite 8 core, but did not authorize a React plugin major change. The current repository was previously used for an experimental Vite 7 bundler trial and now produces the findings captured in `MIGRATION_LOG.md`.

Preserve these product contracts:

- `/ops/` deployment and forwarded development diagnostics
- `es2020` browser output, production source maps, and the existing audit manifest plugin
- dependency optimization exclusion for `react-dom/client`
- a higher-precedence React runtime chunk and a lower-precedence remaining third-party vendor chunk on Windows and POSIX paths

Remove trial-only dependency wiring and migrate incompatible legacy configuration to supported Vite 8-native behavior. Keep the React plugin at its currently authorized major and do not edit its plugin implementation. Do not add unrelated tuning or install dependencies. `REPORT.md` must classify blockers/debt, identify reversible stages, list verification actually performed, and state what still requires install/build/runtime evidence.
