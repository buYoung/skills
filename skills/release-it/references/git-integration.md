# Git Integration

## Default Git Workflow

The Git plugin executes these steps in order:

1. Prerequisite checks (clean dir, branch, upstream, commits)
2. _(Other plugins/hooks may update files here)_
3. `git add . --update`
4. `git commit -m "[git.commitMessage]"`
5. `git tag --annotate --message="[git.tagAnnotation]" [git.tagName]`
6. `git push [git.pushArgs] [git.pushRepo]`

In interactive mode, release-it asks for confirmation before commit, tag, and push.

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

### Default push args and tag-push semantics

`["--follow-tags"]` is the default for `pushArgs`. This is intentional: `--follow-tags` pushes **only annotated tags that are reachable from the commits being pushed**. Lightweight tags, tags on unrelated branches, and abandoned local-only tags stay local. release-it always creates the new release tag as annotated, so the tag the user just selected is always included — and unrelated tags are never silently piggy-backed onto the push.

If you override `pushArgs`, you must re-add `--follow-tags` (or use the strict pattern below). Do **not** add `--tags` — that would push *every* local tag, including experimental or abandoned ones, which defeats the safety the default provides.

### Push only the user-selected tag (strict guarantee, recommended)

`--follow-tags` is a good default, but it still pushes any *other* annotated tag that happens to be reachable from the pushed commits (e.g. older release tags that were never pushed, pre-release tags from a parallel branch). When the requirement is "only the tag the user just chose to release goes to the remote — nothing else, ever", disable the built-in push and push the new tag explicitly through a hook:

```json
{
  "git": {
    "push": false
  },
  "hooks": {
    "after:release": "git push ${repo.remote} HEAD && git push ${repo.remote} refs/tags/${tagName}"
  }
}
```

`${tagName}` resolves to the exact tag release-it just created for this release. The push targets that one ref by name, so no other tag can ride along regardless of what exists locally. Pushing `HEAD` first ensures the tag's commit is reachable on the remote before the tag itself is published.

Use this pattern when:
- Local repos accumulate experimental or CI snapshot tags that must not leak to the remote
- Compliance/audit requires demonstrating that a release published exactly one tag
- You want defense-in-depth against someone later adding `--tags` to `pushArgs`

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

You can still push manually in a hook (see the strict pattern above for the recommended single-tag form):

```json
{
  "git": { "push": false },
  "hooks": {
    "after:release": "git push origin HEAD"
  }
}
```

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
