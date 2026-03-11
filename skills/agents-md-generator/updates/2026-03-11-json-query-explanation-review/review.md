---
#### 작업 정보
- 작업 agent : codex(gpt-5.4 medium)
- 검증/분석 agent : junie(opus 4.6)
- GitHub 주소 : https://github.com/buYoung/intellij-jsoninja
- commit hash : 2cd9544a8f60ee44b4c31b804cddac459b7c354a
- 작업 유형 : 코드 조회 (Patch 아님)
- prompt : "json query의 동작에 대해 설명해줘. 어떤 기능, 흐름, 키 포인트 등등"
- 리뷰 포인트 : 작업시간은 LLM 모델의 그때그때 상태에 따라 다르므로 결과를 중점으로 볼 것

---

### 1. `no AGENTS.md` 결과 리뷰 (1분 2초)

#### 구조
- 서두에서 json query를 2가지 축(query 실행 + path 계산/복사)으로 분류
- 핵심 엔진(`JsonQueryService`) → UI 흐름(`JsonQueryPresenter`, `JsonTabContextFactory`) → path 계산(`JsonPathHelper`) 순으로 설명
- 마지막에 키 포인트 7개를 bullet으로 정리

#### 장점
- **핵심 파일 식별 정확**: `JsonQueryService`, `JsonQueryPresenter`, `JsonTabContextFactory`, `JsonPathHelper`, `CopyJsonQueryAction`, `JsonEditorTooltipListener` 등 관련 파일을 빠짐없이 언급
- **동작 흐름 설명이 명확**: "별도 결과 패널이 아니라 현재 탭 editor 내용 교체 방식"이라는 핵심 설계를 정확히 짚음
- **template placeholder 대응**까지 언급하여 edge case 인지 수준이 양호
- 라인 번호가 포함된 파일 링크 제공

#### 단점
- **엔진별 차이 설명이 얕음**: Jayway JsonPath와 JMESPath의 구체적 차이(예: `SUPPRESS_EXCEPTIONS` 옵션, root 문자 `$` vs `@`)를 키 포인트에서만 간략히 언급
- **실행 흐름이 서술형**: 번호 매김 없이 문단으로 이어져 있어 단계별 추적이 어려움
- **상태 관리 설명 부족**: `originalJson` 유지 구조, `onBeforeSearchCallback` 등 내부 상태 흐름에 대한 설명 없음
- **예외 처리 전략**을 "null로 정리" 수준으로만 언급

---

### 2. `old AGENTS.md` 결과 리뷰 (50초)

#### 구조
- 서두에서 기능 정의 + 설정 기반 엔진 선택이라는 핵심을 한 문장으로 요약
- 기능 2축 → 동작 흐름(6단계 번호 리스트) → 서비스 내부 → 키 포인트 → path 복사/tooltip → template placeholder → 주의할 점 순으로 전개

#### 장점
- **가장 체계적인 구조**: 동작 흐름을 6단계 번호 리스트로 정리하여 추적이 용이
- **상태 관리 설명이 가장 충실**: `originalJson` 기준 재조회 구조, 빈 query = 초기화, `onBeforeSearchCallback`으로 원본 채우기 등을 정확히 설명
- **예외 처리 전략 구체적**: `SUPPRESS_EXCEPTIONS` 옵션, `null` 흡수, UI 안정성 우선 설계를 명시적으로 구분
- **주의할 점 섹션** 별도 제공: 에러 메시지 미표시, 레거시 네이밍(`setupJmesPathPresenter`, `jmesComponent`) 등 실무적 주의사항 포함
- **키 포인트가 가장 풍부**: 5개 항목에 각각 코드 레퍼런스 첨부
- **fallback 처리**(`fromString()`의 `JAYWAY_JSONPATH` fallback) 언급

#### 단점
- **분량이 가장 많음**: 상세한 만큼 빠르게 훑기엔 부담
- 일부 설명이 반복적 (동작 흐름과 키 포인트에서 같은 내용 중복)

---

### 3. `new AGENTS.md` 결과 리뷰 (36초)

#### 구조
- 서두에서 2가지 기능 분류 → 핵심 파일 4개 나열 → 기능/실행 흐름/엔진별 차이/키 포인트/Copy JSON Query 섹션으로 구분

#### 장점
- **가장 빠른 응답 시간**: 36초로 가장 짧으면서도 내용 품질 유지
- **섹션 구분이 명확**: 볼드 헤딩(`기능`, `실행 흐름`, `엔진별 차이`, `키 포인트`)으로 가독성 우수
- **실행 흐름 설명이 정확하고 구체적**: `onBeforeSearchCallback`으로 원본 JSON 채우는 시점, pooled thread → EDT 전환 등 threading 구조까지 설명
- **엔진별 차이를 별도 섹션으로 분리**: Jayway의 `SUPPRESS_EXCEPTIONS`, JMESPath의 Jackson `JsonNode` 파싱 등을 명확히 구분
- **검색 대상이 `originalJson`이라는 핵심 설계**를 키 포인트 첫 항목으로 강조
- 테스트 파일(`JMESPathServiceTest.kt`) 레퍼런스까지 포함

#### 단점
- `주의할 점` 섹션이 없음 (old AGENTS.md에서 다뤘던 레거시 네이밍, 에러 메시지 미표시 등 누락)
- template placeholder 설명이 마지막에 간략하게만 언급

---

### 종합 비교표

| 항목 | no AGENTS.md | old AGENTS.md | new AGENTS.md |
|------|-------------|---------------|---------------|
| **응답 시간** | 1분 2초 | 50초 | **36초** |
| **구조화 수준** | 중 (서술형) | **높음** (번호 리스트) | **높음** (섹션 분리) |
| **핵심 파일 식별** | ✓ | ✓ | **✓** |
| **동작 흐름 정확성** | 중 | **높음** | **높음** |
| **상태 관리 설명** | ✗ | **✓** (가장 상세) | **✓** |
| **엔진별 차이 설명** | 얕음 | 중 | **별도 섹션으로 분리** |
| **예외 처리 전략** | 얕음 | **구체적** | 중 |
| **주의할 점/레거시** | 간략 언급 | **별도 섹션** | ✗ |
| **template placeholder** | ✓ | ✓ | 간략 |
| **테스트 파일 참조** | ✗ | ✗ | **✓** |
| **가독성** | 중 | 중 (분량 많음) | **높음** |

---

### 결론

#### 응답 시간 관점
- new AGENTS.md가 **36초**로 가장 빠르며, no AGENTS.md(1분 2초) 대비 약 **42% 단축**
- old AGENTS.md도 50초로 양호하지만, new AGENTS.md가 더 짧은 시간에 동등 이상의 품질을 달성

#### 결과 품질 관점
- **no AGENTS.md**: 핵심은 잡았지만 상태 관리, 예외 처리 전략 등 깊이가 부족하고 구조화 수준이 낮음
- **old AGENTS.md**: 가장 상세하고 체계적이나, 분량이 많고 일부 중복이 존재. 주의할 점 섹션이 실무적으로 유용
- **new AGENTS.md**: 응답 시간 대비 **가장 효율적인 결과**. 섹션 분리가 명확하고, 엔진별 차이를 별도로 다루며, threading 구조와 상태 관리까지 정확하게 설명. 테스트 파일 참조까지 포함

#### AGENTS.md 효과
- AGENTS.md가 있으면 **응답 속도와 구조화 수준 모두 향상**됨
- 특히 new AGENTS.md는 에이전트가 코드베이스의 패턴(Service-Driven Flows, Threading, Guard Clauses 등)을 빠르게 파악하도록 도와, **짧은 시간에 더 정확하고 구조적인 설명**을 생성하게 함
- old → new AGENTS.md 전환으로 응답 시간 28% 추가 단축, 가독성 향상, 핵심 설계 포인트 강조력 증가
