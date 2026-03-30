---
name: linear-issue-reviewer
description: >
  Review completed Linear sub-issues: cross-validate Done Criteria, code changes, and worker comments to approve, request changes, or ask for clarification.
  Use when asked to review, validate, or QA done Linear issues.
---

# Linear Issue Reviewer

Review sub-issues completed by `linear-issue-worker` and decide whether to approve, request changes, or ask for clarification.

## Position in Pipeline

| Stage | Skill | Role |
|---|---|---|
| 1 | `linear-issue-creator` | Creates main issue + sub-issues with structured templates |
| 2 | `linear-issue-worker` | Picks up sub-issues, performs code work, transitions to Done |
| **3** | **`linear-issue-reviewer`** | **Validates Done sub-issues, approves or rejects** |

The creator writes **Done Criteria** and **Acceptance Criteria** that serve as the contract for this entire pipeline. The worker fulfills that contract; the reviewer verifies it was fulfilled.

### Comment Identifier Convention

Each skill uses a distinct comment prefix so comments can be attributed to the correct stage:

| Skill | Comment Identifiers |
|---|---|
| `linear-issue-worker` | `## 🚀 Work Started`, `## ✅ Work Complete` |
| `linear-issue-reviewer` | `## 리뷰 결과:` |

---

## Workflow

### Step 1 — Receive Main Issue and Collect Sub-Issues

The user provides a main issue identifier (e.g., `PRI-42`).

1. Call `Linear:get_issue` with `includeRelations: true` to fetch the main issue
2. Parse and store the **Acceptance Criteria** from the main issue description (used in final verification)
3. Call `Linear:list_issues` with `parentId` set to the main issue ID
4. For each sub-issue, call `Linear:get_issue` with `includeRelations: true` to get full details and comments

### Step 2 — Identify Review Targets

Filter sub-issues to find those needing review.

**Review target conditions:**
- Status is `Done`
- A `## ✅ Work Complete` comment exists (worker's completion report)
- No `## 리뷰 결과:` comment exists yet (not reviewed)

**Re-review detection:**
- If a `## 리뷰 결과: 🔄 Changes Requested` comment exists AND a newer `## ✅ Work Complete` comment follows it → the worker has re-done the work → this is a **re-review target**

**Status-based handling:**

| Sub-Issue Status | Completion Comment | Review Comment | Decision |
|---|---|---|---|
| Done | Present | Absent | **Review target** |
| Done | Present | Approved | Already reviewed, skip |
| In Progress | Present | Changes Requested | Worker fixing, skip |
| Done | Present | Changes Requested → then new Work Complete | **Re-review target** |
| Done | Absent | Absent | Exception (see Step 3 exceptions) |
| Todo / In Progress | — | — | Skip |

Present the review plan and wait for user confirmation:

```
Review Targets (PRI-42):
1. PRI-43 — [project] Sub-issue title (first review)
2. PRI-45 — [project] Sub-issue title (re-review)

Skipped:
- PRI-44 — Already Approved
- PRI-46 — Still In Progress

Proceed?
```

### Step 3 — Per Sub-Issue Review Cycle

For each review target, execute the following verification cycle.

---

## Sub-Issue Review Cycle

### 3a. Collect Three Sources

Gather the three sources needed for cross-validation:

| Source | Origin | How to Collect |
|---|---|---|
| **Done Criteria** | Creator wrote in sub-issue description | Parse `## Done Criteria` section from description |
| **Completion Comment** | Worker's change summary | Find comment containing `## ✅ Work Complete` |
| **Actual Code** | Changed files | Extract file paths from the Changes section of completion comment → read files |

Also collect:
- **Target Location**: Parse `## Target Location` section from sub-issue description
- **Technical Details**: Parse `## Technical Details` section from sub-issue description

### 3b. Verify Done Criteria

Check each Done Criteria item against both the completion comment and actual code:

1. Find evidence in the completion comment for this criterion
2. Verify in actual code that the condition is implemented
3. Cross-validate: does the comment's claim match the code?

| Evidence in Comment | Confirmed in Code | Verdict |
|---|---|---|
| Yes | Yes | Fulfilled |
| Yes | No | **Not fulfilled** (comment-code mismatch) |
| No | Yes | Fulfilled (flag: comment should be updated) |
| No | No | **Not fulfilled** |

### 3c. Compare Target Location

1. Check the file list specified in the sub-issue's Target Location section
2. Check the file list in the completion comment's Changes section
3. Compare:
   - **Specified file not changed** → flag as possible omission
   - **Unspecified file changed** → flag as possible scope creep
   - Reasonable scope extensions (e.g., adding imports, test files) → allow but note

### 3d. Verify Technical Details Compliance

Cross-check against the Technical Details section:

- **Libraries / patterns**: Were the specified libraries used? Were the prescribed patterns followed?
- **API spec**: Do request/response shapes match the spec?
- **Logic / data flow**: Is the implementation consistent with the described flow?

### 3e. Code Quality Check

Review for general code quality regardless of what the issue specifies:

- Error handling is appropriate
- No hardcoded values (magic numbers, hardcoded URLs, etc.)
- Follows project conventions and code style
- No leftover debug code (`console.log`, `debugger`, commented-out code, etc.)
- Type safety is maintained (if TypeScript)

### 3f. Determine Verdict

Based on steps 3b–3e, choose one of three verdicts:

| Verdict | Condition | Status Change |
|---|---|---|
| **Approved** | All Done Criteria fulfilled, no critical quality issues | Keep Done |
| **Changes Requested** | Any Done Criteria not fulfilled, or critical quality issues found | Done → In Progress (`"started"`) |
| **Clarification Needed** | Implementation choices need explanation, judgment reserved | Keep Done |

### 3g. Post Review Comment

Write a review comment based on the verdict. Use the templates from `references/comment-templates.md`.

For `Changes Requested`, also transition the status:

```
Linear:save_issue
  id: "<sub-issue-id>"
  state: "started"
```

### 3h. Move to Next Sub-Issue

Proceed to the next review target and repeat from 3a.

---

## Main Issue Final Verification

Execute this only when **all** sub-issues have been Approved.

### Pre-condition Check

1. Confirm every sub-issue has a `## 리뷰 결과: ✅ Approved` comment
2. If any sub-issue still has `🔄 Changes Requested` or `❓ Clarification Needed` as its latest review, do NOT proceed with final verification — inform the user which sub-issues are pending

### Acceptance Criteria Cross-Check

1. Retrieve each Acceptance Criteria item from the main issue
2. Map each item to the sub-issue(s) that satisfy it
3. If all items are covered → post final review comment
4. If gaps exist → identify which criteria are unmet and suggest next steps

Post the final review comment on the main issue using the templates from `references/comment-templates.md` (Final Review sections).

---

For exception handling (missing comments, scope creep, conflicts, ambiguous criteria, re-review), see `references/exceptions.md`.

For Linear API details (state values, description parsing, comment identification, tool calls, retry policy), see `references/linear-api.md`.
