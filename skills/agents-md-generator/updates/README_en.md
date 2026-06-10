# Update History & Review Facts

This directory manages factual information regarding improvements and detailed review results for the `agents-md-generator` skill.

## Management Structure

All major updates or improvements are recorded in subdirectories following this naming convention:
`YYYY-MM-DD-[improvement-summary]`

Each folder must contain the following factual information:
- `review.md`: Detailed analysis of the update, improvements made, and rationale for the implementation. (Benchmark records may use `benchmark.md` instead.)
- `*.patch` (optional): Git patch files proving the actual code changes. Include when an output diff is part of the evidence.

## Update History (History)

- [2026-02-25] Initial setup of the update management structure.
- [2026-02-25] [JSON Template Formatting Review](./2026-02-25-json-template-formatting-review/review_en.md): Technical fact-based comparison review of three implementation methods for supporting template syntax during JSON formatting.
- [2026-03-11] [JSON Query Explanation Review](./2026-03-11-json-query-explanation-review/review_en.md): Comparison review of code-explanation quality with and without AGENTS.md.
- [2026-03-21] [Claude Skill 2.0 Apply Benchmark](./2026-03-21-claude-skill-2_0-apply/benchmark.md): Pass-rate comparison before/after deepening Section 3/4 analysis (36.4% → 77.3%).
- [2026-05-07] [JSON Query Explanation Review #2](./2026-05-07-json-query-explanation-review/review_en.md): Three-way comparison review — no AGENTS.md / old / new.
- [2026-06-10] [Adversarial Review Hardening](./2026-06-10-adversarial-review-hardening/review_en.md): Guards and script hardening for failure paths confirmed by sub-agent adversarial review (modifying externally-authored files, custom-section loss, monorepo false positives, budget contradiction, etc.).
