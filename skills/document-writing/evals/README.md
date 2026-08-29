# Document-writing evaluation notes

The manifests define realistic prompts, observable contracts, and private semantic expectations. They prove behavior only when the harness runs the skill in an isolated workspace and validates the resulting response and files.

## Schema-v3 evidence boundary

The harness never asks a worker to report status, telemetry, tool events, or changed paths. It embeds the complete task JSON in the dispatch message so the worker does not retype a task-file path. The worker writes only the user response and permitted workspace artifacts. The finalizer derives the execution receipt from the task, response hash, and before/after manifests.

`required_capabilities` tells the dispatcher what a task needs. `denied_capabilities` is an execution policy, but no raw tool receipt is inferred when the host cannot attest it. Observable files, source markers, binary structure, and workspace manifests form the deterministic evidence. Missing raw telemetry remains `unavailable`; capability evidence remains `unverified`.

## Deterministic checks

- `validate_existing_update.mjs` requires content and accessibility owners while preserving protected existing files.
- `validate_warning_update.mjs` requires the approved warning value to reach its token owner and alert consumer without unrelated changes.
- `validate_preservation.mjs --exact-tree` rejects any create, delete, rename, or edit in review and collision cases.
- `validate_noncanonical_store.mjs` requires an in-place storefront update and rejects a duplicate canonical path.
- `validate_design_system_output.py` checks `index.md`, explicit platform or storefront owners, and an optional filename-independent PNG contract.
- `validate_eval_run.py` checks manifests, allowed paths, questions, real ISO dates, source markers, and PNG structure without using tool events.

Run validators against copies in an evaluation workspace, never against package-owned fixtures.

## Live research checks

Storefront requirements are time-sensitive. Deterministic checks require observable HTTPS sources and a real verification date. The independent grader decides whether each source is first-party and actually supports the recorded requirement. Web-unavailable cases must not invent a domain, date, source title, or mutable requirement.

## Trigger and selection checks

`trigger-evals.json` requires the actual skill-selection mechanism; parsing the file does not establish trigger quality. The production workflow does not execute a new selection benchmark. It reuses the preserved selection result only when the current frontmatter description SHA-256, selection dataset SHA-256, and prior evidence SHA-256 all match exactly.

## Current-only schema-v3 workflow

The production suite defines eval 1 through 32 once with the current skill. It contains no baseline, repetition, blind comparison, or worker self-report. Run the deterministic preflight once before any model dispatch. If it fails, do not call Luna or rerun the preflight in that attempt.

Create a full scope by omitting `--eval-ids`, or a targeted scope by listing the selected evals:

```bash
python3 skills/document-writing/scripts/test_eval_validators.py
python3 skills/document-writing/scripts/run_production_evals.py \
  --stage prepare \
  --eval-ids 22,15,10,26,27,24
```

For strict fail-fast execution, finish one eval before preparing the next. Pass the emitted `dispatch_message` verbatim to one fresh `gpt-5.6-luna` `medium` context; it already contains the authoritative task JSON.

```bash
python3 skills/document-writing/scripts/run_production_evals.py \
  --stage direct-behavior-prepare --iteration <N> --eval-id 22
# Execute the emitted dispatch_message exactly once.
python3 skills/document-writing/scripts/run_production_evals.py \
  --stage direct-behavior-finalize --iteration <N> --eval-id 22
```

If execution and deterministic checks pass, prepare one private grader. The grader sees only the prompt, semantic expectations, response, workspace, execution receipt, and deterministic checks.

```bash
python3 skills/document-writing/scripts/run_production_evals.py \
  --stage direct-grading-prepare --iteration <N> --eval-id 22
# Execute the emitted grader dispatch_message exactly once.
python3 skills/document-writing/scripts/run_production_evals.py \
  --stage direct-grading-finalize --iteration <N> --eval-id 22
```

The independent grader writes this contract and does not report telemetry, tool events, produced paths, or execution status:

```json
{
  "schema_version": 3,
  "status": "completed-independent-grading",
  "provenance": "independent-luna-grader-output",
  "eval_id": 22,
  "grader_task_context_id": "<task value>",
  "model": "gpt-5.6-luna",
  "reasoning_effort": "medium",
  "expectations": [
    {"text": "<exact supplied expectation>", "passed": true, "evidence": "<specific artifact evidence>"}
  ],
  "summary": {"passed": 1, "failed": 0, "total": 1, "pass_rate": 1.0}
}
```

Continue to the next eval only when the current grader is structurally valid and every semantic expectation passes. Any missing, invalid, or failed execution or grade ends the attempt without repair or retry.

After the prepared scope ends, aggregate, generate the skill-creator static review, and publish evidence:

```bash
python3 skills/document-writing/scripts/run_production_evals.py --stage aggregate --iteration <N>
python3 skills/document-writing/scripts/run_production_evals.py --stage review --iteration <N>
python3 skills/document-writing/scripts/run_production_evals.py --stage evidence --iteration <N>
```

The aggregate separately reports planned tasks, present responses, valid execution receipts, deterministic passes and failures, completed independent grades, and semantic passes. With no grades, macro pass rate is `null`, not zero. Harness task IDs are explicitly not raw host model context IDs.

Targeted evidence always keeps `production_ready: false`, even when every selected eval passes. A later full release requires all 32 receipts, all 32 independent grades, all hard gates, macro pass rate at least 0.90, reused selection thresholds, a valid eval 24 document and PNG, and a generated static review.

Ordinary verification for a targeted iteration is:

```bash
python3 skills/document-writing/scripts/validate_package.py skills/document-writing
pnpm test
```

Do not use `--require-production-ready` for targeted evidence. Schema-v2 iterations remain immutable diagnostic audit material and can never satisfy release validation.

## CI limitation

CI validates package structure, hashes, links, syntax, and deterministic negative controls. It does not dispatch model contexts, perform live research, create images, or grade outputs. Passing CI proves the evidence contract, not fresh model quality or storefront-policy currency.
