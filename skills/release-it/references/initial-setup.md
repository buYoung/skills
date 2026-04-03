# Initial Setup Guide

When a user asks to set up release-it for their project, do NOT generate config files immediately. Follow this 3-step flow to produce a config that actually fits their project.

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
| Remote is `github.com` | GitHub platform | `github.release: true` |
| Remote is `gitlab.com` or self-hosted GitLab | GitLab platform | `gitlab.release: true` |
| `workspaces` field exists | Monorepo | Suggest workspace release strategy |
| Scoped name (`@scope/pkg`) + not private | Scoped public package | Remind: `publishConfig.access: "public"` needed |
| `scripts.test` exists | Has test suite | Suggest `hooks.before:init: "npm test"` |
| `scripts.lint` exists | Has linter | Suggest `hooks.before:init` includes lint |
| `scripts.build` exists | Has build step | Suggest `hooks.after:bump: "npm run build"` |
| `CHANGELOG.md` exists with Keep-a-Changelog format | Uses KAC convention | Suggest `@release-it/keep-a-changelog` |
| `CHANGELOG.md` exists or doesn't exist | General case | Suggest `@release-it/conventional-changelog` |
| `.github/workflows/` exists | Uses GitHub Actions | Offer to create release workflow |

### If an existing release-it config is found

Stop the initial setup flow. Instead:
1. Read the existing config
2. Ask: "I found an existing release-it config. Would you like me to review and improve it, or start fresh?"
3. If improving, switch to the configuration modification workflow

---

## Step 2: Propose Inferred Choices

Present the analysis results to the user. Group by confidence:

**Determined from project** (explain reasoning):
- "Your project is on GitHub, so I'll enable GitHub Releases (`github.release: true`)"
- "package.json has `private: true`, so I'll skip npm publishing"
- "You have `scripts.test` and `scripts.lint`, so I'll add pre-release checks"

**Needs your decision** (present with recommendations):
- Questions from Step 3 below

Use a format like:
```
Based on your project analysis:
- Platform: GitHub → github.release: true
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
| Changelog strategy | conventional-changelog / keep-a-changelog / git-cliff / none | conventional-changelog | Auto-determines bump type from commit messages |
| Release branch restriction | `main` only / `main` + `release/*` / none | `main` only | Prevents accidental releases from feature branches |

### Conditional Questions (ask only if relevant)

| Condition | Question | Recommended Default |
|-----------|----------|---------------------|
| npm publish enabled | Dist-tag strategy for pre-releases? | Auto (derived from pre-release id) |
| Any project | Need pre-release workflow (alpha/beta/rc)? | No (can be added later via CLI flags) |
| GitHub Actions available | Generate CI release workflow? | Yes |
| Monorepo detected | Release strategy: all packages same version, or independent? | Same version with `@release-it/bumper` |
| Has build script | Attach build artifacts to release? | No (user usually knows if they want this) |

### What NOT to Ask

These have clear best practices — just apply them:
- `$schema` URL → always include in JSON format
- `git.commitMessage` → use `"chore: release v${version}"` (Conventional Commits)
- `git.requireCleanWorkingDir` → `true` (safe default)
- `git.requireUpstream` → `true` (safe default)
- `git.pushArgs` → `["--follow-tags"]` (default, keep it)
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
       "release": "release-it",
       "release:dry": "release-it --dry-run"
     }
   }
   ```

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
   npm install -D release-it
   # If changelog plugin selected:
   npm install -D @release-it/conventional-changelog
   ```

---

## Decision Trees

### npm Publishing

```
package.json exists?
├─ No → npm: false, suggest @release-it/bumper for version file
└─ Yes
   └─ private: true?
      ├─ Yes → npm.publish: false
      └─ No → npm.publish: true
            └─ Scoped (@scope/name)?
               ├─ Yes → Remind: publishConfig.access: "public" in package.json
               └─ No → Default config OK
```

### Release Platform

```
Git remote host?
├─ github.com → github.release: true, suggest GitHub Actions workflow
├─ gitlab.com → gitlab.release: true, suggest .gitlab-ci.yml
├─ Self-hosted → Ask which platform, configure host/origin
└─ Unknown → Ask user which release platform to use
```

### Changelog Strategy

```
CHANGELOG.md exists?
├─ Yes → Check format
│  ├─ Has "## [Unreleased]" → suggest @release-it/keep-a-changelog
│  └─ Other format → suggest @release-it/conventional-changelog with infile
└─ No → Suggest @release-it/conventional-changelog (most popular)
```

### Monorepo

```
Monorepo detected (workspaces/lerna/nx)?
├─ Yes
│  ├─ All packages same version? → Root-based release with @release-it/bumper
│  └─ Independent versions? → Per-package release-it config, git: false per workspace
└─ No → Standard single-package config
```

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

```json
{
  "$schema": "https://unpkg.com/release-it@20/schema/release-it.json",
  "git": {
    "commitMessage": "chore: release v${version}",
    "requireBranch": "main"
  },
  "npm": {
    "publish": false
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

### Non-Node Project (no package.json)

```json
{
  "$schema": "https://unpkg.com/release-it@20/schema/release-it.json",
  "npm": false,
  "git": {
    "commitMessage": "chore: release v${version}",
    "requireBranch": "main"
  },
  "github": {
    "release": true
  },
  "plugins": {
    "@release-it/bumper": {
      "in": "VERSION",
      "out": "VERSION"
    }
  }
}
```
