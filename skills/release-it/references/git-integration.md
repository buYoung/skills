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

Requires clean tracked files and index (default: `true`). In release-it 21.0.1 the built-in
check is `git diff --quiet HEAD`; it does not reject ordinary untracked files. Setting it
to `false` also prevents the Git plugin from registering its local exit/SIGINT rollback
handlers. It does not disable every recovery path; see [Recovery Policies](#recovery-policies).

```json
{
  "git": {
    "requireCleanWorkingDir": false
  }
}
```

Use this override only with an understood initial-state and recovery policy. Allowing dirty
state can include existing staged changes in the release commit or expose them to a custom
cleanup operation. Do not prescribe this option for every CLI, CI, or API workflow.

### Working State and Staging Scope

Determine these scopes independently before changing a wrapper's preflight:

| Scope | What determines it |
|---|---|
| Version input | The selected version provider, which may differ from the tooling manifest |
| Writes | Version/changelog plugins, build hooks, lockfile updates, generated files, shared outputs |
| Directory staging | Git plugin cwd and `stageDir({ baseDir })`; default baseDir is `.` |
| Commit inputs | The repository-wide index, plus any explicitly customized commit arguments |
| Recoverable changes | Files whose baseline and ownership are known for this execution |

`stageDir()` uses `git add <baseDir> --update` by default, or `--all` with
`addUntrackedFiles: true`. This does not remove existing index entries, nor prevent a hook
or plugin from explicitly staging another file. A newly staged file is already an index
change and is caught by `git status --porcelain --untracked-files=no`.

For a wrapper that requires clean initial tracked state, run that check repository-wide.
Then decide how to handle pre-existing untracked files based on the actual staging and
write scopes. Unrelated untracked files need not block `--update`; untracked files a
writer might overwrite, or `--all` might include, need explicit handling. A file outside
the selected app may still be a shared output. Directory membership alone is not a
complete policy, and ignored files are not a guarantee against a plugin overwriting them.

Check required version inputs and intended outputs as well: an updated but untracked
file may be omitted from the commit unless a plugin stages it. Inspect the final changeset
and index instead of inferring the committed files from a clean preflight.

The packaged Node example rejects repository-wide tracked/index changes, requires existing
version manifests/lockfiles to be tracked, and rejects pre-existing untracked files in the
selected staging directory when `addUntrackedFiles` is enabled. Other unrelated untracked
files are preserved. Adapt this policy for other writers; it cannot discover arbitrary
hook/plugin side effects.

### Recovery Policies

Choose recovery behavior for the workflow instead of treating every interruption as one
transaction. In 21.0.1, `bump` precedes `Git.beforeRelease()`, which enables local rollback
only when both `git.commit` and `git.requireCleanWorkingDir` are enabled, then stages files.
The commit confirmation comes later. A failure during bump can therefore occur before
those handlers are installed.

| Policy | Conditions and limits |
|---|---|
| Keep built-in local rollback | Understand its process-wide exit/SIGINT handlers: it can delete the created local tag and reset the release commit; an API rejection alone does not run an exit handler |
| Preserve interrupted state | Disable those handlers with `requireCleanWorkingDir: false`, enforce the chosen preflight separately, and report the files/index/commit/tag that remain; this is the packaged example's policy |
| Restore owned local changes | Capture the relevant baseline before writes, identify every owned output, and restore only where provenance and completed actions permit it; report skipped or failed restoration |

For a custom restoration policy, unchanged `HEAD` is a guard against discarding a created
commit, not proof that all effects are reversible. Existing staged/unstaged work must not
be replaced with HEAD, untracked generated files need separate ownership handling, and
shared outputs may lie outside the selected directory. `git restore --staged --worktree`
is useful only when its source is the intended baseline and its path list is justified;
it is not a cleanup command for arbitrary generated files. Check Git compatibility if
introducing it into a project that previously used older Git.

Also account for completed external actions. With npm publishing enabled, 21.0.1 can
publish before Git commit; a local file restore cannot undo that publication. See
[lifecycle order](hooks-and-lifecycle.md#plugin-order-and-side-effects). Preserve commits
and tags after a deliberate stop when that is the workflow's contract. Prompt No, prompt
Ctrl+C, process signals outside prompts, execution failures, and partial pushes require
their actual state to be inspected, not the same assumed cleanup.

Disabling local exit rollback does not disable the push-error path: 21.0.1 may attempt
`git push origin --delete <tag>` after a failed push. Report remote state as unknown until
inspected, including when local state appears unchanged.

Source: [21.0.1 Git implementation](https://github.com/release-it/release-it/blob/21.0.1/lib/plugin/git/Git.js).

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

By default, directory staging does not add untracked files. Already staged files and
explicit plugin/hook staging are separate. To include untracked files in `stageDir()`:

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
