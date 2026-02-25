# Git Operations

Commands and patterns for retrieving commit information, range diffs, and fallback-safe review context.

## Commit Metadata Retrieval

### Single Commit Information
```bash
git --no-pager show --stat <commit_hash>
```
- **Output**: Commit hash, author, date, message, and file change statistics

### Commit Message Only
```bash
git --no-pager log -1 --format="%B" <commit_hash>
```
- **Output**: Full commit message body

### Author and Date
```bash
git --no-pager log -1 --format="%an <%ae> | %ai" <commit_hash>
```
- **Output**: Author identity and commit timestamp

## Single-Commit Diff Retrieval

### Standard Commit Diff
```bash
git --no-pager show <commit_hash>
```
- **Output**: Complete diff for the target commit

### Root Commit Diff (No Parent)
```bash
git --no-pager show --root <commit_hash>
```
- **Output**: Diff from an empty tree to the root commit content
- **Use Case**: Parent reference does not exist

### File-Scoped Diff
```bash
git --no-pager show <commit_hash> -- <file_path>
```
- **Output**: Diff for a specific file in the commit

## Merge Commit Handling

Merge commits can present different perspectives based on parent selection.

### First-Parent Perspective (Default)
```bash
git --no-pager show --first-parent <commit_hash>
```
- **Output**: Diff aligned with mainline integration path

### Combined Merge Diff
```bash
git --no-pager show --cc <commit_hash>
```
- **Output**: Combined diff showing multi-parent merge context

## Commit Range Operations

Review targets can be provided as `start_hash~end_hash` where start is earliest and end is latest.

### Primary Range Diff
```bash
git --no-pager diff <start_hash>^..<end_hash>
```
- **Output**: Combined diff from just before start through end

### Range Commit Log with Patches
```bash
git --no-pager log -p <start_hash>^..<end_hash>
```
- **Output**: Commit-by-commit patches in the selected range

## Range Stabilization Fallback (Merge-Base)

When parent-based range calculation is ambiguous, use merge-base fallback.

### Resolve Stable Base
```bash
git merge-base <start_hash> <end_hash>
```
- **Output**: Best common ancestor used as fallback range base

### Fallback Diff
```bash
git --no-pager diff <merge_base_hash>..<end_hash>
```
- **Output**: Deterministic diff from common ancestor to end commit

## Failure and Fallback Matrix

| Failure Condition | Detection Signal | Fallback Action | Interpretation |
|-------------------|------------------|-----------------|----------------|
| **Hash not found** | `bad object` / empty lookup | Verify hash spelling and repository scope using `git rev-parse --verify <hash>` | Target is unresolved; analysis is blocked |
| **Missing parent** | Parent lookup fails on root commit | Switch to `git show --root <commit_hash>` | Review remains valid using empty-tree base |
| **Ambiguous range** | Unexpectedly large/small diff or branch divergence | Resolve `merge-base`, then diff from merge base to end | Produces stable range semantics |
| **Merge complexity** | Parent-specific changes unclear | Compare `--first-parent` and `--cc` outputs | Distinguishes integration effects from branch-local changes |

## Auxiliary Commands

### File Status Summary
```bash
git --no-pager diff --name-status <start_hash>^..<end_hash>
```
- **Output**: A/M/D/R status list for prioritization

### Diff Statistics
```bash
git --no-pager diff --stat <start_hash>^..<end_hash>
```
- **Output**: Changed file count and line churn summary
