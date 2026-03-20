---
name: code-review
description: Performs production-ready code reviews on git changes. Supports commit/range/file-scoped analysis, impact assessment, breaking-change detection, confidence-aware finding classification, and risk-weighted verdict generation.
---

# Code Review Workflow

Use this workflow to review git changes with evidence-backed findings and risk-aware verdicts.

## Step 1: Determine Review Target

Identify what to review from the user's request.

| User Input | Action |
|------------|--------|
| Commit hash provided | Use that commit |
| Commit range (`start~end`) | Use the range (start = earliest, end = latest) |
| "리뷰해줘" / "review" with no hash | Use staged changes (`git diff --cached`). If nothing staged, use `HEAD` |
| File paths specified | Scope review to those files within the target |

Always confirm the target before proceeding:
```bash
git --no-pager show --stat <commit_hash>
# or for staged changes:
git --no-pager diff --cached --stat
```

## Step 2: Retrieve the Diff

Get the full diff for the review target. Refer to **[git_operations.md](references/git_operations.md)** for detailed commands and fallback handling (root commits, merge commits, range stabilization).

```bash
# Single commit
git --no-pager show <commit_hash>

# Staged changes
git --no-pager diff --cached

# Commit range
git --no-pager diff <start_hash>^..<end_hash>

# File-scoped
git --no-pager show <commit_hash> -- <file_path>
```

## Step 3: Classify Changes and Filter Noise

Categorize each changed file and filter out noise before deep review. This prevents wasting review effort on non-reviewable content.

### File Categories

| Category | Examples |
|----------|----------|
| **Source** | `.ts`, `.js`, `.py`, `.java`, `.go`, `.rs`, `.swift`, `.kt`, `.rb`, `.php`, `.c`, `.cpp` |
| **Test** | `*.test.*`, `*.spec.*`, `__tests__/*`, `test_*.*`, `*_test.*` |
| **Config** | `.json`, `.yaml`, `.toml`, `.env*`, `.*rc`, `config/*` |
| **Docs** | `.md`, `.rst`, `.txt`, `docs/*` |
| **Build/CI** | `Dockerfile*`, `Makefile`, `.github/workflows/*`, `*.gradle*` |
| **Deps** | `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `requirements*.txt` |

### Noise Filtering

Skip line-by-line review for these — check consistency/integrity only:

| Noise Type | Pattern | Handling |
|------------|---------|----------|
| Generated files | `generated/`, `*.pb.*`, `*.generated.*` | Inspect generation source instead |
| Lock files | `package-lock.json`, `yarn.lock`, `go.sum`, `Cargo.lock` | Verify manifest consistency only |
| Minified/bundled | `*.min.js`, `*.bundle.js` | Exclude from logic findings |
| Vendor/third-party | `vendor/`, `third_party/` | Evaluate integration impact only |
| Mechanical renames | Status `R`/`C` with no behavioral delta | Validate paths, then deprioritize |
| Format-only changes | Whitespace/indent-only diffs | Note as low-risk, skip deep analysis |

### Review Depth by Scale

| Files Changed | Strategy |
|---------------|----------|
| 1–10 | Full line-by-line review |
| 11–30 | Prioritize source/config, then tests/docs |
| 30+ | Separate noise first, sample low-risk files, full-review high-risk files |

### Always Full-Review (Regardless of Scale)

- Security/auth/authorization files
- Data schema, migration, persistence contracts
- Runtime entrypoints and routing bindings
- Critical production config files

## Step 4: Analyze Reviewable Files

Read the full context of each reviewable file to understand the change, not just the diff. Focus on:

- What behavior changed and why
- Whether the change is correct and complete
- Edge cases, error handling, boundary conditions
- Consistency with surrounding code patterns

## Step 5: Trace Impact

Identify who/what is affected by the changes. Refer to **[impact_detection.md](references/impact_detection.md)** for detailed techniques.

Key actions:
1. **Find consumers** — search for references to changed symbols, APIs, contracts
2. **Check exposure** — is the changed entity publicly consumed or internal-only?
3. **Detect breaking changes** — required inputs increased? Output contract changed? Symbols removed/renamed?
4. **Check test coverage** — do tests cover the changed behavior paths?

```bash
# Find direct callers
rg -F "symbolName(" .
# Find broader references
rg "symbolName" .
```

### Breaking Change Signals

| Change Type | Breaking? |
|-------------|-----------|
| New mandatory parameter/field | Yes |
| Removed/renamed output field | Yes |
| Accepted values narrowed | Yes |
| Endpoint signature changed | Yes |
| Additive optional extension | No (usually) |

If a breaking change has normalized consumers > 0, classify at least as **Critical candidate**.

## Step 6: Classify Findings

Assign each finding a **severity** and **confidence** level.

### Severity Levels

#### Critical
Immediate high risk to security, data integrity, availability, or external contracts.
- Security exposure: injection, credential leakage, auth bypass
- Data integrity: corruption, irreversible mutation, destructive migration without rollback
- Availability: crash loops, deadlock, unbounded resource exhaustion
- Breaking contract: incompatible changes on consumed public interfaces
- Rollback gap: no rollback path for high-impact operational changes

#### Major
Incorrect behavior, reliability degradation, or high operational cost.
- Behavioral defects: wrong branch logic, boundary errors, invalid fallbacks
- Performance: unbounded processing, repeated expensive ops
- Error handling gaps: swallowed failures, incorrect retries
- Concurrency/race conditions
- Observability regression: lost diagnostic context
- Config semantics drift without compatibility handling

#### Minor
Maintainability, readability, or medium-term quality concerns.
- Excessive complexity, duplicated logic
- Ambiguous naming, unclear control flow
- Tight coupling, low cohesion

#### Nit
Low-impact polish and consistency.
- Style/formatting drift
- Naming clarity improvements
- Outdated comments

### Critical vs Major Boundary

| Factor | → Critical | → Major |
|--------|-----------|---------|
| Data risk | Loss/corruption likely, irreversible | Inconsistency possible, recoverable |
| Business logic | Core transaction/auth broken | Limited-path incorrect behavior |
| Rollback | No safe rollback path | Rollback exists and is practical |
| Observability | Incident detection critically degraded | Degraded but manageable |

### Confidence Tiers

| Tier | Meaning |
|------|---------|
| **High** | Strong direct evidence; severity can be acted on directly |
| **Medium** | Credible but partially indirect evidence; include verification note |
| **Low** | Weak or indirect evidence; avoid automatic escalation, request manual verification |

### Escalation Rule

A Major finding becomes a `REQUEST_CHANGES` candidate when ALL of:
- Impacts a critical domain (auth, payment, data integrity, availability)
- High user/service/data impact
- Confidence is Medium or High

## Step 7: Determine Verdict

Combine findings into a final verdict.

### Baseline Rules

| Verdict | Condition |
|---------|-----------|
| **REQUEST_CHANGES** | Any Critical finding |
| **REQUEST_CHANGES** | 3+ Major findings |
| **COMMENT** | 1–2 Major findings |
| **COMMENT** | 5+ Minor findings |
| **APPROVE** | Only Minor/Nit or no findings |

### Risk-Weighted Adjustment (Internal Logic)

Use internally to validate the baseline verdict — do NOT output the score:
- Severity weights: Critical=10, Major=5, Minor=2, Nit=1
- Confidence factor: High=1.0, Medium=0.7, Low=0.4
- Critical domain bonus: +4 per finding in auth/payment/data integrity/availability

| Score | Adjustment |
|-------|------------|
| ≥ 12 with medium+ confidence | REQUEST_CHANGES |
| 6–11 | COMMENT (unless baseline already requests changes) |
| ≤ 5 and no Major+ findings | APPROVE candidate |

### Confidence-Aware Handling

| Evidence Shape | Handling |
|----------------|----------|
| High confidence + high impact | Keep or escalate severity |
| Medium confidence + medium/high impact | Keep severity, add verification note |
| Low confidence | No automatic escalation; request manual verification |

## Step 8: Generate Report

Output the review using the format in **[output_format.md](references/output_format.md)**.

Key requirements:
- Group findings by severity (default) or by file if requested
- Each finding must include: file location, issue, evidence, impact, confidence tier, and suggestion
- State analysis limitations honestly (unverifiable areas, sampling scope)
- Include a `Highlights` section when patch quality deserves recognition
- End with a clear verdict and decision rationale

## Tools

- **Git CLI**: Commit metadata, diffs, history, range context
- **Search tools (`rg`)**: Consumer tracing, reference lookup, test coverage checks

## Reference Files

| File | When to Read |
|------|-------------|
| [git_operations.md](references/git_operations.md) | Step 2 — for edge cases (root commits, merges, range fallbacks) |
| [impact_detection.md](references/impact_detection.md) | Step 5 — for consumer tracing and breaking change detection |
| [output_format.md](references/output_format.md) | Step 8 — for report structure and finding entry format |
