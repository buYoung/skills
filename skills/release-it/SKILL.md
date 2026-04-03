---
name: release-it
description: >-
  release-it configuration, setup, and plugin development. Triggers on .release-it.* config files,
  release-it CLI usage, version bumping, changelog generation, npm publishing, GitHub/GitLab releases,
  git tagging, hooks lifecycle, pre-release workflows, CI/CD pipelines, monorepo strategies,
  and custom plugin development.
---

# release-it Release Automation

release-it is a generic, pluggable CLI tool that automates versioning and package publishing.
It handles version bumping, Git committing/tagging/pushing, npm publishing, and GitHub/GitLab
release creation -- all in a single configurable workflow. Language-agnostic with a powerful
plugin system for extending behavior.

## Quick Start

```bash
npm install -D release-it

# Create minimal config
echo '{ "github": { "release": true } }' > .release-it.json

# First release (interactive)
npx release-it

# CI release
npx release-it --ci
```

For first-time setup with project-aware configuration, follow [initial-setup.md](references/initial-setup.md).

## Capability Index

Read the reference file that matches your task:

| Reference | When to Read |
|-----------|-------------|
| [initial-setup.md](references/initial-setup.md) | First-time setup. Analyze project → propose config → ask user for decisions → generate tailored config |
| [configuration.md](references/configuration.md) | Setting up or modifying `.release-it.*` config in any format, config extends/merging, CLI overrides |
| [hooks-and-lifecycle.md](references/hooks-and-lifecycle.md) | Adding pre/post release commands, understanding execution order, template variables |
| [cli-and-workflow.md](references/cli-and-workflow.md) | CLI flags, increment types, pre-release flow, dry-run, CI mode, programmatic API |
| [git-integration.md](references/git-integration.md) | Tag naming/matching, changelog command, commit messages, branch restrictions, push config |
| [npm-publishing.md](references/npm-publishing.md) | npm auth, scoped packages, dist-tags, OTP/2FA, OIDC Trusted Publishing, monorepo, private registry |
| [github-gitlab-releases.md](references/github-gitlab-releases.md) | GitHub/GitLab release creation, tokens, assets, release notes, comments, draft/pre-release |
| [plugins.md](references/plugins.md) | Setting up official/community plugins (conventional-changelog, bumper, keep-a-changelog, etc.) |
| [custom-plugin-development.md](references/custom-plugin-development.md) | Building a custom release-it plugin from scratch, Plugin class API reference |
| [troubleshooting.md](references/troubleshooting.md) | Debugging release failures, auth errors, CI issues, common error messages |

## Config Formats Overview

release-it supports 6 config file formats. Pick one:

| Format | File | Notes |
|--------|------|-------|
| JSON | `.release-it.json` | Most common. Supports `$schema` for IDE autocomplete |
| TypeScript | `.release-it.ts` | Type hints via `satisfies Config` |
| JS/CJS | `.release-it.js` / `.release-it.cjs` | Dynamic config, functions for `releaseNotes` |
| YAML | `.release-it.yaml` / `.release-it.yml` | Compact syntax |
| TOML | `.release-it.toml` | Table-based config |
| package.json | `"release-it": {}` property | Zero extra files |

JSON schema: `"$schema": "https://unpkg.com/release-it@20/schema/release-it.json"`

Only override options that differ from defaults. See [configuration.md](references/configuration.md) for all defaults and the `extends` mechanism.

## Common Workflows

**Initial setup**: [initial-setup.md](references/initial-setup.md) — analyzes project, proposes config, asks for decisions

**Add changelog generation**: [plugins.md](references/plugins.md) → conventional-changelog or keep-a-changelog section

**CI/CD pipeline (GitHub Actions)**: [cli-and-workflow.md](references/cli-and-workflow.md) → CI mode + [npm-publishing.md](references/npm-publishing.md) → authentication

**Pre-release (alpha/beta/rc)**: [cli-and-workflow.md](references/cli-and-workflow.md) → pre-release workflow

**Custom release steps**: [hooks-and-lifecycle.md](references/hooks-and-lifecycle.md) → hook configuration

**Monorepo**: [npm-publishing.md](references/npm-publishing.md) → monorepo section + [plugins.md](references/plugins.md) → workspaces/bumper

**Something broke**: [troubleshooting.md](references/troubleshooting.md)

**Build a plugin**: [custom-plugin-development.md](references/custom-plugin-development.md)

## Key Concepts

- **Increment types**: `major`, `minor`, `patch` (semver), `premajor`/`preminor`/`prepatch`/`prerelease` (pre-release)
- **Dry-run** (`--dry-run`): Shows what would execute without side effects. `$` = read-only (runs), `!` = write (skipped)
- **CI mode** (`--ci`): Non-interactive, auto-detected in CI environments. No prompts, uses spinners instead
- **npm dist-tags**: `latest` (default), `next`, `beta`, `alpha` -- controls what `npm install` resolves to
- **Plugin lifecycle**: `init` → `getName` → `getLatestVersion` → `beforeBump` → `bump` → `beforeRelease` → `release` → `afterRelease`
- **Hooks**: Shell commands run at lifecycle points (`before:init`, `after:bump`, `after:release`, etc.)
- **Template variables**: `${version}`, `${latestVersion}`, `${tagName}`, `${changelog}`, `${name}` -- available in config strings
- **Config precedence**: CLI args > config file > `extends` base > built-in defaults
