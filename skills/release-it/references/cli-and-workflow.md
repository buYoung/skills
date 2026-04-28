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

Listed in the order the interactive prompt should surface them — most-used choices first (patch, minor), then the pre-release ladder (alpha → beta → rc), then the rarer high-impact bumps. This order matches how teams typically reach for a release: small fix → feature → internal preview → wider testing → release candidate → breaking change.

| Type | Example (from 1.2.3) | Description |
|------|----------------------|-------------|
| `patch` | `1.2.4` | Bug fixes |
| `minor` | `1.3.0` | New features |
| `prepatch` (alpha) | `1.2.4-alpha.0` | Pre-release of next patch — use for early/internal alpha previews. Run with `--preRelease=alpha` to lock the identifier |
| `preminor` (beta) | `1.3.0-beta.0` | Pre-release of next minor — use for broader beta testing. Run with `--preRelease=beta` |
| `prerelease` / `pre` (rc counter) | `1.3.0-rc.0` → `1.3.0-rc.1` | Increment the pre-release counter. Switch to the rc track with `--preRelease=rc` (typically after beta has stabilized) |
| `major` | `2.0.0` | Breaking changes |
| `premajor` | `2.0.0-alpha.0` | Pre-release of next major (less common; used when the next major needs its own alpha/beta/rc cycle) |
| Explicit version | `3.0.0` | Must be valid semver > current |

```bash
release-it minor              # Interactive with minor bump
release-it 2.0.0              # Explicit version
release-it                    # Prompt for increment type
```

> **About the (alpha)/(beta)/(rc) labels.** In semver, the increment **type** (`prepatch`/`preminor`/`premajor`) and the pre-release **identifier** (`alpha`/`beta`/`rc`) are independent axes — `prepatch` could be tagged `-alpha.0`, `-beta.0`, or just `-0` depending on `preReleaseId`. The labels above encode a recommended team convention so the prompt reads naturally for users who aren't semver experts:
>
> - `prepatch` → alpha (first internal preview of the next patch)
> - `preminor` → beta (wider testing of the next minor)
> - `prerelease` with `--preRelease=rc` → rc (release candidate)
>
> Lock the convention in by always passing the matching `--preRelease=<id>` flag, or set it once in config (e.g. `"preRelease": "beta"`) when one channel dominates. If your team needs a different mapping (e.g. `prepatch` mapped to beta for hotfix testing), keep the increment types but rename the labels to match — the convention is yours, not release-it's.

## Pre-release Workflow

Pre-releases follow a sequence: alpha → beta → rc → stable. Mapped to the increment-type convention (see Increment Types above):

```bash
# alpha: first internal preview of the next minor (1.2.3 → 1.3.0-alpha.0)
release-it preminor --preRelease=alpha

# Increment within the alpha track (1.3.0-alpha.0 → 1.3.0-alpha.1)
release-it --preRelease

# beta: open it up for wider testing (1.3.0-alpha.1 → 1.3.0-beta.0)
release-it --preRelease=beta

# rc: release candidate (1.3.0-beta.N → 1.3.0-rc.0)
release-it --preRelease=rc

# Final stable release (1.3.0-rc.0 → 1.3.0)
release-it minor
```

For a patch-line pre-release (hotfix preview), swap `preminor` for `prepatch`. For a major-line pre-release, use `premajor`.

The `--preRelease=id` shorthand automatically sets:
- Increment to `pre[major|minor|patch]` (when combined with one of those increment types) or just bumps the pre-release counter
- `npm.tag` to the pre-release id (e.g. `beta`) — so `npm install pkg@beta` resolves to it
- `github.preRelease` to `true` — marks the GitHub release as pre-release

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
