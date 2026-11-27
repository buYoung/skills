# Linear API Reference

## State Parameter Values

The `state` field in `save_issue` accepts either the state type or state name, but behavior can be inconsistent across statuses. Use these tested, working values:

| Desired Status | `state` value to use | Why |
|---|---|---|
| In Progress | `"started"` | Name `"In Progress"` fails; use the type |
| Done | `"Done"` | Type `"completed"` fails; use the name |
| Back to Todo | `"unstarted"` | Use the type |
| Canceled | `"Canceled"` | Use the name |

Always verify the transition succeeded by checking the `status` field in the API response. If the status didn't change, try the alternative form (name vs type).

## Description Parsing

Linear API may return description text with escaped newlines, where a line break arrives as the two characters `\n`. When splitting sections on headers like `## Task Description`, match both `## ` at the start of a line and `## ` right after a literal `\n`.

## Tool Call Summary

| Action | Tool (example name) | Key Parameters |
|---|---|---|
| Read issue | `get_issue` | `id`, `includeRelations: true` |
| List sub-issues | `list_issues` | `parentId` |
| Read comments | `list_comments` | issue identifier; `cursor`, `limit` for paging |
| Update status | `save_issue` | `id`, `state` |
| Post comment | `save_comment` | `issueId`, `body` |

`save_issue`, `list_issues`, and `list_comments` are names from Linear's MCP changelog; Linear does not publish a full tool list. `get_issue` and `save_comment` stand for the read-issue and post-comment functions. Clients prefix the names (Claude Code shows `mcp__<server>__<tool>`), so use the names the connected server lists (`/mcp` in Claude Code shows each tool's full name) and take parameters from the input schema in the server's tool definitions.

`list_comments` returns comments in pages. Follow `cursor` until every comment is read before deciding which review comment is the latest.

## Retry Policy

If `get_issue` or `list_issues` fails, retry once before falling back to alternative data sources (e.g., inferring relations from sibling issues' `blocks` field). If `list_comments` fails twice, tell the user that review results could not be read instead of treating the issue as unreviewed.
