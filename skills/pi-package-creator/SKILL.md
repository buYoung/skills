---
name: pi-package-creator
description: Create, extend, repair, validate, test, and package Pi coding-agent packages (pi packages, pi-packages, Pi 패키지) for local, npm, or git distribution. Use whenever a request involves a package.json pi manifest, Pi extensions or custom tools, bundled SKILL.md files, prompt templates, themes, resource discovery, host-provided dependencies, package collisions, or install/update/reload behavior. Includes a complete starter, self-contained authoring contracts, package checks, and executable tool tests. Not for Raspberry Pi, Python packages, ordinary npm libraries, Pi monorepo internals, or the experimental server plugin system.
---

# Pi Package Creator

Build a directory that Pi can discover, load, and distribute as one package. A Pi package contains any combination of **extensions, skills, prompt templates, and themes**; it does not need all four.

Each of the five steps below names the reference to read before you act. Every contract, example, starter file, and check you need is in this bundle, and its relative links point to included files. Do not send the user to external documentation, the original analysis, or another skill. An installed Pi and Node.js runtime and the package's declared dependencies are prerequisites for running the package and its checks, not documents to read.

## Compatibility

- This bundle targets Pi commit `cae9fd28a2d3d515c83ea495093e3768cc8efab6` (74 commits after `v1.3.0`), not every build reporting `1.3.0`.
- Node.js must satisfy Pi's `>=22.19.0` requirement.
- Record the user's actual Pi version and, when available, its commit. A matching version string alone does not prove that every behavior described here is present.
- Run the bundled checks against the installed Pi. If an API or behavior differs, report the concrete mismatch. Do not invent a newer contract, and do not make reading external documents a completion step.
- Do not mix legacy `@mariozechner/*` examples with current `@earendil-works/*` imports without saying so.

[Evidence and compatibility](references/evidence.md) records the supported Pi revision, observed differences, and limits.

## 1. Decide the package shape

From the request and existing files, determine the package purpose, destination, namespace, intended resources, runtime access, and delivery source (local, npm, or git). Resolve ordinary layout choices yourself. Ask the user only when a missing decision changes the requested behavior, for example whether to replace a built-in tool, contact a remote service, persist shared data, or publish under an account whose identity is unknown.

Choose the smallest set of resources that delivers the feature, and read the matching reference before implementing it:

| Need | Resource | Read before implementing |
|---|---|---|
| Executable tools, commands, flags, events, providers, MCP, UI | Extension | [extensions](references/extensions.md); also [advanced extensions](references/advanced-extensions.md) for events, state, UI, providers, and MCP |
| Instructions and supporting files the model loads on demand | Skill | [resources](references/resources.md), skills section |
| A slash command that expands text with arguments | Prompt template | [resources](references/resources.md), prompts section |
| Terminal colors and HTML export colors | Theme | [resources](references/resources.md), themes section |
| Distribution, dependencies, paths, filtering | Package manifest | [packaging](references/packaging.md), for every package |
| Post-creation checks, behavioral tests, artifact verification | Validation | [validation](references/validation.md), for every package before delivery |
| Install, update, trust, troubleshooting | Delivery | [operations](references/operations.md), for every package before delivery |

**New package:** copy only the requested parts of [the starter](assets/starter/README.md). Its four resource types show independent options, not a minimum shape. In the parts you keep, rename `@example/pi-workspace-kit`, the `acme` prefix, filenames, frontmatter names, tool/command/flag names, and the theme name. Replace the demonstration behavior with the user's feature. Do not add resources only to match the starter or its tests.

**Existing package:** keep its public resource names and source identity unless the requested change requires a migration.

## 2. Set discovery and dependency boundaries

Discovery rules and host-provided dependencies decide whether an installed package loads at all. The full manifest and filter matrix in [packaging](references/packaging.md) is essential reading for this step.

### Manifest

For npm delivery, include `package.json` with a real name and version. A local package can instead use conventional directories without `package.json`, and a `package.json` without a `pi` field also uses conventional discovery. An explicit manifest makes the resource surface reviewable. This is a complete extensions-only example:

```json
{
  "name": "@example/pi-workspace-kit",
  "version": "0.1.0",
  "type": "module",
  "keywords": ["pi-package"],
  "files": ["extensions", "lib"],
  "pi": {
    "extensions": ["./extensions/index.ts"],
    "skills": [],
    "prompts": [],
    "themes": []
  },
  "peerDependencies": {
    "@earendil-works/pi-coding-agent": "*",
    "typebox": "*"
  }
}
```

- `"type": "module"` is an authoring recommendation, and `"pi-package"` is a gallery-discovery keyword. Neither is required for local loading.
- Use `[]` to mark resource types the package does not provide. Omitting a type is also valid when settings filters cannot expose unintended conventional resources.
- A manifest `[]` is not a complete boundary: a settings filter can still expose files in an unused conventional directory. Remove unused resource directories and their `files` entries.
- An empty `"pi": {}` is not equivalent to having no `pi` manifest.

### Extension entry points

- Declare extensions through `pi.extensions` or an `extensions/` directory. A lone root `index.ts` loads only from a local path; npm and git installs of the same files load nothing.
- Declare only real entry points, and keep helper modules outside scanned `extensions/` roots, as the starter does with `extensions/index.ts` plus `lib/`. Otherwise Pi can treat a helper or `.d.ts` file as an extension and fail startup.

### Dependencies

Declare each imported host package in `peerDependencies` with `"*"`, and keep it out of bundles:

- `@earendil-works/pi-ai`
- `@earendil-works/pi-agent-core`
- `@earendil-works/pi-coding-agent`
- `@earendil-works/pi-tui`
- `typebox`

Put other runtime libraries in `dependencies` and development-only tooling in `devDependencies`. Remove unused host peers from a package without extensions. Pi does not install dependencies for local sources; the author installs them. Git installs omit development dependencies, so ship directly loadable TypeScript or prebuilt JavaScript and every required asset.

## 3. Implement the resources

### Extensions

- Export a default factory that accepts `ExtensionAPI`, and register tools, commands, flags, and handlers there. Put work that needs a session in handlers or on first use. Factories also run for package-management commands and help output: an uncaught factory error stops CLI startup, and unbounded initialization can hang it.
- Import from public package entry points, normally the package root.
- A tool runs as `execute(toolCallId, params, signal, onUpdate, ctx)` and returns `content` and `details`. Report failure by throwing or by returning top-level `isError: true`. Preserve cancellation in downstream work by passing the signal through. Read `ctx.cwd`, `ctx.mode`, and `ctx.hasUI` from the current handler's context.
- Give public names a package prefix to avoid collisions.
- Bound model-facing text that grows with repository contents, subprocess output, or service responses before returning it; a timeout alone does not limit result size. Use the complete [bounded-output helper](assets/patterns/bounded-output.ts) and the integration example in [extensions](references/extensions.md).
- When adding persistent resources, implement cleanup and session-state restoration. After `await ctx.reload()`, return immediately.
- `pi.refreshTools()` does not exist; `registerTool()` refreshes runtime tools itself.

[Extensions](references/extensions.md) has complete tool and command contracts, failure handling, and lifecycle patterns. [Advanced extensions](references/advanced-extensions.md) covers event results, session state, UI, and dynamic resources, and [integrations](references/integrations.md) covers providers and MCP.

### Skills, prompts, and themes

- **Skills:** use `<name>/SKILL.md` with valid YAML frontmatter starting on the first line and a nonempty description that says what the skill does and when to use it. Ship supporting files inside the package and reference them relative to the skill directory.
- **Prompts:** use a unique `.md` basename that is not a built-in interactive command, plus a description, a quoted argument hint, and Pi's substitution syntax. A prompt is text, not a shell program.
- **Themes:** start from the complete [theme asset](assets/starter/themes/acme-midnight.json). Keep all 51 required tokens and use only supported keys and colors. Do not name the theme `system`, `dark`, or `light`; the built-in themes hide those names.

[Resources](references/resources.md) gives exact name rules, argument behavior, optional theme tokens, discovery depth, and collision order.

## 4. Verify the package you will ship

Read [validation](references/validation.md), then choose checks from the requested resources, the implemented features, and the delivery source. Extensions-only, skills-only, prompts-only, themes-only, and mixed packages are all valid, and an extension can provide only commands or events without tools. Validate what the package promises: absent optional resources and unused capabilities are `not_applicable`, not errors or incomplete work.

1. Write an inventory of the intended resource paths, public names, helpers, and supporting files. Start from the [extensions-only example](assets/testing/extensions-only-inventory.json) or the [four-resource example](assets/testing/starter-inventory.json) and adapt names and paths. An explicit `[]` asserts that nothing of that kind is intended; an omitted key is not checked. A load that is empty or free of diagnostics does not prove the package is complete.
2. Run the package validator, [validate-package.mjs](scripts/validate-package.mjs), with `--expect` and `--runtime`. Add `--pack` for npm delivery or a requested tarball; a local-only package needs no npm packing. The validator is a structural checker, not a compiler, so also review relevant imports and build output.
3. If the package provides tools, adapt the [tool cases](assets/testing/starter-cases.json) and run the tool runner, [test-tools.mjs](scripts/test-tools.mjs). Choose the success, input-rejection, operational-failure, cancellation, and output-size cases that apply to those tools. Do not invent tools, long-running work, or failure paths to fill a generic checklist.
4. Exercise the commands, prompts, skills, themes, UI, state, providers, and MCP integrations the package actually provides. Check reload and each supported mode where the package's behavior depends on them. The tool runner uses no model and does not prove these behaviors.
5. Check what you deliver. For npm, install needed production dependencies in the extracted copy and repeat the applicable checks. For git, use a clean checkout of the intended ref. For local delivery, check the actual local directory. Do not use development-only files to make a distribution check pass.

Record each applicable check with its command, target Pi version, and evidence, using these statuses:

| Status | Use when |
|---|---|
| `pass` | The check ran and met its expectation |
| `fail` | A contract or expectation was violated |
| `skipped` | A needed check could not run; never count it as a pass |
| `not_applicable` | The resource or feature is outside the package's scope |
| `warning` | A nonblocking recommendation was not followed |

Repair relevant failures and rerun the affected checks. An optional resource does not become a requirement because this skill has a test recipe for it.

## 5. Deliver the package and its verification commands

Deliver the requested resources, required runtime files, `package.json` when the chosen shape needs it, and a README that covers the items that apply:

- Supported Pi version or commit, and runtime prerequisites.
- Exact local, npm, or git install command and the intended scope.
- Public tool, command, flag, skill, prompt, and theme names and their usage.
- Required credentials, subprocesses, network access, and state location.
- Resource selection, reload, update, pin migration, and removal commands.
- A verification section the user can run: the actual working directory, prerequisites, copyable commands, expected results, and report locations.

Put the verification commands in both your final response and the package README; saying that checks passed does not replace them. Follow [the command handoff recipe](references/validation.md#7-give-the-user-verification-commands):

- Use the actual package paths, resource names, and delivered scripts and fixtures.
- Give native Pi CLI checks and the applicable automated checks. Omit tool tests for a package without tools, and npm packing for local-only delivery.
- Separate shell commands from input typed inside Pi, and mark checks that need a model or a service account.

In the final response, state what you actually verified and any remaining environment limits, and separate commands you ran from commands the user should run. Creating a package and publishing it are separate outcomes: deliver a usable local artifact, and publish only when the user asked for publication.

Before calling the task complete, confirm:

- There are no accidental host runtime copies, undeclared imports, startup collisions, missing packed assets, install-time-only builds, or state written into a managed git checkout.
- Every verification command references delivered files and runs from the stated directory.
