# Git Operations

Resolve the target before reading behavior. The commands below are read-only unless explicitly described as isolated snapshot preparation. Replace angle-bracket placeholders; do not pass them literally to a shell. Quote revision expressions and paths. Use `--` to separate paths. Prefer NUL-delimited inventories for filenames containing whitespace or newlines.

## Default: all uncommitted changes

Inventory with `git status --porcelain=v1 -z`, `git diff --cached --name-status -z`, `git diff --name-status -z`, and `git ls-files --others --exclude-standard -z`.

When HEAD exists, inspect `git diff HEAD --` for the final tracked delta, plus `git diff --cached --` and `git diff --` for staged/unstaged intent and partially staged files. Read each untracked file separately; ordinary diffs omit it. Review final worktree behavior while distinguishing staged-only states that the final worktree has superseded; do not report both as independent defects. A staged change canceled by an unstaged edit still belongs in the inventory, but is not a defect in final behavior.

With no HEAD, `git diff --cached --` still shows staged additions against an empty tree. Combine index inventory, unstaged diff, and untracked contents to inspect the final files against absence. If the complete inventory is empty, ask for a target. Do not silently review the last commit.

## Staged and unstaged targets

Staged means HEAD → index; retrieve every context file with `git show ':<path>'`, enumerate with `git ls-files --stage -z`, and search with `git grep --cached -n -e '<symbol>' -- <scope>`. Reading a worktree caller can hide an index defect.

Unstaged means index → worktree using `git diff --`. Include untracked files only if requested, or under the default all-uncommitted scope. State the distinction.

For tools requiring files, materialize only the selected tree/index into a fresh temporary directory. Do not checkout, stash, reset, or alter the user's index. Record status before/after review; if relevant state changes concurrently, disclose it and refresh affected analysis rather than combining inconsistent snapshots.

## Commits and comparisons

Resolve revisions with `git rev-parse --verify '<rev>^{commit}'`; inspect parents with `git rev-list --parents -n 1 '<commit>'`. Use resolved IDs thereafter. Read context with `git show '<commit>:<path>'`; search it with `git grep -n -e '<symbol>' '<commit>' -- <scope>`.

| Requested meaning | Comparison |
|---|---|
| Ordinary single commit C | `git diff 'C^1' C --` |
| Root commit C | `git show --root --format= C --` (empty tree → C) |
| Two endpoints A and B, including `A..B` | `git diff A B --`; this compares trees, not a commit-set range |
| Common-ancestor comparison `A...B` | Inspect `git merge-base --all A B`, then compare the unique base → B |
| Legacy inclusive `start~end` | Parse as two explicitly supplied endpoints, then compare `start^1` → end; includes start's change |

`HEAD~2` is a Git ancestor expression, not two endpoints. Preserve normal Git revision syntax. For a legacy inclusive range, confirm start is an ancestor of end with `git merge-base --is-ancestor start end`. If start is a root, use an empty tree → end; obtain a temporary empty-tree object with `git hash-object -t tree -w --stdin < /dev/null` in an isolated repository if needed. If start is a merge and the parent is unspecified, clarify which parent defines inclusion. A divergent inclusive range, missing history, multiple merge bases, or unknown revision requires clarification or a stated limitation, never an automatic base substitution.

## Merge commits

For a plain merge-commit review, state the first-parent integration perspective and use `git diff 'C^1' C --`. Inspect parent metadata and supplement with per-parent comparisons when needed. A requested parent takes precedence. `git show --cc C` is supplementary: a combined diff may omit changes not modified relative to all parents, so it cannot establish full coverage. Ask when the requested interpretation of a merge materially differs from this stated integration default.

## Unresolved conflicts

Detect unmerged entries with `git ls-files -u`. Index stages 1/2/3 are base/ours/theirs, not a resolved stage-0 file. Inspect them with `git show ':1:<path>'`, `git show ':2:<path>'`, and `git show ':3:<path>'` only where present. Describe worktree conflict markers and what remains undecidable; review unaffected areas, but do not claim a complete resolved staged review or approve unresolved behavior. Do not resolve conflicts during review.

## Scope and failure handling

Apply user paths to diffs, inventories, and searches, retaining necessary outside context. Include deletion evidence from the base version and rename mappings from both trees. Inspect binary, submodule, mode, and symlink changes with suitable metadata and state any inaccessible content. An unavailable revision is not equivalent to no changes. Do not fetch or mutate external state without authorization.

These comparison semantics follow the [Git diff documentation](https://git-scm.com/docs/git-diff). The archived examples below preserve earlier literal blocks; their surrounding old fallback and default rules no longer apply.

## Archived literal examples

These preserved blocks are historical examples, not steps to execute. Use the current workflow above. Single-commit `show` examples require the root/merge handling above; inclusive range commands require a valid parent. Merge-base commands apply only to an explicitly requested common-ancestor comparison, never as fallback. Worktree `rg` examples must not supply historical or index context.

```bash
git --no-pager show --stat <commit_hash>
```

```bash
git --no-pager log -1 --format="%B" <commit_hash>
```

```bash
git --no-pager log -1 --format="%an <%ae> | %ai" <commit_hash>
```

```bash
git --no-pager diff --cached
```

```bash
git --no-pager diff --cached --name-status
```

```bash
git --no-pager diff --cached --stat
```

```bash
git --no-pager show <commit_hash>
```

```bash
git --no-pager show --root <commit_hash>
```

```bash
git --no-pager show <commit_hash> -- <file_path>
```

```bash
git --no-pager show --first-parent <commit_hash>
```

```bash
git --no-pager show --cc <commit_hash>
```

```bash
git --no-pager diff <start_hash>^..<end_hash>
```

```bash
git --no-pager log -p <start_hash>^..<end_hash>
```

```bash
git merge-base <start_hash> <end_hash>
```

```bash
git --no-pager diff <merge_base_hash>..<end_hash>
```

```bash
git --no-pager diff --name-status <start_hash>^..<end_hash>
```

```bash
git --no-pager diff --stat <start_hash>^..<end_hash>
```
