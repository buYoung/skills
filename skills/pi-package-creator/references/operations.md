# Installation, updates, and troubleshooting

Read this before delivery. It explains how to write install sources and commands that Pi recognizes, how scope and project trust affect them, how updates treat pins and git checkouts, how to run Pi in an isolated environment, and where to look when a package misbehaves. The behavior described here matches the Pi revision recorded in [evidence](evidence.md).

## Write install sources Pi recognizes

| Source | Correct example |
|---|---|
| Exact npm version | `npm:@example/pi-workspace-kit@0.1.0` |
| npm range | `npm:@example/pi-workspace-kit@^0.1.0` |
| Git HTTPS shorthand | `git:github.com/example/pi-workspace-kit@v0.1.0` |
| Git SCP-style SSH | `git:git@github.com:example/pi-workspace-kit@v0.1.0` |
| Explicit URL | `https://github.com/example/pi-workspace-kit` |
| Local directory | `./pi-workspace-kit` or an absolute path |
| Local extension file | `./extension.ts` |

- Use `npm:` for registry packages. Pi reads `github:user/repo`, bare `git@github.com:user/repo`, `user/repo`, and bare npm names as **local paths**.
- Write refs as `git:...@ref`. Avoid ambiguous shorthand and `#ref`.
- A bare `git://...` URL can be misparsed; use the supported HTTPS or SSH forms.

### Relative and local paths

- A relative path passed on the CLI resolves from the working directory.
- A relative path stored in settings resolves from its scope's configuration directory, not from the project root: the personal agent directory (`~/.pi/agent`, or `PI_CODING_AGENT_DIR`) or the project's `<cwd>/.pi`. A project entry `"./tools/x"` therefore means `<cwd>/.pi/tools/x`.
- Absolute paths remove this ambiguity during validation.
- Pi references a local source in place. It does not copy the directory or install its dependencies.

## Scope, trust, and package identity

### Where declarations live

Personal package declarations live in `~/.pi/agent/settings.json`, and `PI_CODING_AGENT_DIR` changes that personal agent directory. Project declarations live in `<project>/.pi/settings.json`; use `-l` with `install` and `remove` for project scope.

### Project trust

Project resources load only after the project is trusted. Inspect a project's declarations before granting trust: packages run code with the Pi process's access, and installing a package can run the lifecycle scripts of the package and its dependencies. Trust is not a filesystem, subprocess, network, or credential sandbox.

Personal extensions can load before the trust decision, including during some package commands. A `project_trust` handler must therefore come from a personal extension; a project extension loads too late. Do not use package startup to grant project trust silently.

Package commands handle trust differently from interactive startup:

- `pi install -l`, `pi remove -l`, and `pi config -l` need a trusted project. When there is no terminal to ask, they stop with `Project is not trusted. Use --approve ...`. Add `-a`/`--approve` to trust the project for that run.
- `pi update` uses only a saved trust decision or `-a`. In a project trusted another way (`defaultProjectTrust`, a `project_trust` handler, or a session-only answer), it reads no project settings. It skips project packages but still prints `Updated packages`, and `pi update <source>` for a project-only package fails with `No matching package found`. Use `-a` when updating project packages.

### Package identity

Pi identifies a package without its npm version or git ref:

- npm: the package name.
- git: the normalized repository URL without the ref.
- local: the resolved absolute path for the scope.

A normal project entry overrides the personal entry for the same package. A project entry with `autoload: false` acts as a filter delta instead. Installing two versions of the same identity does not create two independent packages.

## Commands for authors and users

Run these from the parent directory of a local package. Run only the install or remove variant for the intended scope; each line is a separate action, and the block is not one setup procedure.

```bash
pi -e ./pi-workspace-kit
pi install ./pi-workspace-kit
pi install ./pi-workspace-kit -l
pi list
pi config
pi config -l
pi remove ./pi-workspace-kit
pi remove ./pi-workspace-kit -l
```

- `-e` loads the package for one invocation without adding settings. With an npm or git source, `-e` can still download and install packages, so do not describe it as network-free or free of side effects.
- `pi remove` removes managed npm and git files as well as the declaration. It does not delete a local source directory.

| Goal | Command |
|---|---|
| Update Pi itself | `pi update` |
| Reconcile all package installations | `pi update --extensions` |
| Update a configured package identity | `pi update npm:@example/pi-workspace-kit` |
| Update packages and Pi | `pi update --all` |
| Change an exact npm pin | `pi install npm:@example/pi-workspace-kit@0.2.0` |
| Change a git ref | `pi install git:github.com/example/pi-workspace-kit@v0.2.0` |

- Keep `-l` when you change a project pin through `install`.
- `update` and `list` do not accept `-l`; `config` has its own scope parser.
- `pi install --force` is invalid. The package commands `install`, `remove`, `update`, and `list` reject `--offline`; set `PI_OFFLINE=1` instead.

### Pins and updates

**Never store persistent state, user settings, or irreplaceable work inside an installed package checkout.** When a managed git update moves to a different commit, Pi runs `reset --hard` and `clean -fdx`, which can remove even ignored files. Cleanup can also resume after an incomplete update.

- **npm:** an exact semver spec is pinned; ranges and dist-tags are not. Update skips a pinned npm entry but still prints `Updated <source>`, so that message does not prove a change.
- **git:** package update can fetch every git source. Any configured ref suppresses update notifications, but a branch ref can still advance to the branch's new commit. A branch name is not an immutable release pin.
- `pi update <source>` selects an existing identity and uses its saved source. Putting a new version in that argument does not migrate a pin; use `pi install` with the new version or ref.

### Offline mode

`PI_OFFLINE=1` suppresses automatic resolution downloads and package update work. It is not a security boundary: explicit `pi install` and `pi remove` do not check it, and extension code can still reach the network. An update success message printed while offline does not prove that anything was downloaded.

## Run Pi in an isolated environment

[Validation](validation.md) has the complete post-creation workflow: package checks, the tool-case format, artifact verification, and expected results. This section sets up the interactive environment that workflow uses.

### Load the package in isolation

Create a temporary workspace and agent directory outside the development checkout. A POSIX example:

```bash
package_dir="/absolute/path/to/pi-workspace-kit"
check_dir="$(mktemp -d)"
mkdir -p "$check_dir/agent" "$check_dir/work"
cd "$check_dir/work"
PI_CODING_AGENT_DIR="$check_dir/agent" PI_OFFLINE=1 \
  pi --no-skills --no-prompt-templates --no-themes --no-context-files \
  -e "$package_dir"
```

Replace the absolute path before running, and keep the directory until you finish inspecting it.

- The separate agent directory isolates personal settings and extensions, but it does not by itself suppress shared `~/.agents/skills` discovery. The flags suppress automatic skills, prompts, themes, and context files.
- Resources passed explicitly through `-e` still load, and built-in extension services stay available.
- This isolates resource discovery, not processes or network access.

If the package has third-party runtime dependencies, install them locally in the package before loading it. A starter with only host peers needs no separate copy of Pi. To install development dependencies with npm without auto-installing unneeded peers, run `npm install --ignore-scripts --legacy-peer-deps`. A package with essential native build scripts needs its documented setup instead.

Expect these observations for the resources and capabilities the package actually provides. An absent optional type is not an error.

- No extension factory or load errors.
- No `[Extension issues]`, `[Skill conflicts]`, `[Prompt conflicts]`, or `[Theme conflicts]` caused by the package.
- Public names appear as documented.
- Each tool returns the expected content and details and marks errors correctly.
- A prompt expands representative quoted, empty, and omitted arguments.
- `/skill:<name>` loads the intended skill and its relative references.
- A supplied theme can be selected in `/settings`.

### Check modes and reload

When the package needs a model and model access is configured:

```bash
PI_CODING_AGENT_DIR="$check_dir/agent" PI_OFFLINE=1 \
  pi --no-skills --no-prompt-templates --no-themes --no-context-files \
  -e "$package_dir" -p "Use acme_workspace_info to describe this workspace."
```

Substitute the actual feature. This command calls a model, and an empty isolated agent directory may have no authentication; report that limit instead of claiming the tool ran. For RPC-facing features, also exercise RPC. `ctx.hasUI` alone does not mean a TUI is available.

In the interactive session:

1. Exercise a feature.
2. Run `/reload`.
3. Exercise it again.
4. If the feature creates watchers, timers, processes, or session state, confirm that handles are not duplicated, state is restored correctly, and no old context is reused. A stateless feature does not need any of these.

Extension errors abort a fresh CLI startup, while `/reload` can report errors and keep the session running, so check both paths. The CLI installs strict theme validation; an SDK resource load alone does not prove that a theme passes it.

### Check filters and scope

In the same disposable agent environment, install the local source and open `pi config`. Toggle one resource off and on. Then launch Pi normally there, without `-e` and without the discovery-suppression flags, to observe the saved selection. Check the package's names and paths separately from unrelated shared skills.

Check string and object entries, a user `[]`, and any project override the package claims to support. Confirm that a toggle does not expose unrelated conventional directories. Do not modify the real personal configuration to test this.

### Check the delivered form

- **npm:** inspect and load the packed artifact.
- **git:** use a clean checkout of the intended ref with production dependencies, and prove that startup needs no development-only compiler and no uncommitted asset.
- A local check does not prove registry installation or git update behavior.
- Loading an extracted artifact or a checkout by path also accepts the local-only root `index.ts` fallback described in [packaging](packaging.md). The package validator reports that layout as a separate failure.

## Troubleshooting

| Symptom | Inspect first |
|---|---|
| Package installs but nothing appears | Empty/malformed `pi`, root `index.ts` without `pi.extensions` or `extensions/`, missing packed paths, wrong source syntax, user filters |
| `Extension does not export a valid factory function` | Helper, test, or declaration file discovered as an extension; missing default factory |
| `Extension runtime not initialized` | Factory calling session-dependent APIs |
| Startup exits with a tool/flag conflict | Duplicate public names across enabled extensions |
| Resource appears after `pi config` | Missing or empty manifest type plus a conventional directory |
| Compiled extension has duplicate classes or state | Bundled host API or physical host runtime dependency |
| Local checkout works; git install fails | Development-only runtime imports, missing generated files, install-time build |
| `/skill:name` exists but the model does not discover it | `disable-model-invocation`, missing read/bash capability, conflicting name |
| Theme seems missing | Theme schema or color diagnostics and name collisions; selection errors can hide the original problem |
| Reload works but startup fails | Reload tolerates extension diagnostics that CLI startup rejects |
| State disappears after update | State written into managed package storage |
| Pinned package does not change | Update uses the saved source; install the new version or ref explicitly |

To recover from a broken extension set, run `pi -ne`, then inspect and disable or repair the offending resource.
