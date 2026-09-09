# 변경 기록

이 프로젝트의 주요 변경 사항을 기록합니다.

문서 형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/)을 따르며, 버전은 [Semantic Versioning](https://semver.org/lang/ko/)을 따릅니다.

## [Unreleased]

## [1.8.0] - 2026-09-09

### 추가

- `document-writing`에 문서 유형별 작성 흐름과 디자인 시스템 문서 템플릿 추가
- `react-guide`에 React 18/19 SSR·스트리밍·hydration, `vite-guide`에 Vite 7/8 SSR 통합 가이드 추가

### 개선

- `document-writing`의 디자인 방향 설정, 브랜드 자산 재사용, 반복 피드백 기준 개선
- `agents-md-generator`의 기존 문서 최초 편입 확인, 주요 사실의 출처 추적과 보존 검토 개선
- 코드 리뷰 스킬의 기본 범위를 미커밋 변경 전체로 확대하고 버전별 동작 추적과 오탐 확인 개선
- `jetbrains-vmoptions`의 튜닝을 실제 실행 환경과 측정 근거에 맞추고 재시작 확인·복구 절차 개선
- `kysely-converter`를 쿼리 작성·수정·리팩터링·타입 오류 진단까지 확장하고 Kysely 0.29.5 가이드 개선
- `release-it`의 단일 프로젝트·모노레포 버전 선택과 단계별 확인, 취소 후 남은 상태 안내 개선
- `system-prompt-creator`의 요구사항 기반 평가와 프롬프트 개정 간 비교 절차 개선
- `typst-creator`의 장문·내보내기·발표 자료 작성 가이드와 7개 안정 버전 호환성 확인 개선
- `task-brief-creator`와 caveman 변형의 요구사항 확인, 검토 종료 기준과 briefset 예제 개선

### 수정

- `document-writing`의 FDD 근거 검토와 정책 적용 범위 보존, PNG 검증 기준 수정
- `agents-md-generator`의 여러 줄 Gradle 선언 탐지 오류 수정
- `task-brief-creator`의 경로·Markdown 구조·의존성 검증 오류 수정

### 변경

- `jetbrains-plugin-development`의 API 가이드를 IntelliJ 2026.2.2 기준으로 갱신하고 공개 API만 사용하도록 변경
- 코드 리뷰 결과는 결함과 유지보수성 의견을 구분하고 요청한 경우에만 판정을 제공하도록 변경
- `task-brief-creator`의 최상위 Out of Scope 제외 항목에 `[hard]`·`[deferred]`를 필수화하고, 항목이 없으면 `None — <reason>`만 허용하도록 변경
- `task-brief-creator`의 경로 참조에 `Route:` 표기와 별도 파일시스템 진입점을 요구하도록 변경

### 제거

- `veo-prompt-director` 스킬과 README의 관련 안내 제거

### 추가

- 사람이 읽기 좋은 구조화 문서를 위한 `document-writing` skill 추가 — 10개 문서 유형 라우팅, 점진적 reference 로딩, 근거 기반 편집, 구조 검증 지원. Design System Document는 제품 UI와 storefront 시각 자산 출력 세트를 분리하고, allowlist 없이 범위에 포함된 임의의 디지털 storefront를 동적으로 식별해 현재 1차 자료를 조사. 현실형 fixture 행동 eval, 균형형 선택 사례 60개, 스킬 사용·미사용 쌍대 실행, tool·출처 기록, negative control, blind 비교, 정적 review, 실제 PNG canary와 로컬·CI·release evidence 검증 추가

### 제거

- `feature-design-doc`의 생성·갱신·사실 확인·정규화·템플릿·검증기 계약을 `document-writing`으로 통합하고 독립 패키지 제거

## [1.7.1] - 2026-08-10

### 수정

- `orchestration`이 자동 호출되지 않도록 description 수정

## [1.7.0] - 2026-08-10

### 추가

- `react-guide`와 Vite v8을 지원하는 `vite-guide` skill 추가

### 개선

- `task-brief-creator`를 명확한 작업 지시서 생성 도구로 개선
- `typst-creator`에 Typst 0.13, 0.14, 0.15 지원 추가로 호환성 개선

### 수정

- `iterative-self-review`가 자동 호출되지 않도록 description 수정

### 제거

- `react-vite-guide`와 오래된 React composition·performance optimization reference 제거

## [1.6.0] - 2026-07-06

### 추가

- `orchestration` 대형 작업을 격리된 sub-agent 단계로 나누는 새 skill 추가
- `fable5.md` 기반 운영 지침과 가이드라인 추가

### 개선

- `agents-md-generator` Folder Structure 대신 검증된 Ownership Map을 생성하도록 개선
- `task-brief-creator` brief 생성 흐름 개선

### 수정

- `iterative-self-review` 안내 수정

## [1.5.0] - 2026-06-11

### 추가

- `iterative-self-review` 반복 개선 검증을 위한 새 skill 추가 — sub-agent에 사용자 질의와 작업 산출물 중심의 최소 prompt를 전달하고, 명시적 호출 시에만 실행
- `feature-design-doc` 단일 제품 기능 설계 문서 작성·검토용 skill 추가
- `prompt-engineering.md`와 `delegated-review-loop` 문서 추가

### 개선

- `task-brief-creator`와 `task-brief-creator-caveman` brief 성능 관련 안내 개선
- `system-prompt-creator`와 `agents-md-generator` 안내 개선

## [1.4.0] - 2026-05-10

### 추가

- `task-brief-creator`에 사용자 의사결정 표와 콘텐츠 커버리지 셀프체크 추가

### 개선

- `task-brief-creator` Stage 4 분기형 질문 흐름을 사용자 의사결정 표 중심으로 개선
- `task-brief-creator` briefset 안내와 예시를 새 작업 흐름에 맞게 개선

### 변경

- `task-brief-creator-caveman` caveman 모드를 콘텐츠 압축이 아닌 문체 전용 모드로 설명 변경

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
