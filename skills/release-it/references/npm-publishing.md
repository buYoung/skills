# npm Publishing

## How It Works

With a `package.json` in the current directory, release-it:
1. Runs prerequisite checks (registry up, user authenticated, collaborator for package)
2. Bumps version in `package.json` (and `package-lock.json` if present)
3. Publishes to the npm registry

Disable publishing only: `npm.publish: false`
Ignore package.json entirely: `"npm": false` or `--no-npm`

`npm.ignoreVersion: true` only changes the current-version getter; it does not disable
npm's bump writes in 21.1.3. When another plugin owns the version, connect its reader,
writes, and publishing inputs using the [version source contract](plugins.md#version-source-contract).
Publication can precede the Git commit in the [core lifecycle](hooks-and-lifecycle.md#plugin-order-and-side-effects),
so unchanged HEAD is not proof that no external release occurred.

## Authentication

### Local development

Typically handled by `npm login`, which has issued two-hour session tokens since
2025-12-09. With publishing enabled, release-it 21.1.x runs `npm login` itself when the
`npm whoami` check fails with `ENEEDAUTH` or `E401`, then checks again. It does not do this
in CI, in a dry run, or without a terminal.

### CI/CD environments

Prefer [OIDC Trusted Publishing](#oidc-trusted-publishing) when the CI provider supports it.
npm token rules as of 2026-11-27 ([access tokens](https://docs.npmjs.com/about-access-tokens/)):

- Only granular access tokens remain; classic tokens were revoked on 2025-12-09.
- New write tokens expire after 7 days by default and after at most 90 days.
- Bypass 2FA is off by default. Without it, a publish that requires 2FA asks for an OTP,
  which a CI job cannot supply.
- Direct publishing with a granular token is scheduled for removal in January 2027. A
  "Read and write (stage only)" token works with [staged publishing](#staged-publishing);
  `npm publish` with that token fails with `E_STAGE_REQUIRED`.

Set the token in the CI environment, then configure `.npmrc`:

```bash
npm config set //registry.npmjs.org/:_authToken $NPM_TOKEN
```

Or create `.npmrc` directly:

```text
//registry.npmjs.org/:_authToken=${NPM_TOKEN}
```

Make sure to `.gitignore` the `.npmrc` file.

### GitHub Actions

`actions/setup-node` with `registry-url` writes an `.npmrc` that reads `NODE_AUTH_TOKEN`:

```yaml
steps:
  - uses: actions/setup-node@v7
    with:
      node-version: 'lts/*'
      registry-url: 'https://registry.npmjs.org'
      package-manager-cache: false
  - run: npx release-it --ci
    env:
      NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

Without `registry-url`, write the `.npmrc` line above and pass the secret as `NPM_TOKEN`.
See [cli-and-workflow.md](cli-and-workflow.md#github-actions-example) for the complete job.

## Two-Factor Authentication (2FA / OTP)

If 2FA is enabled for the package, release-it will prompt for OTP in interactive mode.

Provide via CLI (not recommended — defeats 2FA purpose):

```bash
release-it --npm.otp=123456
```

## Scoped Packages

Scoped packages (e.g. `@user/package`) are private by default. To publish publicly:

```json
{
  "publishConfig": {
    "access": "public"
  }
}
```

## npm Dist-Tags

| Tag | When Used |
|-----|-----------|
| `latest` | Default for stable releases |
| Pre-release id | Auto-derived from version (e.g. `2.0.0-beta.3` → tag `beta`) |
| Custom | Override with `--npm.tag=next` |

```json
{
  "npm": {
    "tag": "next"
  }
}
```

## Private Registry

Set the registry in `package.json`:

```json
{
  "publishConfig": {
    "registry": "https://npm.pkg.github.com"
  }
}
```

### Custom public path (e.g. Verdaccio)

```json
{
  "publishConfig": {
    "publicPath": "/-/web/detail"
  }
}
```

### Yarn compatibility

Yarn may override global env vars causing auth issues. Explicitly set the registry:

```json
{
  "publishConfig": {
    "registry": "https://registry.npmjs.org"
  }
}
```

## Skip Prerequisite Checks

Some registries don't support every prerequisite check (`npm ping`, `npm whoami`, `npm access`). For example, Verdaccio 7.1.2 answered `npm ping` and `npm whoami` but not `npm access` (checked 2026-11-27):

```json
{
  "npm": {
    "skipChecks": true
  }
}
```

Also required for OIDC Trusted Publishing.

## Publish Path

Publish from a subdirectory (e.g. `dist/`):

```json
{
  "npm": {
    "publishPath": "dist"
  }
}
```

## Alternate Package Manager

Use pnpm or bun instead of npm:

```json
{
  "npm": {
    "publishPackageManager": "pnpm"
  }
}
```

## Extra Arguments

```json
{
  "npm": {
    "versionArgs": ["--allow-same-version", "--workspaces-update=false"],
    "publishArgs": ["--include-workspace-root"]
  }
}
```

## OIDC Trusted Publishing

Secure, token-free publishing from CI/CD using OpenID Connect. Eliminates long-lived npm tokens.

Trusted publishing requires npm CLI 11.5.1 or later and Node 22.14.0 or later
([trusted publishers](https://docs.npmjs.com/trusted-publishers)).

### Step 1: Configure npmjs.com

1. Go to package settings on npmjs.com
2. Under "Select your publisher", configure your GitHub repository
3. Check "Allowed actions". Publisher configurations created after 2026-09-03 allow only
   `npm stage publish` by default. Either also allow direct `npm publish`, or set
   `npm.stage: true` so release-it stages the version

### Step 2: Configure release-it

```json
{
  "npm": {
    "skipChecks": true
  }
}
```

### Step 3: GitHub Actions workflow

```yaml
jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      id-token: write    # Required for OIDC

    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-node@v7
        with:
          node-version: 'lts/*'
          registry-url: 'https://registry.npmjs.org'
          package-manager-cache: false
      - name: git config
        run: |
          git config user.name "${GITHUB_ACTOR}"
          git config user.email "${GITHUB_ACTOR}@users.noreply.github.com"
      # OIDC requires npm v11.5.1+ and Node 22.14.0+
      - run: npm install -g npm@latest
      - run: npm ci
      - run: npx release-it --ci
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          # No NPM_TOKEN needed with OIDC!
```

## Staged Publishing

With `npm.stage: true`, release-it runs `npm stage publish` (or `pnpm stage publish`) instead
of `npm publish`. Staging does not require 2FA, so release-it does not ask for an OTP. The
version is not installable when release-it finishes; a maintainer approves it afterwards with
`npm stage approve <stage-id>` or on npmjs.com, which requires 2FA.

```json
{
  "npm": {
    "stage": true
  }
}
```

Requires npm CLI 11.15.0+ (or pnpm 11.3.0+) and Node 22.14.0+. See npm's
[staged publishing](https://docs.npmjs.com/staged-publishing) guide.

## Monorepo Strategies

For the default one-service-app command, use [monorepo.md](monorepo.md) and
[interactive-workflow.md](interactive-workflow.md). The multi-package publishing examples
below are explicit alternatives; do not copy their workspace iteration or `git: false`
into the service-app flow. npm publishing is not enabled there by default.

### Single package in monorepo

For a single-package release, `git.commitsPath` scopes the Git plugin's commit-count check.
It does not scope staging, the shared index, or a separate changelog plugin:

```json
{
  "git": {
    "commitsPath": "packages/my-package"
  },
  "npm": {
    "versionArgs": ["--workspaces-update=false"]
  }
}
```

### All packages at same version

Use the root-based approach with `@release-it/bumper`:

**Root package.json**:

```json
{
  "workspaces": ["packages/a", "packages/b"],
  "scripts": {
    "release": "npm run release --workspaces && release-it"
  },
  "release-it": {
    "git": { "requireCleanWorkingDir": false },
    "npm": { "publish": false }
  }
}
```

**Each workspace package.json**:

```json
{
  "scripts": { "release": "release-it" },
  "release-it": {
    "git": false,
    "plugins": {
      "@release-it/bumper": {
        "out": {
          "file": "package.json",
          "path": ["dependencies.package-a"]
        }
      }
    }
  }
}
```

### Dedicated workspace plugins

- **@release-it-plugins/workspaces** — release all workspace packages
- **release-it-pnpm** — pnpm workspace support

See [plugins.md](plugins.md) for plugin configuration.

## Miscellaneous

- `"private": true` in package.json is respected — npm publish is skipped
- `npm version` failure aborts the release (except with `--no-increment`)
- `ENEEDAUTH` error while manual `npm publish` works — check `.npmrc` token configuration
