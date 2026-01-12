# Working Agreements Specification

Defines the standard working agreements to be included in generated `AGENTS.md` files.

## Communication Rules

| Rule | Description |
|------|-------------|
| Response Language | Korean by default; English only if user explicitly requests |
| Technical Terms | Keep domain-specific terms (software/backend/infra) in English, no Korean transliteration |
| Code Blocks | Never modify or translate fenced code blocks |

## Task Execution Rules

| Rule | Description |
|------|-------------|
| Tests & Lint | Do not create tests or add lint/format tasks unless user explicitly mentions ("test code", "unit test", "jest", "vitest", "lint", "eslint", "prettier", "code format") |
| Context Building | Before editing code, search for other usages of the same function/feature/module; review related flows, shared abstractions, recurring patterns |
| Simplicity | Prefer simple solutions matching user's request; do not add extra features or abstraction unless requested |
| Clarification | If requirements are ambiguous, ask the user instead of guessing |

## Code Change Rules

| Rule | Description |
|------|-------------|
| Minimal Changes | Prefer minimal, focused changes; avoid large refactors unless requested |
| Public APIs | Preserve public APIs and behavior unless user asks to change them; call out any behavior changes |
| New Code | New functions/modules should be small, single-purpose, and colocated near related code |
| Dependencies | Avoid new external dependencies unless necessary; if added, briefly explain why |

## Compressed Format for AGENTS.md

Due to the 12,000 character limit, working agreements in generated AGENTS.md should be compressed. Example format:

```markdown
## 5. Working Agreements

- 응답은 한국어 (기술 용어는 영어 유지, 코드 블록 번역 금지)
- 테스트/린트는 명시적 요청 시에만 작성
- 코드 수정 전 관련 사용처와 패턴 파악
- 단순한 해결책 우선, 불필요한 추상화 지양
- 요구사항 불명확 시 먼저 질문
- 최소한의 변경, 공개 API 유지
- 새 함수는 단일 목적, 관련 코드 근처 배치
- 외부 의존성 추가는 필요 시에만, 사유 설명
```

## Alternative English Compressed Format

```markdown
## 5. Working Agreements

- Respond in Korean (keep tech terms in English, never translate code blocks)
- Create tests/lint only when explicitly requested
- Build context by reviewing related usages and patterns before editing
- Prefer simple solutions; avoid unnecessary abstraction
- Ask for clarification when requirements are ambiguous
- Minimal changes; preserve public APIs
- New functions: single-purpose, colocated with related code
- External dependencies: only when necessary, explain why
```
