# Git Integration

## Default Git Workflow

The Git plugin executes these steps in order:

1. Prerequisite checks (clean dir, branch, upstream, commits)
2. _(Other plugins/hooks may update files here)_
3. `git add . --update`
4. `git commit -m "[git.commitMessage]"`
5. `git tag --annotate --message="[git.tagAnnotation]" [git.tagName]`
6. `git push [git.pushArgs] [git.pushRepo]`

For the default project command, use the Inquirer adapter in [interactive-workflow.md](interactive-workflow.md). It asks at each built-in Git step and stops the entire remaining flow on no/cancel. The stock prompt only skips a declined step. Files may already be bumped and staged before the commit question.

Minimum required Git version: v2.0.0.

## Tag Naming

By default, the tag name equals the version. If the latest tag has a `v` prefix, it's automatically reused — no need to set `git.tagName: "v${version}"`.

### Custom tag patterns

```bash
--git.tagName='${branchName}-${version}'
--git.tagName='${repo.project}-${version}'
--git.tagName='${npm.name}@${version}'    # For monorepo scoped packages
```

## Tag Matching

### tagMatch

Override how release-it finds the latest tag. Uses glob (not regex):

```json
{
  "git": {
    "tagMatch": "[0-9]*.[0-9]*.[0-9]*"
  }
}
```

### tagExclude

Exclude specific tags when finding the latest. Useful to skip pre-release tags:

```json
{
  "git": {
    "tagExclude": "*[-]*"
  }
}
```

`tagExclude` has no effect when `getLatestTagFromAllRefs: true`.

### getLatestTagFromAllRefs

By default, Git finds the latest tag that is _reachable from the current commit_ (via `git describe`). Set to `true` to consider all tags sorted by version, including unreachable ones (e.g. tags on other branches):

```json
{
  "git": {
    "getLatestTagFromAllRefs": true
  }
}
```

This is useful for parallel branch development (e.g. releasing from `develop` while `main` has newer tags).

## Changelog Generation

The default changelog command:

```
git log --pretty=format:"* %s (%h)" ${from}...${to}
```

Override with any command that outputs to stdout:

```json
{
  "git": {
    "changelog": "git log --no-merges --pretty=format:'* %s (%h)' ${latestTag}...HEAD"
  }
}
```

The changelog is shown during interactive mode and used as GitHub/GitLab release notes (unless overridden by `github.releaseNotes` or `gitlab.releaseNotes`).

For richer changelogs, use a plugin like `@release-it/conventional-changelog`, `auto-changelog`, or `git-cliff`. See [plugins.md](plugins.md).

## Commit Configuration

### Commit message

```json
{
  "git": {
    "commitMessage": "chore(release): v${version}"
  }
}
```

### Sign commits

```json
{
  "git": {
    "commitArgs": ["-S"]
  }
}
```

### Skip commit

```json
{
  "git": {
    "commit": false
  }
}
```

## Push Configuration

### Default push args and tag transfer

`["--follow-tags"]` is the default for `pushArgs`. Git transfers missing annotated tags
reachable from the pushed commits; this may include tags other than the current release.
It excludes lightweight tags but does not guarantee isolation of the selected service
app's tag. Do not use `--tags` to solve single-tag transfer: it sends every local tag.

### Transfer only the selected tag through the built-in push

Keep `git.push: true` so the Inquirer confirmation remains at the actual push point. When
single-tag transfer is required, compute the exact tag and upstream ref before calling
release-it, then pass explicit push arguments. For an already verified `origin/main`
upstream and an app tag template of `api-v${version}`, the entry script can use:

```js
const tagName = `api-v${selectedVersion}`;
const gitOptions = {
  ...options.git,
  push: true,
  pushRepo: '',
  requireUpstream: true,
  pushArgs: [
    '--atomic',
    '--no-follow-tags',
    'origin',
    'HEAD:refs/heads/main',
    `refs/tags/${tagName}:refs/tags/${tagName}`
  ]
};
```

Pass these options as `git` in the same interactive API call, retaining the wrapper's
clean-check/rollback handling. Adapt and verify the remote, upstream branch, and tag
policy for the actual target; the computed tag must equal release-it's selected tag.
Do not insert literal `${tagName}` templates into a JSON `pushArgs` array: 21.0.1 does not
format array arguments. The built-in method appends its upstream arguments after
`pushArgs`; with an existing upstream and `pushRepo: ''` it appends none. Inspect this
ordering again on a version upgrade.

`--atomic` requires server support; do not silently retry with weaker semantics or a
broader refspec if it fails. [Git push documentation](https://git-scm.com/docs/git-push)
explains atomic updates and tag transfer. A branch push still publishes the branch's
commits; selecting one app does not isolate unrelated commits already on that branch.

Disabling `git.push` and moving direct Git commands into `after:release` is excluded from
the interactive recommended path: it bypasses the push confirmation and can run after a
skipped stage. Use the built-in task callback, not a replacement shell push.

### Multiple push args

```bash
release-it minor --git.pushArgs=--follow-tags --git.pushArgs=--force
```

### Custom remote

```json
{
  "git": {
    "pushRepo": "upstream"
  }
}
```

Or use a Git URL: `"pushRepo": "https://github.com/user/repo.git"`

### Skip push

```json
{
  "git": {
    "push": false
  }
}
```

Skipping push is an explicit alternative outside the default interactive contract.
Do not replace it with an automatic push hook. The base command requires commit, tag,
and push to remain enabled; a user can decline at the relevant confirmation instead.

## Prerequisite Checks

### requireBranch

Restrict releases to specific branches:

```json
{
  "git": {
    "requireBranch": "main"
  }
}
```

Array and wildcards supported:

```json
{
  "git": {
    "requireBranch": ["main", "release/*"]
  }
}
```

### requireCleanWorkingDir

Must have clean working directory (default: `true`). Set to `false` to allow uncommitted changes:

```json
{
  "git": {
    "requireCleanWorkingDir": false
  }
}
```

Useful in monorepo setups where other packages' `package.json` files are modified during the release process.

### requireUpstream

If no upstream branch is configured, release-it halts. Disable to auto-set upstream:

```bash
release-it --no-git.requireUpstream
```

This adds `--set-upstream [remote] [branch]` to the push command.

Useful when releasing from a new branch or a project that hasn't pushed to remote yet.

### requireCommits

Stop the process if there are no commits since the latest tag:

```json
{
  "git": {
    "requireCommits": true
  }
}
```

Set `requireCommitsFail: false` to continue but exit with code 0 instead of 1.

### commitsPath

Only check for commits in a specific directory (useful in monorepos):

```json
{
  "git": {
    "commitsPath": "packages/my-package"
  }
}
```

## Untracked Files

By default, untracked files are not added to the release commit. Override:

```json
{
  "git": {
    "addUntrackedFiles": true
  }
}
```

## Skip Git Entirely

```bash
release-it --no-git
```

Or in config:

```json
{
  "git": false
}
```

Useful for npm-only releases or when another tool manages Git.
