# Updating this skill for a new Pi version

This file is for maintaining the skill itself. It is not part of the package-authoring workflow, and `SKILL.md` does not route to it.

## Reference source

| Item | Value |
|---|---|
| Repository | `earendil-works/pi` |
| Commit | `fb0fe823539f6d04850f6e34748c01f01f212e1f` (committed 2026-11-27 UTC) |
| Relation to release | Exact `v1.7.0` tag; `packages/coding-agent/package.json` reports `1.7.0` |
| Node engine | `>=22.19.0` |
| Provenance | Original analysis: `pi-packages-analysis.md` (2026-10-15), based on `b06c1f2cf1dea6af8748ddeee18c23587d2cb7c6`; earlier updates: 91 commits through `cae9fd28a`, then 7 commits through `v1.4.0` (`4a080252f`), then 1186 commits through `v1.6.1` (`ef4a1cfcc`); current update: the following 781 commits through `v1.7.0` |

The contracts, examples, and scripts in this skill were verified against the source at that commit. When the source and the analysis disagree, the source decides.

## Procedure

1. List the changes since the reference commit: `git log --oneline fb0fe823539f6d04850f6e34748c01f01f212e1f..<new-commit> -- <paths>`, using the paths in the source map below, and read the diffs of the files mapped to each skill file. For a long range, `git diff --stat <old-tag> <new-tag> -- <paths>` shows which mapped files changed.
2. Update each affected rule from the new source, not from documentation, the analysis, or a release build alone. Check tag ancestry for each changed behavior. For example, `v1.4.0` includes the `/models` loader mapping, stacked editor-slot dialogs, codemode admission queue, client identity, and the classifier-image and tool-restoration changes. The earlier `v1.3.0` release lacks those additions. A released tag and a later development commit reporting the same version remain separate targets.
3. Move the whole bundle to one commit. Do not mix rules from different commits.
4. Update the version-specific statements listed below.
5. Rerun the bundled checks against a built SDK at the new revision: the starter validator with `--runtime --pack`, the extracted-artifact rerun, the starter tool cases, and applicable negative cases. An unbuilt checkout is not an executable `--pi-root`; install dependencies with `npm ci --ignore-scripts`, hydrate missing model data with `npm run hydrate:model-data`, and build the needed workspaces first. On macOS, build from the physical path (`/private/tmp/...`, not `/tmp/...`): mixed paths make TypeScript load two copies of the Pi AI declarations and fail the `durable` build. Set a persistent temporary output directory if the command runner cleans its own scratch directory. Run the relevant existing upstream regressions for changed contracts. Record the exact revision, Pi and Node versions, results, and unverified scenarios in `references/evidence.md`; keep release-build results separate.

## Source map

Paths are under `packages/coding-agent/src/` unless they start with `packages/`.

| Skill file | Source to compare |
|---|---|
| `references/packaging.md`, `references/operations.md` | `core/package-manager.ts`, `package-manager-cli.ts`, `core/pi-manifest.ts`, `core/settings-manager.ts`, `core/project-trust.ts`, `core/trust-manager.ts`, `utils/git.ts`, `utils/changelog.ts`, `main.ts` (offline flag, project trust, and `--agent-dir`), `cli/agent-dir-arg.ts`, `config.ts` (`getAgentDir()`), `core/extensions/pi-ai-extension-view.ts` |
| `references/extensions.md`, `references/advanced-extensions.md` | `core/extensions/loader.ts`, `core/extensions/virtual-modules.ts`, `core/extensions/runner.ts`, `core/extensions/types.ts`, `core/resource-loader.ts`, `core/agent-session.ts`, `core/exec.ts`, `core/tools/truncate.ts`, `core/tools/grep.ts`, `core/tools/find.ts`, `core/tools/read.ts`, `main.ts`, `extensions/index.ts`, `extensions/mcp/index.ts`, `extensions/codemode/execute.ts`, `modes/interactive/interactive-mode.ts`, `packages/agent/src/agent-loop.ts`, `packages/ai/src/utils/validation.ts` (tool argument validation), `packages/tui/src/tui.ts` (`Component` and `Container`) |
| `references/integrations.md` | `core/provider-composer.ts`, `core/agent-session-services.ts`, `core/model-runtime.ts`, `core/sdk.ts`, `core/client-identity.ts`, `core/mcp-servers.ts`, `extensions/mcp/index.ts`, `extensions/mcp/config.ts`, `extensions/mcp/oauth.ts`, `packages/mcp/src/config.ts`, `packages/mcp/src/client.ts`, `packages/mcp/src/protocol/types.ts`, `packages/mcp/src/oauth/client-settings.ts`, `core/extensions/loader.ts` and `core/extensions/virtual-modules.ts` (host module mapping), `packages/ai` public, `models`, and `compat` entry points, `packages/ai/src/utils/identity.ts`, `packages/ai/src/types.ts`, `packages/ai/src/models.ts` (`calculateCost()`), `packages/ai/src/telemetry.ts`, `packages/ai/src/providers/compat-schema.ts`, `packages/ai/src/providers/model-schema.ts` (model `cost`), `extensions/codemode/execute.ts` (`models.generateImages()` options), the System One classifier adapters under `packages/ai/src/api/`, and `packages/ai/src/api/json-request.ts` (their shared request path) |
| `references/resources.md`, `scripts/lib/theme.mjs` | `core/skills.ts`, `core/prompt-templates.ts`, `utils/frontmatter.ts`, `modes/interactive/interactive-mode.ts` (built-in commands), `modes/interactive/theme/theme.ts`, `modes/interactive/theme/theme-schema.ts`, `modes/interactive/theme/theme-tokens.ts`, `packages/tui/src/colors.ts` |
| `scripts/validate-package.mjs`, `scripts/test-tools.mjs`, `scripts/lib/runtime.mjs` | Exports in `index.ts` (`DefaultResourceLoader`, `DefaultPackageManager`, `SettingsManager`, `ModelRuntime`, `SessionManager`, `createAgentSession`) and the session members the runner calls (`bindExtensions`, `agent.prompt`, `extensionRunner`, pending provider/MCP registrations); `packages/ai` faux provider exports (`fauxProvider`, `fauxAssistantMessage`, `fauxToolCall`, `InMemoryCredentialStore`) |
| `assets/starter/`, `assets/patterns/` | `ExtensionAPI` types and the `truncateHead`/`truncateTail` exports |

## Version-specific statements

Search the bundle for `fb0fe823`, `reference commit`, `reference revision`, `this revision`, `baseline`, `1.7.0`, `Since`, and `post-tag`. Update current support statements together; preserve explicitly dated history and older-version boundaries, including `ef4a1cfc`, `4a080252`, `cae9fd28`, `b06c1f2`, `1.6.x`, `1.5.x`, `1.4.0`, `1.3.0`, and `1.2.0`. Recheck ordinary version-dependent rules through the source map as well.

| Location | Statement |
|---|---|
| `SKILL.md`, `references/evidence.md` | Compatibility baseline, "Supported Pi revision" block, release boundaries, provenance, and the latest revision record |
| `assets/starter/README.md` | Design baseline commit and the empty quoted argument note |
| `references/resources.md`, `references/validation.md` | Prompt example, the `v1.2.0` versus `v1.3.0` empty-argument boundary, and the `v1.5.1` quoting rules |
| `references/advanced-extensions.md` | Header-default ordering, dialog stacking and `blockedKind`, editor replacement during dialogs, read-only `render()` output, custom-overlay completion, and recovery context pairs |
| `references/extensions.md` | Tool argument validation, `pi.exec` output limit and exit codes, codemode worker admission, tool activation and pending tools on resume/tree navigation, built-in grep isolation and search operations, and package install failures at startup |
| `references/operations.md` | Project trust precedence, `--agent-dir`, `-e` refresh, `pi update` output, offline output, `--offline` rejection, and diagnostic labels |
| `references/integrations.md`, `references/packaging.md` | Resource-manifest detection, `changelogPath`, `/models` and `pi-ai` root mapping, classifier images and `compat`, image options and `cost.imageOutput`, request identity and attribution, telemetry, MCP protocol revisions, OAuth client registration, and MCP BOM handling |
| `references/validation.md` | Argument coercion in rejection cases, tool-activation, and classifier-image checks for the selected target |
| `scripts/lib/theme.mjs` | Header commit and the embedded token and color contract |
