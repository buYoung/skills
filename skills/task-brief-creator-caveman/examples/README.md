# Examples

End-to-end worked scenarios for `task-brief-creator-caveman`. Each file
contains the input, what the skill did at each stage, and the resulting
executable implementation plan (or halt response). Examples `01`, `02`, `04`, `05`, and `06`
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

**How to read these files.** The saved plan in each example is the *work
instruction*. Its nine required H2 sections include `Execution Plan`, the
authoritative stage sequence for a single plan or child plan. The meta sections (input, codebase review notes, decision
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
| [01-pm-paste-feat.md](01-pm-paste-feat.md) | Pasted PM spec, ~20 lines | `feat` | Confirmed/inferred As-Is evidence, ordered stages, and a bounded worker choice instead of a technical Open Question; only the saved plan uses caveman full. |
| [02-rough-typed-fix.md](02-rough-typed-fix.md) | One-line typed task | `fix` | `Reproduction` gates Stage 1, stage completion stays separate from whole-work acceptance, and credentials remain references; step order survives caveman conversion. |
| [03-halt-ambiguous.md](03-halt-ambiguous.md) | Vague one-liner | — | Halt case; what the four-anchor check rejects, what additional input would flip it to CONTINUE, and where the narrow target probe fits when only TARGET is missing. (No saved brief — chat-only, normal prose.) |
| [04-briefset-checkout-i18n.md](04-briefset-checkout-i18n.md) | Tech-lead Korean note | briefset (`refactor`+`feat`+`fix`) | Addressable handoffs, pairwise parallel/hotspot rules, no-change branches, and verification inputs/signals; saved parent and child bodies use caveman full without compressing fixed fields. |
| [05-stage-4-walkthrough.md](05-stage-4-walkthrough.md) | Korean refactor note | `refactor` | Codebase probes remove technical questions, one user-owned scope decision remains, and Stage 5.5 reconstructs the executable route while checking caveman ambiguity. |
| [06-caveman-style-feat.md](06-caveman-style-feat.md) | Pasted English spec | `feat` | Minimal conversion demo preserving evidence tags, full execution grammar, `(proposed)`, `≤ 100ms`, tooltip text, and structured normal-prose questions. |

Stage 4 always runs an ownership pass and uses the Markdown decision table
with `순번`, `내용`, `수정 추천안`, and `근거` only when user-owned decisions remain.
Saved questions use `- [non-blocking] ... — Default: ...; Reconfirm before: ...`;
technical unknowns and reversible choices move into stages, replan boundaries, or worker decisions.
Use `01` / `02` / `04` for type-specific output shape (`feat` /
`fix` / briefset), use `05` for the most focused Stage 4
decision-table walkthrough plus the shortest Stage 5.5 execution reconstruction and Stage 5.7 cold-pickup
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
skill package directory. When extracted briefs live outside the
hypothetical host repo, pass that host repo as
`--repo-root <repository-root>` so standard entry-point paths do not
need artifact-only rewrites.
