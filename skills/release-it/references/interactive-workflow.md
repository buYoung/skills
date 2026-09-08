# Interactive Release Workflow

## Contract

Use these question/action sequences for the default service-app release:

- Single project: `pnpm release → version → commit? / commit → tag? / tag → push? / push`.
- Monorepo: `pnpm release → one service app → version → commit? / commit → tag? / tag → push? / push`.

All questions use `@clack/prompts`. A single project starts directly with the version
question; neither a target picker nor a start confirmation belongs before it. Read-only
preflight checks may fail before the first question. In a monorepo, always show the service
app picker, including when there is only one eligible app. Configure the eligible apps
during setup; do not guess from every workspace package. See [monorepo.md](monorepo.md).

The version menu shows the current version and each concrete next version. A suggested bump
can be a label or initial selection, but still requires a submitted answer. Pass an exact
semver selected by the user to release-it. Do not first ask all three Git confirmations:
each confirmation belongs at its action's execution point.

## Copyable Project Example

Copy these complete files into the applying project's `scripts/` directory:

- [release.mjs](../examples/interactive-release/release.mjs): terminal and repository checks,
  structure detection, target selection, version menu, release-it API call, state reporting.
- [release-prompts.mjs](../examples/interactive-release/release-prompts.mjs): clack adapter,
  stop exception, and a plugin that checks the chosen version before any bump.

These are project-generation examples, not commands to release the skill repository.
Their supported base is a service app whose `package.json` owns the version. For VERSION
files or other version providers, adapt both the version reader and the guard to that same
provider; do not show the root package version and bump another source.

Install the tested dependency set with the project's package manager (add `-w` for pnpm
workspace-root tooling):

```bash
pnpm add -D -E release-it@21.0.1 @clack/prompts@1.8.0 semver@7.8.5
# When using the changelog configuration below:
pnpm add -D -E @release-it/conventional-changelog@12.0.0 conventional-changelog-conventionalcommits@10.4.0
```

`semver` computes and validates menu values. Clack owns the questions; release-it and its
changelog plugin own the writes. Add the entry command to the root `package.json`:

```json
{
  "scripts": {
    "release": "node scripts/release.mjs"
  }
}
```

A single-project `.release-it.json` starts with:

```json
{
  "$schema": "https://unpkg.com/release-it@21.0.1/schema/release-it.json",
  "git": {
    "commit": true,
    "tag": true,
    "push": true,
    "requireBranch": "main",
    "requireUpstream": true,
    "tagName": "v${version}",
    "tagMatch": "v[0-9]*",
    "commitMessage": "chore(release): v${version}"
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
      "tagPrefix": "v"
    }
  }
}
```

Choose branch/tag/changelog conventions for the applying project. Track the scripts,
configuration, version file, and initial changelog before running the command. Inspect
existing release hooks, npm version lifecycle scripts, and plugins: none may commit, tag,
push, publish, deploy, request a separate start confirmation, or modify another target
before the appropriate step. The example disables npm version lifecycle scripts explicitly;
add any required preparation separately after reviewing its effects. Do not automatically
add CI workflows, hosted releases, npm publishing, or deployment hooks.

The entry script loads the selected app's configuration after changing its working directory.
Apply the interactive mode controls to the initial `new Config(...)` as well as the final
API call: snapshot shorthand expansion during `Config.init()` can rewrite Git branch/tag
options and `npm.ignoreVersion` before later overrides get a chance to act.
It passes the resolved options once with `config: false`, avoiding a second config load,
then overrides only the controls necessary for the interactive contract:

```js
await release({
  ...options,
  config: false,
  extends: false,
  ci: false,
  'only-version': false,
  'release-version': false,
  changelog: false,
  'dry-run': false,
  snapshot: false,
  preRelease: false,
  increment: selectedVersion,
  git: { ...options.git, requireCleanWorkingDir: false },
  plugins: {
    [guardPath]: { currentVersion, selectedVersion },
    ...options.plugins
  }
}, { prompt });
```

The complete script performs the clean-repository check before this call. It rejects CLI
arguments instead of forwarding `--ci`, `--only-version`, increments, or auto-answer flags.
It explicitly disables CI detection even when `CI=true` or a vendor CI variable is present
in a real terminal. Without TTY input **and** output, it exits before loading release config
or executing hooks, version writes, or Git actions. Piped answers are not a fallback.

The example is a real release command, not a dry-run command. Configure separate diagnostic
or CI commands when requested; do not quietly turn this command into either mode. Existing
recommendation and pre-release settings cannot overwrite the exact selection. The first
external plugin checks release-it's resolved current/next versions in `beforeBump`, before
file writes. Review custom plugins for earlier side effects or version-provider overrides;
the example's tested changelog integration is conventional-changelog 12.0.0.

## Prompt Adapter Interface and Compatibility

Source-confirmed integration for **release-it 21.0.1**:

| Surface | Required behavior |
|---|---|
| `release(options, { prompt })` | Second argument supplies the prompt instance; a top-level `createPrompt` option is not sufficient |
| `register(definitions, namespace = 'default')` | Merge a plugin's named definitions into its namespace |
| `show({ enabled = true, prompt, namespace = 'default', task, context })` | Resolve the registered definition, ask via clack, then await `task(answer)` |
| Git definitions | `commit`, `tag`, `push`, each with `type: 'confirm'` and `message(context)` |
| Disabled step | Return false without asking or executing; setup rejects disabled Git actions for the default flow |
| No/cancel | Throw `ReleaseStopped`; never return a false answer to release-it and continue |

There is no `run()` method in this interface. The adapter supports the three Git confirmations
and fails on an unexpected enabled prompt. npm publishing/OTP and hosted release prompts
require an explicitly extended adapter, with clack input/select/confirm handlers and their
own evaluation; use the existing publishing/CI references for those workflows.

`@clack/prompts` confirmation returns a boolean or cancellation symbol. Check `isCancel`
before truthiness. Use the registered message with its execution-time context so the commit
message and selected tag stay visible. The adapter calls the supplied task exactly once on
yes and awaits it before the next question; it never shells out to Git itself.

This injection is visible in source and is not a promised stable prompt customization API.
Before changing versions, inspect the installed dependency and re-run the PTY checks:

- [21.0.1 entry point](https://github.com/release-it/release-it/blob/21.0.1/lib/index.js)
- [Prompt registration and execution](https://github.com/release-it/release-it/blob/21.0.1/lib/prompt.js)
- [Plugin step routing](https://github.com/release-it/release-it/blob/21.0.1/lib/plugin/Plugin.js)
- [Git actions and rollback](https://github.com/release-it/release-it/blob/21.0.1/lib/plugin/git/Git.js)
- [Config and CI precedence](https://github.com/release-it/release-it/blob/21.0.1/lib/config.js)

The executable example is checked on Node **24.14.0**, release-it **21.0.1**, clack **1.8.0**,
semver **7.8.5**, and conventional-changelog **12.0.0**. Inspect installed `engines` when
applying it: release-it 21.0.1 and conventional-changelog 12.0.0 require Node
`^22.21.0 || >=24.0.0`, while clack
1.8.0 requires `>=20.12.0`. Compatibility with another release-it version is unverified
until its interface and behavior are checked; do not change a project's runtime silently.

## Stopping and Remaining State

release-it's stock Git plugin continues after a false confirmation result. Throwing stops
the remaining lifecycle, but its default clean-directory mode also installs exit/SIGINT
handlers that can delete the tag and reset the commit. The example checks the entire
repository with `git status --porcelain --untracked-files=all` itself, then passes
`git.requireCleanWorkingDir: false` to prevent those handlers. This deliberately preserves
unfinished work for inspection instead of triggering destructive automatic rollback.

| Stop at | Expected local state after normal preparation | Subsequent work |
|---|---|---|
| App/version selection | Original version, index, HEAD, tags | No release-it invocation |
| Commit confirmation | Version/changelog edits may already be staged | No commit, tag, or push |
| Tag confirmation | Release commit remains locally | No tag or push |
| Push confirmation | Release commit and selected tag remain locally | No push |

Always inspect actual state; preparation can differ and a callback may complete without
creating a new commit. The example reports on-disk version, `HEAD` before/after, index/worktree
status, exact local tag ref, and whether push was attempted/completed. It makes no automatic
rollback claim. Never invoke `after:release` push hooks as a substitute for the push step.

An execution error or signal outside a prompt is different from declining a confirmation.
A failed push can partially affect the remote; 21.0.1 may also attempt `git push origin
--delete <tag>` in its own push-error path even with local exit rollback disabled. Report
the remote state as unverified until inspected. Do not promise recovery of arbitrary hooks
or remote systems, and do not automatically delete local work after a deliberate stop.

## Evaluation

Use [evals.json](../evals/evals.json) for generated-output comparisons and the isolated
PTY runner in [run_interactive.py](../evals/run_interactive.py) for executable behavior.
Test first-question order, selected app/version propagation, confirmation/action interleaving,
every no/cancel boundary, recommended increments, inherited CI/mode options, and non-TTY
input/output. The runner requires an already installed dependency directory and writes only
temporary repositories. It replaces every `git push` with an argument-recording executable;
it never calls a remote push or deployment. Inspect both the event log and final Git/file
state; a source-text assertion or dry run alone does not demonstrate these behaviors.
