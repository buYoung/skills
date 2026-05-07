# 변경 기록

이 프로젝트의 주요 변경 사항을 기록합니다.

문서 형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/)을 따르며, 버전은 [Semantic Versioning](https://semver.org/lang/ko/)을 따릅니다.

## [Unreleased]

## [1.3.0] - 2026-05-07

### 추가

- 설치 안내에 `analysis-skills`·`devops-skills` 플러그인 번들 추가

### 개선

- README에서 `jetbrains-plugin-development`는 Available Skills로 승격, `ux-design-guide`는 Under Evaluation으로 환원하도록 카탈로그 개선
- `agents-md-generator`: `AGENTS.md` 갱신 흐름과 Working Agreements 규칙을 정비하고 사용자 추가 내용은 `## Custom Instructions`에 보존하도록 개선

### 내부

- 저장소 구조와 일치하도록 프로젝트 자체 `AGENTS.md` 정리
- `agents-md-generator/updates/`에 `2026-05-07-json-query-explanation-review` 리뷰 폴더 도입

## [1.2.0] - 2026-05-05

### 추가

- `task-brief-creator`용 `grill-me` skill 추가
- `task-brief-creator-caveman`용 caveman skill 추가

### 제거

- 사용할 수 없는 skill 제거

### 내부

- `release-it`에서 `claude plugin` 버전도 함께 갱신하도록 정리
- 기타 관리 항목 정리

## [1.1.0] - 2026-05-01

### 추가

- `agents-md-generator`에 character budget 계산용 `loc_to_limit.py`, monorepo 마커 탐지용 `detect_monorepo.py`, update 모드 섹션 파싱용 `parse_sections.py` 헬퍼 스크립트 추가

### 개선

- `task-brief-creator` fix·perf·refactor 브리프에 Reproduction, Baseline Measurement, Behavior Contract 같은 타입 조건부 섹션을 두도록 개선
- `task-brief-creator validate_brief.py`가 타입 조건부 섹션 본문과 Entry Points 경로 실존 여부까지 검증하도록 개선
- `task-brief-creator` Stage 3 코드베이스 리뷰를 inline 도구 강제에서 Serena·ast-grep·짧은 subagent 허용으로 개선
- `task-brief-creator` 예제에 "Picked Up Cold — Coding Agent's First Actions" 블록을 추가하고 saved brief가 작업 지시서임을 README에 명시하도록 개선
- `agents-md-generator` SKILL.md에 6단계 Execution Workflow와 "Single-Context Execution (No Subagents)" scope 경계를 명문화하도록 개선
- `agents-md-generator` monorepo 감지에 moonrepo·Buck2 마커가 추가되도록 개선
- `agents-md-generator` 읽기 전용 탐색이 Serena MCP 심볼 도구를 우선하고 rg·grep·find을 fallback으로 쓰도록 개선
- `agents-md-generator` working agreements에서 테스트·린트 안내가 사용자 명시적 요청 시에만 노출되도록 개선

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
