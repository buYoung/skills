# Linear API Reference

## State Parameter Values

The `state` field in `Linear:save_issue` accepts either the state type or state name, but behavior can be inconsistent across statuses. Use these tested, working values:

| Desired Status | `state` value to use | Why |
|---|---|---|
| In Progress | `"started"` | Name `"In Progress"` fails; use the type |
| Done | `"Done"` | Type `"completed"` fails; use the name |
| Back to Todo | `"unstarted"` | Use the type |
| Canceled | `"Canceled"` | Use the name |

Always verify the transition succeeded by checking the `status` field in the API response. If the status didn't change, try the alternative form (name vs type).

## Description Parsing

Linear API may return description text with escaped newlines (`\\n` as `\\\\n` in JSON). When parsing section headers like `## Task Description`, account for this escaping — look for both `## ` and `\\n## ` patterns when splitting sections.

## Tool Call Summary

| Action | Tool | Key Parameters |
|---|---|---|
| Read issue | `Linear:get_issue` | `id`, `includeRelations: true` |
| List sub-issues | `Linear:list_issues` | `parentId` |
| Update status | `Linear:save_issue` | `id`, `state` |
| Post comment | `Linear:save_comment` | `issueId`, `body` |

## Retry Policy

If `Linear:get_issue` or `Linear:list_issues` fails, retry once before falling back to alternative data sources (e.g., inferring relations from sibling issues' `blocks` field).
