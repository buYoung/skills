# Configuration Reference

## Initial Setup Considerations

Before writing a config file, analyze the project first. See [initial-setup.md](initial-setup.md) for the full setup flow (Analyze → Propose → Confirm).

Key rules for new configs:
- **Always include `$schema`** in JSON configs for IDE autocomplete and validation
- **Only override options that differ from defaults** — release-it has sane defaults, don't repeat them
- **Match the project's convention** — if the repo uses Conventional Commits, set `commitMessage` accordingly
- **Check existing files** — don't create a new config if one already exists in another format

### Quick Reference: Which options to set by project type

| Project Type | Key Options |
|-------------|-------------|
| npm package (public) | `github.release: true`, `npm.publish: true`, changelog plugin |
| Private/internal | `github.release: true`, `npm.publish: false`, changelog plugin |
| Application (no publish) | `github.release: true`, `npm: false` or `npm.publish: false` |
| Non-Node project | `npm: false`, `@release-it/bumper` for version file |
| Monorepo (same version) | Root: `git.requireCleanWorkingDir: false`, workspace: `git: false` |

---

## Config File Formats

release-it looks for config files in the project root in this order:

### JSON (most common)

```json
{
  "$schema": "https://unpkg.com/release-it@20/schema/release-it.json",
  "git": {
    "commitMessage": "chore: release v${version}"
  },
  "github": {
    "release": true
  }
}
```

### TypeScript

```ts
import type { Config } from 'release-it';

export default {
  git: {
    commit: true,
    tag: true,
    push: true
  },
  github: {
    release: true
  },
  npm: {
    publish: true
  }
} satisfies Config;
```

### JavaScript (ESM or CJS)

```js
// .release-it.js (ESM) or .release-it.cjs (CommonJS)
export default {
  github: {
    release: true,
    releaseNotes(context) {
      return context.changelog.split('\n').slice(1).join('\n');
    }
  }
};
```

Use JS/CJS when you need functions (e.g. `releaseNotes` as a function).

### YAML

```yaml
# .release-it.yaml or .release-it.yml
git:
  requireCleanWorkingDir: false
  commitMessage: "chore: release v${version}"
```

### TOML

```toml
# .release-it.toml
[hooks]
"before:init" = "npm test"

[git]
commitMessage = "chore: release v${version}"
```

### package.json

```json
{
  "name": "my-package",
  "devDependencies": {
    "release-it": "*"
  },
  "release-it": {
    "github": {
      "release": true
    }
  }
}
```

## Extending Configuration

Use `extends` to inherit config from a remote source:

```json
{
  "extends": "github:release-it/release-it-configuration",
  "git": {
    "commitMessage": "chore: release v${version}"
  }
}
```

Supported schemas:
- `github:owner/repo` — default branch
- `github:owner/repo#tag` — specific tag
- `github:owner/repo:subdir#tag` — subdirectory in repo
- `gitlab:`, `bitbucket:`, `https:` — other hosts

Powered by the [c12](https://github.com/unjs/c12) library.

## CLI Overrides

Any config option can be set via CLI and takes highest priority:

```bash
release-it minor --git.requireBranch=main --github.release
```

Negate booleans with `--no-` prefix:

```bash
release-it --no-npm.publish --no-git.push
```

Plugin options from CLI:

```bash
release-it --no-plugins.@release-it/keep-a-changelog.strictLatest
```

## Config Precedence

1. CLI arguments (highest)
2. Local config file
3. Extended config (`extends`)
4. Built-in defaults (lowest)

## Git Options (defaults)

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `git.changelog` | string | `git log --pretty=format:"* %s (%h)" ${from}...${to}` | Changelog generation command |
| `git.requireCleanWorkingDir` | boolean | `true` | Require clean working directory |
| `git.requireBranch` | string/array/false | `false` | Restrict releases to specific branches (supports wildcards) |
| `git.requireUpstream` | boolean | `true` | Require upstream remote exists |
| `git.requireCommits` | boolean | `false` | Fail if no commits since latest tag |
| `git.requireCommitsFail` | boolean | `true` | Continue if no commits but exit code 0 |
| `git.commitsPath` | string | `""` | Directory to check for commits |
| `git.addUntrackedFiles` | boolean | `false` | Add untracked files to release commit |
| `git.commit` | boolean | `true` | Execute commit step |
| `git.commitMessage` | string | `"Release ${version}"` | Commit message template |
| `git.commitArgs` | array | `[]` | Extra args for `git commit` |
| `git.tag` | boolean | `true` | Execute tag step |
| `git.tagExclude` | string/null | `null` | Exclude tags matching pattern |
| `git.tagName` | string/null | `null` | Custom tag name (auto-detects `v` prefix) |
| `git.tagMatch` | string/null | `null` | Glob pattern for finding latest tag |
| `git.getLatestTagFromAllRefs` | boolean | `false` | Consider all tags, not just reachable ones |
| `git.tagAnnotation` | string | `"Release ${version}"` | Annotated tag message |
| `git.tagArgs` | array | `[]` | Extra args for `git tag` |
| `git.push` | boolean | `true` | Execute push step |
| `git.pushArgs` | array | `["--follow-tags"]` | Extra args for `git push` |
| `git.pushRepo` | string | `""` | Remote name or URL (default: auto-detected) |

## npm Options (defaults)

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `npm.publish` | boolean | `true` | Execute npm publish |
| `npm.publishPath` | string | `"."` | Directory to publish |
| `npm.publishArgs` | array | `[]` | Extra args for `npm publish` |
| `npm.publishPackageManager` | string | `"npm"` | Use `pnpm` or `bun` instead |
| `npm.tag` | string/null | `null` | npm dist-tag (auto-derived for pre-releases) |
| `npm.otp` | string/null | `null` | One-time password for 2FA |
| `npm.ignoreVersion` | boolean | `false` | Ignore `package.json` version, use git tag |
| `npm.allowSameVersion` | boolean | `false` | Allow same version as current |
| `npm.versionArgs` | array | `[]` | Extra args for `npm version` |
| `npm.skipChecks` | boolean | `false` | Skip registry/auth checks |
| `npm.timeout` | number | `10` | Registry response timeout (seconds) |

## GitHub Options (defaults)

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `github.release` | boolean | `false` | Create GitHub release |
| `github.releaseName` | string | `"Release ${version}"` | Release name |
| `github.releaseNotes` | string/function/object/null | `null` | Custom release notes |
| `github.autoGenerate` | boolean | `false` | Let GitHub auto-generate notes |
| `github.preRelease` | boolean | `false` | Mark as pre-release (auto-set for pre-releases) |
| `github.draft` | boolean | `false` | Create as draft |
| `github.tokenRef` | string | `"GITHUB_TOKEN"` | Env var name for GitHub token |
| `github.assets` | string[]/null | `null` | Glob patterns for assets |
| `github.host` | string/null | `null` | GitHub Enterprise host |
| `github.timeout` | number | `0` | API timeout (0 = no timeout) |
| `github.proxy` | string/null | `null` | Proxy URL |
| `github.skipChecks` | boolean | `false` | Skip token/permission checks |
| `github.web` | boolean | `false` | Open web interface (auto-enabled if no token) |
| `github.comments.submit` | boolean | `false` | Comment on related PRs/issues |
| `github.comments.issue` | string | _(template)_ | Issue comment template |
| `github.comments.pr` | string | _(template)_ | PR comment template |

## GitLab Options (defaults)

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `gitlab.release` | boolean | `false` | Create GitLab release |
| `gitlab.releaseName` | string | `"Release ${version}"` | Release name |
| `gitlab.releaseNotes` | string/null | `null` | Custom release notes command |
| `gitlab.milestones` | array | `[]` | Associate milestones with release |
| `gitlab.tokenRef` | string | `"GITLAB_TOKEN"` | Env var name for GitLab token |
| `gitlab.tokenHeader` | string | `"Private-Token"` | HTTP header for token |
| `gitlab.certificateAuthorityFile` | string/null | `null` | CA file for self-hosted SSL |
| `gitlab.secure` | boolean | `false` | Verify server certificate |
| `gitlab.assets` | string[]/null | `null` | Glob patterns for assets |
| `gitlab.useIdsForUrls` | boolean | `false` | Use project IDs in URLs (GitLab 17.2+) |
| `gitlab.useGenericPackageRepositoryForAssets` | boolean | `false` | Use generic package repo |
| `gitlab.genericPackageRepositoryName` | string | `"release-it"` | Package repo name |
| `gitlab.origin` | string/null | `null` | Custom origin URL |
| `gitlab.skipChecks` | boolean | `false` | Skip token/permission checks |
