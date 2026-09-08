# Output Format

## Current report contract

Write in the user's language, translating prose and severity labels while preserving paths, identifiers, logs, and requested verdict tokens. Keep the report proportional to findings, without filling empty categories or adding formal praise.

Use this order:

1. **Review target**: selected revision(s) or index/worktree scope, comparison meaning/base, and path restrictions. Mention meaningful coverage exclusions.
2. **Defects**, ordered by actual importance. If none are confirmed, say so explicitly. Each entry contains a concise title and severity, a precise location in the reviewed version (prefer the smallest relevant changed range), trigger, code-supported execution path, expected versus actual behavior, impact, and remediation direction. Do not attach current-worktree line numbers to historical evidence; identify the revision and path. For deletions, cite the base location explicitly.
3. **Maintainability observations**, only when supported. Cite present complexity/duplication/coupling, current maintenance cost, and a concrete improvement benefit. These are non-blocking observations, separate from defect severity.
4. **Verification and limitations**: exact checks actually run and results, static-only analysis, unreviewed areas, external consumers not inspected, and unresolved questions with the missing evidence needed. Never claim an unrun check passed.

Severity describes demonstrated impact and trigger conditions: **Critical** for severe security/data/availability consequences, **Major** for material incorrect behavior, **Minor** for bounded low-impact defects. Style-only preferences are omitted unless requested. Lack of tests and number of consumers do not promote severity. Evidence gaps belong in verification questions, not speculative confirmed findings or numeric confidence scores.

Example defect in prose: **[Major] Forward request options to transport** at `client.py:28` in revision C. When a caller supplies a timeout and cancellation token, the wrapper drops both before `transport.send`, which waits without those controls. Forward the supported options while preserving caller values. Static tracing establishes the dropped arguments; no runtime test was run.

Example maintainability observation: `checkout.py:18` and `renewal.py:31` independently encode the same current discount policy. Both paths must be updated for each policy revision. A shared policy function would centralize that rule while preserving each path's orchestration.

## Verdict only on request

Do not emit an approval or change-request verdict by default. If explicitly requested, append one token with a concise reason:

| Verdict | Evidence-based decision |
|---|---|
| `REQUEST_CHANGES` | A confirmed defect needs correction, regardless of count. |
| `COMMENT` | No established correction already determines the decision, but unresolved facts prevent a sound approval. Name what must be verified. |
| `APPROVE` | Review is sufficiently complete for the stated scope and no blocking defect is established. |

Confirmed defects needing correction take precedence over unresolved questions. Maintainability observations alone do not block changes. Do not derive the verdict from counts, weighted scores, consumer totals, or missing tests alone. A claimed no-defect result does not establish completeness.

## Archived output examples (not the current contract)

The literal blocks below are retained solely to preserve existing fenced content. They describe the former schema, including confidence tiers, empty severity sections, Highlights, and an unconditional verdict. Do not use that schema for new reports; apply the current contract above. The old grouping example also mixes maintainability with defect severity; new reports keep them separate.

```
## Review Summary
- **Target**: <commit_hash | start_hash~end_hash | staged changes>
- **Author**: <name>
- **Files Changed**: <count>
- **Lines**: +<added> / -<deleted>

## Findings

### Critical (<count>)
...

### Major (<count>)
...

### Minor (<count>)
...

### Nit (<count>)
...

## Analysis Limitations
- <unverifiable area or analysis constraint>

## Highlights
- <notable positive practice, if any>

## Decision Rationale
- <why this verdict was selected>

## Verdict
<APPROVE | REQUEST_CHANGES | COMMENT>
```

```
#### [<severity>] <title>
- **File**: `<file_path>:<line_number>`
- **Issue**: <description>
- **Evidence**: <specific code/path/behavioral evidence>
- **Impact**: <user/service/data/operational impact>
- **Confidence**: <High | Medium | Low>
- **Suggestion**: <at least one remediation direction>
```

```
#### [Major] Incompatible output contract for downstream consumer
- **File**: `service/account/response_mapper.ext:118`
- **Issue**: Response field `accountStatus` was renamed to `status` without compatibility mapping
- **Evidence**: Consumer adapters still reference `accountStatus` in runtime parsing logic
- **Impact**: Downstream consumers may fail to parse responses, causing request failures
- **Confidence**: High
- **Suggestion**: Add compatibility mapping or versioned response contract before removing old field
```

```
## path/to/file.ext
- [Major] Contract incompatibility (L118)
- [Minor] Error context is underspecified (L44)
```
