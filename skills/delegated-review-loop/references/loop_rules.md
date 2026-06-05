# Loop Rules

## Severity definitions

| Severity | Meaning | Loop effect |
|----------|---------|-------------|
| **blocker** | The artifact fails the task request or is broken (does not run, claim is false, required item missing) | Must be fixed; loop continues |
| **major** | Works, but a real problem the user would want fixed before accepting (wrong edge-case behavior, breaking a caller, misleading section) | Must be fixed or rebutted; loop continues |
| **minor** | Worth knowing, not worth another round (naming nit, optional polish, style preference) | Never triggers a round; carried to the final summary |

## Merging panel findings

The orchestrator reads the `reviews/<lens>_<n>.md` files and merges them before anything reaches the worker. The merged blocker/major list is written to `merged_findings_<n>.md` — that document (its path, never its content inline) is the only review material the worker receives:

1. **Deduplicate.** Two lenses flagging the same underlying problem become one finding at the higher severity, keeping the strongest evidence.
2. **Drop evidence-free findings.** A finding with no quote, file:line, or reproducible observation is discarded. If it sounds important anyway, downgrade to minor and carry it to the summary as an open question — never send it to the worker as work.
3. **Resolve contradictions.** If two reviewers pull in opposite directions (e.g., Simplicity says "remove the abstraction", Regression risk says "keep it for the callers"), the orchestrator decides using the task request as the tiebreaker and records the decision. If the contradiction changes what the user receives, defer it to the user in the final summary instead of guessing.
4. **Re-grade inflated severities.** Reviewers see only one lens, so they over-rate within it. The orchestrator owns the final severity: would the user actually reject the deliverable over this? If not, it is not a blocker.

## Worker rebuttals

When the worker rebuts a finding instead of fixing it:

- Rebuttal references the task request or concrete code and is sound → accept it, mark the finding rejected with the reason, do not re-send it next round.
- Rebuttal is hand-waving → re-send the finding once with a note that the rebuttal was insufficient. If the worker rebuts the same finding twice without new substance, the orchestrator decides the point itself.
- Accepted rebuttals appear in the final summary's "검토 후 유지한 결정" line so the user can overrule.

## Termination

Evaluated after each merge, in this order — first match ends the loop:

1. **Clean pass** — every reviewer reports PASS (only minors or nothing). Success.
2. **Round cap** — 3 improvement rounds completed and blockers/majors remain. Stop and report honestly; more rounds past this point historically oscillate rather than converge.
3. **No progress** — a full round resolved zero findings (all fixes failed re-check or were rebutted without acceptance). Stop; the loop is stuck and the user needs to weigh in.
4. **Worker failure** — the worker errors out twice on the same instruction. Stop and report what exists.

Only clean pass is silent success. Every other termination must be stated plainly in the summary — never dressed up as a normal completion.

Session cleanup follows termination, per [session_protocol.md](session_protocol.md): delete the session directory on a clean pass; on any other termination, preserve it and print its path in the summary so the user can trace what got stuck.

## Final summary format

Written for someone who will not read transcripts. In the user's language, no internal vocabulary (no "lens", "merge", "round cap" jargon — describe in plain words). Keep it under ~15 lines.

Use this exact structure — same sections, same order, labels translated to the user's language but not replaced with improvised ones. A consistent shape is what lets a user who runs this loop often scan straight to the section they care about:

```
## 결과
<one or two sentences: what was built and where it lives>

## 검토 과정
- 리뷰어 패널: <lenses, in plain words> · 반복 <N>회
- 발견되어 수정된 문제: <count>건
  - <one line each: what was wrong → how it was fixed>
- 검토 후 유지한 결정: <accepted rebuttals, one line each; omit section if none>

## 남은 참고 사항
- <minor findings, one line each; "없음" if none>

<If termination was anything other than a clean pass: a plain-language
paragraph stating why the loop stopped, exactly what remains open, and the
preserved session-directory path for tracing what got stuck.>
```
