# Linear API Reference

## State Parameter Values

Values for the `state` field in `Linear:save_issue`:

| Desired Status | `state` Value | Note |
|---|---|---|
| In Progress | `"started"` | Do not use `"In Progress"` — use the type value |
| Done | `"Done"` | Do not use `"completed"` — use the name value |
| Back to Todo | `"unstarted"` | Type value |

After changing state, verify the transition succeeded by checking the API response. If it fails, try the alternative format (name vs. type).

## Description Parsing

Linear API may return escaped newlines in descriptions (`\n` appearing as `\\n`). When parsing section headers like `## Done Criteria`, account for both `## ` and `\n## ` patterns.

## Comment Identification Rules

| Comment to Find | Search String |
|---|---|
| Worker start comment | `## 🚀 Work Started` |
| Worker completion comment | `## ✅ Work Complete` |
| Reviewer review comment | `## 리뷰 결과:` |

For re-review detection, check comment **chronological order**: if `## 리뷰 결과: 🔄 Changes Requested` appears before a later `## ✅ Work Complete`, the sub-issue needs re-review.

## Tool Call Summary

| Action | Tool | Key Parameters |
|---|---|---|
| Read issue | `Linear:get_issue` | `id`, `includeRelations: true` |
| List sub-issues | `Linear:list_issues` | `parentId` |
| Change status | `Linear:save_issue` | `id`, `state` |
| Post comment | `Linear:save_comment` | `issueId`, `body` |

## Retry Policy

If `Linear:get_issue` or `Linear:list_issues` fails, retry once. If still failing, proceed with available data and report the issue to the user.
