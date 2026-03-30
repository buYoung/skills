# Exception Handling

## No completion comment from worker

- Review based on code changes only
- State this in the review comment
- Request the worker to post a completion comment

## Changes beyond Done Criteria scope

- Flag as scope creep
- Determine if the extra changes are reasonable (imports, tests, etc.) or problematic
- Unreasonable scope creep becomes a reason for `Changes Requested`

## Conflicts between sub-issues

- If two sub-issues modify the same part of a file differently, record the conflict in both review comments
- Issue `Changes Requested` and suggest a resolution approach

## Ambiguous Done Criteria

- Do not judge arbitrarily — state the interpretation used in the review comment
- Consider using `Clarification Needed` verdict

## Re-review after Changes Requested

- Use only the most recent `## ✅ Work Complete` comment as the review basis
- Additionally verify that all issues from the previous `## 리뷰 결과: 🔄 Changes Requested` have been addressed
