# Hooks and Lifecycle

## Lifecycle Order

release-it executes lifecycle methods in this order across all plugins:

```
1. init          — validate prerequisites, gather version/package details
2. getName       — return package/project name
3. getLatestVersion — return current version (SemVer)
4. getChangelog  — generate changelog text
5. getIncrement  — determine increment type
6. getIncrementedVersionCI / getIncrementedVersion — calculate next version
7. beforeBump    — prepare for version increment
8. bump          — update version in files
9. beforeRelease — stage files before release
10. release      — main release actions (commit, tag, push, publish)
11. afterRelease — post-release tasks (success details, notifications)
```

## Hook Format

Hooks are shell commands that run at specific points in the lifecycle.

Format: `[before|after]:[plugin]:[method]`

Where `plugin` is optional (omit to run for all plugins):

```json
{
  "hooks": {
    "before:init": "npm test",
    "after:bump": "npm run build",
    "after:git:release": "echo 'Tag pushed: ${tagName}'",
    "after:release": "echo 'Released ${name} v${version}'"
  }
}
```

## Available Hooks

### Global hooks (run for all plugins)

| Hook | When |
|------|------|
| `before:init` | Before any plugin initializes |
| `after:init` | After all plugins initialized |
| `before:bump` | Before any version bumping |
| `after:bump` | After all version files updated |
| `before:release` | Before any releasing |
| `after:release` | After all releasing complete |

### Plugin-specific hooks

| Hook | When |
|------|------|
| `before:git:init` / `after:git:init` | Before/after Git plugin init |
| `before:git:bump` / `after:git:bump` | Before/after Git version bump |
| `before:git:release` / `after:git:release` | Before/after Git commit, tag, push |
| `before:npm:init` / `after:npm:init` | Before/after npm plugin init |
| `before:npm:bump` / `after:npm:bump` | Before/after npm version bump |
| `before:npm:release` / `after:npm:release` | Before/after npm publish |
| `before:github:init` / `after:github:init` | Before/after GitHub plugin init |
| `before:github:release` / `after:github:release` | Before/after GitHub release creation |
| `before:gitlab:release` / `after:gitlab:release` | Before/after GitLab release creation |

## Hook Values

Hooks accept a single command string or an array of commands:

```json
{
  "hooks": {
    "before:init": ["npm run lint", "npm test"],
    "after:bump": "npm run build",
    "after:release": [
      "npm run deploy",
      "notify-slack.sh v${version}"
    ]
  }
}
```

## Template Variables

All hooks (except `init`) have access to these template variables:

### Core variables

| Variable | Description | Example |
|----------|-------------|---------|
| `${version}` | New version being released | `2.1.0` |
| `${latestVersion}` | Previous/current version | `2.0.3` |
| `${changelog}` | Generated changelog text | `* feat: ... (abc123)` |
| `${name}` | Package/project name | `my-package` |
| `${tagName}` | Git tag name | `v2.1.0` |
| `${latestTag}` | Previous Git tag | `v2.0.3` |
| `${branchName}` | Current Git branch | `main` |

### Repository variables

| Variable | Description | Example |
|----------|-------------|---------|
| `${repo.remote}` | Remote URL | `git@github.com:user/repo.git` |
| `${repo.protocol}` | Protocol | `ssh` |
| `${repo.host}` | Host | `github.com` |
| `${repo.owner}` | Repository owner | `user` |
| `${repo.repository}` | Full repo path | `user/repo` |
| `${repo.project}` | Project name | `repo` |

### Release variables (available in `after:release`)

| Variable | Description |
|----------|-------------|
| `${releaseUrl}` | URL to the created release page |
| `${releaseName}` | Name of the release |

## Hook Execution Rules

1. Hooks are **not** executed if the corresponding step is skipped (e.g. `after:git:release` won't run if `git.push: false`)
2. If a plugin method returns `false`, the associated `after:` hook is skipped
3. Use `-V` (verbose) flag to see hook output during release
4. Use `-VV` for extra verbose output including internal commands

## Common Hook Patterns

### Test before release

```json
{
  "hooks": {
    "before:init": "npm test"
  }
}
```

### Build after version bump

```json
{
  "hooks": {
    "after:bump": "npm run build"
  }
}
```

### Update changelog file after bump

```json
{
  "hooks": {
    "after:bump": "npx auto-changelog -p"
  }
}
```

### Notify after release

```json
{
  "hooks": {
    "after:release": "curl -X POST ${SLACK_WEBHOOK} -d '{\"text\": \"Released ${name} v${version}\"}'"
  }
}
```

### Fetch tags before init (GitLab CI fix)

```json
{
  "hooks": {
    "before:init": "git fetch --prune --prune-tags origin"
  }
}
```

### Full workflow example

```json
{
  "hooks": {
    "before:init": ["npm run lint", "npm test"],
    "after:bump": [
      "npm run build",
      "npm run generate-docs"
    ],
    "after:git:release": "echo 'Pushed tag ${tagName} to ${repo.repository}'",
    "after:release": "echo 'Successfully released ${name} v${version} to ${releaseUrl}'"
  }
}
```
