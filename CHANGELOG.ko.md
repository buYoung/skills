# 변경 기록

이 프로젝트의 주요 변경 사항을 기록합니다.

문서 형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/)을 따르며, 버전은 [Semantic Versioning](https://semver.org/lang/ko/)을 따릅니다.

## [Unreleased]

## [1.1.0] - 2026-05-01

### 추가

- 추가했습니다: Codex와 Claude Code 설치 가이드로 시작 과정을 더 쉽게 따라갈 수 있습니다.
- 추가했습니다: `code-review`에서 commit hash 기준 리뷰를 사용할 수 있습니다.
- 추가했습니다: `biz-opportunity-scout`, `typst`, `system-prompt-creator`, `code-security-audit`, `veo-prompt-director` 스킬을 사용할 수 있습니다.
- 추가했습니다: `doc-coauthoring`, `release-it`, `jetbrains-plugin-development`, `task-brief-creator` 스킬을 사용할 수 있습니다.
- 추가했습니다: `linear-issue-creator`, `linear-issue-worker`, `linear-issue-reviewer`로 Linear 작업 흐름을 다룰 수 있습니다.
- 추가했습니다: `task-brief-creator`에서 여러 실행 문서를 나누어 만드는 briefset 모드를 사용할 수 있습니다.

### 개선

- 개선했습니다: `agents-md-generator`가 monorepo 구조를 더 잘 감지하고 `AGENTS.md` 갱신 흐름을 더 명확히 안내합니다.
- 개선했습니다: `task-brief-creator`가 작업 유형별 필수 섹션과 첫 실행 지침을 더 구체적으로 작성합니다.
- 개선했습니다: `jetbrains-vmoptions`가 JetBrains IDE VM 옵션과 UI 가이드 관련 판단을 더 잘 지원합니다.
- 개선했습니다: `react-vite-guide`, `typst`, `release-it`, `skill-creator` 안내를 최신 사용 방식에 맞게 다듬었습니다.

### 수정

- 수정했습니다: Claude Code 설치 가이드의 잘못된 안내를 바로잡았습니다.

### 변경

- 변경했습니다: `skill-creator`를 `skill-maker`로 정리한 뒤, 더 효과적인 Claude `skill-creator`를 쓰도록 기존 스킬을 제거했습니다.

### 내부

- 정리했습니다: README, `SKILL_GUIDELINES.md`, `.gitignore`, release-it 설정, changelog 생성 흐름을 정비했습니다.

## [1.0.0] - 2026-04-30

### 초기화

- `agents-md-generator`: 저장소 구조를 분석해 `AGENTS.md`를 생성하거나 갱신할 때 사용합니다.
- `task-brief-creator`: 구현 전에 작업 범위, 제약, 완료 기준을 브리프로 정리할 때 사용합니다.
- `code-review`: 커밋, 변경 범위, 특정 파일을 제품 코드 리뷰 관점에서 확인할 때 사용합니다.
- `code-security-audit`: OWASP 기준으로 보안 취약점과 위험 패턴을 점검할 때 사용합니다.
- `kysely-converter`: 원시 SQL을 타입 안전한 Kysely 코드로 바꿀 때 사용합니다.
- `react-vite-guide`: React 19와 Vite 기반 화면을 설계, 구현, 개선할 때 사용합니다.
- `ui-guide`: 실제 코드베이스의 색상, 타이포그래피, 컴포넌트 규칙을 문서화할 때 사용합니다.
- `ux-design-guide`: 기존 UI의 사용성, 접근성, 레이아웃 문제를 검토할 때 사용합니다.
- `doc-coauthoring`: 문서, 제안서, 기술 명세, 결정 기록을 함께 작성할 때 사용합니다.
- `typst-creator`: Typst 기반 문서, 보고서, 논문, 발표 자료를 작성할 때 사용합니다.
- `system-prompt-creator`: 제품 요구사항에 맞는 시스템 프롬프트를 설계할 때 사용합니다.
- `release-it`: `release-it` 설정, 배포 흐름, changelog 생성을 다룰 때 사용합니다.
- `jetbrains-vmoptions`: JetBrains IDE의 버전별 VM 옵션과 메모리 설정을 조정할 때 사용합니다.
- `jetbrains-plugin-development`: IntelliJ Platform 플러그인을 설계하고 구현할 때 사용합니다.
- `biz-opportunity-scout`: 시장 규모, 수익성, 경쟁 구도를 바탕으로 사업 기회를 검토할 때 사용합니다.
- `veo-prompt-director`: Google Veo용 영상 생성 프롬프트를 구조화할 때 사용합니다.
- `linear-issue-creator`: Linear에 메인 이슈와 하위 이슈를 구조적으로 등록할 때 사용합니다.
- `linear-issue-worker`: Linear 하위 이슈의 구현 작업을 수행할 때 사용합니다.
- `linear-issue-reviewer`: 완료된 Linear 하위 이슈의 기준 충족 여부를 검토할 때 사용합니다.
