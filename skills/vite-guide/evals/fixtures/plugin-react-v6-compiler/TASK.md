# COMP-118: restore Compiler integration after plugin-major trial

Vite core and Node are already fixed at the versions in `package.json`. The dependency council has separately authorized `@vitejs/plugin-react` v6, but a trial upgrade rejects the existing inline `babel` configuration. Fast Refresh must remain active, and the React team requires the unchanged semantics recorded in `COMPILER_CONTRACT.md`.

Repair only the Vite/plugin adapter:

- use the supported plugin-react v6 integration path rather than retaining a removed inline option;
- preserve the existing virtual module plugin implementation, forwarded diagnostics, and production source maps;
- keep virtual release flags available before React processing and apply Compiler transformation after the React/Fast Refresh integration;
- preserve caller-owned Compiler options and React source exactly;
- keep dependency and configuration changes separately reversible.

Do not install dependencies or infer performance gains. `REPORT.md` must derive the required compatibility gates, explain plugin ordering, separate development and production verification, and give rollback points.
