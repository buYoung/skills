# Git Operations

Commands and syntax for retrieving commit information and changes.

## Commit Metadata Retrieval

### Single Commit Information
```bash
git show --stat <commit_hash>
```
- **Output**: Commit hash, author, date, message, and file change statistics

### Commit Message Only
```bash
git log -1 --format="%B" <commit_hash>
```
- **Output**: Full commit message body

### Author and Date
```bash
git log -1 --format="%an <%ae> | %ai" <commit_hash>
```
- **Output**: Author name, email, and commit date

## Diff Operations

### Full Diff with Context
```bash
git show <commit_hash>
```
- **Output**: Complete diff with default context lines

### Diff Statistics Summary
```bash
git diff --stat <commit_hash>^..<commit_hash>
```
- **Output**: Files changed, insertions, deletions summary

### File List Only
```bash
git diff --name-status <commit_hash>^..<commit_hash>
```
- **Output**: Status prefix (A/M/D/R) with file paths
  - `A` - Added
  - `M` - Modified
  - `D` - Deleted
  - `R` - Renamed

### Specific File Diff
```bash
git show <commit_hash> -- <file_path>
```
- **Output**: Diff for specified file only

## Commit Range Operations

### Range Diff
```bash
git diff <start_hash>..<end_hash>
```
- **Output**: Combined diff between two commits

### Log with Diffs
```bash
git log -p <start_hash>..<end_hash>
```
- **Output**: Each commit with its diff in the range

## Parent Commit Reference

| Syntax | Meaning |
|--------|---------|
| `<hash>^` | First parent of commit |
| `<hash>~1` | One commit before |
| `<hash>~n` | n commits before |
