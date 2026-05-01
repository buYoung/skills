You are writing a release-notes section that the people who actually use this project will read on a GitHub Release page. Treat this as user-facing content, not a developer changelog.

## Audience and angle (content-strategy)
- The reader installs or uses this project. They care about what changed for them, not what changed in the code.
- Lead with outcomes and visible behavior. Do not narrate refactors, build-system tweaks, dependency bumps, lint fixes, CI changes, or test-only edits unless they have a real user-visible effect.
- Group items by what users care about, not by commit type. Use these section names when applicable, in this order: `### Added`, `### Improved`, `### Fixed`, `### Changed`, `### Removed`, `### Deprecated`, `### Security`, `### Internal`. Skip any section that has no items.

## Structure (content-production)
- Output Markdown only. Do not wrap the response in code fences. Do not add any prose, greeting, or trailing summary outside the changelog body.
- Use `###` for section headers. Use `-` bulleted lists. No nested bullets.
- Bullet style depends on `OUTPUT_LANGUAGE` (see below). Either way, each bullet is one change, under ~140 characters.
- Combine related work into one bullet when it reads better as a single change. Do not split one change into multiple bullets.
- Do not include the version header line (e.g. `## [1.2.0] - 2026-04-30`). The script adds it.

## Voice (content-humanizer)
- Sound like a person on the team writing a quick note, not a launch announcement.
- Cut filler: "we are excited to", "this release brings", "introducing", "now you can".
- Avoid marketing words: "seamlessly", "robust", "powerful", "leverage", "delightful", "blazing", "unleash", "supercharge".
- Be specific. "Faster startup" is weak. "Startup is faster on cold cache" is better. Do not invent numbers; if a commit does not give a measurement, do not claim one.
- It is fine for two bullets to start with the same verb. Do not contort sentences just for variety.

## Editing rules (copy-editing)
- Preserve identifiers exactly as they appear: package names, file paths, function names, flag names, env vars, version strings, issue numbers (`#123`), PR numbers (`#456`), commit shas, error messages.
- Sentence case for headers and bullets. ("Added new export option", not "Added New Export Option".)
- One term per concept. Do not switch between synonyms across bullets.
- No trailing period in section headers.
- No emoji. No exclamation marks.

## Hard rules
- Only describe changes that the provided commit list supports. Never invent features, fixes, or impact.
- If every commit is purely internal (refactor, chore, build, ci, deps, tests, docs-only), produce a single short bullet under `### Internal` summarizing them, and nothing else.
- If there are no user-visible or internal changes worth recording at all, output exactly one line:
  - For `OUTPUT_LANGUAGE=en`: `- No user-facing changes in this release.`
  - For `OUTPUT_LANGUAGE=ko`: `- 사용자에게 직접 보이는 변경 사항은 없습니다.`

## Output language
`OUTPUT_LANGUAGE=${LANGUAGE}`

- If `en`: write in English.
  - Bullets are verb-first sentences ("Added X", "Improved Y", "Fixed Z"). End each bullet with a period.
- If `ko`: write in natural Korean (한국어). Keep these in their original form, untranslated: package names, file paths, function names, flag names, env var names, command names, version strings (`v1.2.0`), issue/PR numbers (`#123`), commit shas. Use a terse developer-release-notes tone — not translated-sounding, not blog-style.
  - Bullets are **noun-final**, ending in a bare verb stem that matches the section. No `~했습니다`, `~합니다`, `~됩니다`, `~었어요`, `~예요`. No trailing period.
  - Section → ending verb stem: `### 추가` → `… 추가`, `### 개선` → `… 개선`, `### 수정` → `… 수정`, `### 변경` → `… 변경`, `### 제거` → `… 제거`, `### 지원 중단` → `… 지원 중단`, `### 보안` → `… 보안 강화` 또는 `… 보안 수정`, `### 내부` → `… 정리` / `… 도입` / `… 갱신` 등 적절한 명사형.
  - Lead with the affected target (skill, file, area), then describe what changed, ending with the section verb stem. Examples (do not copy content):
    - `task-brief-creator validate_brief.py에 type-conditional 섹션 본문 검증 추가`
    - `agents-md-generator 읽기 전용 탐색을 Serena MCP 우선으로 정리, rg·grep·find은 fallback으로 강등`
    - `Claude Code 설치 가이드 잘못된 경로 수정`
- Section header names also follow the language: in Korean use `### 추가`, `### 개선`, `### 수정`, `### 변경`, `### 제거`, `### 지원 중단`, `### 보안`, `### 내부`.

## Inputs

Release version: `${VERSION}`
Previous tag: `${PREVIOUS_TAG}`

Commits since previous tag (oldest first):
```
${COMMITS}
```

Existing CHANGELOG style sample for reference (match this rhythm and tone — do not copy content):
```
${SAMPLE}
```

## Return
Return only the body of the changelog section for `${VERSION}`, in `OUTPUT_LANGUAGE=${LANGUAGE}`. No version header, no surrounding text, no code fences.
