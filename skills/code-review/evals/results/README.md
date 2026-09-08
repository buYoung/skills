# Evaluation Results

[Open the comparison viewer](review.html). The Outputs tab contains six review reports and their individual grades. The Benchmark tab compares the revised `with_skill` configuration with the previous `old_skill` configuration. [Structured results](benchmark.json) retain the evidence for each assessment.

Both configurations used independent `gpt-5.6-sol` agents with `high` reasoning and no shared conversation history. Agents received their assigned skill, an isolated repository copy, and the same case prompt. They were instructed not to read answer keys, evaluation assertions, or counterpart results. The main agent graded the reports against the fixtures and executor-authored investigation records; the grader was not blind to configuration.

| Dimension | Revised | Previous | Interpretation |
|---|---:|---:|---|
| Defect detection / correct no-defect result | 3/3 | 3/3 | Both found the shipping calculation and historical option-loss defects, and accepted the compatible response adapter. |
| No behavioral false positives | 3/3 | 3/3 | Neither treated compatibility or absent tests as a behavioral defect. |
| Target fidelity | 3/3 | 2/3 | Previous skill explicitly excluded unstaged changes and the untracked consumer in the default review. |
| Grounded maintainability or appropriate omission | 2/3 | 3/3 | Revised mixed-case report inferred a shared policy from equal 10% literals without an established shared policy owner. Both correctly described the explicitly shared policy in the compatibility case. |
| No unsolicited verdict | 3/3 | 0/3 | Previous reports emitted COMMENT, COMMENT, and APPROVE; revised reports omitted verdicts. |
| Total expectations | 14/15 | 11/15 | Descriptive case results, not a review approval score or overall quality guarantee. |

The mixed-case maintainability observation explains a possible centralization benefit, but matching values alone do not prove that checkout and renewal rates must change together. This was graded conservatively as insufficient evidence, not hidden by the aggregate result. The separate compatibility fixture explicitly establishes one shared policy and both reports ground their observations in it.

The previous historical review initially searched worktree files but then reconfirmed its conclusions against the selected revision. It therefore passes target fidelity for this outcome. The compatibility fixture's worktree equals its index, so success there does not demonstrate that the previous skill would preserve index semantics under divergence.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python3 skills/code-review/evals/verify_git_examples.py`: passed the unborn/root, endpoint/common-ancestor, inclusive range, merge-parent, partial-staging, untracked, clean-state, and unresolved-conflict checks in temporary repositories.
- Package link, fenced-block preservation, skill-name/catalog-state, evaluation-shape, and Python syntax checks passed.
- `git diff --check -- skills/code-review README.md`: passed.
- Existing fenced blocks remain verbatim in explicitly inactive archival sections. The active prose replaces their former unconditional output and fallback rules.
- No source changes were made in the fixture repositories by review agents. Some agents placed requested transcript artifacts inside their isolated repositories or created and removed Python cache files; these are distinguished from the original fixture content.

## Limitations

This is one run per configuration on three small synthetic cases. No repeated-run variance, general detection advantage, or production accuracy is established. Token and duration telemetry was unavailable. Investigation records are agent-authored summaries rather than complete raw execution transcripts. Explicit verdict requests, every Git failure mode, large changes, and inaccessible external consumers were not behaviorally evaluated.

Fixture reproduction scripts and prompts are in the [evaluation directory](../README.md). Baseline skill copies and execution repositories remain in temporary storage. Reports below preserve the agents' original Korean responses and recorded commands; temporary paths are historical execution evidence, not portable setup instructions.

| Case | Revised report | Previous report |
|---|---|---|
| Mixed changes | [Report](mixed/with_skill/review.md) | [Report](mixed/old_skill/review.md) |
| Historical commit | [Report](historical/with_skill/review.md) | [Report](historical/old_skill/review.md) |
| Compatibility and policy | [Report](compatibility/with_skill/review.md) | [Report](compatibility/old_skill/review.md) |
