# Linear API Reference

## State Parameter Values

Values for the `state` field in `save_issue`:

| Desired Status | `state` Value | Note |
|---|---|---|
| In Progress | `"started"` | Do not use `"In Progress"` — use the type value |
| Done | `"Done"` | Do not use `"completed"` — use the name value |
| Back to Todo | `"unstarted"` | Type value |

After changing state, verify the transition succeeded by checking the API response. If it fails, try the alternative format (name vs. type).

## Description Parsing

Linear API may return description text with escaped newlines, where a line break arrives as the two characters `\n`. When splitting sections on headers like `## Done Criteria`, match both `## ` at the start of a line and `## ` right after a literal `\n`.

## Comment Identification Rules

| Comment to Find | Search String |
|---|---|
| Worker start comment | `## 🚀 Work Started` |
| Worker completion comment | `## ✅ Work Complete` |
| Reviewer review comment | `## 리뷰 결과:` |

For re-review detection, compare comment creation times instead of relying on the order the tool returns: if the latest `## 리뷰 결과: 🔄 Changes Requested` or `## 리뷰 결과: ❓ Clarification Needed` was created before a later `## ✅ Work Complete`, the sub-issue needs re-review.

## Tool Call Summary

| Action | Tool (example name) | Key Parameters |
|---|---|---|
| Read issue | `get_issue` | `id`, `includeRelations: true` |
| List sub-issues | `list_issues` | `parentId` |
| Read comments | `list_comments` | issue identifier; `cursor`, `limit` for paging |
| Change status | `save_issue` | `id`, `state` |
| Post comment | `save_comment` | `issueId`, `body` |

`save_issue`, `list_issues`, and `list_comments` are names from Linear's MCP changelog; Linear does not publish a full tool list. `get_issue` and `save_comment` stand for the read-issue and post-comment functions. Clients prefix the names (Claude Code shows `mcp__<server>__<tool>`), so use the names the connected server lists (`/mcp` in Claude Code shows each tool's full name) and take parameters from the input schema in the server's tool definitions.

`list_comments` returns comments in pages. Follow `cursor` until every comment is read; review detection depends on the full comment history.

## Retry Policy

If `get_issue` or `list_issues` fails, retry once. If still failing, proceed with available data and report the issue to the user.

If `list_comments` fails twice for a sub-issue, do not classify it as a review target or post a review comment on it; tell the user its comments could not be read.
