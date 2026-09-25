# Initial Setup Guide

Identify whether the request concerns CLI/CI configuration, a programmatic caller, an
interactive service-app command, or a plugin. Analyze the existing entry point, version
source, enabled actions, and release-it version before generating the needed artifacts.
For an interactive service-app command, use [interactive-workflow.md](interactive-workflow.md).
Its first runtime question is version selection for a single project, or selection of one
service app for a monorepo; setup decisions do not add a runtime start confirmation.

## Flow: Analyze → Resolve Missing Decisions → Generate

```
1. Analyze project files silently
2. Preserve explicit requirements and relevant existing choices
3. Ask only about unresolved decisions that affect the requested behavior
4. Generate tailored config + supporting files
```

---

## Step 1: Analyze the Project

Read these files/directories to infer project context. Each file provides specific signals:

| Source | What to Read | What It Tells You |
|--------|-------------|-------------------|
| `package.json` | `name`, `private`, `scripts`, `workspaces`, `publishConfig` | Scoped package? npm publish needed? Existing build/test/lint? Monorepo? |
| Application manifests, version files, tags, configured plugins | Actual current-version source, format, readers and writers | Product versioning may be independent of the Node tooling manifest |
| Installed release-it and plugin manifests | Versions, `engines`, interfaces used by wrappers | Which source behavior and examples apply |
| `git remote -v` or `.git/config` | Remote URL | GitHub vs GitLab vs Bitbucket → which release platform |
| `.release-it.*` or `package.json["release-it"]` | Existing config | Already set up — switch to modification mode, not initial setup |
| `CHANGELOG.md` or `HISTORY.md` | File existence and format | Existing changelog convention → suggest matching plugin |
| `.github/workflows/` | Directory existence | GitHub Actions already in use → offer CI workflow |
| `.gitlab-ci.yml` | File existence | GitLab CI in use → offer GitLab CI config |
| `pnpm-workspace.yaml` / `lerna.json` / `nx.json` | File existence | Monorepo → suggest workspace strategy |
| `.npmrc` | Auth config | Existing registry/auth setup → respect it |
| `tsconfig.json` | File existence | TypeScript project → suggest `.release-it.ts` format option |

### Inference Rules

From the analysis, you can immediately determine these config values:

| Signal | Inference | Config |
|--------|-----------|--------|
| `private: true` in package.json | No npm publish | `npm.publish: false` |
| Version is owned outside `package.json` | Separate version provider | Match that provider; disable npm versioning if it would write an unrelated tooling manifest |
| Remote is `github.com` | GitHub platform is available | Enable `github.release` only if requested |
| Remote is `gitlab.com` or self-hosted GitLab | GitLab platform is available | Enable `gitlab.release` only if requested |
| `workspaces` field exists | Multiple possible release units | Resolve one-app, one-package, or synchronized release scope from the request |
| Scoped name (`@scope/pkg`) + not private | Scoped public package | Remind: `publishConfig.access: "public"` needed |
| `scripts.test` exists | Has test suite | Suggest `hooks.before:init: "npm test"` |
| `scripts.lint` exists | Has linter | Suggest `hooks.before:init` includes lint |
| `scripts.build` exists | Has build step | Suggest `hooks.after:bump: "npm run build"` |
| `CHANGELOG.md` exists with Keep-a-Changelog format | Uses KAC convention | Suggest `@release-it/keep-a-changelog` |
| `CHANGELOG.md` exists or doesn't exist | General case | Suggest `@release-it/conventional-changelog` |
| `.github/workflows/` exists | Uses GitHub Actions | Preserve existing CI; create release automation only if requested |

### If an existing release-it config is found

Read the existing config and entry point. Change only the requested behavior, preserving
relevant version providers, mode flags, hooks, and enabled actions. Add an interactive entry
point only when that workflow is being set up. Resolve incompatible requirements during
setup instead of forcing a CLI/CI or publishing workflow through the Git-only adapter.

---

## Step 2: Propose Inferred Choices

Present the analysis results to the user. Group by confidence:

**Determined from project** (explain reasoning):
- "Your project uses GitHub; the base flow ends with Git push. Hosted release creation is optional."
- "package.json has `private: true`, so I'll skip npm publishing"
- "Existing test/lint scripts are available if release-time checks are part of this request"

**Needs your decision** (present with recommendations):
- Questions from Step 3 below

Use a format like:
```
Based on your project analysis:
- Platform: GitHub → Git remote identified; hosted release only if requested
- npm publish: No (private: true)
- Available checks: npm run lint + npm test
- Available preparation: npm run build; inspect its writes before adding a release hook

I need a few decisions from you to finalize the config:
1. ...
2. ...
```

---

## Step 3: Ask the User

Reuse explicit requirements and compatible existing settings. Ask only when a missing
decision materially changes behavior; use the listed defaults for ordinary unspecified choices.

### Decisions to Resolve

| Question | Options | Recommended Default | Why Ask |
|----------|---------|---------------------|---------|
| Config format | JSON / TS / YAML / TOML / package.json | Existing format, otherwise JSON with `$schema` | Avoid converting a config as part of an unrelated change |
| Changelog strategy | conventional-changelog / keep-a-changelog / git-cliff / none | conventional-changelog | Generates history; its recommended bump never replaces the runtime version choice |
| Release branch restriction | `main` only / `main` + `release/*` / none | `main` only | Prevents accidental releases from feature branches |

### Conditional Questions (ask only if relevant)

| Condition | Question | Recommended Default |
|-----------|----------|---------------------|
| npm publish enabled | Dist-tag strategy for pre-releases? | Auto (derived from pre-release id) |
| Any project | Need pre-release workflow (alpha/beta/rc)? | No (can be added later via CLI flags) |
| CI automation requested | Which trigger and explicit version input should it use? | Separate CI command |
| Monorepo service boundary unclear | Which directories are deployable service apps? | One verified service app per release |
| Cancellation/recovery behavior is being changed | Preserve state, retain built-in recovery, or restore owned changes? | Preserve the existing policy; use [Git recovery criteria](git-integration.md#recovery-policies) |
| Hooks or plugins write beyond the selected target | Which shared outputs belong to this release? | Record the actual write and staging scope before changing checks |
| Has build script | Attach build artifacts to release? | No (user usually knows if they want this) |

### What NOT to Ask

For the interactive service-app workflow, the following defaults are already defined:
- `$schema` URL → always include in JSON format
- `git.commitMessage` → use `"chore: release v${version}"` (Conventional Commits)
- Require clean tracked files and index repository-wide. Derive untracked-file handling
  from the actual writers and staging options; see [git-integration.md](git-integration.md)
- Confirm commit, tag, and push with `default: true`; Enter approves each displayed action
- The packaged wrapper preserves interrupted state and disables built-in local exit
  rollback. Apply a different recovery policy only with its required baseline and ownership checks
- `git.requireUpstream` → `true` (safe default)
- Keep built-in `git.commit`, `git.tag`, and `git.push` enabled; inspect tag transfer scope in [git-integration.md](git-integration.md)
- `GITHUB_TOKEN` / `GITLAB_TOKEN` → standard env var name

---

## Step 4: Generate Config

Based on analysis + user answers, generate these files:

### Generate for the Selected Workflow

1. **Release config file** (user's chosen format, default `.release-it.json`)
   - Always include `$schema` if JSON format
   - Only override options that differ from defaults
   - Include plugin config if changelog strategy was chosen

2. **Entry command** — preserve or adapt the project's runner. For the interactive example:
   ```json
   {
     "scripts": {
       "release": "node scripts/release.mjs"
     }
   }
   ```

For an interactive service-app request, copy and adapt the example modules from
[interactive-workflow.md](interactive-workflow.md). For its monorepo mode, also generate
`.release-targets.json` and app configs using [monorepo.md](monorepo.md). A CLI/CI config edit
or custom plugin request does not require those wrapper files.

### Conditionally generate

3. **GitHub Actions workflow** (if user agreed)
   - Use `workflow_dispatch` trigger with increment input
   - `fetch-depth: 0` for changelog plugins
   - Git user config from `GITHUB_ACTOR`
   - `GITHUB_TOKEN` for GitHub releases
   - `NPM_TOKEN` only if npm publish enabled

4. **CHANGELOG.md** (if changelog plugin selected and file doesn't exist)
   - For conventional-changelog: empty file (plugin will populate)
   - For keep-a-changelog: template with `## [Unreleased]` header

### Suggest installing

5. **Dependencies** — match the chosen workflow, package manager, and runtime. The checked
   interactive example uses this set; retain compatible installed versions for existing work:
   ```bash
   pnpm add -D -E release-it@21.0.1 @inquirer/prompts@8.5.2 semver@7.8.5
   # If changelog plugin selected:
   pnpm add -D -E @release-it/conventional-changelog@12.0.0 conventional-changelog-conventionalcommits@10.4.0
   ```

---

## Decision Trees

### Publishing and Platform

The default service-app flow ends after Git push with `npm.publish: false`,
`github.release: false`, and `gitlab.release: false`. Remote host and package visibility
are context, not instructions to publish. Preserve publishing and CI capabilities when
explicitly requested and use their dedicated references and commands. For non-Node
version sources, follow the [version source contract](plugins.md#version-source-contract)
and adapt every consumer listed in the interactive reference.

### Changelog Strategy

```
CHANGELOG.md exists?
├─ Yes → Check format
│  ├─ Has "## [Unreleased]" → suggest @release-it/keep-a-changelog
│  └─ Other format → suggest @release-it/conventional-changelog with infile
└─ No → Suggest @release-it/conventional-changelog (most popular)
```

### Monorepo

Detect workspace metadata, identify deployable service apps, and configure each app's
version source, changelog path/history, and tag namespace. Generate a single-select menu
from that verified list. Shared libraries and root tooling are not automatically release
targets. Without monorepo metadata, omit the app picker and ask for the version first.
Use bulk or synchronized package release strategies only when explicitly requested.

---

## Config Templates by Project Type

### npm Package (public)

```json
{
  "$schema": "https://unpkg.com/release-it@21.0.1/schema/release-it.json",
  "git": {
    "commitMessage": "chore: release v${version}",
    "requireBranch": "main"
  },
  "npm": {
    "publish": true
  },
  "github": {
    "release": true
  },
  "plugins": {
    "@release-it/conventional-changelog": {
      "preset": "conventionalcommits",
      "infile": "CHANGELOG.md"
    }
  }
}
```

### Private/Internal Package or Application

Use the complete base config and Inquirer entry scripts in
[interactive-workflow.md](interactive-workflow.md). For service apps in a workspace,
apply the target-specific overrides in [monorepo.md](monorepo.md).

### Non-Node Version Provider (adapt all version consumers)

```json
{
  "$schema": "https://unpkg.com/release-it@21.0.1/schema/release-it.json",
  "npm": false,
  "git": {
    "commitMessage": "chore: release v${version}",
    "requireBranch": "main"
  },
  "github": {
    "release": false
  },
  "plugins": {
    "@release-it/bumper": {
      "in": "VERSION",
      "out": "VERSION"
    }
  }
}
```
