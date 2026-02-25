---
#### 요구사항
- JSON 포맷팅 시 템플릿 문법(`{{.value}}`)도 포맷팅 결과에 포함되도록 함
- 예시: `{ "test": {{.value}} }` 포맷 후에도 `{ "test": {{.value}} }`와 같이 유지되어야 함

---

### 1. `no-agents-test.patch` 상세 리뷰

#### 구현 방식
- **정규식**: `("([^"\\]|\\.)*")|(\{\{.*?\}\}|\$\{.*?\}|<%.*?%>)` — 문자열 리터럴과 3종류의 템플릿 문법(`{{...}}`, `${...}`, `<%...%>`)을 한 번에 처리
- **플레이스홀더**: `"__JSONINJA_TEMPLATE_${counter++}__"` (따옴표 포함)
- **치환/복원**: `prepareJsonForFormatting()` / `restoreTemplates()`
- **변수명 변경**: `var formatState = formatState` → `var currentFormatState = formatState` (parameter shadowing 제거)

#### 장점
- `${...}`, `<%...%>` 등 **다양한 템플릿 문법 지원** (확장성 높음)
- 정규식에서 문자열 리터럴 그룹을 먼저 매칭하여 **문자열 내부 템플릿을 자연스럽게 보존**
- parameter shadowing 문제 해결 (`currentFormatState`)
- KDoc 주석이 잘 작성됨

#### 단점
- **기존 테스트 파일(`JsonFormatterServiceTest.kt`)을 직접 수정** — whitespace 정리(trailing space 제거) + `assertEquals` 포맷 변경 등 불필요한 변경이 대량 포함
- 테스트가 기존 파일에 추가되어 **template 관련 테스트가 분리되지 않음**
- `DOT_MATCHES_ALL` 옵션 사용 — `{{...}}` 안에 개행이 있는 경우까지 매칭하는데, 이것이 의도적인지 불명확
- `combinedTemplateRegex`가 클래스 필드로 선언되어 있어 `companion object`의 상수 패턴과 불일치

#### 테스트 커버리지
- `testFormatJsonWithTemplate`: 기본 value 템플릿, 다중 템플릿, key 템플릿, 문자열 내부 템플릿, uglify 모드
- `testIsValidJsonWithTemplate`: 유효성 검사
- 커버리지는 양호하나, **negative case(잘못된 템플릿)** 테스트 없음

---

### 2. `agents-v1-test.patch` 상세 리뷰

#### 구현 방식
- **정규식**: `\{\{.*?\}\}` (단순히 `{{...}}`만 매칭)
- **2단계 치환**:
    1. 모든 `{{...}}`를 `__JNJ_TPL_N__`으로 치환
    2. 따옴표 밖에 있는 플레이스홀더만 `"__JNJ_TPL_Q_N__"`으로 감싸기 (lookahead/lookbehind 사용)
- **복원**: `_TPL_Q_` 포함 여부로 따옴표 제거 여부 결정

#### 장점
- **문자열 안의 템플릿 vs 밖의 템플릿을 2단계로 분리 처리** — 로직이 명시적
- `sortedByDescending { it.length }`로 긴 플레이스홀더 먼저 치환하여 부분 매칭 방지
- fast-exit: `if (!json.contains("{{"))` 체크
- 별도 테스트 파일(`JsonTemplateFormatTest.kt`)로 분리

#### 단점
- **2단계 치환이 불필요하게 복잡** — 첫 단계에서 모든 `{{...}}`를 일괄 치환 후, 각각에 대해 다시 `Regex`를 생성하여 체크하므로 **성능 및 가독성 모두 비효율적**
- `(?<!["'])placeholder(?!["'])` lookbehind 패턴이 **문자열 내부 깊은 곳의 템플릿을 정확히 구분하지 못할 수 있음** (예: `"url": "http://{{host}}/api"` 같은 경우 `"` 바로 앞이 아닌 위치에서 문제 발생 가능)
- `${...}`, `<%...%>` 등 **다른 템플릿 문법 미지원**
- `isValidJson()`에서 `replaceTemplates` 호출 후 `trimedJson` 변수를 재할당하는 방식이 원본과 다르게 변경됨
- `formatJson`에서 `var formatState = formatState` parameter shadowing이 그대로 남아있음

#### 테스트 커버리지
- Go template, 다중 템플릿, 따옴표 내부 템플릿, 공백 포함 템플릿, mixed 템플릿
- 비교적 다양하지만 **uglify 모드 테스트 없음**, negative case 없음

---

### 3. `agents-v2-test.patch` 상세 리뷰

#### 구현 방식
- **정규식**: `("(?:\\.|[^\\"])*")|(\{\{.*?\}\})` — 문자열 리터럴과 `{{...}}`를 한 번에 매칭
- **플레이스홀더**: `"__JSONINJA_TEMPLATE_${counter++}__"` (따옴표 포함)
- **치환/복원**: `replaceTemplates()` / `restoreTemplates()` — 단순하고 직관적

#### 장점
- **가장 간결하고 깔끔한 구현** — 약 30줄의 핵심 로직
- 정규식에서 문자열 리터럴을 먼저 매칭하여 **문자열 내부 템플릿을 한 번의 패스로 정확히 보존** (no-agents와 동일한 원리지만 더 간결)
- **별도 테스트 파일(`JsonFormatterTemplateTest.kt`)로 분리** — 관심사 분리 원칙 준수
- 기존 코드 변경 최소화 — whitespace 정리만 포함, 불필요한 변경 없음
- `formatJson`에서 `var formatState = formatState` 유지하여 **기존 API/동작과의 호환성 보존**
- **negative test 포함** (`testIsValidJsonWithTemplate`에서 broken template `{{.value}` 검증)
- nested template 테스트 포함 (`{{.value { "foo": "bar" } }}`)

#### 단점
- `${...}`, `<%...%>` 등 다른 템플릿 문법 미지원 (단, 요구사항이 `{{...}}`이므로 YAGNI 원칙에 부합)
- fast-exit 최적화 없음 (`{{` 포함 여부 사전 체크 없음 — 미미한 차이)
- KDoc 주석이 없음 (한국어 인라인 코멘트만 존재)

#### 테스트 커버리지
- 기본 포맷팅, key 템플릿, mixed(문자열 내부 + 외부), nested template, validity 검증(positive + **negative**)
- **가장 균형 잡힌 테스트 구성**

---

### 종합 비교표

| 항목 | no-agents | agents-v1 | agents-v2 |
|------|-----------|-----------|-----------|
| **코드 간결성** | 중 | 낮음 (2단계 치환 복잡) | **높음** |
| **정확성** | 높음 | 중 (lookbehind 불안정) | **높음** |
| **기존 코드 변경 범위** | 넓음 (whitespace+리팩터링) | 중간 | **최소** |
| **테스트 분리** | ✗ (기존 파일에 추가) | ✓ | **✓** |
| **Negative 테스트** | ✗ | ✗ | **✓** |
| **확장성** (`${...}` 등) | ✓ | ✗ | ✗ |
| **Parameter shadowing 수정** | ✓ | ✗ | ✗ |
| **변경 라인 수** | ~384줄 | ~243줄 | **~193줄** |

---

### 최종 추천: `agents-v2-test.patch`

#### 추천 이유

1. **최소 변경 원칙(Minimal Changes)**: AGENTS.md에서 명시한 "Minimal changes; preserve public APIs" 원칙에 가장 부합합니다. 기존 코드 구조를 거의 건드리지 않으면서 핵심 기능만 추가합니다.

2. **정규식 전략의 정확성**: `("(?:\\.|[^\\"])*")|(\{\{.*?\}\})` 패턴은 한 번의 패스로 문자열 리터럴 내부/외부를 정확히 구분합니다. agents-v1의 2단계 lookahead/lookbehind 방식보다 훨씬 안정적이고, no-agents의 `DOT_MATCHES_ALL` 옵션 없이도 충분합니다.

3. **YAGNI 원칙**: 요구사항은 `{{...}}` 문법만이므로, `${...}`나 `<%...%>` 지원(no-agents)은 과도한 확장입니다. 나중에 필요할 때 정규식에 그룹을 추가하면 됩니다.

4. **테스트 품질**: 유일하게 **negative case**(broken template)와 **nested template** 테스트를 포함하여, edge case 커버리지가 가장 우수합니다.

5. **코드 가독성**: 30줄 내외의 핵심 로직으로 의도가 명확하며, agents-v1처럼 `_TPL_Q_` 같은 복잡한 구분자 로직이 불필요합니다.

#### 보완하면 좋을 점
- `replaceTemplates`/`restoreTemplates`에 KDoc 주석 추가
- uglify 모드 테스트 추가
- `if (!json.contains("{{"))` fast-exit 추가 (선택사항)
