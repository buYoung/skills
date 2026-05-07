# Result B — `old AGENTS.md`

- 작업 agent: codex (gpt-5.5 medium)
- AGENTS.md 모드: old
- 경과 시간: 1분 4초
- 프롬프트: "json query의 동작에 대해 설명해줘. 어떤 기능, 흐름, 키 포인트 등등"

---

**전체 그림**

`JSON Query`는 탭 상단의 검색 입력칸에서 현재 JSON 문서에 쿼리식을 적용하고, 결과 JSON으로 에디터 내용을 교체해 보여주는 기능입니다. 현재 지원 언어는 `Jayway JsonPath`와 `JMESPath` 두 가지이고, 기본값은 `Jayway JsonPath`입니다. 선택값은 `JsoninjaSettingsState.jsonQueryType`에 저장됩니다: [JsoninjaSettingsState.kt](https://github.com/buYoung/intellij-jsoninja/blob/v1.9.0/src/main/kotlin/com/livteam/jsoninja/settings/JsoninjaSettingsState.kt#L21), [JsonQueryType.kt](https://github.com/buYoung/intellij-jsoninja/blob/v1.9.0/src/main/kotlin/com/livteam/jsoninja/model/JsonQueryType.kt#L3).

**주요 기능**

1. 탭 상단 쿼리 입력
   각 JSON 탭이 만들어질 때 `JsonQueryPresenter`와 검색 입력칸이 에디터 위쪽에 붙습니다. 결과는 같은 에디터에 다시 써집니다: [JsonTabContextFactory.kt](https://github.com/buYoung/intellij-jsoninja/blob/v1.9.0/src/main/kotlin/com/livteam/jsoninja/ui/component/tab/JsonTabContextFactory.kt#L43).

2. 엔터 키 실행
   사용자가 쿼리 입력칸에서 엔터를 누르면 `JsonQueryPresenter`가 현재 입력값을 읽습니다. 입력값이 비어 있으면 원본 JSON으로 되돌리고, 값이 있으면 `performSearch`를 실행합니다: [JsonQueryPresenter.kt](https://github.com/buYoung/intellij-jsoninja/blob/v1.9.0/src/main/kotlin/com/livteam/jsoninja/ui/component/jsonQuery/JsonQueryPresenter.kt#L41).

3. 설정 기반 쿼리 언어 선택
   실제 실행은 `JsonQueryService`가 담당합니다. 매 실행마다 설정의 `jsonQueryType`을 읽고, `JAYWAY_JSONPATH`면 `queryJsonPath`, `JMESPATH`면 `queryJmesPath`로 분기합니다: [JsonQueryService.kt](https://github.com/buYoung/intellij-jsoninja/blob/v1.9.0/src/main/kotlin/com/livteam/jsoninja/services/JsonQueryService.kt#L41).

4. 선택 노드의 경로 복사
   에디터 우클릭 메뉴의 `CopyJsonQueryAction`은 현재 커서 위치의 JSON 요소를 찾아, 설정된 쿼리 언어 형식에 맞는 경로를 클립보드에 복사합니다. 템플릿 자리표시자도 먼저 처리합니다: [CopyJsonQueryAction.kt](https://github.com/buYoung/intellij-jsoninja/blob/v1.9.0/src/main/kotlin/com/livteam/jsoninja/actions/CopyJsonQueryAction.kt#L13), [JsonPathHelper.kt](https://github.com/buYoung/intellij-jsoninja/blob/v1.9.0/src/main/kotlin/com/livteam/jsoninja/utils/JsonPathHelper.kt#L88).

5. 보조 툴팁
   수정자 키를 누른 채 에디터 위를 이동하면 현재 위치의 쿼리 경로를 툴팁으로 보여줍니다. 이때도 설정된 쿼리 언어를 기준으로 경로가 만들어집니다: [JsonEditorTooltipListener.kt](https://github.com/buYoung/intellij-jsoninja/blob/v1.9.0/src/main/kotlin/com/livteam/jsoninja/ui/component/editor/JsonEditorTooltipListener.kt#L47).

**실행 흐름**

1. 탭 생성 시 원본 JSON을 `JsonQueryUiState.originalJson`에 저장합니다.
2. 사용자가 쿼리 입력칸에서 엔터를 누릅니다.
3. `JsonQueryPresenter.performSearch`가 먼저 원본 JSON이 비어 있거나 유효하지 않은지 검사합니다.
4. 쿼리 표현식을 `JsonQueryService.isValidExpression`으로 먼저 컴파일 검증합니다.
5. 검증이 통과하면 백그라운드 스레드에서 쿼리를 실행합니다.
6. 결과가 있으면 화면 갱신은 다시 이벤트 디스패치 스레드에서 수행합니다.
7. `JsonTabContextFactory`의 콜백이 결과 JSON을 현재 포맷 설정으로 정리한 뒤 에디터에 씁니다: [JsonQueryPresenter.kt](https://github.com/buYoung/intellij-jsoninja/blob/v1.9.0/src/main/kotlin/com/livteam/jsoninja/ui/component/jsonQuery/JsonQueryPresenter.kt#L66), [JsonTabContextFactory.kt](https://github.com/buYoung/intellij-jsoninja/blob/v1.9.0/src/main/kotlin/com/livteam/jsoninja/ui/component/tab/JsonTabContextFactory.kt#L92).

**키 포인트**

- 원본 JSON과 결과 JSON을 분리해서 관리합니다. 쿼리 결과로 에디터가 바뀌어도 `model.originalJson`은 기준 입력으로 남아 있습니다.
- 쿼리 실행은 백그라운드에서 하고, 화면 갱신만 이벤트 디스패치 스레드로 돌아옵니다.
- 결과가 `null`이면 화면을 바꾸지 않고 이전 상태를 유지합니다.
- `Jayway JsonPath`는 `Option.SUPPRESS_EXCEPTIONS`가 켜져 있어 일부 조회 실패가 예외 대신 `null`처럼 처리될 수 있습니다.
- 경로 생성은 PSI 구조를 위로 타고 올라가며 객체 키와 배열 인덱스를 조합합니다. 일반 키는 점 표기, 특수 문자가 있는 키는 따옴표 표기를 사용합니다.
- 구현상 입력칸 이름과 일부 주석은 아직 `JMESPath` 중심으로 남아 있지만, 실제 실행 서비스는 두 쿼리 언어를 모두 지원합니다.
