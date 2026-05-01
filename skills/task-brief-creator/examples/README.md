# Examples

End-to-end worked scenarios for `task-brief-creator`. Each file contains the
input, what the skill did at each stage, the resulting brief (or halt
response), and a `Picked Up Cold` section showing the first actions a
coding agent takes from the saved brief alone.

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
| [01-pm-paste-feat.md](01-pm-paste-feat.md) | Pasted PM spec, ~10 lines | `feat` | Long-input case; how Stage 3 codebase review trims As-Is and how Out-of-Scope guards a downstream agent. |
| [02-rough-typed-fix.md](02-rough-typed-fix.md) | One-line typed task | `fix` | Short-input case; how `fix`-type behavior profile shapes Acceptance Criteria and Side Effect Checkpoints (reproduce-first). |
| [03-halt-ambiguous.md](03-halt-ambiguous.md) | Vague one-liner | — | Halt case; what the four-anchor check rejects and what additional input would flip it to CONTINUE. |
| [04-briefset-checkout-i18n.md](04-briefset-checkout-i18n.md) | Tech-lead Korean note | briefset (`refactor`+`feat`+`fix`) | Briefset mode; how mixed types, ordered dependencies, and a shared i18n conflict hotspot drive the parent + 3 children decomposition. |

The brief outputs in `01` and `02` pass `scripts/validate_brief.py`. The
parent + children in `04` pass `scripts/validate_briefset.py` (and each
child also passes `validate_brief.py`). Treat all of them as the
structural reference shape for their respective modes.
