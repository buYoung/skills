# Interactive Release Evaluation

The requests in [evals.json](evals.json) cover configuration, CLI/CI preservation, separate
version providers, plugins, single service apps, monorepos, and inherited mode/version
settings. Compare fresh generation with an appropriate skill snapshot using the same
prompt. Grade complete
scripts and configurations, not the presence of the requested words. Keep generated-output
grades separate from execution results for the packaged examples.
See [comparison-results.md](comparison-results.md) for the historical generated-output
comparison and its remaining verification-guidance gap. That comparison predates the Inquirer
migration; the evaluation prompts now request Inquirer, but their generated-output scores
have not been rerun. The execution results below cover the current packaged examples
and documented plugin code; they are not new generated-output benchmark scores.

## Executable Example Checks

[run_interactive.py](run_interactive.py) copies the exact packaged example scripts into
new temporary repositories and runs `pnpm release` through POSIX pseudoterminals. It uses
only the Python standard library and preinstalled project dependencies. From the repository
root, run it with a new disposable output directory:

```bash
python3 skills/release-it/evals/run_interactive.py \
  --dependencies /path/to/preinstalled/node_modules \
  --output /tmp/release-it-interactive-check
```

Install the dependency versions in [interactive-workflow.md](../references/interactive-workflow.md)
in a temporary environment first. The runner does not install dependencies or use the
skill repository's release configuration. `--case single-success` runs one named scenario.

Each scenario writes an ordered question/action log, raw terminal transcript, and disposable
Git repository. The run also records dependency/tool versions and SHA-256 hashes of the
example modules. Actual `npm version`, changelog generation, local Git commit, and local
tag operations execute. Git fetch is a local stub and **every Git push** records its full
arguments and cwd without contacting a remote. No publishing or deployment runs.

The assertions verify:

- The first question is version selection for a single project, including one with a
  settings-only `pnpm-workspace.yaml`; a monorepo first selects one service app.
- Choosing API or Web changes that app's version/changelog/tag and leaves the root,
  sibling app, and shared library manifests/changelogs unchanged.
- Patch, minor, beta, and custom exact choices reach the real version file and changelog.
- Every commit/tag/push confirmation precedes exactly one awaited matching action;
  no/cancel leaves the observed staged files, commit, or local tag and stops later actions.
- Enter alone approves each Git confirmation, including push, with `(Y/n)` displayed.
  Invalid custom versions can be corrected and
  submitted, while Ctrl+C during custom input stops before writes. Cancellation is reported
  with its stage instead of exposing an Inquirer exception.
- Recommended major increments, inherited CI/version/snapshot flags, `CI=true`, and
  `GITHUB_ACTIONS=true` do not replace the patch selection or skip confirmations.
- A plugin returning a different resolved version stops before writes.
- Redirected input, output, or both, and bypass flags stop before release work.
- Unrelated untracked files inside/outside the app survive `--update`; pre-existing
  untracked files in the staging scope are rejected with `addUntrackedFiles: true`, while
  files outside it remain untouched. Existing version inputs must be tracked.
- Tracked sibling changes and newly staged files outside the app block before version
  writes, and the original work/index content remains intact.
- Cancellation, preparation failure, and preflight errors produce one reason message.
  Missing local tags do not leak Git fatal output, and an injected lookup failure is
  reported as an inspection failure rather than "tag absent".

The runner waits for prompt markers before answering. It does not infer a question from
an interval with no output. Its preserve-state assertions describe the packaged example's
policy; a generated restoration policy needs separate baseline/ownership checks.

## Documented Plugin Checks

[run_plugin_contracts.mjs](run_plugin_contracts.mjs) extracts the minimal version-provider
and complete webhook plugin from the reference and loads their actual code into release-it.
Run from the repository root with the same dependency directory and a new output directory:

```bash
node skills/release-it/evals/run_plugin_contracts.mjs \
  /path/to/preinstalled/node_modules /tmp/release-it-plugin-check
```

The checks verify product-version reads/writes with a separate tooling package version,
npm-plugin disabling, named prompt definitions and default Yes through release-it's stock
prompt, explicit decline, and dry-run preservation of files and notification calls.
A marker fixture verifies external A/B ordering relative to the core version plugin in
each lifecycle phase. Another verifies that the API logs and rethrows one plugin error.
Prompt answers and `fetch` are local stubs; no notification is sent.

## Independent Forward Check

One fresh-context generation applied the skill to an existing `release-it --ci` workflow
with GitHub Releases, a tooling package at 9.9.9, and product versions in `VERSION` and
`release-manifest.json`. It generated a provider/config without introducing an interactive
wrapper and exercised the real API and CLI with network sinks replaced locally.

All five checks passed: CLI dry-run, API release, CLI release, a repeated fixed target,
and malformed manifest input. Product files reached 2.3.5 while the tooling manifest stayed
byte-identical; local release commits contained the two intended outputs. Dry-run and
rejected-input checks preserved files and Git state. GitHub request payloads received the
selected tag/version through a stub. [forward-results.json](forward-results.json) records
the generated artifact hashes, check outcomes, and the temporary evidence location.

This is one generated scenario, not a rerun of all nine evaluation prompts or the historical
comparison. Mid-write failure recovery, real remote publication, and authentication were
not verified. The fixed-target repeat guard is that generated solution's policy, not a
universal CLI requirement. This check exposed the distinction between stock equal-version
resolution and the interactive menu's strict increase rule; the CLI reference now documents it.

## Recorded Result

On 2026-09-25, **43/43 PTY scenarios and 7/7 plugin checks passed** using Node 24.14.0,
npm 11.9.0, pnpm 10.11.0, Git 2.50.1 (Apple Git-155), release-it 21.0.1,
`@inquirer/prompts` 8.5.2, semver 7.8.5, and conventional-changelog 12.0.0.
See [interactive-results.json](interactive-results.json) for per-scenario outcomes,
recorded push arguments, and example hashes; [plugin-results.json](plugin-results.json)
records the reference hash and plugin outcomes.

Supporting checks passed for all three JavaScript modules, the Python runner, evaluation
JSON files, JSON reference blocks, and package-local Markdown links/fragments. The
skill-creator `quick_validate.py` passed using an isolated Python environment with PyYAML.

The prior 2026-09-08 run passed 32/32 PTY scenarios under the former default-No policy.
Its separate check against the copied Inquirer example verified real `AbortSignal` cancellation
becomes a stage-specific `ReleaseStopped`, an unexpected error is rethrown unchanged, and a
false answer remains false for the adapter to decline. Those separate helper checks were
not rerun in the 2026-09-25 execution set.

These results do not establish real remote behavior, remote push recovery, deployment,
publishing/OTP extensions, arbitrary project hooks/plugins, Windows execution, or another
release-it version. Re-run the checks after adapting the examples to the applying project.
