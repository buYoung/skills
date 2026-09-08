# Impact Detection

## Trace a concrete behavior

Start with the requirement and changed entrypoint in the selected version. Identify the calling inputs and follow each relevant value through wrappers, defaults, option merges, adapters, and final I/O or state changes. Track returns, rejection/error translation, cleanup, and cancellation back to the caller as well.

For an options change, inspect property names, units, defaulting operators, merge order, spread order, and overwritten values. Verify timeout and cancellation reach the operation that waits or performs I/O, rather than stopping at a wrapper argument. Check declared runtimes and dependency versions before relying on an API's semantics.

Use repository navigation for symbol definitions, callers, re-exports, route/event registrations, generated wiring, and configuration readers. Searches are candidate evidence, not a consumer census: aliases, callbacks, dynamic dispatch, and external consumers may require other evidence. Use Git revision/index searches for non-worktree targets. Scope searches to relevant directories and file types; the archived broad-search blocks below are not a reason to search the entire repository by default.

## Evaluate contracts in context

Inspect public exports, request/response shapes, persistence schemas, accepted values, errors, ordering, and operational settings. A removed member or stricter input is a compatibility signal, not an automatic defect. Follow compatibility adapters, fallbacks, version negotiation, migration order, and actual consumers before deciding whether a supported path breaks. Optional additions can still affect exhaustive matching, strict schemas, or serialization.

Check both direct callers and transitive/shared-state consumers. Describe the failing supported behavior and its impact; neither raw match counts nor normalized consumer counts set severity. If external consumers cannot be inspected, name the unresolved contract and evidence needed rather than assuming either safety or breakage.

## Test evidence

Read the assertions and what reaches them: inputs, mocks, boundaries, asynchronous completion, and observed outputs. Distinguish a test checking an intermediate argument from one verifying behavior at the final consumer. Existing tests are not proof merely because their names mention the feature. Missing tests are a verification gap, not a standalone behavioral defect or severity multiplier. Recommend focused validation only where useful; do not create tests as part of a review request.

## Counterevidence and maintainability

For each candidate defect, verify the trigger is reachable, inspect existing defenses, and compare the selected base. Discard intentionally supported behavior and pre-existing issues; consolidate one root cause across layers into one finding.

Maintainability observations need present evidence: repeated policy that must be updated together, branching that obscures a current invariant, or coupling that forces unrelated callers to change. Cite the locations, describe the current cost, and suggest a bounded improvement with a concrete benefit. Do not relabel maintainability as a defect without an actual incorrect execution path.

## Limits

Separate code-supported conclusions from execution results and open questions. State unresolved dynamic wiring, unavailable dependencies, unreviewed files, and inaccessible external consumers precisely. Do not invent confidence percentages or use uncertainty to escalate severity.

## Archived literal examples

These preserved blocks are historical examples, not steps to execute. Use the current workflow above. Single-commit `show` examples require the root/merge handling above; inclusive range commands require a valid parent. Merge-base commands apply only to an explicitly requested common-ancestor comparison, never as fallback. Worktree `rg` examples must not supply historical or index context.

```bash
rg -F "<symbol_name>(" .
```

```bash
rg "<symbol_name>" .
```

```bash
rg "<entrypoint_or_contract_name>" .
```

```bash
rg "<public_surface_indicator>.*<symbol_name>|<symbol_name>.*<public_surface_indicator>" .
```
