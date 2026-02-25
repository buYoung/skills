# Git Operations

Commands and syntax for retrieving commit information and changes.

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
- **Output**: Author name, email, and commit date

## Diff Operations

### Full Diff with Context
```bash
git --no-pager show <commit_hash>
```
- **Output**: Complete diff with default context lines

### Diff Statistics Summary
```bash
git --no-pager diff --stat <commit_hash>^..<commit_hash>
```
- **Output**: Files changed, insertions, deletions summary

### File List Only
```bash
git --no-pager diff --name-status <commit_hash>^..<commit_hash>
```
- **Output**: Status prefix (A/M/D/R) with file paths
  - `A` - Added
  - `M` - Modified
  - `D` - Deleted
  - `R` - Renamed

### Specific File Diff
```bash
git --no-pager show <commit_hash> -- <file_path>
```
- **Output**: Diff for specified file only

## Commit Range Operations

Review targets are provided as a start~end commit range. The start commit is the earliest change and the end commit is the latest. No commits prior to the start are included.

### Range Diff
```bash
git --no-pager diff <start_hash>^..<end_hash>
```
- **Output**: Combined diff from just before the start commit to the end commit
- **Note**: Use `<start_hash>^` as the base to include the start commit's own changes

### Log with Diffs
```bash
git --no-pager log -p <start_hash>^..<end_hash>
```
- **Output**: Each commit with its diff in the range (start commit included)
