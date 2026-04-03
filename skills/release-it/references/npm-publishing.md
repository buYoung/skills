# npm Publishing

## How It Works

With a `package.json` in the current directory, release-it:
1. Runs prerequisite checks (registry up, user authenticated, collaborator for package)
2. Bumps version in `package.json` (and `package-lock.json` if present)
3. Publishes to the npm registry

Disable publishing only: `npm.publish: false`
Ignore package.json entirely: `"npm": false` or `--no-npm`

## Authentication

### Local development

Typically handled by `npm login`. Token stored in `~/.npmrc`.

### CI/CD environments

Set `NPM_TOKEN` in the CI environment, then configure `.npmrc`:

```bash
npm config set //registry.npmjs.org/:_authToken $NPM_TOKEN
```

Or create `.npmrc` directly:

```text
//registry.npmjs.org/:_authToken=${NPM_TOKEN}
```

Make sure to `.gitignore` the `.npmrc` file.

### GitHub Actions

```yaml
steps:
  - run: npx release-it --ci
    env:
      NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

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

Some registries (Nexus, Verdaccio) don't support `npm ping`/`npm whoami`/`npm access`:

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

### Step 1: Configure npmjs.com

1. Go to package settings on npmjs.com
2. Under "Select your publisher", configure your GitHub repository

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
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 'lts/*'
          registry-url: 'https://registry.npmjs.org'
      # OIDC requires npm v11.5.1+
      - run: npm install -g npm@latest
      - run: npm ci
      - run: npx release-it --ci
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          # No NPM_TOKEN needed with OIDC!
```

## Monorepo Strategies

### Single package in monorepo

release-it handles one package at a time. Use `git.commitsPath` to scope commits:

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
