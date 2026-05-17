# Routing Rules

The main agent routes each item in the sub-agent report using the rules below. This file is the **canonical** location for the Step 5.5 routing-completion gate and the rejection log schema; other files reference it.

## 4-1. Regular `issues` / `missing` routing

For each `issues[*]` and `missing[*]`:

| Condition | Decision |
|-----------|----------|
| `evidence` is a direct quote and the fact is verifiable | **Accept** |
| `evidence` is an explicit cue from the user's input (Coverage / Constraints axes) | **Accept** |
| `evidence` missing, or is a paraphrase rather than a direct quote | **Downgrade** per `report_format.md` |
| Finding expands beyond the applicable user request or explicitly narrowed verification scope (matches out-of-scope items in `verification_criteria.md`) | **Reject** |
| The same or equivalent finding was accepted in a prior iteration and is already addressed | **Reject** |
| Finding contradicts a verified fact | **Reject** |

**Always log the reason for rejection internally.** Required for Stable findings and Oscillation detection in the next iteration.

Missing user-requested requirements are non-minor by default. Treat each accepted `missing[*]` item as `major` unless the evidence clearly shows it is only a minor presentation/detail omission that cannot change the response direction.

### `scope_creep` routing

For `issues[*].criterion=scope_creep`:

- If the same root cause also creates a factual, coverage, reasoning, constraints, or evidence issue with `blocker` or `major` severity, route that separate non-scope issue through the auto-fix path first.
- Otherwise, do not auto-fix, silently remove, or silently keep the overreach.
- Mark it as a pending Phase B user-decision item: ask whether to keep or remove it only after Phase A has produced a round with no accepted non-minor fixes. It is not terminal until the user decision is recorded or the main agent determines the item was invalid and rejects it with a logged reason.

## 4-2. `unverified_assertions` routing (3-way branch)

Branch by `source_of_uncertainty` × `affects_direction`:

| source_of_uncertainty | affects_direction | Decision |
|-----------------------|-------------------|----------|
| `user_input_ambiguity` | true | **Ask user in Phase B** after accepted non-minor fixes have been re-verified |
| `user_input_ambiguity` | false | Use default, state the assumption |
| `unverifiable_fact` | true | Main resolves before termination (see procedure below). **Never ask the user.** |
| `unverifiable_fact` | false | Rewrite as a hedge |
| `minor_default` | (any) | State the assumption, leave as is |

### `unverifiable_fact` + `affects_direction=true` resolution procedure

Each item must be driven to one of two terminal states before Step 5.5 (routing-completion gate) passes:

1. **Direct verification path** — Main agent uses read-only tools (Read, Glob, Grep; WebFetch for response-cited URLs only) or, where allowed, runs verification commands. Reflect the verified fact in the new draft (correct, confirm, or remove the assertion).
2. **Hedge path** — If direct verification is impossible in this environment, rewrite the assertion in the draft so it no longer asserts the unverified fact (hedge wording, narrow the claim, or remove it).

Mark the item with a resolution tag in the routing log:

```yaml
unverifiable_fact_resolution:
  - assertion_id: u1
    state: verified_reflected | hedged
    iteration: <n>
```

The Step 5.5 gate requires zero items in any other state. Positive termination triggers (`clean_pass`, `severity_floor`) cannot fire while unresolved items remain — see `termination_triggers.md`.

### User-question format

If multiple `user_input_ambiguity` items appear at once, **batch them into a single question turn** to conserve the user's context. If the current iteration also accepted any non-minor fix, defer the question until the next verification round confirms that those fixes are clean. After the user answers, resume from Step 1 — **do not reset the iteration counter**.

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

## Step 5.5 — Routing-completion gate (canonical definition)

Before evaluating termination (Step 6), confirm every routed item is in a terminal state. A handled item is one of:

- `issues[*]` / `missing[*]`: accepted (integrated into the new draft) or rejected (with reason logged in the rejection log).
- `issues[*].criterion=scope_creep`: either rejected with a logged reason, or logged as a pending Phase B keep/remove decision item after Phase A is clean. A pending Phase B item blocks positive termination.
- `unverified_assertions[*]` with `affects_direction=true` and `source_of_uncertainty=unverifiable_fact`: marked `verified_reflected` or `hedged` in `unverifiable_fact_resolution` above.
- `unverified_assertions[*]` with `source_of_uncertainty=user_input_ambiguity` and `affects_direction=true`: either answered by the user or logged as a pending Phase B user-question item after Phase A is clean. A pending Phase B item blocks positive termination.
- All other `unverified_assertions[*]`: handled per section 4-2 (hedge or stated assumption).

If any item remains unresolved, return to Step 5 and resolve it before Step 6. **Positive termination triggers (`clean_pass`, `severity_floor`) cannot fire while unresolved items or pending Phase B user-decision items exist.**

## After routing

- Integrate all accepted items into the new response.
- If at least one item was accepted and integrated, immediately run another clean-context verification round before surfacing Phase B items to the user.
- Hedge changes and assumption statements should be woven into the prose naturally. Do not force a separate "Notes" section unless the user requested one.
- The updated text becomes the next iteration's `current_response`.
