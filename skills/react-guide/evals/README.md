# Evaluation Cases

`evals.json` contains the three existing regression cases and one SSR case. Inputs live in `fixtures/`; each case has a matching `validators/<case-name>.mjs`. Execute an evaluation on an isolated copy of its fixture, following the selected skill version and the case prompt. Keep original fixture files unchanged and save the agent's `REPORT.md` beside its repaired source.

Run the matching validator against that output directory:

```sh
node skills/react-guide/evals/validators/ssr-profile-hydration.mjs /absolute/path/to/repaired-fixture
```

Validators emit JSON `checks` with `text`, `passed`, and `evidence`, and exit nonzero when a check fails. They use Node built-ins and do not install React, Vite, or browser tooling. The fixture package metadata describes the target application contract, not an instruction to install dependencies during evaluation.

## Mechanical Checks and Semantic Review

The SSR validator executes the store factory to check snapshot identity, immutable updates, fixed hydration snapshots, request isolation, and unsubscribe behavior. Source indicators cover bootstrap, IDs, timestamp, and retained interactions. Review the complete server-to-client payload flow and HTML-safe serialization separately; regex presence cannot prove them. Real React rendering/hydration, concurrent host requests, focus/drafts, streaming, and cancellation need a configured application runtime.

The existing validators include source-pattern heuristics and report-topic checks. Retain their raw results when a semantic reviewer identifies a false positive or false negative. Review the actual implementation and report claims against each expectation; record the reason for any different semantic grade. Do not change a validator or weaken an expectation solely to make an output pass.

For version comparisons, use the same prompt, fixture, model, and effort for the original and revised skills. Keep both outputs, raw checks, semantic grades, and verification limits. Separate original-case regression results from the new SSR case. A single paired run does not establish statistical improvement, and source checks do not establish application performance. Generate the comparison viewer with skill-creator's `eval-viewer/generate_review.py` so the report and code changes can be inspected together.
