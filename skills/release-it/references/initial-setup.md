# Initial Setup Guide

Analyze the project and resolve decisions needed for its release configuration, then generate the entry script, Inquirer adapter, and target config from [interactive-workflow.md](interactive-workflow.md). Setup questions are separate from runtime questions: the first runtime question is version selection for a single project, or selection of one service app for a monorepo. Do not add a runtime start confirmation.

## Flow: Analyze → Propose → Confirm

```
1. Analyze project files silently
2. Propose inferred config choices to user
3. Ask about decisions that require user input
4. Generate tailored config + supporting files
```

---

## Step 1: Analyze the Project

Read these files/directories to infer project context. Each file provides specific signals:

| Source | What to Read | What It Tells You |
|--------|-------------|-------------------|
| `package.json` | `name`, `private`, `scripts`, `workspaces`, `publishConfig` | Scoped package? npm publish needed? Existing build/test/lint? Monorepo? |
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
| No `package.json` at all | Non-Node project | `npm: false`, use `@release-it/bumper` plugin |
| Remote is `github.com` | GitHub platform is available | Enable `github.release` only if requested |
| Remote is `gitlab.com` or self-hosted GitLab | GitLab platform is available | Enable `gitlab.release` only if requested |
| `workspaces` field exists | Monorepo | Identify service apps; generate a one-app target manifest |
| Scoped name (`@scope/pkg`) + not private | Scoped public package | Remind: `publishConfig.access: "public"` needed |
| `scripts.test` exists | Has test suite | Suggest `hooks.before:init: "npm test"` |
| `scripts.lint` exists | Has linter | Suggest `hooks.before:init` includes lint |
| `scripts.build` exists | Has build step | Suggest `hooks.after:bump: "npm run build"` |
| `CHANGELOG.md` exists with Keep-a-Changelog format | Uses KAC convention | Suggest `@release-it/keep-a-changelog` |
| `CHANGELOG.md` exists or doesn't exist | General case | Suggest `@release-it/conventional-changelog` |
| `.github/workflows/` exists | Uses GitHub Actions | Preserve existing CI; create release automation only if requested |

### If an existing release-it config is found

Read the existing config and preserve relevant target settings while adding the requested interactive entry point. Check mode flags, version providers, hooks, and plugin actions against the interactive contract. Resolve conflicting requested publishing or bulk-workspace behavior during setup; do not silently enable those operations or add a runtime confirmation gate.

---

## Step 2: Propose Inferred Choices

Present the analysis results to the user. Group by confidence:

**Determined from project** (explain reasoning):
- "Your project uses GitHub; the base flow ends with Git push. Hosted release creation is optional."
- "package.json has `private: true`, so I'll skip npm publishing"
- "You have `scripts.test` and `scripts.lint`, so I'll add pre-release checks"

**Needs your decision** (present with recommendations):
- Questions from Step 3 below

Use a format like:
```
Based on your project analysis:
- Platform: GitHub → Git remote identified; hosted release only if requested
- npm publish: No (private: true)
- Pre-release hooks: npm run lint + npm test (found in scripts)
- Build hook: npm run build (found in scripts)

I need a few decisions from you to finalize the config:
1. ...
2. ...
```

---

## Step 3: Ask the User

These decisions cannot be inferred — ask the user. Provide a recommended default for each.

### Required Questions

| Question | Options | Recommended Default | Why Ask |
|----------|---------|---------------------|---------|
| Config format | JSON / TS / YAML / TOML / package.json | JSON (with `$schema`) | JSON is most common, $schema gives IDE autocomplete |
| Changelog strategy | conventional-changelog / keep-a-changelog / git-cliff / none | conventional-changelog | Generates history; its recommended bump never replaces the runtime version choice |
| Release branch restriction | `main` only / `main` + `release/*` / none | `main` only | Prevents accidental releases from feature branches |

### Conditional Questions (ask only if relevant)

| Condition | Question | Recommended Default |
|-----------|----------|---------------------|
| npm publish enabled | Dist-tag strategy for pre-releases? | Auto (derived from pre-release id) |
| Any project | Need pre-release workflow (alpha/beta/rc)? | No (can be added later via CLI flags) |
| CI automation requested | Which trigger and explicit version input should it use? | Separate CI command |
| Monorepo service boundary unclear | Which directories are deployable service apps? | One verified service app per release |
| Has build script | Attach build artifacts to release? | No (user usually knows if they want this) |

### What NOT to Ask

These have clear best practices — just apply them:
- `$schema` URL → always include in JSON format
- `git.commitMessage` → use `"chore: release v${version}"` (Conventional Commits)
- Require a clean repository/index; the interactive wrapper performs that check itself
  and overrides `git.requireCleanWorkingDir` to prevent exit rollback after a deliberate stop
- `git.requireUpstream` → `true` (safe default)
- Keep built-in `git.commit`, `git.tag`, and `git.push` enabled; inspect tag transfer scope in [git-integration.md](git-integration.md)
- `GITHUB_TOKEN` / `GITLAB_TOKEN` → standard env var name

---

## Step 4: Generate Config

Based on analysis + user answers, generate these files:

### Always generate

1. **Release config file** (user's chosen format, default `.release-it.json`)
   - Always include `$schema` if JSON format
   - Only override options that differ from defaults
   - Include plugin config if changelog strategy was chosen

2. **package.json scripts** (add or suggest)
   ```json
   {
     "scripts": {
       "release": "node scripts/release.mjs"
     }
   }
   ```

Copy `scripts/release.mjs` and `scripts/release-prompts.mjs` from [interactive-workflow.md](interactive-workflow.md). For a monorepo, also generate `.release-targets.json` and one config per service app using [monorepo.md](monorepo.md).

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

5. **Dependencies** — remind user to install:
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
version sources, adapt the interactive version reader and pre-bump guard together.

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
  "$schema": "https://unpkg.com/release-it@20/schema/release-it.json",
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

### Non-Node Version Provider (adapt the interactive reader and guard)

```json
{
  "$schema": "https://unpkg.com/release-it@20/schema/release-it.json",
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
