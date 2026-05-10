# Examples

End-to-end worked scenarios for `task-brief-creator-caveman`. Each file
contains the input, what the skill did at each stage, the resulting
brief (or halt response), and a `Picked Up Cold` section showing the
first actions a coding agent takes from the saved brief alone.

**All saved-brief code blocks in these examples are written in caveman
full mode** per `references/caveman-style.md`. Stage 4 interview prose,
Stage 6 save reports, the meta sections, and this README itself stay in
normal prose — caveman applies only to the saved brief artifact, never
to chat / interview / status surfaces. See
`references/caveman-style.md` for the full conversion rules and
Auto-Clarity carve-outs (paths, identifiers, error strings, ordered
repro, contract precision).

**How to read these files.** The saved brief in each example is the *work
instruction*. The meta sections (input, codebase review notes, interview
exchange, notes) explain how the skill arrived at that instruction — they
are commentary, not deliverable. If you only have time to skim one part,
read the saved-brief code block plus `Picked Up Cold` and you have the
core contract.

**A note on paths.** Saved-brief code blocks use illustrative paths
(`src/auth/validation.ts`, `src/i18n/messages.ko.json`, …) that do not
exist in this repository. They are written from the perspective of a
hypothetical host repo. If you copy a saved-brief block into a real
`docs/briefs/` and run `validate_brief.py`, the path-existence check will
correctly flag those paths as missing. Replace them with paths from your
own repository.

| File | Input shape | Type | What it shows |
|---|---|---|---|
| [01-pm-paste-feat.md](01-pm-paste-feat.md) | Pasted PM spec, ~10 lines | `feat` | Long-input case; how Stage 3 codebase review *grounds* As-Is in concrete files (without dropping concerns from the input) and how Out-of-Scope guards a downstream agent. Saved brief in caveman full — register-only, same enumerate depth as the normal-mode equivalent. |
| [02-rough-typed-fix.md](02-rough-typed-fix.md) | One-line typed task | `fix` | Short-input case; how `fix`-type behavior profile shapes Acceptance Criteria and Side Effect Checkpoints (reproduce-first). Reproduction step order preserved through caveman. |
| [03-halt-ambiguous.md](03-halt-ambiguous.md) | Vague one-liner | — | Halt case; what the four-anchor check rejects and what additional input would flip it to CONTINUE. (No saved brief — chat-only, normal prose.) |
| [04-briefset-checkout-i18n.md](04-briefset-checkout-i18n.md) | Tech-lead Korean note | briefset (`refactor`+`feat`+`fix`) | Briefset mode; how mixed types, ordered dependencies, and a shared i18n conflict hotspot drive the parent + 3 children decomposition. Parent and child briefs both in caveman full. |
| [05-stage-4-walkthrough.md](05-stage-4-walkthrough.md) | Korean refactor note | `refactor` | Focused Stage 4 example; how codebase probes remove technical questions and the remaining scope decisions become a user decision table. Behavior Contract precision still survives caveman. |
| [06-caveman-style-feat.md](06-caveman-style-feat.md) | Pasted English spec | `feat` | Simplest caveman demo on a small `feat` input; how the body compresses while the `(proposed)` marker, `≤ 100ms` threshold, and tooltip string stay verbatim. Use this as the minimum-friction reference when learning the conversion. |

Current Stage 4 uses a Markdown decision table with `순번`, `내용`,
`수정 추천안`, and `근거` after codebase-resolvable nodes are probed.
Use `01` / `02` / `04` for type-specific output shape (`feat` /
`fix` / briefset), use `05` for the most focused Stage 4
decision-table walkthrough, and use `06` for the smallest caveman
conversion. See `references/stage-4-interview.md` for the current
decision-table policy and `references/caveman-style.md` for the
caveman conversion rules.

The brief outputs in `01`, `02`, `05`, and `06` pass
`scripts/validate_brief.py`. The parent + children in `04` pass
`scripts/validate_briefset.py` (and each child also passes
`validate_brief.py`). Caveman compresses prose, not structure — the
structural validator does not check writing style, so caveman bodies
pass exactly the same checks as their normal-prose equivalents.
