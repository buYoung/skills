# One Service App per Interactive Release

The default monorepo command is `pnpm release → one service app → version → commit? /
commit → tag? / tag → push? / push`. Use the entry script and adapter in
[interactive-workflow.md](interactive-workflow.md).

## Identify Service Apps During Setup

Inspect workspace declarations, app manifests, and actual build/deployment entry points.
`private: true` or membership in `workspaces` alone does not distinguish a deployable
service from a shared library. If that boundary is unclear, ask which directories are
service apps before generating the target manifest. This is a setup decision, not an
extra start question each time the release command runs.

Generate a root `.release-targets.json` using the verified apps, for example:

```json
{
  "serviceApps": [
    { "name": "API", "path": "apps/api", "config": ".release-it.json" },
    { "name": "Web", "path": "apps/web", "config": ".release-it.json" }
  ]
}
```

The entry script reads actual projects with [`pnpm list --recursive --depth -1 --json`](https://pnpm.io/cli/list),
package workspace declarations, and this setup-verified manifest, then offers the list
with Inquirer `select`. A `pnpm-workspace.yaml` containing only build settings does not by
itself make a single project a monorepo. Other workspace systems can use the manifest
generated from their verified project graph during setup.
Never use `multiselect`, select all by default, or recursively execute workspace release
commands. An absent/empty manifest is an actionable setup error. Adapt the detection for
other workspace systems when applying the skill; do not silently treat an unrecognized
monorepo as a single project. Do not list the root tooling package as a service app.

## Bind the Selected Target Through the Entire Flow

After the one selection, change cwd to the app before reading its config or invoking
release-it. Resolving an app config path alone does not change the cwd used by versioning
or relative paths. Keep the root entry command and shared dependency installation at root.

For `apps/api/.release-it.json`, use the single-project config with these app-specific
values (the paths here are relative to the selected app's cwd):

```json
{
  "git": {
    "requireBranch": "main",
    "requireUpstream": true,
    "commit": true,
    "tag": true,
    "push": true,
    "tagName": "api-v${version}",
    "tagMatch": "api-v[0-9]*",
    "commitsPath": ".",
    "commitMessage": "chore(api): release ${version}"
  },
  "npm": {
    "publish": false,
    "versionArgs": ["--ignore-scripts", "--workspaces-update=false"]
  },
  "github": { "release": false },
  "gitlab": { "release": false },
  "plugins": {
    "@release-it/conventional-changelog": {
      "preset": "conventionalcommits",
      "infile": "CHANGELOG.md",
      "tagPrefix": "api-v",
      "gitRawCommitsOpts": { "path": "." },
      "commitsOpts": { "path": "." }
    }
  }
}
```

Give Web its own prefix, version, and changelog. `git.commitsPath` scopes the Git plugin's
commit-count check; it does not scope a separate changelog plugin, version writes, or the Git
index. Scope the changelog's history and recommendation inputs separately as shown, and
verify the resulting changelog with distinct commits from both apps. For shared-library
changes that affect a service, determine its history inclusion policy during setup.

Require the entire repository/index to be clean first. release-it stages from the selected
cwd, but Git commit consumes the whole index. Inspect hooks and workspace-version tooling
for writes to sibling apps, shared lockfiles, or root manifests. With package.json versioning,
release-it supplies `--workspaces=false`; the example also disables workspace dependency
updates and version scripts. Confirm this behavior with the project's npm/pnpm versions.
Projects that need a shared lockfile update need an explicitly scoped preparation strategy.

The selected app supplies `tagName`, `tagMatch`, and changelog `tagPrefix` together. The
normal Git push is still a branch push, and default `--follow-tags` can include other
reachable annotated tags. If only the selected tag may be transferred, use the explicit
refspec recipe in [git-integration.md](git-integration.md) while keeping the built-in push
step and confirmation enabled; do not claim `--follow-tags` isolates one app.

## Other Monorepo Workflows

Keep synchronized package versions, bulk workspace publishing, and npm distribution as
explicit alternative workflows. The examples in [npm-publishing.md](npm-publishing.md)
and workspace plugins in [plugins.md](plugins.md) remain available when requested, but
they are not the default one-service-app path. Do not set `git: false` on the selected
service config, because that removes the required commit/tag/push stages.
