# Examples

End-to-end worked scenarios for `task-brief-creator`. Each file contains the
input, what the skill did at each stage, and the resulting brief (or halt
response). Use these to see what the contract looks like in practice.

| File | Input shape | Type | What it shows |
|---|---|---|---|
| [01-pm-paste-feat.md](01-pm-paste-feat.md) | Pasted PM spec, ~10 lines | `feat` | Long-input case; how Stage 3 codebase review trims As-Is and how Out-of-Scope guards a downstream agent. |
| [02-rough-typed-fix.md](02-rough-typed-fix.md) | One-line typed task | `fix` | Short-input case; how `fix`-type behavior profile shapes Acceptance Criteria and Side Effect Checkpoints (reproduce-first). |
| [03-halt-ambiguous.md](03-halt-ambiguous.md) | Vague one-liner | — | Halt case; what the four-anchor check rejects and what additional input would flip it to CONTINUE. |

The brief outputs in `01` and `02` pass `scripts/validate_brief.py`. Treat
them as the structural reference shape.
