# Document-writing evaluation notes

The manifests define realistic prompts and observable expectations. They do not prove behavior until a harness copies the listed fixture files into an isolated workspace, executes the skill, and grades the resulting files and transcript.

`required_capabilities` lists tools that the harness must enable. A dispatcher that supports per-run tool policies must withhold `denied_capabilities`; the direct runner also rejects any reported denied use. On hosts that cannot physically remove tools per subagent, the resulting local-unattested evidence proves only the published policy and recorded events, not raw platform-level absence.

## Deterministic fixture checks

- Existing update: run `node evals/validators/validate_existing_update.mjs <fixture-root> <result-root>`; it requires the new content/accessibility owners and index links while preserving exact token, team-note, and integration files.
- Review or collision: run `node evals/validators/validate_preservation.mjs <fixture-root> <result-root> --exact-tree` so any create, delete, rename, or edit fails.
- Existing non-canonical storefront: run `node evals/validators/validate_noncanonical_store.mjs <fixture-root> <result-root>` to require ownership at the established path, an in-place update, and no duplicate file for the same storefront.

Run these commands from the `skills/document-writing` directory against copies in a temporary evaluation workspace. Never run a mutating eval against the package-owned fixture directory.

## Live research checks

Storefront research is intentionally live because mutable requirements must be current. Grade the execution transcript as well as the final files:

- Confirm that the agent opened first-party operator pages rather than relying on a search snippet or remembered value.
- Match each mutable requirement to an opened URL and verification date.
- Run web-unavailable behavior separately; the agent must not invent a domain, attempted URL, source title, or requirement.

Live research results are time-sensitive and should not be treated as deterministic snapshots.

## Trigger checks

`trigger-evals.json` must be run through the actual skill-selection mechanism using the current frontmatter description. Parsing the JSON alone does not establish trigger precision or recall.

## Production benchmark workflow

Run the production benchmark from the active Codex task with direct subagents, web access, and image-generation capability. CI does not replace this run or claim that it executed an LLM.

Run these commands from the repository root. Use the iteration number emitted by the first command as `<N>` in every later command.

```bash
python3 skills/document-writing/scripts/test_eval_validators.py
python3 skills/document-writing/scripts/run_production_evals.py --stage prepare
python3 skills/document-writing/scripts/run_production_evals.py --stage direct-behavior-prepare --iteration <N>
python3 skills/document-writing/scripts/run_production_evals.py --stage direct-selection-prepare --iteration <N>
```

Use one agent per run: each direct behavior agent receives only one task from `direct-behavior-tasks.json`, its isolated workspace, and the current answer-free skill snapshot (the `without_skill` task has no skill path). Dispatch the two behavior configurations in paired concurrent batches, then write `direct-response.md` and `direct-agent-report.json`. The execution model is `gpt-5.6-luna` with reasoning effort `medium`. The report must include `produced_paths` (workspace-relative changed files), `telemetry_status`, and nullable `duration_ms`/`total_tokens`, plus an allowlisted terminal status, exit/timeout/stderr fields, and strict `{name,input,status,output}` events. Those events are agent-reported capability claims—not raw Codex platform telemetry—and the reconstructed transcript must disclose that provenance. After all 40 runs finish, finalize their deterministic artifacts.

Use `gpt-5.6-sol` with reasoning effort `medium` for failure analysis. Run the two blind comparators independently with that same model and effort; the forward and reversed comparator records are separate inputs and must not share reasoning.

```bash
python3 skills/document-writing/scripts/run_production_evals.py --stage direct-behavior-finalize --iteration <N>
```

Selection uses three fresh Codex contexts for the current description only. Give each agent only one `direct-selection/*-input.json`; it must write the corresponding output JSON with exactly 60 `{id, selected, reason}` decisions. Finalize those decisions into 180 per-case receipts (60 cases × 3).

These receipts are local-unattested independent Codex judgments over the current frontmatter description. They measure the routing contract consistently, but they are not product-runtime automatic-selection telemetry and must not be described as such. Publish the three original label-free batch inputs, batch outputs, context identifiers, batch durations, stderr, and hashes. Per-case transcripts are declared synthetic projections of those batch outputs and must not duplicate batch duration as per-case timing.

```bash
python3 skills/document-writing/scripts/run_production_evals.py --stage direct-selection-finalize --iteration <N>
```

After the two behavior repetitions, an independent grader must replace every `grading.json` with `status: completed-independent-grading`. Copy every entry from `deterministic-grading.json` exactly—including failed integrity checks—and add exactly one `{text, passed, evidence}` record for each semantic expectation in `eval_metadata.json`. Do not add scoring filler or duplicate an expectation. Recalculate the summary from that exact combined array. An integrity-invalid run is an execution failure and is excluded from quality scoring; it must never be converted into a failed quality expectation. Integrity checks reject writes to directories or outside the workspace, mismatched manifests or `produced_paths`, forbidden/denied capability use, missing required capability, mutations under `deny_write_tools`, workspace changes after `clarification_required`, and `without_skill` skill/sibling-result evidence.

```json
{
  "status": "completed-independent-grading",
  "expectations": [
    {"text": "<exact deterministic or semantic expectation>", "passed": true, "evidence": "<specific transcript or output evidence>"}
  ],
  "summary": {"passed": 1, "failed": 0, "total": 1, "pass_rate": 1.0}
}
```

If a run is integrity-invalid, exclude it from scoring. Use `gpt-5.6-sol` with reasoning effort `medium` to record the failure cause, rebuild both sides of that exact eval/repetition from their original fixtures, and dispatch the pair again in two fresh contexts. Do not add a third scored repetition. Generate final evidence only after all 40 base runs are valid, the blind comparison records one anonymized verdict for each of the 20 pairs, the Google Play document-plus-image canary is copied into the iteration with `image-canary.json`, and the static review exists.

```bash
python3 skills/document-writing/scripts/run_production_evals.py --stage aggregate --iteration <N>
python3 skills/document-writing/scripts/run_production_evals.py --stage compare-prepare --iteration <N>
```

Run two independent comparators for every `comparisons/eval-*-run-*` directory, giving each only anonymized `A/` and `B/` outputs, their per-side grading summaries, `pair.json`, and the comparator contract. Save forward and reversed verdicts as `comparison-forward.json` and `comparison-reversed.json`; the reversed input swaps A/B. Do not expose `.blind-mapping.json`. Each verdict needs non-generic reasoning, at least two concrete evidence references, rubric/expectation detail, and must agree with the authoritative deterministic checks. The runner maps both verdicts back to the real outputs: agreement yields `current` or `without_skill`, disagreement is a tie. A tie is credited to the current skill while raw wins and ties remain separately recorded. The aggregate reports `total_pairs`, `current_wins`, `without_skill_wins`, `ties`, `credited_current_wins = current_wins + ties`, and `current_win_rate = credited_current_wins / total_pairs`. The production gate is 0.95.

```bash
python3 skills/document-writing/scripts/run_production_evals.py --stage compare-finalize --iteration <N>
```

`generate_review.py` creates the static review page from the same iteration's graded `benchmark.json`.
Set `CC_SKILL_CREATOR_PATH` to the skill-creator package root or directly to
`generate_review.py` when it is not installed under `CODEX_HOME/skills/skill-creator`.

```bash
python3 skills/document-writing/scripts/run_production_evals.py --stage review --iteration <N>
```

The image canary manifest binds eval 24 to both deliverables. Paths are relative to the iteration root. `generated_source_path` is the untouched built-in image output; `source_path` is the exact `1024×500` no-alpha export. Hash the exact built-in prompt text as UTF-8 and both PNG files as bytes.

```json
{
  "eval_id": 24,
  "passed": true,
  "source_path": "image-canary/orbit-notes-feature-graphic-1024x500.png",
  "generated_source_path": "image-canary/orbit-notes-feature-graphic.png",
  "document_source_path": "image-canary/docs/marketing/google-play",
  "document_response_path": "image-canary/assistant-response.md",
  "source_urls": ["https://support.google.com/googleplay/android-developer/answer/9866151?hl=en"],
  "width": 1024,
  "height": 500,
  "image_tool_calls": 1,
  "generation_tool": "image_gen",
  "generation_prompt": "<exact built-in image prompt>",
  "generation_prompt_sha256": "<sha256>",
  "generated_source_sha256": "<sha256>"
}
```

The evidence stage checks the manifest against the suite's eval ID and artifact name, preserves the generated source, copies the final PNG, validates PNG chunks and scanlines, and writes content-addressed generation and document bundles under `evals/evidence/`.

```bash
python3 skills/document-writing/scripts/run_production_evals.py --stage evidence --iteration <N>
python3 skills/document-writing/scripts/validate_package.py skills/document-writing
pnpm test
```

The runner generates `production-evidence.json` and artifacts under `evals/evidence/`. Evidence declares `trust_boundary: local-unattested`: the package validator checks internal consistency, real calendar dates, the current contract hash, artifact paths and hashes, run metadata, hard gates, selection metrics, blind comparison, and the image canary, but it is not a cryptographically signed remote attestation. A `diagnostic-failed` schema-v2 snapshot may be accepted by the ordinary package-structure check only as a clearly labelled measurement; it must not be represented as 40 fully attested runs, and missing context/tool telemetry or receipts must not be invented. Use `--require-production-ready` for release validation; it rejects diagnostic evidence and `production_ready: false`. Iteration-8 is diagnostic-only and is never accepted as production evidence. The contract digest excludes evidence files and evidence artifacts so refreshing evidence does not create a digest cycle.

## CI limitation

CI and the release hook run only the package validator and deterministic validator self-tests. They do not dispatch Codex subagents, perform live web research, generate images, grade outputs, or run blind comparison. A passing CI result therefore establishes the evidence format, hashes, and negative controls—not fresh model quality or the factual currency of storefront policy.
