# Plugins

## How Plugins Work

release-it uses a plugin architecture internally. Core plugins (`git`, `github`, `gitlab`, `npm`, `version`) are built-in. External plugins extend the release process.

### Plugin configuration syntax

```json
{
  "plugins": {
    "plugin-name": {
      "option": "value"
    },
    "./local/plugin.js": {
      "key": "value"
    }
  }
}
```

### Core plugin auto-enable rules

- `git` — enabled when Git recognizes the cwd as part of a repository and `git` is not `false` (including subdirectories and linked worktrees)
- `github` — enabled if `github.release: true`
- `gitlab` — enabled if `gitlab.release: true`
- `npm` — enabled if `package.json` is accessible in the cwd and `npm` is not `false`
- `version` — always enabled

An external plugin can also disable core plugins with `disablePlugin()`.

## Version Source Contract

Identify the product's version source independently of the files used to install release
tooling. A repository can contain `package.json` while its release version belongs to a
manifest, a plain version file, Git tags, or a custom plugin.

Connect the same source through current-version reading, candidate calculation, resolved
version checks, actual writes, state reporting, and any requested restoration. Record
every output, including changelogs, lockfiles, generated files, and shared paths. The
staging and recovery scope must cover those effects without claiming ownership of unrelated
changes; see [git-integration.md](git-integration.md#working-state-and-staging-scope).

Choose the writer that fits the project's format: the npm plugin, a configured bumper,
or a custom plugin. Preserve version semantics such as pre-release identifiers and build
metadata; the packaged semver menu is not a parser for every versioning scheme.
External getter precedence does not automatically stop other plugins from writing.

In 21.0.1, `npm.publish: false` disables publishing but retains npm version writes.
`npm.ignoreVersion: true` changes getter selection, not npm's bump method. Use `npm: false`
or an appropriate `disablePlugin()` when that plugin must not touch a tooling manifest;
if npm publication is also required, design its version inputs and writes together.
See the [npm source](https://github.com/release-it/release-it/blob/21.0.1/lib/plugin/npm/npm.js).

For a generated interactive command, adapt all consumers listed in
[interactive-workflow.md](interactive-workflow.md#copyable-project-example). A custom plugin
must also respect dry-run and the actual prompt API in
[custom-plugin-development.md](custom-plugin-development.md).

---

## @release-it/conventional-changelog

Recommended bump from commit messages + changelog generation following Conventional Commits.

### Install

```bash
npm install -D @release-it/conventional-changelog
```

### Basic config

```json
{
  "plugins": {
    "@release-it/conventional-changelog": {
      "preset": "angular",
      "infile": "CHANGELOG.md"
    }
  }
}
```

### Key options

| Option | Description |
|--------|-------------|
| `preset` | Commit convention preset: `angular`, `conventionalcommits`, `atom`, `ember`, `eslint`, `jshint` |
| `infile` | Path to changelog file to update (e.g. `CHANGELOG.md`) |
| `header` | Text to prepend to changelog file |
| `types` | Array of type objects to customize which commit types appear |
| `writerOpts` | Options passed to `conventional-changelog-writer` |

### Custom commit types

```json
{
  "plugins": {
    "@release-it/conventional-changelog": {
      "preset": {
        "name": "conventionalcommits",
        "types": [
          { "type": "feat", "section": "Features" },
          { "type": "fix", "section": "Bug Fixes" },
          { "type": "perf", "section": "Performance" },
          { "type": "docs", "section": "Documentation", "hidden": false }
        ]
      },
      "infile": "CHANGELOG.md"
    }
  }
}
```

### How it works

1. Reads commit messages since the latest tag
2. Determines recommended bump (major/minor/patch) based on commit types
3. Generates changelog from categorized commits
4. Updates `CHANGELOG.md` if `infile` is set

If `infile` is set, the changelog file update is included in the release commit automatically.

---

## @release-it/bumper

Read/write version from any file — not just `package.json`. Useful for non-Node projects or monorepos.

### Install

```bash
npm install -D @release-it/bumper
```

### Basic config

Read version from a file:

```json
{
  "plugins": {
    "@release-it/bumper": {
      "in": "VERSION",
      "out": "VERSION"
    }
  }
}
```

### Multiple output files

```json
{
  "plugins": {
    "@release-it/bumper": {
      "in": "package.json",
      "out": [
        "VERSION",
        {
          "file": "manifest.json",
          "path": "version"
        },
        {
          "file": "package.json",
          "path": ["dependencies.package-a", "devDependencies.package-b"]
        }
      ]
    }
  }
}
```

### Without package.json

For non-Node projects:

```json
{
  "npm": false,
  "plugins": {
    "@release-it/bumper": {
      "in": "VERSION",
      "out": "VERSION"
    }
  }
}
```

---

## @release-it/keep-a-changelog

Updates `CHANGELOG.md` following the [Keep a Changelog](https://keepachangelog.com) convention.

### Install

```bash
npm install -D @release-it/keep-a-changelog
```

### Basic config

```json
{
  "plugins": {
    "@release-it/keep-a-changelog": {
      "filename": "CHANGELOG.md"
    }
  }
}
```

### Key options

| Option | Description |
|--------|-------------|
| `filename` | Path to changelog file (default: `CHANGELOG.md`) |
| `head` | Heading to use for unreleased section |
| `addUnreleased` | Add an empty "Unreleased" section after release |
| `addVersionUrl` | Add version comparison URL |
| `versionUrlFormats` | Custom URL format for version links |
| `strictLatest` | Strict version comparison for "latest" |
| `keepUnreleased` | Keep the unreleased section content after release |

### Workflow

1. Maintain a `## [Unreleased]` section in CHANGELOG.md during development
2. On release, the plugin renames it to `## [x.y.z] - YYYY-MM-DD`
3. Optionally adds a new empty `## [Unreleased]` section

---

## release-it-calver-plugin

Calendar versioning (CalVer) instead of semantic versioning.

### Install

```bash
npm install -D release-it-calver-plugin
```

### Basic config

```json
{
  "plugins": {
    "release-it-calver-plugin": {
      "format": "YYYY.MM.DD"
    }
  }
}
```

### Format tokens

| Token | Description | Example |
|-------|-------------|---------|
| `YYYY` | Full year | `2024` |
| `YY` | Short year | `24` |
| `MM` | Month (zero-padded) | `03` |
| `0M` | Month (zero-padded) | `03` |
| `DD` | Day (zero-padded) | `15` |
| `0D` | Day (zero-padded) | `15` |
| `MINOR` | Auto-incrementing counter | `1`, `2`, `3` |
| `MICRO` | Auto-incrementing counter | `1`, `2`, `3` |

---

## @release-it-plugins/workspaces

Release multiple packages in a monorepo workspace when bulk publishing is explicitly requested. For the default one-service-app command, use [monorepo.md](monorepo.md); do not add workspace-wide release plugins.

### Install

```bash
npm install -D @release-it-plugins/workspaces
```

### Basic config

```json
{
  "plugins": {
    "@release-it-plugins/workspaces": {
      "publish": true,
      "workspaces": ["packages/*"]
    }
  }
}
```

---

## release-it-pnpm

pnpm workspace support for releasing.

### Install

```bash
npm install -D release-it-pnpm
```

---

## auto-changelog (companion tool)

Not a plugin but a companion tool used via hooks:

```json
{
  "git": {
    "changelog": "npx auto-changelog --stdout --commit-limit false -u --template https://raw.githubusercontent.com/release-it/release-it/main/templates/changelog-compact.hbs"
  },
  "hooks": {
    "after:bump": "npx auto-changelog -p"
  }
}
```

---

## git-cliff (companion tool)

Customizable changelog generator following Conventional Commits. Used as a companion:

```json
{
  "git": {
    "changelog": "npx git-cliff --latest --strip header"
  },
  "hooks": {
    "after:bump": "npx git-cliff -o CHANGELOG.md"
  }
}
```

---

## Discovering Plugins

All packages tagged with [`release-it-plugin` on npm](https://www.npmjs.com/search?q=keywords:release-it-plugin).

## CLI Override for Plugins

Plugin options can be set from the command line:

```bash
release-it --plugins.@release-it/conventional-changelog.preset=angular
release-it --no-plugins.@release-it/keep-a-changelog.strictLatest
```
