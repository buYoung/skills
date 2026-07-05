# Examples

End-to-end worked scenarios for `task-brief-creator-caveman`. Each file
contains the input, what the skill did at each stage, and the resulting
brief (or halt response). Examples `01`, `02`, `04`, `05`, and `06`
additionally include a `Picked Up Cold` section showing the first
actions a coding agent takes from the saved brief alone; `03` is a halt
case, so there is no brief to pick up.
`Picked Up Cold` is example commentary only.
It is not part of the saved brief template and should not be emitted into
real `docs/briefs/` artifacts.

**All saved-brief code blocks in these examples are written in caveman
full mode** per `references/caveman-style.md`. Stage 4 decision tables,
Stage 6 save reports, validator transcripts, the meta sections, and
this README itself stay in normal prose — caveman applies only to the
saved brief artifact, never to chat / interview / status surfaces. The
`## Open Questions` section inside each saved brief also stays in
normal prose per the Auto-Clarity carve-outs (alongside paths,
identifiers, error strings, ordered repro, and contract precision); see
`references/caveman-style.md` for the full conversion rules.

**How to read these files.** The saved brief in each example is the *work
instruction*. The meta sections (input, codebase review notes, decision
table, notes) explain how the skill arrived at that instruction — they
are commentary, not deliverable. If you only have time to skim one part,
read the saved-brief code block plus the commentary-only `Picked Up Cold`
section and you have the core contract.

**A note on paths (precondition for the pass claims below).** Saved-brief
code blocks use illustrative paths (`src/auth/validation.ts`,
`src/i18n/messages.ko.json`, …) that do not exist in this repository.
They are written from the perspective of a hypothetical host repo, and
the validators check that inline-code entry points exist on disk. The
pass claims at the bottom of this file therefore hold when each brief is
extracted into a scratch directory's `docs/briefs/` with every referenced
path created as a dummy file. If you copy a saved-brief block into your
own repository instead, replace the illustrative paths with real ones —
otherwise the path-existence check will correctly flag them as missing.

| File | Input shape | Type | What it shows |
|---|---|---|---|
| [01-pm-paste-feat.md](01-pm-paste-feat.md) | Pasted PM spec, ~20 lines | `feat` | Long-input case; how Stage 3 codebase review *grounds* As-Is in concrete files (without dropping concerns from the input) and how Out-of-Scope guards a downstream agent. Saved brief in caveman full — register-only, same enumerate depth as the normal-mode equivalent. |
| [02-rough-typed-fix.md](02-rough-typed-fix.md) | One-line typed task | `fix` | Short-input case; how `fix`-type behavior profile shapes Acceptance Criteria and Side Effect Checkpoints (reproduce-first), and how credentials are referenced instead of embedded. Reproduction step order preserved through caveman. |
| [03-halt-ambiguous.md](03-halt-ambiguous.md) | Vague one-liner | — | Halt case; what the four-anchor check rejects, what additional input would flip it to CONTINUE, and where the narrow target probe fits when only TARGET is missing. (No saved brief — chat-only, normal prose.) |
| [04-briefset-checkout-i18n.md](04-briefset-checkout-i18n.md) | Tech-lead Korean note | briefset (`refactor`+`feat`+`fix`) | Briefset mode; how mixed types, ordered dependencies, and a shared i18n conflict hotspot drive the parent + 3 children decomposition, with cold-pickup running on parent + every child. Parent and child briefs both in caveman full. |
| [05-stage-4-walkthrough.md](05-stage-4-walkthrough.md) | Korean refactor note | `refactor` | Focused Stage 4 example; how codebase probes remove technical questions, the remaining scope decisions become a user decision table, Stage 5.5 checks downstream interpretation, and the Stage 5.7 cold-pickup gate fires on a `refactor` type with the caveman-only `over_terse_bullets` report field. Behavior Contract precision still survives caveman. |
| [06-caveman-style-feat.md](06-caveman-style-feat.md) | Pasted English spec | `feat` | Simplest caveman demo on a small `feat` input; how the body compresses while the `(proposed)` marker, `≤ 100ms` threshold, and tooltip string stay verbatim. Use this as the minimum-friction reference when learning the conversion. |

Stage 4 always runs as a Markdown decision table with `순번`, `내용`,
`수정 추천안`, and `근거` after codebase-resolvable nodes are probed.
Use `01` / `02` / `04` for type-specific output shape (`feat` /
`fix` / briefset), use `05` for the most focused Stage 4
decision-table walkthrough plus the shortest Stage 5.5 interpretation and Stage 5.7 cold-pickup
demonstration, and use `06` for the smallest caveman conversion. See
`references/stage-4-interview.md` for the decision-table policy,
`references/cold-pickup.md` for the cold-pickup execution rules, and
`references/caveman-style.md` for the caveman conversion rules.

Under the dummy-path precondition above, the brief outputs in `01`,
`02`, `05`, and `06` each pass `scripts/validate_brief.py` with exit
code 0 and 0 warnings.
For `04`, the parent and child 01 as shown — together with minimal
conforming caveman versions of children 02 and 03, which the example
only sketches — pass `scripts/validate_briefset.py` (one invocation,
transitive child checks) with exit code 0 and 0 warnings; each child
also passes `validate_brief.py` individually with 0 warnings. Caveman
compresses prose, not structure — the structural validator does not
check writing style, so caveman bodies pass exactly the same checks as
their normal-prose equivalents. Run the validators from the installed
skill package directory:
`python3 <skill-dir>/scripts/validate_brief.py docs/briefs/<file>.md`.
