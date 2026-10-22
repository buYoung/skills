# Evidence and compatibility boundaries

Read this to find the Pi revision these contracts describe, the `1.4.0` release boundary and differences from `1.3.0`, the common assumptions the contracts correct, and the limits of what the bundled checks prove. The [revision history](#revision-history-for-maintainers) at the end records how the bundle was checked; you do not need it to build a package.

## Supported Pi revision

These values were checked directly against the repository:

```text
repository: earendil-works/pi
commit: 4a080252f06caf63a525d7873c5d94d3c23887e0
commit date: 2026-10-22
package: @earendil-works/pi-coding-agent
package.json version: 1.4.0
relationship to release: exact v1.4.0 tag
Node engine: >=22.19.0
```

The bundle's source contracts were rechecked against this commit, including unchanged contracts carried forward from the earlier baseline. Use this revision when a generated package's README states the supported Pi version or commit; list release compatibility separately when it was actually checked.

### Release boundaries through `1.4.0`

The reference now matches the released `v1.4.0` tag rather than a development build reporting `1.3.0`. All behaviors in the following table are included in `v1.4.0`; the middle column records whether they were already present in the older release. Tag ancestry establishes these boundaries:

| Behavior | In `v1.3.0`? | Relevant change |
|---|---|---|
| Preserve empty quoted prompt arguments | Yes | `9fe3f3716`; the older `v1.2.0` release drops them |
| Close a custom overlay's own handle rather than the topmost overlay | Yes | `a4f67eb65` |
| Map the public `@earendil-works/pi-ai/models` entry point for extensions | No | `22dc6c26f` |
| Stack concurrent editor-slot extension dialogs | No | `38847563f` |
| Queue codemode scripts at the process-wide worker limit | No | `885a564b3` |
| Use request `telemetry` spans instead of `telemetryContext` | No | `2ec55d808` |
| Carry client identity through Pi AI and apply it in API adapters | No | `adc5fa9f8`, `04a93bad8` |
| Read and edit `mcp.json` with a leading UTF-8 BOM | No | `bdd9f0399` |
| Send classifier images using the service's System One format and `compat` | No | `7f225f25d` |
| Activate eligible extension tools absent from an older branch's recorded loadout | No | `bd3c9b823` |
| Omit truncated tool calls and their results together during recovery | No | `02726086d` |
| Keep built-in grep independent of `RIPGREP_CONFIG_PATH` | No | `8c4e87389` |

The 2026-10-21 record below established starter compatibility with installed Pi `1.3.0`. It does not establish that release's support for the later features, and it is not a substitute for the separate `v1.4.0` checks.

### Provenance

The original user-supplied analysis `pi-packages-analysis.md` (dated 2026-10-15) and its linked references target `b06c1f2cf1dea6af8748ddeee18c23587d2cb7c6`. The 2026-10-21 update compared the following 91 commits through `cae9fd28a` directly with that baseline. The 2026-10-22 update compares 7 further commits through the `v1.4.0` tag. The analysis is historical provenance, not a runtime dependency or evidence for later changes; the current source decides any disagreement.

The contracts were derived from the package manifest, discovery, and CLI implementation; the extension types, loader, and runner; agent tool execution; the skill and prompt loaders; theme schema, tokens, and color resolution; provider contracts; and MCP configuration at that commit. These names record how the contracts were established; they are not additional reading tasks.

This bundle contains the resulting rules, complete examples, the complete theme, the starter resources, and executable checks. It depends on no external documentation link, remote theme schema, or the original analysis file, and it needs no local absolute path from the analysis. Service endpoints and install sources in examples are placeholders for application configuration, not documentation references.

## Corrections to common assumptions

These corrections are preserved from the original analysis.

| Tempting simplification | Accurate rule at this revision |
|---|---|
| Any versioned npm spec is pinned | Only exact semver specs are pinned |
| A git ref never moves | A branch ref can advance on an explicit package update |
| User filters only narrow declared types | Missing or empty manifest types can fall back to conventional directories |
| A failed extension is merely skipped | A fresh CLI startup exits on extension errors |
| Tool and flag conflicts are only warnings | They create extension errors and stop a fresh CLI startup |
| `details.error` marks a tool failure | Throw, or set top-level `isError: true` |
| A runtime tool needs `refreshTools()` | No such public method exists; registration triggers the refresh |
| Install commands never run scripts | Lifecycle scripts of the package and its dependencies can run |
| Package-root ignore files hide all resources | Ignore rules apply from the collector's traversal root |
| Skill name violations are fatal | Most name and length issues only warn; a missing description prevents loading |
| `enableSkillCommands: false` disables invocation | It hides autocomplete; manual expansion still works |
| `system` is a schema-invalid theme name | The schema accepts it, but built-in lookup hides it; avoid it when authoring |
| SDK theme loading proves CLI validity | Strict validation is installed on the CLI path |
| `agent_end` is final completion | Follow-up work can remain; use `agent_settled` |

These corrections describe this revision; they are not an invitation to depend on quirks. Prefer layouts and public API usage that stay unambiguous when the implementation changes.

## Limits of the checks

- Static source inspection establishes contracts. It does not prove that an external service integration works or that every platform is compatible.
- When the target Pi version changes, including when the user's Pi differs from the supported revision, rerun the bundled package and tool checks, then the applicable CLI and integration scenarios in [validation](validation.md). Preserve the reported version or commit and any concrete API or behavior mismatch. If these contracts do not support the target, report that boundary instead of guessing a replacement contract or sending the user to external documents.
- The checks do not establish registry or gallery publication, package-manager lifecycle policy, immutable remote git tags, or operating-system compatibility unless those flows were actually exercised. When the delivered package promises them, record those outcomes separately.

## Revision history (for maintainers)

These records explain how the bundle was checked and why it changed. They are not steps for building a package.

### Starter validation (2026-10-15)

The bundled starter was checked with installed Pi `1.2.0` and Node `v24.14.0`:

- Pi's own skill parser loaded this skill with no diagnostics.
- The `npm pack` dry-run file list contained all eight intended starter files.
- An isolated `DefaultResourceLoader` loaded one extension, skill, prompt, and theme with no resource diagnostics.
- The CLI's theme validator was installed explicitly for the SDK check; the theme passed and supplies all 51 required plus 5 optional tokens.
- Direct calls to the loaded tool definition kept the supplied working directory, honored the compact flag, preserved result details, and rejected an aborted call.
- Prompt expansion with quoted arguments, positional defaults, and an argument slice passed.
- Repeating the resource-loader reload kept one copy of each resource. This was not a check of live agent-session replacement.
- The starter TypeScript and the complete reference examples for echo, state, dynamic resources, both provider forms, and HTTP MCP passed type checking against the installed declarations.

The generic skill-creator Python validator could not run because PyYAML was absent; YAML and frontmatter validation used Pi's installed YAML parser and its actual skill loader instead.

No model request, interactive terminal rendering, live session replacement, provider authentication, MCP connection, registry installation or publication, or git update or removal was exercised. The original analysis did not run full package lifecycle flows either. Generated packages need their own checks; the starter validation does not establish those outcomes for them.

### Independent authoring audit

A later audit on 2026-10-15 gave fresh agents two tasks without the original analysis, the Pi source, or external documentation: build a four-resource Git audit package, and repair a duration-parser package with discovery, dependency, factory, naming, and error-result defects. Each task had one run with this skill and one control run using existing knowledge. The skill bundle supplied the domain contracts, and the resulting package files were inspected and exercised through installed Pi `1.2.0`.

- Both with-skill outputs passed the original 20 acceptance checks across the two tasks: resource loading, host peers, propagation of the current working directory, tool success, failure, and cancellation, a direct command, valid skill, prompt, and theme resources, artifact coverage, filter boundaries, and correct installation and update guidance.
- The controls missed the current package-update command in both READMEs and the wildcard host-peer rule in the four-resource package.
- This is a small qualitative sample, not a general reliability estimate.

An additional check exposed a gap that the original criteria missed: both generated Git tools returned 231,420 bytes across 2,601 lines without truncation. The skill had mentioned truncation but offered neither a complete reusable implementation nor an explicit completion check for oversized results. The revision added [bounded-output.ts](../assets/patterns/bounded-output.ts), a shared tool and command integration example, and a required oversized-output check when result size can grow.

A fresh follow-up agent, given the revised skill and a Git tool and command task without an explicit truncation request, used the helper. Its package loaded, handled success, error, and cancellation, and returned 51,310 bytes, including the truncation notice, for the same 231,420-byte result. The referenced complete-output file exactly matched Git's full output. This was a targeted follow-up, not a rerun of every original acceptance check.

The helper also passed type checking and direct checks for unchanged small output, oversized multiline Unicode output, a single oversized Unicode line, cancellation, complete-file contents, and private file permissions. The body uses Pi's 50 KiB and 2000-line limits, and the path notice adds a small amount to the returned text.

The audit also made two execution details explicit: `ctx.mode` is `"print"` for text-print operation, and changing `PI_CODING_AGENT_DIR` alone does not suppress shared skill discovery. The isolated-load recipe now passes the relevant discovery flags while keeping the package's explicit `-e` resources.

Parent-side checks called the loaded tool definitions with an explicit context and captured the direct command's message bridge; they did not call a model. The independent author also reported an interactive CLI load, command execution, `/reload`, and theme selection for the four-resource package. This audit did not establish external provider authentication, MCP connections, the registry lifecycle, a cross-platform matrix, or any custom protocol implementation.

### Bundled validation and test tools

A subsequent revision added [validation](validation.md), [validate-package.mjs](../scripts/validate-package.mjs), [test-tools.mjs](../scripts/test-tools.mjs), and complete starter inventory and case files. It removed external documentation links and the starter's remote schema reference, while keeping provenance here without making it a prerequisite.

With installed Pi `1.2.0` and Node `v24.14.0`:

- The package validator passed the starter's exact resources and names, loader diagnostics, string/object and wildcard selection, per-type disabling, the local theme contract, the actual npm archive, and the required-file byte comparisons. The extracted artifact passed a separate runtime check.
- Seven deliberately broken copies were rejected: a malformed manifest field, a wrong host peer range, a missing packed helper, a missing theme token, wildcard exposure of an unused skill, a throwing factory, and a nonterminating factory. The hanging-factory test exposed a termination weakness; the worker now uses a hard deadline signal, and that failure path was rerun successfully.
- The tool runner uses public Pi exports and the real agent loop with in-memory assistant responses. Its checks covered valid output, flags, schema errors, thrown and returned errors, nested invocation, cancellation during execution, subprocess setup, and complete-output comparison.
- A 1 MiB fixture exercised file-based worker input instead of process-argument limits. A fixture that overwrote the expected file was rejected, because the comparison uses the bytes captured before execution.
- Unsupported provider and lifecycle operations produced `incomplete` with exit code 2 instead of passing as expected tool errors. A nonterminating tool produced a failed deadline check. Separate 3-line output checks passed a 3-line ceiling and failed a 2-line ceiling.
- The embedded theme checker passed 115 focused contract assertions covering every required token, the optional tokens, types and unknown keys, color syntax and ranges, shared references, missing references, cycles, and strict versus runtime-reachable validation. These establish syntax and reference validity, not terminal rendering quality.

These are local checks of the authoring tools. Live providers and MCP, terminal and RPC behavior, session restoration, registry publication, git-managed update and removal, and platform compatibility remain separate scenarios in the bundled guide.

### Validation scope correction

A subsequent review found that the procedure leaned on the four-resource example and always requested npm packing. The validator already compared only the supplied inventory keys, but it wrongly failed a locally loadable extensions-only package for missing npm identity, `type: module`, and a gallery keyword, although the package's single extension loaded during that reproduction.

The workflow now selects checks from the requested resources, the implemented capabilities, and the delivery source:

- Absent optional resources are `not_applicable`.
- `--pack` selects the npm identity and artifact checks, and the module and gallery recommendations do not fail the package.
- The bundled extensions-only inventory explicitly expects no skills, prompts, or themes.
- An extension with only commands does not require tool tests.

With the same Pi `1.2.0` and Node `v24.14.0`, separate extensions-only, skills-only, prompts-only, themes-only, commands-only, and conventionally discovered local packages without `package.json` all passed. An npm extension package without the gallery keyword or module declaration passed with recommendations, and the four-resource starter stayed valid. A missing declared extension, unintended skill exposure through wildcard filters, and missing npm identity when packing were still rejected. These checks covered resource loading, selection boundaries, and the applicable packaging assertions; they did not establish handler, UI, or service behavior that was not run.

### Source review corrections

A 2026-10-15 review compared the bundle with the source at commit `b06c1f2cf1dea6af8748ddeee18c23587d2cb7c6` and corrected the following:

- `reachesTools` must return words that contain the `mcp__<server>` namespace; a bare server name made the MCP extension skip waiting.
- Startup failures now include registration errors thrown in the factory, such as MCP server name conflicts, and provider registrations validated after all factories finish. `user_bash` errors block like `tool_call` errors, and `skipConversationRestore` is documented as unread.
- Packaging and operations now cover the local-only root `index.ts` fallback, the role of `version`, the package's own lifecycle scripts, the base directory for project-relative paths, project trust for `update` and `-a`, the rejection of `--offline`, and the misleading `Updated` message for pinned entries.
- Resources now cover frontmatter starting on the first line, the order in which local resources beat package resources, traversal exclusions, prompt YAML quoting, built-in interactive command names, theme discovery depth, and reserved theme names.
- The output helper keeps a byte-bounded prefix for an oversized first line and accepts `"tail"` for logs. The package validator reports the implicit package-directory extension and rejects reserved theme names. The tool runner reports a case process that stays alive after shutdown as a lingering-handle failure while keeping its observations.

With installed Pi `1.2.0` and Node `v24.14.0`, the starter still passed the package validator with `--runtime --pack`, the extracted-artifact rerun, and its tool cases, and the earlier broken copies were still rejected. Two separate cases, a package whose only extension is a root `index.ts` and a theme named `system`, now each fail with dedicated messages, and an unreleased `session_start` timer fails in about 3 seconds instead of at the 20-second deadline. The helper passed many-line head and tail, single Unicode line head and tail, small-output, thrown-error, and cancellation cases, and it type-checked against the commit's source types with TypeScript 5.8.3. Interactive CLI behavior, live MCP waiting, and provider registration failures were verified by reading the source only.

### Latest-source compatibility update (2026-10-21)

A fresh clone of `earendil-works/pi` at `cae9fd28a2d3d515c83ea495093e3768cc8efab6` was compared with the previous baseline. The package manager, manifest/filtering code, extension types and runner, resource loader, skill and prompt parsers, theme schema/tokens/color resolver, and the SDK exports used by the bundled checks were unchanged. Their contracts were retained rather than replaced with conflicting high-level documentation.

The changed contracts were traced through their consumers:

- `core/extensions/loader.ts` and `core/extensions/virtual-modules.ts`: Node aliases and bundled mappings for the public `/models` entry point.
- Pi AI's `packages/ai/src/types.ts`, `packages/ai/src/models.ts`, `packages/ai/src/utils/identity.ts`, `packages/ai/src/api/`, and `packages/ai/src/telemetry.ts`, together with coding-agent `core/sdk.ts`, `core/client-identity.ts`, and `core/model-runtime.ts`: identity precedence, header suppression, telemetry spans, and the later application of API identity defaults.
- `modes/interactive/interactive-mode.ts`: editor-slot dialog stacking and completion of the correct custom overlay.
- `extensions/codemode/execute.ts`: shared capacity, FIFO admission, cancellation, and deadlines that include the wait.
- `extensions/mcp/config.ts`: BOM handling on both read and edit.

Source paths above are under `packages/coding-agent/src/` unless explicitly qualified. These are maintenance evidence, not additional reading requirements for package authors.

**Runtime preparation:** Node `v24.14.0`; `npm ci --ignore-scripts`; the required SDK workspaces built from the cloned source. The initial offline AI build stopped because generated model JSON was absent. Running the repository's `npm run hydrate:model-data` resolved that prerequisite, after which the AI, agent, and unbundled coding-agent builds passed. The source checkout had no tracked or untracked changes afterward; generated model data and build output are ignored. The installed release was checked separately, not substituted for the source build.

**Checks actually run:**

| Check | Result |
|---|---|
| Starter `validate-package.mjs --expect ... --runtime --pack`, using the source SDK and then installed `1.3.0` | Both passed: 77 passing assertions, no failed assertions |
| Runtime validation of each actual extracted npm artifact | Both passed: 55 passing assertions, no failed assertions |
| Existing `starter-cases.json`, on the starter and each extracted artifact, against both SDKs | All four runs passed all 3 cases: session cwd, compact flag/details, and non-object input rejection |
| Existing Pi AI identity and telemetry regressions | 3 files, 35 tests passed |
| Existing coding-agent SDK identity, codemode admission, dialog/overlay, MCP, prompt, and `/models` mapping regressions | 7 files, 179 tests passed |
| Pi's skill parser on this skill | One skill loaded, no diagnostics |
| Package-local Markdown file links and script syntax | No missing linked files; all 4 `.mjs` files passed `node --check` |
| Patch whitespace | `git diff --check` passed |

The upstream regression commands, from the respective package directories, were:

```bash
# packages/ai
npm exec -- vitest run test/identity.test.ts test/telemetry-options.test.ts test/telemetry.test.ts

# packages/coding-agent
npm exec -- vitest run test/sdk-client-identity.test.ts test/codemode-worker-admission.test.ts test/interactive-mode-extension-dialogs.test.ts test/interactive-mode-status.test.ts test/mcp-extension.test.ts test/prompt-templates.test.ts test/suite/regressions/11156-pi-ai-models-virtual-module.test.ts
```

The validator deliberately leaves semantic import/bundle inspection as `skipped`; its archive report also requests a separate extracted-artifact run, which was completed here. No new evaluation cases were added. The older deliberately broken package fixtures were not rerun in this update. Upstream UI tests use controlled components and do not establish physical terminal rendering. Live provider authentication, remote MCP services, registry publication, git-managed updates/removal, cross-platform behavior, and model-based skill effectiveness were not verified by this update.

### Released `v1.4.0` update (2026-10-22)

The `v1.4.0` tag resolves to `4a080252f06caf63a525d7873c5d94d3c23887e0`, seven commits after the previous `cae9fd28a` baseline. The tag includes every formerly post-`v1.3.0` boundary listed above. No later `main` changes were included.

The source comparison added four author-facing contracts:

- System One classifier image encoding and opt-in headers, from `packages/ai/src/api/system-one-shared.ts` and its TypeSafe/Workers AI adapters. Public classifier types, `compat-schema.ts`, and coding-agent `core/provider-composer.ts` establish how extension model metadata and provider-level `models.json` overrides reach those encoders.
- Resume and tree-navigation activation from `core/agent-session.ts`: branch additions/removals, eligible unmentioned extension tools, pending registration, startup selection precedence, and allowlist/exclusion boundaries.
- Recovery keeps omitted assistant/tool-result pairs together instead of replaying orphaned results, including after session resume.
- Built-in grep uses `--no-config`, preserving its declared search semantics against ambient ripgrep configuration.

Coding-agent source paths above are under `packages/coding-agent/src/`. Package discovery, extension loading/types, skill and prompt parsers, UI/codemode/MCP implementations, theme contracts, truncation helpers, and the SDK exports used by the bundled validators were unchanged from the previous baseline. Their existing contracts and executable examples were retained.

**Validation environment:** Node `v24.14.0`; SDK built directly from the `v1.4.0` checkout with `npm ci --ignore-scripts`, `npm run hydrate:model-data`, and the required workspace builds, ending with coding-agent `build:unbundled`. Generated model data and build output stayed ignored; the source checkout remained clean. These results use that source-built `1.4.0` SDK, not the separately installed `1.3.0` SDK or an assumed registry installation.

| Check | Result |
|---|---|
| Starter package validator with `--expect`, `--runtime`, and `--pack` | 77 assertions passed; no failures |
| Runtime validation of the actual extracted npm artifact | 55 assertions passed; no failures |
| Existing starter tool cases on source and extracted artifact | Both runs passed all 3 cases, including invalid-input rejection |
| TypeSafe and Workers AI System One regressions | 2 files, 29 tests passed |
| Classifier runtime, default tool selection/restoration, and recovery-pair regressions | 3 files, 24 tests passed |
| `tools.test.ts -t RIPGREP_CONFIG_PATH` | Selected regression passed; 85 unrelated tests were intentionally not run |
| Skill parser, internal links, and script syntax | One skill loaded without diagnostics; 58 linked file references resolved; all 4 `.mjs` files passed `node --check` |
| Patch whitespace | `git diff --check` passed |

The upstream regression commands were:

```bash
# packages/ai
npm exec -- vitest run test/typesafe-system-one.test.ts test/cloudflare-workers-ai-system-one.test.ts

# packages/coding-agent
npm exec -- vitest run test/model-runtime-classifiers.test.ts test/default-tools-setting.test.ts test/suite/regressions/11227-recovery-omits-tool-results.test.ts
npm exec -- vitest run test/tools.test.ts -t RIPGREP_CONFIG_PATH
```

The 54 selected upstream tests use controlled requests or local fixtures; no live classifier service was called. Package reports still mark semantic import/bundle inspection as `skipped`; the archive report's separate extracted-artifact checks were completed as recorded above. No new test cases were added, and the earlier deliberately broken package fixtures were not rerun. Physical terminal rendering, live authentication/MCP/classifier services, published-package installation, git update/removal, other operating systems, independent model review, and model-based skill effectiveness remain unverified for this update.
