# CLI and Workflow

## Basic Usage

```bash
release-it [increment] [options]
```

## CLI Flags

| Flag | Alias | Description |
|------|-------|-------------|
| `--config <file>` | `-c` | Configuration file path. Use `--config false` to skip config file |
| `--dry-run` | `-d` | Simulate without executing write operations |
| `--help` | `-h` | Print help text |
| `--increment <type>` | `-i` | Version increment type (see below) |
| `--version` | `-v` | Print release-it version |
| `--verbose` | `-V` | Log hook output. Use `-VV` for internal command output too |
| `--ci` | | Non-interactive CI mode (auto-detected in CI environments) |
| `--only-version` | | Prompt only for version, automate the rest |
| `--release-version` | | Print version to be released, then exit |
| `--changelog` | | Print changelog, then exit |
| `--preRelease[=id]` | | Create pre-release with optional identifier |
| `--preReleaseId=id` | | Pre-release identifier (alpha, beta, rc, etc.) |
| `--preReleaseBase=n` | | Start pre-release counter at `n` (default: 0) |
| `--snapshot=id` | | Create snapshot release |

### Nested config overrides

```bash
release-it minor \
  --git.requireBranch=main \
  --github.release \
  --npm.tag=beta \
  --no-git.push \
  --no-npm.publish
```

Boolean flags negate with `--no-` prefix.

## Increment Types

| Type | Example (from 1.2.3) | Description |
|------|----------------------|-------------|
| `major` | `2.0.0` | Breaking changes |
| `minor` | `1.3.0` | New features |
| `patch` | `1.2.4` | Bug fixes |
| `premajor` | `2.0.0-alpha.0` | Pre-release of next major |
| `preminor` | `1.3.0-alpha.0` | Pre-release of next minor |
| `prepatch` | `1.2.4-alpha.0` | Pre-release of next patch |
| `prerelease` / `pre` | `1.2.4-alpha.1` | Increment pre-release counter |
| Explicit version | `3.0.0` | Must be valid semver > current |

```bash
release-it minor              # Interactive with minor bump
release-it 2.0.0              # Explicit version
release-it                    # Prompt for increment type
```

## Pre-release Workflow

Pre-releases follow a sequence: alpha → beta → rc → stable.

```bash
# Start a major pre-release (1.2.3 → 2.0.0-beta.0)
release-it major --preRelease=beta

# Increment pre-release (2.0.0-beta.0 → 2.0.0-beta.1)
release-it --preRelease

# Switch to RC (2.0.0-beta.1 → 2.0.0-rc.0)
release-it --preRelease=rc

# Final release (2.0.0-rc.0 → 2.0.0)
release-it major
```

The `--preRelease=id` shorthand automatically sets:
- Increment to `pre[major|minor|patch]`
- `npm.tag` to the pre-release id (e.g. `beta`)
- `github.preRelease` to `true`

Use `--preReleaseBase=1` to start at `-beta.1` instead of `-beta.0`.

### Changelog for final release after pre-releases

To include all commits since the last stable tag (excluding pre-release tags):

```bash
release-it major --git.tagExclude='*[-]*'
```

## Snapshot Releases

Development snapshots between releases:

```bash
release-it --snapshot=canary
```

Auto-sets: `tagMatch`, `getLatestTagFromAllRefs`, `requireBranch: false`, `requireUpstream: false`, `npm.ignoreVersion: true`.

## Dry Run

Shows what would execute without side effects:

```bash
release-it --dry-run
```

Output conventions:
- `$ git log ...` — Read-only command (actually executes)
- `! git commit ...` — Write command (skipped)

### Print-only modes

```bash
release-it --release-version   # Print next version, exit
release-it --changelog          # Print changelog, exit
```

## Interactive vs CI Mode

| Aspect | Interactive (default) | CI (`--ci`) |
|--------|-----------------------|-------------|
| Version selection | Prompts user | Uses provided increment |
| Step confirmation | Asks before each step | Executes automatically |
| Progress | Prompts with details | Spinners |
| Detection | Local terminal | Auto-detected via `ci-info` |

CI environments auto-detected: GitHub Actions, GitLab CI, Jenkins, Travis, CircleCI, etc.

### Only-version mode (hybrid)

```bash
release-it --only-version    # Prompt for version only, automate the rest
```

## Skip Entire Sections

```bash
release-it --no-git           # Skip all git steps
release-it --no-npm           # Skip all npm steps
release-it --no-github        # Skip GitHub release
release-it --no-gitlab        # Skip GitLab release
```

## Update Existing Release

Re-run release-it to update an existing release (e.g. add assets, toggle draft):

```bash
release-it \
  --no-increment \
  --no-git \
  --no-npm \
  --github.release \
  --github.update \
  --github.assets=dist/*.zip \
  --no-github.draft
```

## GitHub Actions Example

```yaml
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-node@v4
        with:
          node-version: 'lts/*'
          registry-url: 'https://registry.npmjs.org'
      - name: git config
        run: |
          git config user.name "${GITHUB_ACTOR}"
          git config user.email "${GITHUB_ACTOR}@users.noreply.github.com"
      - run: npm ci
      - run: npx release-it --ci
        env:
          NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

`fetch-depth: 0` is needed if using conventional-changelog or any plugin that reads git history.

## Programmatic API

```js
import release from 'release-it';

const output = await release({
  git: { requireBranch: 'main' },
  github: { release: true }
});

console.log(output);
// { version, latestVersion, name, changelog }
```

## Debug Mode

```bash
NODE_DEBUG=release-it:* release-it
```

Outputs detailed debug logs namespaced by plugin (e.g. `release-it:git`, `release-it:npm`).
