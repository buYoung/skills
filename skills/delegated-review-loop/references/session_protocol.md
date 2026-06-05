# Session Protocol

All inter-agent content flows through documents in a per-session directory. The main agent owns the session lifecycle: it creates the directory, decides which paths each sub-agent receives, and cleans up at the end. Sub-agents never pass content to each other directly — they write documents and return paths, and the main agent routes those paths.

## Why paths, not content

- The main agent's context stays lean: long reports and research notes never pass through its prompt assembly.
- Isolation becomes enforceable: "the reviewer must not see the worker's reasoning" stops being an honor-system rule and becomes "the reviewer was never handed that path."
- The session directory doubles as an audit trail while the loop runs.

The rule is absolute: the main agent hands sub-agents file paths only and never inlines a session document's content into a prompt. Each sub-agent reads its inputs itself.

## Directory layout

```
.agents/agents-community/<session-id>/
├── task_request.md           # immutable task request — written once at Step 1
├── research/
│   └── context.md            # scout output (only if the scout ran)
├── worker_report_<n>.md      # worker's report per round (0 = initial build)
├── reviews/
│   └── <lens>_<n>.md         # one file per reviewer per round
└── merged_findings_<n>.md    # orchestrator's merged blocker/major list per round
```

`<session-id>` is decided by the main agent: `<YYYYMMDD>-<short-task-slug>` (e.g., `20260605-login-rate-limit`). If the slug collides with an existing directory, append `-2`, `-3`, …

The deliverable itself (code, the actual document) lives at its real repository path. The session directory holds **coordination documents only** — never the artifact.

If the project is a git repository and `.agents/` is not ignored, add it to `.gitignore` (or confirm with the user) before the first write — session documents are scratch coordination data, not project content.

## Read-access matrix

This table is the isolation contract. Granting a path outside it breaks blind review.

| Document | Scout | Worker | Reviewer | Main agent |
|----------|:-----:|:------:|:--------:|:----------:|
| `task_request.md` | reads | reads | reads | writes |
| `research/context.md` | writes | reads | **never** | routes path only |
| `worker_report_<n>.md` | — | writes | **never** | reads |
| `reviews/<lens>_<n>.md` | — | **never** | own file only, focused re-check rounds only | reads |
| `merged_findings_<n>.md` | — | reads | **never** | writes |
| Artifact (real repo path) | reads | writes | reads | routes path only |

Notes:

- The reviewer exception is deliberate and narrow: in focused re-check mode (round 2+), a reviewer receives the path to **its own** previous review file, because checking resolution requires knowing what it flagged. It still never sees another lens's file or any worker/scout document.
- The worker never reads raw review files — only the merged findings document. The orchestrator's merge (dedup, evidence filter, severity re-grade) is the quality gate between reviewer output and worker input.
- The main agent reads `worker_report` and `reviews/*` because merging and loop-control decisions require it. It writes `task_request.md` and `merged_findings_<n>.md`; everything else is written by the sub-agent named in the table.

## Cleanup

Cleanup is the main agent's job, at Step 8, after the final summary is composed:

- **Clean pass** → delete the entire session directory. The final summary already carries everything the user needs.
- **User declines at the simplicity gate** (Step 3) → delete the session directory immediately; the loop never ran, so there is nothing to trace. The task itself is then handled as an ordinary request outside this skill.
- **Any other termination** (round cap, no progress, worker failure) → **preserve** the session directory and print its path in the final summary, so the user can trace exactly what got stuck and where. Deleting the trail at the moment of failure destroys the only diagnostic the user has.
- Never delete mid-loop, and never delete a preserved directory in a later session without the user asking.
