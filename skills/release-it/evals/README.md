# Interactive Release Evaluation

The three added prompts in [evals.json](evals.json) cover a single service app, one app
in a monorepo, and inherited mode/version settings. Compare fresh generation with the
original skill snapshot and the improved skill using the same prompt. Grade complete
scripts and configurations, not the presence of the requested words. Keep generated-output
grades separate from execution results for the packaged examples.
See [comparison-results.md](comparison-results.md) for the recorded generated-output
comparison and its remaining verification-guidance gap.

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
- Recommended major increments, inherited CI/version/snapshot flags, `CI=true`, and
  `GITHUB_ACTIONS=true` do not replace the patch selection or skip confirmations.
- A plugin returning a different resolved version stops before writes.
- Redirected input, output, or both, and bypass flags stop before release work.

## Recorded Result

On 2026-09-08, **27/27 scenarios passed** using Node 24.14.0, npm 11.9.0, pnpm 10.11.0,
Git 2.55.0, release-it 21.0.1, clack 1.8.0, semver 7.8.5, and conventional-changelog 12.0.0.
See [interactive-results.json](interactive-results.json) for per-scenario outcomes,
recorded push arguments, and example hashes.

JavaScript and Python syntax, evaluation JSON, JSON reference examples, and package-local
Markdown links were also checked. The skill-creator Python frontmatter validator could
not import PyYAML; the YAML frontmatter and its name/description constraints were checked
with the available Node `yaml` 2.9.0 parser instead. Do not report the unavailable Python
validator as passing.

These results do not establish real remote behavior, remote push recovery, deployment,
publishing/OTP extensions, arbitrary project hooks/plugins, Windows execution, or another
release-it version. Re-run the checks after adapting the examples to the applying project.
