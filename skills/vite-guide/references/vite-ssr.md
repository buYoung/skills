# Vite 7/8 SSR Integration

## Read When

Read for Vite's own SSR development/production integration in an existing host: middleware, server module loading, client/server builds, manifests, external dependencies, and runtime resolution. UI-framework guidance owns rendering and hydration. Framework-specific APIs, RSC/Server Functions implementation, and custom runtime construction are outside this guide.

## Establish the Application Path

Inspect installed Vite/Node/plugin versions, package engines, the host's request handler, rendering mode, client/server entries, HTML template ownership, build scripts/output directories, module format, deployment base, static serving, dependency installation, and runtime environment variables. Follow the actual path from request through module loading/rendering to browser scripts and assets. Missing version facts restrict dependent choices, not the whole investigation.

## Development and Production

| Concern | Development | Production |
|---|---|---|
| Vite lifetime | Create a dev server in middleware mode inside the existing host; mount `vite.middlewares` | Do not create a Vite dev server |
| HTML | Read source HTML and call `transformIndexHtml(url, template)` for HMR/plugin transforms | Read the client build's transformed HTML, normally `dist/client/index.html` |
| Server entry | `ssrLoadModule('/src/entry-server.js')` transforms/loads source | Import the actual emitted server entry from `dist/server` |
| Browser assets | Vite serves source/transformed modules | Host/CDN serves `dist/client` at the configured base |
| Error evidence | Use `ssrFixStacktrace` for development SSR errors | Preserve production errors/source maps through the host's diagnostics |

Use `server.middlewareMode: true` with `appType: 'custom'` when the host owns HTML handling. Keep the existing dev server lifecycle rather than creating one per request. See [Vite 7 SSR](https://v7.vite.dev/guide/ssr) and [JavaScript API](https://vite.dev/guide/api-javascript).

When Vite is a development dependency, put `await import('vite')` inside the development branch as well as the `createServer()` call. A top-level static Vite import is resolved before an `isProduction` branch runs, so guarding only the call still makes production require Vite. Check production startup with development dependencies absent, not just with the dev server disabled.

Build client and server separately, for example:

```sh
vite build --outDir dist/client
vite build --outDir dist/server --ssr src/entry-server.js
```

Adapt names to the actual emitted files and existing module format. Keep outputs separate so one build does not erase the other. The production import must load compiled output, not a source JSX/TS entry. Preserve template placeholders and insert rendered content into the built template. Keep client HTML, server output, and assets from the same release. See [Vite SSR production integration](https://vite.dev/guide/ssr#building-for-production).

## Manifests and Assets

Enable `build.ssrManifest: true` or `--ssrManifest` on the **client build** when the renderer consumes module-to-client-asset mappings for preload/style links. With `outDir: 'dist/client'`, the default path is `dist/client/.vite/ssr-manifest.json`; a string value sets a path relative to that output directory. Generation alone does nothing: the rendering integration must identify used module IDs and consume the mapping. It is optional when no such consumer is needed. See [SSR manifest](https://vite.dev/guide/ssr#generating-preload-directives).

The ordinary `build.manifest` maps source entries to emitted files and their imports/CSS/assets; its default is `.vite/manifest.json`. Use it when a backend constructs entry tags instead of consuming built HTML. It is not interchangeable with the SSR manifest. Do not require both by habit. SSR asset emission is normally delegated to the client build; inspect `ssrEmitAssets`/`emitAssets` support before overriding that behavior. See [build options](https://vite.dev/config/build-options#build-ssrmanifest) and [backend integration](https://vite.dev/guide/backend-integration).

Inspect emitted URLs and the manifest's actual values before adding `base`: avoid both missing and doubled subpaths. Serve hashed JS/CSS and public assets from the client output; do not expose server bundles or the whole project as static files. `new URL(..., import.meta.url)` asset patterns have different server/browser meanings and are not a general SSR asset solution. See [asset handling](https://vite.dev/guide/assets) and [deployment](vite-deployment.md).

## Dependencies and Runtime Resolution

Dependencies are normally externalized for SSR, while linked packages normally stay in the transform pipeline for HMR. Use targeted `ssr.noExternal` for packages requiring Vite transformation; use `ssr.external` for packages that must load through the runtime, including linked packages when appropriate. Explicit names in `ssr.external` take priority over `noExternal`. Verify external dependencies exist in the deployed runtime. See [SSR options](https://vite.dev/config/ssr-options).

Separate `ssr.resolve.conditions` for transformed/bundled dependencies from `ssr.resolve.externalConditions` for externalized imports. For custom external conditions, align Node's `--conditions` in development and production; a build setting cannot change a later native Node import by itself. Conditional `exports` take precedence over `mainFields`. Vite 7 documents external conditions defaulting to `['node']`; current Vite 8 documents `['node', 'module-sync']`. Check the target minor/tag before relying on that default difference. See [Vite 7 SSR options](https://v7.vite.dev/config/ssr-options) and [Vite 8 SSR options](https://vite.dev/config/ssr-options).

`ssr.target` defaults to `node`; `webworker` changes platform resolution, including browser-oriented conditions, but does not supply a host, fetch adapter, or Node polyfills. Node-target built-ins are externalized by default. Do not prescribe blanket `noExternal: true` as a universal fix: inspect built-ins, runtime APIs, package conditions, and bundle size for the target. Validate the actual deployment runtime independently of Vite's build-time Node engine.

## Version, Environment API, and Environment Variables

Vite 7's standard pipeline uses Rollup build options and esbuild dependency optimization; Vite 8 uses Rolldown/Oxc and native `build.rolldownOptions` / `optimizeDeps.rolldownOptions`. Client dev optimization does not prove SSR production compatibility. Audit the version-native configuration and emitted imports using [build/plugins](vite-build-plugins.md) and [Vite 8 migration](vite-7-to-8-migration.md).

Keep working `ssrLoadModule` integration unless a separate change is justified. If the project already uses Environment API, inspect its environment configuration, module runner, plugin integration, and target-version stability. Current docs mark the API Release Candidate with some experimental parts; do not silently migrate or call the whole surface stable. See [Environment instances](https://vite.dev/guide/api-environment-instances).

`import.meta.env.SSR` selects server versus client code; `import.meta.env` values are build-time replacements in built modules. Keep runtime secrets in server-only runtime configuration and out of `VITE_*`, `define`, client imports, and serialized HTML. A production process changing an environment variable does not rewrite already-built client constants. Inspect mode, build-time values, and host-time configuration separately with [env and mode](https://vite.dev/guide/env-and-mode) and [client runtime](vite-client-runtime.md).

## Verify and Report

Verify development HTML transforms/module updates, both production builds, and production startup from emitted files without the dev server. Exercise direct/refresh routes at the real base, client interactivity, CSS/assets/preload links, manifest consumers, external package resolution/conditions, and server-only environment boundaries. For React, pair this with `react-guide` for hydration, streaming, and per-request state.

Report source/config checks, executed build/import smoke checks, browser hydration, and deployment verification separately. A config load, synthetic manifest, or `vite preview` run cannot establish the production SSR host's correctness. Keep unrun or environment-blocked checks explicit.
