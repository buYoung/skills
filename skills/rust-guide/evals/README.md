# Evaluation Cases

`evals.json` holds six prompt-only cases, one per routing area: collections, concurrency, build configuration, edition 2024 migration, unsafe/FFI review, and release-range upgrade planning. Each `expected_output` describes the judgments and evidence labels a good answer contains; there are no fixtures or validators yet.

Run a case by giving the prompt to an agent with this skill loaded and grading the response against `expected_output`, preferably next to a run without the skill. Version-specific claims in a response should be checked against `references/versions/index.md` and the per-version files and the official release notes, because the correct answer changes with each stable release.
