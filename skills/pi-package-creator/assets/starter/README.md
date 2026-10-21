# Pi Workspace Kit starter

A complete local Pi package containing one extension, one skill, one prompt, and one theme. It uses no external service or third-party runtime library. The extension reads the session working-directory value without scanning files or writing persistent state.

The design baseline is Pi commit `cae9fd28a2d3d515c83ea495093e3768cc8efab6` (74 commits after `v1.3.0`). Node.js `>=22.19.0` is required. A version string alone does not establish support for every behavior added after that tag.

## Run locally

Copy this entire directory to the desired package location. From its parent:

```bash
pi -e ./pi-workspace-kit
```

Use the actual copied directory name. Host dependencies are supplied by Pi; this starter needs no standalone dependency installation to load through Pi.

| Resource | Invocation |
|---|---|
| Workspace tool | Ask Pi to call `acme_workspace_info` |
| Local command, no model call | `/acme-info` |
| Compact output flag | `pi -e ./pi-workspace-kit --acme-compact` |
| Orientation skill | `/skill:acme-orient` |
| Investigation prompt | `/acme-focus "src" "error handling"` |
| Theme | Select `acme-midnight` in `/settings` |

The skill and prompt need a configured model and file-reading capability to complete an investigation. The tool and command return the current session workspace. The flag changes displayed text while preserving result details.

The prompt supports omitted arguments through defaults. Empty quoted arguments are preserved in `v1.3.0` and at the baseline commit; the older `v1.2.0` release drops them.

## Keep or remove resources

Remove any unneeded resource directory, set the corresponding `pi` field to `[]`, and remove the directory from `files`. Remove the `lib` directory and unused peer declarations if the extension is removed. Do not retain an unused conventional directory for sample files.

Rename the npm package, the `acme` resource prefix, all corresponding filenames, the skill's frontmatter name, and the theme's JSON name. Set real publishing metadata and a license before publishing.

## Install and manage

For a personal local installation:

```bash
pi install ./pi-workspace-kit
pi config
pi remove ./pi-workspace-kit
```

These are separate actions; run removal only when uninstalling. Add `-l` to `install` and `remove` for project scope and use `pi config -l` for project selection. Project resources require project trust.

Run `/reload` after editing. Pi does not automatically reload package extensions or this packaged theme when files change.

After replacing the example identity and publishing, users can install with `pi install npm:<real-name>@<version>` or `pi install git:github.com/<owner>/<repo>@<ref>`. Use `pi update --extensions` to reconcile package installations. To change an exact version/ref, run `pi install` with the new source and preserve `-l` for project scope. An unqualified `pi update` updates Pi itself.

Do not put runtime state in a managed package checkout: git updates may discard modified, untracked, and ignored files.

## Inspect the distributable

From this directory:

```bash
npm pack --dry-run --ignore-scripts --json
```

For this unchanged four-resource starter, the file list must include `extensions/index.ts`, `lib/workspace.ts`, the skill and its output guide, the prompt, and the theme. If you keep only some resources, require only those resources and their supporting files. An extensions-only package needs neither a skill, prompt, nor theme. There are no installation lifecycle scripts or compilation steps.

## Verify the local package yourself

Run this from the package directory with Node.js `>=22.19.0` and the target Pi installed:

```bash
node --version
pi --version
package_dir="$(pwd -P)"
verification_dir="$(mktemp -d)"
mkdir -p "$verification_dir/agent" "$verification_dir/work"
(
  cd "$verification_dir/work" || exit 1
  PI_CODING_AGENT_DIR="$verification_dir/agent" PI_OFFLINE=1 \
    pi --no-skills --no-prompt-templates --no-themes --no-context-files \
    -e "$package_dir"
)
```

Pi should start without load/conflict diagnostics for this package. The command uses temporary settings and does not install the package into your personal configuration; it does not sandbox extension execution.

Enter these commands inside Pi, not in the shell:

```text
/acme-info
/reload
/acme-info
```

Both command invocations should display `work` and the same temporary workspace path. They do not call a model. For this complete starter, also select `acme-midnight` in `/settings` and check that it loads without fallback. The orientation skill and investigation prompt require a configured model to perform their tasks; this isolated settings directory may not have authentication.

These are instructions for you to execute, not a claim that interactive verification already passed on your installation. If adapting the starter to fewer resources, retain only the relevant checks and replace all renamed commands.
