# agents-md-generator Benchmark Report — Iteration 1

## Summary

| Metric | Improved Skill | Baseline (Old) | Delta |
|---|---|---|---|
| **Overall Pass Rate** | **77.3%** (17/22) | **36.4%** (8/22) | **+40.9%p** |
| json-helper2 (IntelliJ Plugin) | 90.0% (9/10) | 40.0% (4/10) | +50.0%p |
| corral (Tauri + React) | 66.7% (8/12) | 33.3% (4/12) | +33.4%p |

## What Changed

Section 3 (Core Behaviors & Patterns)과 Section 4 (Conventions)의 분석 깊이를 개선.

**변경 파일:**
- `references/agents_md_template.md` — Section 3에 3단계 분석 프로세스(Surface → Deep Tracing → Validation) 도입, 패턴 카테고리 3개 추가(Resilience & Recovery, Cross-boundary Wiring, Shared Resource Management). Section 4에 분석 접근법 강화, 관례 카테고리 4개 추가(API & Interface Design, Configuration & Registration Structure, Boundary Conventions, Component Composition).
- `references/read_only_commands.md` — Deep Analysis Strategy 섹션 추가 (cross-reference callers, end-to-end flow tracing, config file sampling, role comparison, failure path analysis).
- `SKILL.md` — Section 3/4 설명 업데이트.

## Eval 0: json-helper2 (IntelliJ Plugin, Kotlin)

### Assertion Results

| Assertion | Improved | Baseline | Category |
|---|---|---|---|
| s3-scope-marker | FAIL | FAIL | Section 3 |
| s3-shared-service-reuse | PASS | PASS | Section 3 |
| s3-callback-wiring | PASS | PASS | Section 3 |
| s3-centralized-lookup | **PASS** | FAIL | Section 3 |
| s4-action-lifecycle | **PASS** | FAIL | Section 4 |
| s4-thin-shell | **PASS** | FAIL | Section 4 |
| s4-config-grouping | **PASS** | FAIL | Section 4 |
| s4-message-key-hierarchy | **PASS** | FAIL | Section 4 |
| s3-pattern-depth | PASS | PASS | Quality |
| s4-convention-depth | PASS | PASS | Quality |

### Key Differences

**Improved skill이 새로 포착한 패턴:**
- Shared ObjectMapper reuse: 단순 접근 방법이 아닌, 어떤 서비스들이 공유하는지 구체적 흐름 기술
- Callback Registration in Tab Management: nullable lambda 필드 + setOn*Listener() 기반 wiring 메커니즘
- Centralized action lookup: `JsonHelperActionUtils.getPanel(e)` 중앙화 패턴
- Template Placeholder Flow: two-phase extract/restore with UUID sentinel
- Content Size Routing: 100KB 임계값 기반 EDT vs background thread 분기
- PrettyPrinter Caching: ConcurrentHashMap keyed on (indentSize, useCompactArrays)

**Improved skill이 새로 포착한 관례:**
- Action Shell Pattern: actionPerformed/update 2-method 분리
- plugin.xml Action Registration: feature context별 그룹핑 + separator 클러스터링
- Localization Keys: `context.component.role` 계층 구조
- Icon Access: JsoninjaIcons.get*Icon(project?) 중앙화 패턴
- Method Chaining: setter가 `this` 반환하는 fluent 패턴

**여전히 누락:**
- s3-scope-marker: plugin-owned 문서에만 적용하는 userData marker 기반 범위 제한 패턴. 매우 도메인 특화적이며 extension-point 구현체 내부를 깊이 분석해야 발견 가능.

## Eval 1: corral (Tauri + React, Rust/TypeScript)

### Assertion Results

| Assertion | Improved | Baseline | Category |
|---|---|---|---|
| s3-self-healing | **PASS** | FAIL | Section 3 |
| s3-permission-flow | FAIL | FAIL | Section 3 |
| s3-degraded-startup | PASS | PASS | Section 3 |
| s3-settings-mutation-flow | FAIL | FAIL | Section 3 |
| s3-linked-history | FAIL | FAIL | Section 3 |
| s4-callback-naming | FAIL | FAIL | Section 4 |
| s4-hook-return-shape | **PASS** | FAIL | Section 4 |
| s4-component-composition | **PASS** | FAIL | Section 4 |
| s4-boundary-convention | **PASS** | PASS | Section 4 |
| s4-localization-convention | PASS | PASS | Section 4 |
| s3-pattern-depth | PASS | PASS | Quality |
| s4-convention-depth | PASS | PASS | Quality |

### Key Differences

**Improved skill이 새로 포착한 패턴:**
- Settings persistence with resilience: corrupt 감지 → quarantine (timestamped, 최대 5개) → backup restore → defaults fallback 전체 흐름
- Poisoned-lock recovery: clear_poison() + inner value 반환 + 구조화된 로깅
- Cross-layer error flow: Result<T, AppError> → String 변환 (IPC boundary) → renderer resolveErrorMessage 전체 체인
- Output / event dispatcher: OnceLock<AppHandle> 기반 centralized dispatch + stdout 호환
- Window close vs. process exit: ApplicationExitState AtomicBool 기반 두 경로 분리

**Improved skill이 새로 포착한 관례:**
- Hook return shape: flat object with isLoading/errorMessage/in-flight flags + named action callbacks
- Component composition: BaseModal/ConfirmDialog/ToggleSwitch → feature-specific modal wrapping
- Boundary error flattening: AppError code()/message() → plain String at adapter boundary
- Schema drift absorption: #[serde(default)] + Default impl + normalization-on-load
- Structured Rust logging: event=name key=value 형식

**여전히 누락 (4개):**
- s3-permission-flow: PermissionFlowState가 이름으로 언급되지만, paired event 프로토콜(permission:required / permission:granted)과 idempotent state machine 동작이 기술되지 않음. 여러 파일에 걸친 renderer↔native 이벤트 쌍 추적이 필요.
- s3-settings-mutation-flow: persist → local snapshot push → server sync trigger가 4+ command adapter에서 반복되는 cross-cutting 패턴이나, 각 adapter를 비교 분석하지 않으면 발견 어려움.
- s3-linked-history: group_id 기반 set 단위 복원 + SQLite schema migration/drop-recreate. persistence 내부 깊은 곳의 패턴.
- s4-callback-naming: handle*/on*/set* 구분은 체계적 이벤트 핸들러 샘플링이 필요한 미묘한 관례.

## Analysis

### Non-discriminating Assertions
- `s3-pattern-depth`와 `s4-convention-depth`는 old/new 모두 통과. 이 품질 체크는 임계값이 너무 관대할 수 있음. 향후 "describes full multi-layer flow" 등 더 엄격한 기준으로 분리 필요.

### Remaining Gap Pattern
여전히 누락된 5개 assertion은 공통 특성을 가짐:
1. **Multi-file cross-reference 필요**: 단일 파일 분석으로 발견 불가. 4+ 파일의 동일 패턴을 비교해야 함.
2. **레이어 간 paired protocol**: native↔renderer 이벤트 쌍, adapter 간 공통 흐름 등 두 레이어를 동시에 추적해야 발견.
3. **도메인 특화 깊이**: userData marker, group_id undo/redo 등 프레임워크 API 수준의 이해가 필요한 패턴.

### Improvement Direction
이 gap을 메우려면:
- "같은 역할의 구현체 3개 이상을 비교하라"는 가이드를 더 강화
- "native↔renderer 이벤트 쌍을 양쪽에서 추적하라"는 cross-boundary tracing 가이드 추가
- "persistence 레이어의 write path와 recovery path를 모두 확인하라"는 가이드 추가

## Files

- Eval outputs: `iteration-1/*/outputs/AGENTS.md`
- Grading details: `iteration-1/*/grading.json`
- Benchmark data: `iteration-1/benchmark.json`
- Interactive viewer: `/tmp/agents-md-generator-review.html`
