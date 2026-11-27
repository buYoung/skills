# Examples

End-to-end worked scenarios for `task-brief-creator`. Each file contains
the input, what the skill did at each stage, and the resulting executable implementation plan (or
halt response). Examples `01`, `02`, `04`, and `05` additionally include
a `Picked Up Cold` section showing the first actions a coding agent takes
from the saved brief alone; `03` is a halt case, so there is no brief to
pick up.
`Picked Up Cold` is example commentary only.
It is not part of the saved brief template and should not be emitted into
real `docs/briefs/` artifacts.

**How to read these files.** The saved plan in each example is the *work
instruction*; its `Execution Plan` section is the authoritative stage
sequence for a single plan or child plan. The meta sections (input,
codebase review notes, decision table, notes) explain how the skill
arrived at that instruction and are not part of the deliverable.

**A note on paths.** Saved-brief code blocks use illustrative paths
(`src/auth/validation.ts`, `src/i18n/messages.ko.json`, …) from a
hypothetical host repository, and the validators check that inline-code
entry points exist on disk. The pass claims below hold only after each
brief is extracted into a scratch directory's `docs/briefs/` with every
referenced path created as a dummy file. When you copy a saved-brief block
into your own repository, replace the illustrative paths with real ones.

| File | Input shape | Type | What it shows |
|---|---|---|---|
| [01-pm-paste-feat.md](01-pm-paste-feat.md) | Pasted PM spec, ~20 lines | `feat` | Long-input case; confirmed/inferred As-Is evidence, ordered execution stages, and a bounded worker choice instead of a technical Open Question. |
| [02-rough-typed-fix.md](02-rough-typed-fix.md) | One-line typed task | `fix` | Short-input case; how `Reproduction` gates Stage 1, stage completion stays separate from whole-work acceptance, and credentials are referenced instead of embedded. |
| [03-halt-ambiguous.md](03-halt-ambiguous.md) | Vague one-liner | — | Halt case; what the four-anchor check rejects, what additional input would flip it to CONTINUE, and where the narrow target probe fits when only TARGET is missing. |
| [04-briefset-checkout-i18n.md](04-briefset-checkout-i18n.md) | Tech-lead Korean note | briefset (`refactor`+`feat`+`fix`) | Addressable handoffs, pairwise parallel/hotspot rules, no-change branches, and verification inputs/signals; the parent owns child coordination while each child `Execution Plan` owns its internal stages. |
| [05-stage-4-walkthrough.md](05-stage-4-walkthrough.md) | Korean refactor note | `refactor` | Focused Stage 4 example; codebase probes remove technical questions, one user-owned scope decision remains, the Stage 5.6 self-check confirms intent fidelity, and a user-requested cold-pickup pass comes back clean. |

See `references/stage-4-interview.md` for the decision-table policy and
`references/cold-pickup.md` for the opt-in cold-pickup execution rules.

Under the dummy-path precondition above, extract the complete saved blocks in
`01`, `02`, `04`, and `05` using their documented filenames. Example `04`
includes the parent and all three complete children, so it needs no invented
stand-in children. Run `validate_brief.py` for single plans and
`validate_briefset.py` for the parent from the target repository root using
the absolute installed script path. For an isolated artifact tree, pass
`--repo-root <repository-root>` explicitly. Example `03` is intentionally
invalid.
The displayed semantic review reports are worked illustrations, not measured
agent-run results; a live run must report the checks it actually completed.