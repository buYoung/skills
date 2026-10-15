# Updating this skill for a new Pi version

This file is for maintaining the skill itself. It is not part of the package-authoring workflow, and `SKILL.md` does not route to it.

## Reference source

| Item | Value |
|---|---|
| Repository | `earendil-works/pi` |
| Commit | `b06c1f2cf1dea6af8748ddeee18c23587d2cb7c6` (2026-10-14) |
| Relation to release | 46 commits after `v1.2.0`; `packages/coding-agent/package.json` still reports `1.2.0` |
| Node engine | `>=22.19.0` |
| Provenance | `pi-packages-analysis.md` (2026-10-15) and its linked references, written against the same commit |

The contracts, examples, and scripts in this skill were verified against the source at that commit. When the source and the analysis disagree, the source decides.

## Procedure

1. List the changes since the reference commit: `git log --oneline b06c1f2cf1dea6af8748ddeee18c23587d2cb7c6..<new-commit> -- <paths>`, using the paths in the source map below, and read the diffs of the files mapped to each skill file.
2. Update each affected rule from the new source, not from documentation, the analysis, or a release build alone. A release can lag a commit: npm `1.2.0` predates the reference commit and still drops empty quoted prompt arguments, which `9fe3f3716` fixed.
3. Move the whole bundle to one commit. Do not mix rules from different commits.
4. Update the version-specific statements listed below.
5. Rerun the bundled checks against an installed Pi at the new revision: the starter validator with `--runtime --pack`, the extracted-artifact rerun, the starter tool cases, and representative broken packages. Record the Pi and Node versions and the results in `references/evidence.md`.

## Source map

Paths are under `packages/coding-agent/src/` unless they start with `packages/`.

| Skill file | Source to compare |
|---|---|
| `references/packaging.md`, `references/operations.md` | `core/package-manager.ts`, `package-manager-cli.ts`, `core/pi-manifest.ts`, `core/settings-manager.ts`, `core/project-trust.ts`, `core/trust-manager.ts`, `utils/git.ts` |
| `references/extensions.md`, `references/advanced-extensions.md` | `core/extensions/loader.ts`, `core/extensions/runner.ts`, `core/extensions/types.ts`, `core/resource-loader.ts`, `core/agent-session.ts`, `core/tools/truncate.ts`, `main.ts`, `extensions/index.ts`, `extensions/mcp/index.ts`, `packages/agent/src/agent-loop.ts` |
| `references/integrations.md` | `core/provider-composer.ts`, `core/agent-session-services.ts`, `core/mcp-servers.ts`, `extensions/mcp/index.ts`, `core/extensions/loader.ts` (host module mapping), `packages/ai` public and `compat` entry points |
| `references/resources.md`, `scripts/lib/theme.mjs` | `core/skills.ts`, `core/prompt-templates.ts`, `utils/frontmatter.ts`, `modes/interactive/interactive-mode.ts` (built-in commands), `modes/interactive/theme/theme.ts`, `modes/interactive/theme/theme-schema.ts`, `modes/interactive/theme/theme-tokens.ts`, `packages/tui/src/colors.ts` |
| `scripts/validate-package.mjs`, `scripts/test-tools.mjs`, `scripts/lib/runtime.mjs` | Exports in `index.ts` (`DefaultResourceLoader`, `DefaultPackageManager`, `SettingsManager`, `ModelRuntime`, `SessionManager`, `createAgentSession`) and the session members the runner calls (`bindExtensions`, `agent.prompt`, `extensionRunner`, pending provider/MCP registrations); `packages/ai` faux provider exports (`fauxProvider`, `fauxAssistantMessage`, `fauxToolCall`, `InMemoryCredentialStore`) |
| `assets/starter/`, `assets/patterns/` | `ExtensionAPI` types and the `truncateHead`/`truncateTail` exports |

## Version-specific statements

Search the bundle for `b06c1f2`, `reference commit`, `this revision`, `baseline`, `1.2.0`, and `post-tag`. The statements tied to the reference commit or the `1.2.0` release are listed below. Other matches, such as "at this revision" in `references/packaging.md`, `references/extensions.md`, `references/integrations.md`, and `references/advanced-extensions.md`, mark ordinary rules; recheck those through the source map.

| Location | Statement |
|---|---|
| `references/evidence.md` | "Supported Pi revision" block, the observed difference from the `1.2.0` release, provenance, and the revision history |
| `assets/starter/README.md` | Design baseline commit and the empty quoted argument note |
| `references/resources.md` | "At the reference commit" prompt example and the post-`v1.2.0` empty-argument note |
| `references/validation.md` | Prompt row's post-tag difference in empty-argument handling |
| `references/advanced-extensions.md` | Note on event surfaces changed after `v1.2.0` |
| `scripts/lib/theme.mjs` | Header commit and the embedded token and color contract |
