# Stage 6 Save Report

`SKILL.md` Stage 6 fixes what the save report must distinguish and which outcomes must be named. This file holds the banner examples and the reporting details for single plans. Briefset banners use the collapsed formats in `cold-pickup.md` and `briefset.md`; cold-pickup line formats are defined in `cold-pickup.md` under Banner Phrasing.

## Banner Examples

**English (validator + self-check passed, cold-pickup not requested):**
> Saved — `docs/briefs/2026-04-23-feat-dark-mode-settings.md` (`feat`: Dark mode toggle in Settings; structural validation passed; content validation passed — content and intent self-check passed). Open it and let me know if anything needs editing.

**Korean (validator + self-check passed, cold-pickup not requested):**
> 저장 완료 — `docs/briefs/2026-04-23-feat-dark-mode-settings.md` (`feat`: Dark mode toggle in Settings; 구조 검증 통과; 내용 검증 통과 — 내용/의도 자체 검증 통과). 파일 열어보고 고칠 부분 있으면 알려줘.

**English (user requested cold-pickup, clean):**
> Saved — `docs/briefs/2026-04-23-feat-dark-mode-settings.md` (`feat`: Dark mode toggle in Settings; structural validation passed; content validation passed — content and intent self-check passed; cold-pickup: clean (no intent deviations, no ask-backs, no missing concerns)). Open it and let me know if anything needs editing.

**English (user requested cold-pickup, findings):**
> Saved — `docs/briefs/2026-04-23-feat-dark-mode-settings.md` (`feat`: Dark mode toggle in Settings; structural validation passed; content validation passed — content and intent self-check passed after 1 patch; cold-pickup flagged 3 item(s): 2 patched in place, 1 left as a user decision).
> - d1 (`scope_narrower`): the input asks for the toggle on mobile too; added the mobile settings route to In Scope and Stage 2.
> - m1 (`infer_and_patch`): the input's "remember the last choice" requirement was missing; added to Acceptance Criteria.
> - a1 (`user_input_ambiguity`, affects direction): "system default" could mean the OS theme or the app default — see the decision table below.

**English (validator still fails after two repair attempts):**
> Saved — `docs/briefs/2026-04-23-feat-dark-mode-settings.md`, but structural validation still flags 2 issue(s) after two repair attempts: ✗ <first failure verbatim> ✗ <second failure verbatim>. The file is on disk; content validation did not run.

If the user had requested cold-pickup for that run, the same banner ends with `cold-pickup unavailable (structural validation failed)`.

Mirror any banner into the user's chat language as the Korean example above shows — translate the prose, keep paths, filenames, and technical fields (finding ids, `kind` values, classifications, validator messages) verbatim.

## Reporting Patches

- If the Stage 5.6 self-check surfaced gaps fixed within the budget, say what you patched (e.g., "self-check found 2 input concerns missing from In Scope; added them, re-validated").
- If Stage 5.7 patched the brief, list each patched and residual finding as bullets under the banner, as shown above.
- If the user requested cold-pickup and it could not run, report `cold-pickup unavailable (<actual reason>)` instead of a result.

## Why Save-Then-Review

An earlier iteration rendered the full brief in chat for approval *before* writing to disk. In hands-on use that flooded the conversation with markdown that renders poorly inside a code fence and was awkward to edit conversationally. Writing to disk first lets the user review in their editor (real markdown, real diff tools, real inline edits) and lets the validator surface structural issues immediately. The tradeoff — a file briefly on disk before approval — is neutral: `docs/briefs/` is the intended home for these files, and the commit step stays with the user.
