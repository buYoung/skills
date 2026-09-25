# Interactive Release Workflow

## Contract

Use this reference when generating an interactive service-app command. Existing CLI/CI,
publishing, and other programmatic workflows retain their own contracts unless the request
changes them. For this command, use these question/action sequences:

- Single project: `pnpm release → version → commit? / commit → tag? / tag → push? / push`.
- Monorepo: `pnpm release → one service app → version → commit? / commit → tag? / tag → push? / push`.

All questions use `@inquirer/prompts`. A single project starts directly with the version
question; neither a target picker nor a start confirmation belongs before it. Read-only
preflight checks may fail before the first question. In a monorepo, always show the service
app picker, including when there is only one eligible app. Configure the eligible apps
during setup; do not guess from every workspace package. See [monorepo.md](monorepo.md).

The version menu shows the current version and each concrete next version. A suggested bump
can be a label or initial selection, but still requires a submitted answer. Pass an exact
semver selected by the user to release-it. Do not first ask all three Git confirmations:
each confirmation belongs at its action's execution point.
Use Inquirer's native `y/n` confirmation with `default: true` for commit, tag, and push:
`(Y/n)` means Enter approves the displayed action. This includes push and any automation
triggered by it. An explicit No stops that action and the remaining flow; Ctrl+C cancels
an active selection, input, or confirmation. Defaults and stop behavior are separate:
changing a confirmation default must not turn No into "skip this action and continue".

## Copyable Project Example

Copy these complete files into the applying project's `scripts/` directory:

- [release.mjs](../examples/interactive-release/release.mjs): terminal and repository checks,
  structure detection, target selection, version menu, release-it API call, state reporting.
- [release-prompts.mjs](../examples/interactive-release/release-prompts.mjs): Inquirer adapter,
  stop exception, and a plugin that checks the chosen version before any bump.

These are project-generation examples, not commands to release the skill repository.
Their supported base is a pnpm-invoked service app whose `package.json` owns a semver
version. This is a concrete example, not a requirement that every product use Node
versioning. Adapt the connected consumers below when using a different provider, runner,
or version format. See the [version source contract](plugins.md#version-source-contract).

| Consumer | Adaptation |
|---|---|
| Target discovery | Resolve the applying project's release units; a tooling workspace need not describe every application |
| `readCurrentVersion(directory)` | Read the selected product's actual source; both selection and state reporting use this function |
| `checkVersionSource(options, directory)` | Validate the selected provider, required inputs, and tracked/generated-file policy; allow `npm: false` when a custom plugin owns writes |
| `chooseVersion(currentVersion)` | Generate and validate candidates using the product's version format, including any build metadata policy |
| Resolved-version guard | Compare release-it's current/next values with what was displayed and selected before writes |
| Bump plugin and other writers | Update the same source and identify all additional outputs, including shared files outside the app |
| Staging and recovery | Apply the [working-state and recovery policy](git-integration.md#working-state-and-staging-scope) to those outputs and the shared index |

Changing only the reader is insufficient. The Node example's provider checks deliberately
reject a different configuration until these connections have been adapted.

Install the tested dependency set with the project's package manager (add `-w` for pnpm
workspace-root tooling):

```bash
pnpm add -D -E release-it@21.0.1 @inquirer/prompts@8.5.2 semver@7.8.5
# When using the changelog configuration below:
pnpm add -D -E @release-it/conventional-changelog@12.0.0 conventional-changelog-conventionalcommits@10.4.0
```

`semver` computes and validates menu values. Inquirer owns the questions; release-it and its
changelog plugin own the writes. Declare `@inquirer/prompts` as a direct development dependency
even though release-it also depends on it. Wrapper-owned cancellation and state messages
use `console.info`; inspection failures and other wrapper errors use stderr. The API logs
its own errors before throwing, and the wrapper avoids reprinting them. Its logger controls
the output stream, so capture both stdout and stderr when checking diagnostics.
Add the entry command to the root `package.json`:

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

The complete script checks repository-wide tracked/index state before selection, validates
the selected version inputs, and handles pre-existing untracked files according to the
staging options before this call. Review other plugin outputs during setup; those checks
are not automatic discovery of every writer. It rejects CLI
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
| `show({ enabled = true, prompt, namespace = 'default', task, context })` | Resolve the registered definition, ask via Inquirer, then await `task(answer)` |
| Git definitions | `commit`, `tag`, `push`, each with `type: 'confirm'` and `message(context)` |
| Disabled step | Return false without asking or executing; setup rejects disabled Git actions for the default flow |
| No/cancel | Throw `ReleaseStopped`; never return a false answer to release-it and continue |

There is no `run()` method in this interface. The adapter supports the three Git confirmations
and fails on an unexpected enabled prompt. npm publishing/OTP and hosted release prompts
require an explicitly extended adapter, with Inquirer input/select/confirm handlers and their
own evaluation; use the existing publishing/CI references for those workflows.

`@inquirer/prompts` confirmation resolves to a boolean; Ctrl+C rejects with `ExitPromptError`,
and an aborted signal rejects with `AbortPromptError`. Pass the prompt Promise to the async
`requireAnswer` helper without awaiting it first, so it can convert those two errors into a
stage-specific `ReleaseStopped`. Other errors propagate unchanged. The helper wraps only the
question, not the task callback, so execution errors are not classified as user cancellation.
Use the registered message with its execution-time context so the commit message and selected
tag stay visible. The adapter calls the supplied task exactly once on yes and awaits it before
the next question; it never shells out to Git itself.

For selections, use `choices` with `value`, `name`, and optional `description`; preserve the
selected app object and exact version as the returned values. Use `input` for a custom version,
with validation returning `true` on success or an error string on failure. Returning `undefined`
does not accept a valid answer in Inquirer.

This injection is visible in source and is not a promised stable prompt customization API.
Before changing versions, inspect the installed dependency and re-run the PTY checks:

- [21.0.1 entry point](https://github.com/release-it/release-it/blob/21.0.1/lib/index.js)
- [Prompt registration and execution](https://github.com/release-it/release-it/blob/21.0.1/lib/prompt.js)
- [Plugin step routing](https://github.com/release-it/release-it/blob/21.0.1/lib/plugin/Plugin.js)
- [Git actions and rollback](https://github.com/release-it/release-it/blob/21.0.1/lib/plugin/git/Git.js)
- [Config and CI precedence](https://github.com/release-it/release-it/blob/21.0.1/lib/config.js)

The executable example is checked on Node **24.14.0**, release-it **21.0.1**, Inquirer **8.5.2**,
semver **7.8.5**, and conventional-changelog **12.0.0**. Inspect installed `engines` when
applying it: release-it 21.0.1 and conventional-changelog 12.0.0 require Node
`^22.21.0 || >=24.0.0`, while `@inquirer/prompts`
8.5.2 requires `>=23.5.0 || ^22.13.0 || ^20.17.0`. Compatibility with another release-it version
is unverified until its interface and behavior are checked; do not change a project's runtime silently.

## Stopping and Remaining State

release-it's stock Git plugin continues after a false confirmation result. The adapter
throws to stop the remaining lifecycle. The example chooses to preserve interrupted work:
it prechecks tracked/index state, then passes `git.requireCleanWorkingDir: false` to prevent
the Git plugin's local exit/SIGINT rollback handlers. It does not automatically restore
version files after No or Ctrl+C. This is one explicit policy; use the
[recovery criteria](git-integration.md#recovery-policies) when a project requests restoration
or retains built-in rollback, and update the expected-state checks to match that policy.

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

This table applies to the Git-only example with reviewed preparation. Other enabled
plugins may already have published or performed external work before a Git question.
Execution failures, signals outside prompts, and failed pushes require separate state
inspection; disabling local rollback does not disable push-error remote cleanup.
See [lifecycle order](hooks-and-lifecycle.md#plugin-order-and-side-effects) and
[programmatic error ownership](cli-and-workflow.md#errors-and-diagnostic-commands).

## Evaluation

Use [evals.json](../evals/evals.json) for generated-output comparisons and the isolated
PTY runner in [run_interactive.py](../evals/run_interactive.py) for executable behavior.
Test first-question order, selected app/version propagation, confirmation/action interleaving,
every no/cancel boundary, Enter's default approval at all three Git steps, invalid custom-version
retry, recommended increments, inherited CI/mode options, and non-TTY input/output. Also check
untracked-file policy under both staging settings, preservation of unrelated files,
single cancellation/error diagnostics, and expected versus failed ref lookups.
The runner requires an already
installed dependency directory and writes only temporary repositories. It replaces every
`git push` with an argument-recording executable;
it never calls a remote push or deployment. Inspect both the event log and final Git/file
state; a source-text assertion or dry run alone does not demonstrate these behaviors.
It responds to observed prompt markers, not a fixed period of silence. To verify actual
ref transfer, use a separate disposable local bare remote and ensure every remote/push URL
points there. A push recorder proves call ordering and arguments, not remote effects.
