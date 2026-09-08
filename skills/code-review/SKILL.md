---
name: code-review
description: Review Git changes for concrete defects and evidence-backed maintainability concerns. Use for code review of commits, ranges, staged changes, uncommitted changes, or selected files. With no target, review all staged, unstaged, and untracked changes; ask for a target if none exist. Trace behavior in the selected version, challenge suspected defects, exclude style-only preferences, and provide an approval verdict only when requested.
---

# Code Review Workflow

Review changes without modifying code or publishing an external review. Respond in the user's language. A clear target authorizes immediate review; ask only when ambiguity materially changes scope or intent.

## 1. Resolve the target and version

Read [Git operations](references/git_operations.md) before retrieving a diff. Record the requested scope, resolved commit IDs or index/worktree state, comparison base, and any path restriction.

- No target: include staged, unstaged, and untracked changes. If none exist, ask what to review; do not substitute HEAD.
- Explicit staged review: use index contents for both changes and surrounding callers, including unchanged files.
- Commit or range: use the selected revisions for context and consumers, never current worktree files as evidence of that revision's behavior.
- File paths narrow findings to those paths; follow necessary consumers outside that boundary for context and disclose the boundary.
- Distinguish endpoint comparison, merge-base comparison, and the legacy inclusive `start~end` notation. Do not silently change the base to make a command succeed.

Inspect status for unresolved conflicts and handle roots and merges explicitly. Preserve the user's index and working tree.

## 2. Inventory the change and explain intended behavior

Read requirements, relevant contracts, and before/after code in the selected versions. Establish what inputs should produce what observable results. A commit message is context, not proof of correctness.

Track each changed file as reviewed, mechanically checked with a reason, or unreviewed. Prioritize by behavioral impact without sampling source solely by file count. Inspect generated artifacts, lockfiles, vendored code, and bundles according to their actual deployment or dependency effects; a filename is not proof that content is irrelevant. Check generators and outputs together where necessary. Disclose skipped areas if the review cannot be completed.

## 3. Trace behavior through consumers

Read [impact detection](references/impact_detection.md). Trace callers → intermediate layers/shared abstractions → final consumers. Follow arguments, defaults, configuration, return values, errors, and cancellation signals through transformations and precedence rules. Confirm changed values actually affect runtime behavior.

Check public exports, adapters, serialized data, dynamic registration, and external consumers where accessible. Search results identify candidate paths; inspect those paths before drawing conclusions. Use version-aware search or an isolated snapshot for historical/index review.

## 4. Apply relevant practical checks

Read [review checks](references/review_checks.md) and select checks supported by the change surface. Examine edge conditions, authorization, state transitions, concurrency, resource lifetime, retries/idempotency, compatibility, costs, and test assertions where relevant. Do not turn the reference into a compulsory checklist in the report.

Assess maintainability separately: identify present complexity, duplicated policy, or coupling and explain the concrete benefit of a local improvement. Exclude personal style preferences and speculative abstractions by default.

## 5. Challenge every suspected defect

Before reporting, establish a reachable trigger, the execution path, expected versus actual behavior, code evidence, and impact. Look for counterevidence: caller validation, compatibility layers, intentional requirements, cleanup/fallback logic, or runtime guarantees.

Compare the base version: omit pre-existing problems not introduced or made worse by this change. Merge reports sharing one root cause, even when several files or consumers expose it. Static evidence can establish a defect without an executed reproduction; say which kind of evidence supports it. If a missing fact could invalidate the claim, state a verification question under limitations instead of presenting it as a confirmed defect.

## 6. Classify and report

Read [output format](references/output_format.md). Determine defect severity from actual impact and trigger conditions: Critical for severe security/data/availability consequences, Major for material incorrect behavior, Minor for bounded low-impact defects. Keep uncertainty separate; do not calculate confidence scores or promote severity because tests are missing or consumers are numerous.

Default order: target, defects by importance, maintainability observations, verification and limitations. Explicitly state when no confirmed defects were found. Omit empty optional sections and ceremonial praise. Only if the user asks for a verdict, apply the qualitative decision rules in the output reference; never use finding counts or weighted scores.

## Tools and boundaries

Use Git and available repository navigation tools, preferring codemap-search when available and appropriate. Search relevant paths and file types. Navigation indexes of the current worktree are not evidence for historical or staged content; use Git blobs/search or an isolated matching snapshot instead. Use existing verification commands when authorized and relevant; report the exact command, execution location, and result. A review request alone does not authorize source changes, new tests, or external posting.

## Archived literal examples

These preserved blocks are historical examples, not steps to execute. Use the current workflow above. Single-commit `show` examples require the root/merge handling above; inclusive range commands require a valid parent. Merge-base commands apply only to an explicitly requested common-ancestor comparison, never as fallback. Worktree `rg` examples must not supply historical or index context.

```bash
git --no-pager show --stat <commit_hash>
# or for staged changes:
git --no-pager diff --cached --stat
```

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

```bash
# Find direct callers
rg -F "symbolName(" .
# Find broader references
rg "symbolName" .
```
