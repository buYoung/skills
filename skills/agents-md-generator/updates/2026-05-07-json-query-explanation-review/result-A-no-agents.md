# Result A — `no AGENTS.md`

- 작업 agent: codex (gpt-5.5 medium)
- AGENTS.md 모드: 없음
- 경과 시간: 1분 14초
- 프롬프트: "json query의 동작에 대해 설명해줘. 어떤 기능, 흐름, 키 포인트 등등"

---

**전체 구조**
`json query`는 탭 상단 입력창에 쿼리를 넣고 Enter를 누르면, 현재 탭의 원본 JSON에 쿼리를 실행한 뒤 결과 JSON으로 편집기 내용을 교체하는 기능입니다. 핵심 코드는 [JsonQueryPresenter.kt](https://github.com/buYoung/intellij-jsoninja/blob/v1.9.0/src/main/kotlin/com/livteam/jsoninja/ui/component/jsonQuery/JsonQueryPresenter.kt#L41), [JsonQueryService.kt](https://github.com/buYoung/intellij-jsoninja/blob/v1.9.0/src/main/kotlin/com/livteam/jsoninja/services/JsonQueryService.kt#L41), [JsonTabContextFactory.kt](https://github.com/buYoung/intellij-jsoninja/blob/v1.9.0/src/main/kotlin/com/livteam/jsoninja/ui/component/tab/JsonTabContextFactory.kt#L72)에 나뉘어 있습니다.

**지원 기능**
- 설정에서 쿼리 언어를 고릅니다. 기본값은 `JAYWAY_JSONPATH`이고, `JMESPATH`도 지원합니다.
- 입력창에서 쿼리를 실행하면 결과만 편집기에 표시됩니다.
- 쿼리 입력을 비우고 Enter를 누르면 저장해 둔 원본 JSON을 다시 표시합니다.
- 편집기에서 우클릭하면 현재 커서 위치의 JSON 경로를 설정된 쿼리 언어 형식으로 복사할 수 있습니다. 이 부분은 [CopyJsonQueryAction.kt](https://github.com/buYoung/intellij-jsoninja/blob/v1.9.0/src/main/kotlin/com/livteam/jsoninja/actions/CopyJsonQueryAction.kt#L14)와 [JsonPathHelper.kt](https://github.com/buYoung/intellij-jsoninja/blob/v1.9.0/src/main/kotlin/com/livteam/jsoninja/utils/JsonPathHelper.kt#L22)가 담당합니다.
- 보조키를 누른 채 마우스를 올리면 현재 노드의 쿼리 경로를 툴팁으로 보여줍니다.

**실행 흐름**
1. 탭이 만들어질 때 `JsonQueryUiState`와 `JsonQueryPresenter`가 생성되고, 쿼리 입력창이 편집기 위쪽에 붙습니다. [JsonTabContextFactory.kt](https://github.com/buYoung/intellij-jsoninja/blob/v1.9.0/src/main/kotlin/com/livteam/jsoninja/ui/component/tab/JsonTabContextFactory.kt#L28)
2. 초기 JSON이 있으면 `model.originalJson`에 저장합니다. 이 값이 이후 쿼리의 기준 원본입니다. [JsonTabContextFactory.kt](https://github.com/buYoung/intellij-jsoninja/blob/v1.9.0/src/main/kotlin/com/livteam/jsoninja/ui/component/tab/JsonTabContextFactory.kt#L77)
3. 사용자가 쿼리 입력창에서 Enter를 누르면 `JsonQueryPresenter`가 입력값을 읽습니다. 빈 값이면 원본 JSON을 다시 표시하고, 값이 있으면 `performSearch`를 호출합니다. [JsonQueryPresenter.kt](https://github.com/buYoung/intellij-jsoninja/blob/v1.9.0/src/main/kotlin/com/livteam/jsoninja/ui/component/jsonQuery/JsonQueryPresenter.kt#L41)
4. 실행 전 원본 JSON이 비어 있거나 유효하지 않으면 중단합니다. 표현식 자체도 먼저 검증합니다. [JsonQueryPresenter.kt](https://github.com/buYoung/intellij-jsoninja/blob/v1.9.0/src/main/kotlin/com/livteam/jsoninja/ui/component/jsonQuery/JsonQueryPresenter.kt#L73)
5. 실제 쿼리는 백그라운드 스레드에서 실행하고, 결과 반영은 화면 갱신 스레드에서 처리합니다. [JsonQueryPresenter.kt](https://github.com/buYoung/intellij-jsoninja/blob/v1.9.0/src/main/kotlin/com/livteam/jsoninja/ui/component/jsonQuery/JsonQueryPresenter.kt#L85)
6. 결과는 현재 포맷 설정에 맞춰 다시 정리된 뒤 편집기에 표시됩니다. [JsonTabContextFactory.kt](https://github.com/buYoung/intellij-jsoninja/blob/v1.9.0/src/main/kotlin/com/livteam/jsoninja/ui/component/tab/JsonTabContextFactory.kt#L92)

**쿼리 엔진**
`JsonQueryService`는 설정값을 읽어서 분기합니다. [JsonQueryService.kt](https://github.com/buYoung/intellij-jsoninja/blob/v1.9.0/src/main/kotlin/com/livteam/jsoninja/services/JsonQueryService.kt#L41)

- `JAYWAY_JSONPATH`: `JsonPath.using(...).parse(jsonString)` 후 `context.read(expression)`을 실행합니다.
- `JMESPATH`: Jackson으로 JSON을 `JsonNode`로 읽고, `JacksonRuntime().compile(expression)` 후 `search`를 실행합니다.
- 두 경우 모두 결과는 `objectMapper.writeValueAsString(result)`로 JSON 문자열화됩니다.
- 결과가 `null`이면 화면은 갱신하지 않고 로그만 남깁니다.

**키 포인트**
가장 중요한 설계 포인트는 “원본 JSON”과 “현재 표시 중인 결과 JSON”을 분리한다는 점입니다. 쿼리 결과가 편집기에 표시되어도 `model.originalJson`은 그대로 유지되므로, 다음 쿼리는 결과가 아니라 원본을 기준으로 실행됩니다. 다만 현재 구현에서는 원본이 이미 설정된 뒤 편집기 내용을 사용자가 직접 크게 바꿔도, 그 변경분이 자동으로 `originalJson`에 다시 반영되는 흐름은 제한적입니다.

경로 복사 기능은 실행 쿼리와 별개지만 같은 설정을 씁니다. `JMESPATH`면 `foo.bar[0]` 계열로, `JAYWAY_JSONPATH`면 `$.foo.bar[0]` 계열로 만듭니다. 특수 문자가 들어간 키는 따옴표 기반 표기로 처리합니다.
