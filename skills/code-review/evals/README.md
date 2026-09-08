# Code Review Evaluation

This is a small regression comparison, not a general performance guarantee. Three synthetic Python repositories cover mixed uncommitted changes, historical option propagation, and compatibility with duplicated policy. There is one independent run per case and skill version, using `gpt-5.6-sol` with `high` reasoning. No repeated-run variance or production-wide accuracy is established.

## Reproduce

1. Before changing the skill, copy the existing package into a temporary directory outside the repository. Keep the snapshot and execution repositories temporary.
2. Run `python3 skills/code-review/evals/build_fixtures.py <fresh-temporary-directory>/fixtures` from the repository root. The builder refuses to reuse existing case directories and uses local fixture commits without hooks or remote access.
3. Make separate filesystem copies of each fixture for each configuration, preserving `.git`, staged contents, unstaged changes, and untracked files. Supply each independent agent only its skill path, its repository path, and the corresponding prompt from `evals.json`. Do not provide expected outputs, assertions, sibling repositories, prior findings, or counterpart results. Use the same model and reasoning for both configurations.
4. Save each report to `iteration-1/eval-<id>-<name>/<with_skill|old_skill>/outputs/review.md`, and record executed commands and investigated paths in `transcript.md` beside `outputs/`. Store the prompt and assertions in the parent `eval_metadata.json` for grading, outside the review agent's inputs.
5. Grade the five dimensions separately using reports and investigation records: defect detection, false positives, target fidelity, evidence for maintainability, and unsolicited verdicts. Findings must have correct causal evidence, not merely match keywords. A no-defect case tests restraint; an omitted maintainability section is acceptable only in cases without an expected maintainability observation.
6. Generate the comparison page with the skill-creator `eval-viewer/generate_review.py`, using a benchmark file and `--static <output.html>`. Label the baseline as the previous skill, even if a viewer schema names it `without_skill`. Keep reports and evidence alongside the page. Do not treat an aggregate pass count as a code-review verdict.

Run `PYTHONDONTWRITEBYTECODE=1 python3 skills/code-review/evals/verify_git_examples.py` from the repository root for deterministic Git examples. It checks unborn/root histories, endpoint versus common-ancestor comparisons, inclusive ranges, merge-parent views and combined-diff omissions, partial staging, untracked files, clean state, and unresolved index stages. All repositories are temporary; these checks do not modify the working repository's index.

## Scope limits

The behavior comparison does not measure explicit verdict requests, large repositories, real external consumers, every Git failure mode, or model variance. Those rules are checked by reading the skill contract and Git examples, not claimed as agent-evaluated outcomes. Missing runtime/token telemetry is unknown, never zero. Temporary agent copies may contain verification artifacts; compare tracked/index/untracked state to distinguish these from source modifications.
