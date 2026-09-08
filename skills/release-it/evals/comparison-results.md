# Generated-Output Comparison

Checked on 2026-09-08 using the three added prompts, with one fresh generation per prompt
and skill version in each iteration. The baseline was a copy of the original skill taken
before editing. Each run produced project scripts, config, and usage instructions. A
separate grader inspected those artifacts and recorded assertion-level evidence.

| Scenario | Improved skill, final comparison | Original skill, final comparison |
|---|---:|---:|
| Single project, version first | 7/7 | 5/7 |
| One service app in a monorepo | 6/7 | 5/7 |
| Inherited modes, recommendation, and terminal requirements | 7/7 | 5/7 |
| Total | 20/21 | 15/21 |

The earlier comparison scored 19/21 for the initial improvement and 14/21 for the original
skill. Its snapshot-mode failure led to applying interactive overrides before the initial
`Config.init()`, not only at the final API call. The corrected Node requirement for
release-it 21.0.1 also appeared in the final generated artifacts.

The remaining improved-output failure is a missing verification procedure/evidence for
sibling-app file stability in the monorepo-generated instructions. The output checks the
initial whole-repository index, scopes its target, and disables workspace updates, but
does not demonstrate that other apps stayed unchanged. This is a generated-output
handoff gap; the separate packaged-example PTY checks do verify sibling/root manifests
and changelogs remain unchanged.

Original-skill outputs still used wrapper-owned Git operations or disabled the selected
app's Git workflow, missed a write-time version guard, or supplied insufficient isolated
verification. One original mode-handling output skipped a declined task and continued
later tasks; that issue is also recorded in its review notes.

These scores describe these generated samples and are not a statistical reliability
estimate. The final generated artifacts underwent 15 JavaScript, 19 JSON, and one Python
syntax checks plus the grader's stated mock-contract/source checks. They were not all run
as complete real release workflows. Timing/token comparisons were omitted because complete
measurements were unavailable. See [README.md](README.md) and
[interactive-results.json](interactive-results.json) for the separate **27/27** execution
result on the packaged examples. No real remote push or deployment was performed.
