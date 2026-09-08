# Evaluation Cases

`evals.json` contains the three existing regression cases and one SSR case. Inputs live in `fixtures/`; each case has a matching `validators/<case-name>.mjs`. Execute an evaluation on an isolated copy of its fixture, following the selected skill version and the case prompt. Keep original fixture files unchanged and save the agent's `REPORT.md` beside its repaired source.

Run the matching validator against that output directory:

```sh
node skills/vite-guide/evals/validators/ssr-production-artifacts.mjs /absolute/path/to/repaired-fixture
```

Validators emit JSON `checks` with `text`, `passed`, and `evidence`, and exit nonzero when a check fails. They use Node built-ins and do not install React, Vite, or browser tooling. The fixture package metadata describes the target application contract, not an instruction to install dependencies during evaluation.

## Mechanical Checks and Semantic Review

The SSR validator loads the existing production adapter against synthetic built HTML, a built server module, and a client SSR manifest without installed Vite. It also checks source/configuration and launch commands. This is an artifact-loading smoke check, not a Vite build or deployment test. Review development lifecycle, build flag placement, manifest consumer semantics, conditional exports, and runtime dependencies separately. Real builds, external package resolution, browser interactivity, and host deployment need the configured application environment.

The existing validators include source-pattern heuristics and report-topic checks. Retain their raw results when a semantic reviewer identifies a false positive or false negative. Review the actual implementation and report claims against each expectation; record the reason for any different semantic grade. Do not change a validator or weaken an expectation solely to make an output pass.

For version comparisons, use the same prompt, fixture, model, and effort for the original and revised skills. Keep both outputs, raw checks, semantic grades, and verification limits. Separate original-case regression results from the new SSR case. A single paired run does not establish statistical improvement, and source checks do not establish application performance. Generate the comparison viewer with skill-creator's `eval-viewer/generate_review.py` so the report and code changes can be inspected together.
