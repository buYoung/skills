# Routing Rules

The main agent routes each item in the sub-agent report using the rules below.

## 4-1. Regular `issues` / `missing` routing

For each `issues[*]` and `missing[*]`:

| Condition | Decision |
|-----------|----------|
| `evidence` is a direct quote and the fact is verifiable | **Accept** |
| `evidence` is an explicit cue from the user's input (Coverage / Constraints axes) | **Accept** |
| `evidence` missing, or is a paraphrase rather than a direct quote | **Downgrade** per `report_format.md` |
| Finding expands scope beyond the user's request (matches out-of-scope items in `verification_criteria.md`) | **Reject** |
| The same or equivalent finding was accepted in a prior iteration and is already addressed | **Reject** |
| Finding contradicts a verified fact | **Reject** |

**Always log the reason for rejection internally.** Required for Stable findings and Oscillation detection in the next iteration.

## 4-2. `unverified_assertions` routing (3-way branch)

Branch by `source_of_uncertainty` × `affects_direction`:

| source_of_uncertainty | affects_direction | Decision |
|-----------------------|-------------------|----------|
| `user_input_ambiguity` | true | **Ask user** (pause loop) |
| `user_input_ambiguity` | false | Use default, state the assumption |
| `unverifiable_fact` | true | Main verifies directly (tools / search) or rewrites as a hedge. **Never ask the user.** |
| `unverifiable_fact` | false | Rewrite as a hedge |
| `minor_default` | (any) | State the assumption, leave as is |

### User-question format

If multiple `user_input_ambiguity` items appear at once, **batch them into a single question turn** to conserve the user's context. After the user answers, resume from Step 1 — **do not reset the iteration counter**.

## Rejection log schema

Required for every rejected item:

```yaml
rejected:
  - issue_id: i3
    reason: scope_creep | redundant | factually_wrong | weak_evidence
    iteration: <n>
```

This log feeds:

- **Oscillation detection** — has the same issue alternated between accept and reject?
- **Stable findings detection** — does the same issue keep reappearing?
- **Final metadata** — the `rejected_findings[]` array in the termination block.

## After routing

- Integrate all accepted items into the new response.
- Hedge changes and assumption statements should be woven into the prose naturally. Do not force a separate "Notes" section unless the user requested one.
- The updated text becomes the next iteration's `current_response`.
