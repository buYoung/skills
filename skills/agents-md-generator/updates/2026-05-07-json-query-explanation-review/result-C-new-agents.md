# Result C — `new AGENTS.md`

- 작업 agent: codex (gpt-5.5 medium)
- AGENTS.md 모드: new
- 경과 시간: 1분 7초
- 프롬프트: "json query의 동작에 대해 설명해줘. 어떤 기능, 흐름, 키 포인트 등등"

---

**개요**
`json query`는 탭 상단의 검색 입력창에 쿼리를 넣고 `Enter`를 누르면 현재 탭의 JSON에서 값을 추출해, 에디터 내용을 쿼리 결과로 바꾸는 기능입니다. 지원 언어는 설정값 `jsonQueryType`에 따라 `Jayway JsonPath` 또는 `JMESPath` 둘 중 하나입니다. 기본값은 `Jayway JsonPath`입니다.

**주요 흐름**
1. 탭 생성 시 [JsonTabContextFactory.kt](https://github.com/buYoung/intellij-jsoninja/blob/v1.9.0/src/main/kotlin/com/livteam/jsoninja/ui/component/tab/JsonTabContextFactory.kt#L28)에서 `JsonQueryUiState`, `JsonEditorView`, `JsonQueryPresenter`를 함께 만듭니다.
2. 상단 입력창은 [JsonQueryView.kt](https://github.com/buYoung/intellij-jsoninja/blob/v1.9.0/src/main/kotlin/com/livteam/jsoninja/ui/component/jsonQuery/JsonQueryView.kt#L13)의 `SearchTextField`입니다.
3. 사용자가 쿼리를 입력하고 `Enter`를 누르면 [JsonQueryPresenter.kt](https://github.com/buYoung/intellij-jsoninja/blob/v1.9.0/src/main/kotlin/com/livteam/jsoninja/ui/component/jsonQuery/JsonQueryPresenter.kt#L39)가 입력값을 읽습니다.
4. 쿼리가 비어 있으면 원본 JSON을 다시 표시합니다.
5. 쿼리가 있으면 원본 JSON 유효성을 확인한 뒤 백그라운드 스레드에서 [JsonQueryService.kt](https://github.com/buYoung/intellij-jsoninja/blob/v1.9.0/src/main/kotlin/com/livteam/jsoninja/services/JsonQueryService.kt#L20)를 호출합니다.
6. 결과가 나오면 UI 스레드로 돌아와 결과 JSON을 현재 포맷 설정으로 정리한 뒤 에디터에 넣습니다.

**쿼리 실행 방식**
`JsonQueryService`가 설정을 읽어서 실행기를 고릅니다.

- `JAYWAY_JSONPATH`: `JsonPath.using(...).parse(jsonString).read(expression)`로 실행합니다.
- `JMESPATH`: `JacksonRuntime().compile(expression)` 후 `search(jsonNode)`로 실행합니다.

두 경우 모두 결과는 `objectMapper.writeValueAsString(...)`로 JSON 문자열화됩니다. 그래서 단일 값도 JSON 표현으로 들어갑니다. 예를 들어 문자열 결과면 따옴표가 포함된 JSON 문자열이 됩니다.

**상태 관리의 핵심**
`JsonQueryUiState`는 원본 JSON과 마지막 쿼리를 들고 있습니다. 중요한 점은 쿼리 결과가 에디터에 표시되어도 쿼리 기준은 `model.originalJson`입니다. 즉 “현재 보이는 결과”를 다시 쿼리하는 구조가 아니라, 저장된 원본 JSON에 대해 쿼리를 반복 실행하는 구조입니다.

초기 콘텐츠가 있으면 탭 생성 시 원본 JSON으로 저장됩니다. 초기 콘텐츠 없이 사용자가 에디터에 JSON을 입력한 뒤 처음 검색하면, 검색 직전에 에디터 내용을 원본 JSON으로 캡처합니다.

**설정 연동**
설정 화면의 `Query Language` 콤보박스가 [JsoninjaSettingsState.kt](https://github.com/buYoung/intellij-jsoninja/blob/v1.9.0/src/main/kotlin/com/livteam/jsoninja/settings/JsoninjaSettingsState.kt#L24)의 `jsonQueryType`에 저장됩니다. 이 값은 쿼리 실행뿐 아니라 경로 복사와 툴팁에도 같이 쓰입니다.

**경로 복사와 툴팁**
오른쪽 클릭 메뉴의 `JSON 경로 복사`는 [CopyJsonQueryAction.kt](https://github.com/buYoung/intellij-jsoninja/blob/v1.9.0/src/main/kotlin/com/livteam/jsoninja/actions/CopyJsonQueryAction.kt#L13)에서 처리합니다. 현재 커서 위치의 JSON 요소를 찾아 설정된 쿼리 언어에 맞는 경로를 클립보드에 복사합니다.

경로 생성은 [JsonPathHelper.kt](https://github.com/buYoung/intellij-jsoninja/blob/v1.9.0/src/main/kotlin/com/livteam/jsoninja/utils/JsonPathHelper.kt#L18)가 담당합니다. 일반 키는 점 표기법을 쓰고, 특수문자나 숫자로 시작하는 키는 따옴표가 필요한 표기법으로 만듭니다. 템플릿 자리표시자가 있는 JSON도 임시 토큰으로 바꿔 경로 계산을 시도합니다.

**주의할 점**
현재 구현상 `JsonQueryPresenter`와 `JsonQueryView`의 일부 주석과 placeholder는 아직 `JMESPath` 중심 표현이 남아 있지만, 실제 실행은 설정값에 따라 `Jayway JsonPath`와 `JMESPath`를 모두 지원합니다. 또한 원본 JSON이 처음 검색 시점에 캡처되는 구조라, 이후 에디터를 직접 수정해도 이미 저장된 원본이 있으면 검색 기준이 자동으로 최신 에디터 내용으로 갱신되지는 않습니다.
