# Archived Entry-Point Examples

These literal blocks were kept in `SKILL.md` until they moved here, so the entry point no longer loads them. Nothing in the current workflow routes to this file.

These preserved blocks are historical examples, not steps to execute. Use the current workflow in `SKILL.md` and [Git operations](git_operations.md). Single-commit `show` examples require the root/merge handling described there; inclusive range commands require a valid parent. Merge-base commands apply only to an explicitly requested common-ancestor comparison, never as fallback. Worktree `rg` examples must not supply historical or index context.

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
