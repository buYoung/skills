# Updating this skill for a new Pi version

This file is for maintaining the skill itself. It is not part of the package-authoring workflow, and `SKILL.md` does not route to it.

## Reference source

| Item | Value |
|---|---|
| Repository | `earendil-works/pi` |
| Commit | `4a080252f06caf63a525d7873c5d94d3c23887e0` (2026-10-22) |
| Relation to release | Exact `v1.4.0` tag; `packages/coding-agent/package.json` reports `1.4.0` |
| Node engine | `>=22.19.0` |
| Provenance | Original analysis: `pi-packages-analysis.md` (2026-10-15), based on `b06c1f2cf1dea6af8748ddeee18c23587d2cb7c6`; previous update: 91 commits through `cae9fd28a`; current update: the following 7 commits through `v1.4.0` |

The contracts, examples, and scripts in this skill were verified against the source at that commit. When the source and the analysis disagree, the source decides.

## Procedure

1. List the changes since the reference commit: `git log --oneline 4a080252f06caf63a525d7873c5d94d3c23887e0..<new-commit> -- <paths>`, using the paths in the source map below, and read the diffs of the files mapped to each skill file.
2. Update each affected rule from the new source, not from documentation, the analysis, or a release build alone. Check tag ancestry for each changed behavior. For example, `v1.4.0` includes the `/models` loader mapping, stacked editor-slot dialogs, codemode admission queue, client identity, and the classifier-image and tool-restoration changes. The earlier `v1.3.0` release lacks those additions. A released tag and a later development commit reporting the same version remain separate targets.
3. Move the whole bundle to one commit. Do not mix rules from different commits.
4. Update the version-specific statements listed below.
5. Rerun the bundled checks against a built SDK at the new revision: the starter validator with `--runtime --pack`, the extracted-artifact rerun, the starter tool cases, and applicable negative cases. An unbuilt checkout is not an executable `--pi-root`; install dependencies with `npm ci --ignore-scripts`, hydrate missing model data with `npm run hydrate:model-data`, and build the needed workspaces first. Set a persistent temporary output directory if the command runner cleans its own scratch directory. Run the relevant existing upstream regressions for changed contracts. Record the exact revision, Pi and Node versions, results, and unverified scenarios in `references/evidence.md`; keep release-build results separate.

## Source map

Paths are under `packages/coding-agent/src/` unless they start with `packages/`.

| Skill file | Source to compare |
|---|---|
| `references/packaging.md`, `references/operations.md` | `core/package-manager.ts`, `package-manager-cli.ts`, `core/pi-manifest.ts`, `core/settings-manager.ts`, `core/project-trust.ts`, `core/trust-manager.ts`, `utils/git.ts` |
| `references/extensions.md`, `references/advanced-extensions.md` | `core/extensions/loader.ts`, `core/extensions/virtual-modules.ts`, `core/extensions/runner.ts`, `core/extensions/types.ts`, `core/resource-loader.ts`, `core/agent-session.ts`, `core/tools/truncate.ts`, `core/tools/grep.ts`, `main.ts`, `extensions/index.ts`, `extensions/mcp/index.ts`, `extensions/codemode/execute.ts`, `modes/interactive/interactive-mode.ts`, `packages/agent/src/agent-loop.ts` |
| `references/integrations.md` | `core/provider-composer.ts`, `core/agent-session-services.ts`, `core/model-runtime.ts`, `core/sdk.ts`, `core/client-identity.ts`, `core/mcp-servers.ts`, `extensions/mcp/index.ts`, `extensions/mcp/config.ts`, `core/extensions/loader.ts` and `core/extensions/virtual-modules.ts` (host module mapping), `packages/ai` public, `models`, and `compat` entry points, `packages/ai/src/utils/identity.ts`, `packages/ai/src/types.ts`, `packages/ai/src/models.ts`, `packages/ai/src/telemetry.ts`, `packages/ai/src/providers/compat-schema.ts`, and the System One classifier adapters under `packages/ai/src/api/` |
| `references/resources.md`, `scripts/lib/theme.mjs` | `core/skills.ts`, `core/prompt-templates.ts`, `utils/frontmatter.ts`, `modes/interactive/interactive-mode.ts` (built-in commands), `modes/interactive/theme/theme.ts`, `modes/interactive/theme/theme-schema.ts`, `modes/interactive/theme/theme-tokens.ts`, `packages/tui/src/colors.ts` |
| `scripts/validate-package.mjs`, `scripts/test-tools.mjs`, `scripts/lib/runtime.mjs` | Exports in `index.ts` (`DefaultResourceLoader`, `DefaultPackageManager`, `SettingsManager`, `ModelRuntime`, `SessionManager`, `createAgentSession`) and the session members the runner calls (`bindExtensions`, `agent.prompt`, `extensionRunner`, pending provider/MCP registrations); `packages/ai` faux provider exports (`fauxProvider`, `fauxAssistantMessage`, `fauxToolCall`, `InMemoryCredentialStore`) |
| `assets/starter/`, `assets/patterns/` | `ExtensionAPI` types and the `truncateHead`/`truncateTail` exports |

## Version-specific statements

Search the bundle for `4a080252`, `reference commit`, `reference revision`, `this revision`, `baseline`, `1.4.0`, and `post-tag`. Update current support statements together; preserve explicitly dated history and older-version boundaries, including `cae9fd28`, `b06c1f2`, `1.3.0`, and `1.2.0`. Recheck ordinary version-dependent rules through the source map as well.

| Location | Statement |
|---|---|
| `SKILL.md`, `references/evidence.md` | Compatibility baseline, "Supported Pi revision" block, release boundaries, provenance, and the latest revision record |
| `assets/starter/README.md` | Design baseline commit and the empty quoted argument note |
| `references/resources.md`, `references/validation.md` | Prompt example and the `v1.2.0` versus `v1.3.0` empty-argument boundary |
| `references/advanced-extensions.md` | Header-default ordering, dialog stacking, custom-overlay completion, and recovery context pairs |
| `references/extensions.md`, `references/operations.md` | Codemode worker admission, tool activation on resume/tree navigation, and built-in grep isolation |
| `references/integrations.md`, `references/packaging.md` | `/models` mapping, classifier images and `compat`, request identity, telemetry, and MCP BOM handling |
| `references/validation.md` | Tool-activation and classifier-image checks for the selected target |
| `scripts/lib/theme.mjs` | Header commit and the embedded token and color contract |
