# Working Agreements 코드 작성 규칙 추가와 실측 검증

이번 업데이트로 `agents-md-generator`가 생성하는 `## 5. Working Agreements`(monorepo 루트는 `## 3.`)에 작업 범위와 코드 작성에 관한 새 규칙 14개(N1~N14)가 들어간다. 기존 규칙 9개 중 함수 규칙 1개는 새 함수 추출 규칙에 흡수되어, 타입 검사기가 있는 저장소의 규칙은 9개에서 22개가 된다. 바뀐 파일은 [`references/working_agreements.md`](../../references/working_agreements.md) 하나다.

Sonnet 하위 에이전트로 같은 과제를 반복 실행한 결과, 생성된 AGENTS.md를 따르는 에이전트는 다음과 같이 달라졌다.

- 분기가 셋인 계산을 중첩 삼항식으로 쓰지 않았다.
- 한 번만 쓰는 계산을 함수로 빼는 일이 줄었다.
- TypeScript에서 외부 JSON을 타입만 적어 믿지 않고, 들어올 때 형태를 검사했다.

반면 Python에서는 외부 JSON 검사가 생기지 않았다. 또 바꾸는 함수 안의 기존 줄까지 정리하는 경향이 생겼다. 모든 결과는 쇼핑몰 할인 과제 두 종류를 언어별로 3회씩 실행한 소규모 실험에서 나왔다.

## 바뀐 점

### 새로 생성되는 규칙

아래 ID는 실측 보고서와 같은 ID다. 실제로 생성되는 영문 전문은 [부록](#부록-생성되는-working-agreements-전체-목록)에 있다.

| ID | 에이전트에게 요구하는 것 |
| --- | --- |
| N1 | 가능성이 아주 낮은 경합·보안 상황을 위해 복잡도를 더하기 전에, 실패 상황·가능성·비용을 설명하고 사용자 동의를 받는다. 확인된 근본 원인을 고치는 일은 여기에 해당하지 않는다. |
| N2 | 지금 쓰는 호출자나 소비자가 없는 매개변수·설정·플래그·호환 계층을 만들지 않는다. |
| N3 | 아래 코드 규칙은 새로 쓰는 코드와 작업상 바꿔야 하는 기존 코드에만 적용한다. 문서화되었거나 도구가 강제하는 저장소 관례가 다르면 관례를 따르되, 타입 검사를 약화시키는 관례는 따르지 않는다. |
| N4 | 두 곳 이상에서 호출하거나, 복잡한 경계를 감추거나, 이름이 개념을 드러낼 때만 함수로 뺀다. 같은 일을 하는 기존 함수가 있으면 재사용한다. 기존 E8("새 함수는 한 가지 목적")을 흡수했다. |
| N5 | 한 번만 쓰는 지역 변수는 인라인한다. 이름이 의미를 더하거나 실행 시점·횟수·수명이 바뀌면 예외다. |
| N14 | 조건 표현식(`a ? b : c`, `b if a else c`)은 한 단계까지만 쓴다. 분기가 더 많으면 `if`, 조기 반환, 조회 표를 쓴다. |
| N6 | 구현이 하나뿐인 인터페이스·기반 클래스나 호출자가 하나뿐인 팩토리를 만들지 않는다. 프레임워크, 공개 계약, 강제되는 의존 규칙, 테스트 같은 현재 필요가 있으면 예외다. |
| N7 | 값은 소유 객체를 통해 접근한다(`order.total`). 동작상 필요하거나 언어 관용구이거나 소유자가 의미를 더하지 않으면 예외다. |
| N8 | 스키마·생성자·내부 타입이 이미 보장한 값은 다시 검증하지 않는다. 요청·파일·환경 변수·역직렬화 데이터 같은 외부 데이터는 시스템에 들어오는 곳에서 형태를 검사한 뒤에 사용한다. |
| N9 | 그 자리에서 처리하거나 확립된 경계에서 변환할 수 없는 오류는 전파한다. 문맥을 붙일 때도 호출자가 검사하는 오류 타입이나 원인을 유지한다. 함수 계약에 없는 기본값으로 실패를 숨기지 않는다. |
| N10 | 이번 변경으로 쓰이지 않게 된 import·비공개 코드와 직접 넣은 디버그 출력은 지운다. 무관한 기존 죽은 코드는 그대로 둔다. |
| N11 | 타입 검사를 통과시키려고 `any` 같은 탈출 타입, 검사 없는 캐스트, 검사 억제를 쓰지 않는다. |
| N12 | 타입은 추론에 맡기고, 언어가 요구하거나 공개 API·타입 검사·명확성에 필요할 때만 적는다. |
| N13 | 드러나지 않는 제약과 예상 밖 동작, 그 이유만 주석으로 남긴다. 자명한 코드나 변경 이력은 주석으로 쓰지 않는다. |

### 생성 조건

- N11과 N12는 문서가 다루는 코드에 타입 검사기가 있을 때만 들어간다. monorepo 루트 문서는 패키지 하나에라도 타입 검사기가 있으면 넣는다. 패키지 문서가 루트 규칙을 상속하기 때문이다.
- 타입 검사 명령 규칙(E7)이 들어가는지는 기존 루트·패키지 검증 규칙대로 따로 정한다.
- N14를 포함한 나머지 규칙은 언어와 관계없이 모든 문서에 들어간다.

### 문서 길이

기본 규칙 목록 기준으로 Working Agreements 섹션은 타입 검사기가 있는 저장소에서 949자에서 4,108자로, 없는 저장소에서 866자에서 3,637자로 늘어난다. 가장 작은 저장소의 전체 한도는 10,000자이므로, 이 섹션이 한도의 41%를 차지한다.

전체 글자 수 한도와 섹션별 시작 할당(`loc_measurement.md`의 Working Agreements 15%)은 바꾸지 않았다. 그래서 작은 저장소에서는 다른 분석 섹션에 남는 공간이 줄어든다. 실험 저장소에서 실제로 생성된 AGENTS.md는 TypeScript가 3,772자에서 6,751자로, Python이 5,423자에서 8,193자로 늘었다.

### 기존 AGENTS.md를 갱신할 때

갱신 모드는 관리 섹션인 Working Agreements를 기본 규칙 목록으로 다시 만든다. 따라서 이미 이 스킬로 만든 AGENTS.md도 다음 갱신 때 새 목록으로 바뀐다. 관리 섹션 안에 직접 넣은 문구는 이전처럼 갱신 보고에 표시된 뒤 사라진다. 계속 유지할 규칙은 사용자 섹션으로 옮겨야 한다.

## 에이전트가 쓰는 코드는 이렇게 달라진다

아래 비교에서 "변경 전"은 이번 업데이트 전 스킬로 생성한 AGENTS.md, "변경 후"는 최종 규칙을 담은 AGENTS.md를 받은 에이전트의 결과다. 숫자는 3회 중 규칙에 맞게 행동한 횟수다.

| 행동 | 언어 | 변경 전 | 변경 후 |
| --- | --- | ---: | ---: |
| 분기가 셋인 배송비를 중첩 삼항식 없이 작성 | TypeScript | 2/3 | 3/3 |
| 분기가 셋인 배송비를 중첩 삼항식 없이 작성 | Python | 2/3 | 3/3 |
| 한 번만 쓰는 할인 계산을 함수로 빼지 않음 | TypeScript | 0/3 | 1/3 |
| 한 번만 쓰는 할인 계산을 함수로 빼지 않음 | Python | 0/3 | 3/3 |
| 외부 JSON을 들어올 때 형태 검사 | TypeScript | 0/3 | 3/3 |
| 외부 JSON을 들어올 때 형태 검사 | Python | 0/3 | 0/3 |
| 쓰지 않는 기본값 매개변수를 만들지 않음 | Python | 0/3 | 3/3 |
| 바꾸는 함수 안의 기존 줄을 그대로 둠 | TypeScript | 3/3 | 1/3 |
| 같은 로직이 다시 필요할 때 공통 함수로 재사용 | 두 언어 | 6/6 | 6/6 |

분기가 셋인 배송비와 공통 함수 행은 N8을 바꾸기 직전 규칙(v5)으로 생성한 문서에서 측정했다. 최종 규칙과 v5는 N8의 둘째 문장만 다르다. 이 두 과제는 N8을 바꾼 뒤 다시 실행하지 않았다. 나머지 행은 최종 규칙으로 실행한 결과다. 모든 실행이 동작 테스트와 타입 검사(`tsc --noEmit`, Python은 컴파일)를 통과했으므로, 규칙에 따른 차이는 코드 모양과 수정 범위에서만 나타났다.

### 분기가 셋인 계산: 중첩 삼항식 대신 `if`

배송비를 "4줄 이상 무료, 2~3줄 299, 1줄 499"로 바꾸게 했다. 변경 전 문서에서는 TypeScript와 Python에서 각 1회씩 중첩 삼항식이 나왔다. 변경 후에는 6회 모두 `if`로 나눴다. 규칙 없이 인라인만 권하는 안(N14 없는 v4)으로 따로 실험했을 때는 TypeScript 3회 모두 중첩 삼항식을 썼다. 그래서 N4·N5의 인라인 권고가 이 부작용을 만들고, N14가 이를 막는 것으로 판단했다.

변경 전:

```ts
const shippingCents = items.length > 3 ? 0 : items.length >= 2 ? 299 : 499;
```

변경 후:

```ts
function shippingCents(lineItemCount: number): number {
  if (lineItemCount > 3) {
    return 0;
  }
  return lineItemCount >= 2 ? 299 : 499;
}
```

N14는 한 단계 삼항식을 허용하므로 마지막 줄은 규칙에 맞다.

### 한 번만 쓰는 계산: 호출하는 자리에 둔다

변경 전 문서에서는 6회 모두 할인 계산 한 줄을 `discountCentsFor` 같은 함수로 뺐다. 변경 후에는 Python 3회 모두와 TypeScript 1회가 계산을 쓰는 함수 안에 그대로 뒀다.

변경 전:

```ts
export function discountCentsFor(subtotalCents: number, percent: number): number {
  return Math.floor((subtotalCents * percent) / 100);
}

const discountCents = discountCentsFor(subtotalCents(order), lookup.discountCode.percent);
```

변경 후(할인 코드를 사용 처리하는 함수 안에 계산을 둠):

```ts
  discountCode.used += 1;
  writeTextFile(DISCOUNTS_PATH, JSON.stringify(discountCodes, null, 2) + "\n");
  return Math.floor((subtotalCents * discountCode.percent) / 100);
```

TypeScript에서는 최종 규칙(1/3회)이 N8 수정 직전 규칙(2/3회)보다 낮았다. 외부 JSON 검사 코드를 새로 쓰면서 계산 함수도 함께 뺀 실행이 늘었다. 원인은 확인하지 못했다.

### 외부 JSON: 타입만 적지 않고 형태를 검사한다 (TypeScript)

변경 전 문서에서는 3회 모두 `JSON.parse` 결과를 검사 없이 캐스트했다. N8의 둘째 문장을 "보장되지 않은 것으로 취급한다"로 쓴 v5에서는 3회 중 2회가 타입만 적은 변수에 바로 담았다. 최종 문구("들어오는 곳에서 형태를 검사한 뒤에 사용한다")에서는 3회 모두 `unknown`으로 받은 뒤 검사했다.

변경 전:

```ts
const allDiscountCodes = JSON.parse(readTextFile(DISCOUNTS_PATH)) as DiscountCode[];
```

v5 문구:

```ts
const discounts: DiscountCode[] = JSON.parse(readTextFile(DISCOUNTS_PATH));
```

변경 후:

```ts
function isDiscountCode(value: unknown): value is DiscountCode {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const entry = value as Record<string, unknown>;
  return (
    typeof entry.code === "string" &&
    typeof entry.percent === "number" &&
    typeof entry.maxUses === "number" &&
    typeof entry.used === "number"
  );
}

function readDiscountCodes(): DiscountCode[] {
  const parsed: unknown = JSON.parse(readTextFile(DISCOUNTS_PATH));
  if (!Array.isArray(parsed) || !parsed.every(isDiscountCode)) {
    throw new DiscountError(`${DISCOUNTS_PATH} must be an array of discount codes`);
  }
  return parsed;
}
```

N8 문구는 두 안을 비교한 뒤 정했다. 반례를 덧붙인 정의형 안("타입 표기나 캐스트는 검사가 아니다")도 TypeScript 3/3회였다. 다만 추가된 코드가 더 길었다(62~73줄 대 50~58줄). 한 줄 계산을 함수로 빼지 않은 실행도 더 적었다(0/3회 대 1/3회). 그래서 행동형 안을 택했다.

### 쓰지 않는 기본값 매개변수 (Python)

변경 전 문서에서는 3회 모두 호출자가 하나뿐이고 항상 값을 넘기는데도 기본값을 붙였다. 변경 후에는 3회 모두 필수 매개변수로 선언했다.

변경 전:

```py
def total_cents(order: Order, discount_percent: int = 0) -> int:
```

변경 후:

```py
def total_cents(order: Order, discount_cents: int) -> int:
```

### 같은 로직이 다시 필요할 때: 공통 함수 (변화 없음)

할인 로직이 한 함수에 인라인된 저장소에 "사용 횟수를 늘리지 않는 미리보기 기능"을 추가하게 했다. 변경 전과 후 모두 12회 전부 공통 함수를 만들어 두 기능이 재사용했다. 할인 계산·코드 조회·JSON 읽기의 중복은 0건이었다. N4의 "두 곳 이상에서 부르면 뺀다"는 원래 성향과 같아서 차이가 나지 않았다.

다만 공통 함수를 나누는 방식은 대부분 boolean 매개변수였다. 변경 전 6회는 모두 아래처럼 썼고, 변경 후에는 TypeScript 2회만 가격 계산과 저장을 분리했다.

```ts
export function handleCheckout(body: unknown): CheckoutResult {
  return checkout(body, true);
}

export function previewCheckout(body: unknown): CheckoutResult {
  return checkout(body, false);
}
```

boolean 매개변수로 동작을 나누는 방식을 막는 규칙은 이번에 넣지 않았다.

## 주의할 점

- **바꾸는 함수 안의 기존 줄:** 할인을 적용하려고 `totalCents`를 고칠 때, 변경 후에는 TypeScript 3회 중 2회가 같은 함수의 기존 일회용 변수(`const subtotal = subtotalCents(order);`)까지 인라인했다. 변경 전에는 0회였다. N3의 "작업상 바꿔야 하는 기존 코드에도 적용한다"가 함수 단위로 읽히는 것으로 보인다. 줄 단위로 좁히는 문구는 아직 실험하지 않았다.
- **Python의 외부 데이터 검사:** Python에서는 어떤 N8 문구에서도 `json.loads` 결과를 검사하지 않았다(9회 중 0회). 잘못된 파일이면 `KeyError`나 `TypeError`로 실패한다. 타입 검사기가 없는 저장소에서는 N11·N12가 빠지는 것과 관련이 있어 보이지만, 원인은 확인하지 못했다.
- **문서 길이:** 작은 저장소에서는 Working Agreements가 늘어난 만큼 저장소 분석 섹션의 공간이 줄어든다.

## 검증 방법

모든 코딩은 Claude Sonnet 하위 에이전트가 맡았다. 각 실행은 깨끗한 픽스처 저장소를 하나씩 받았다. 에이전트는 사용자와 대화할 수 없어, 질문이 필요하면 보고서에 적도록 했다.

| 단계 | 비교한 규칙 | 과제 | 실행 |
| --- | --- | --- | ---: |
| 1차 | 기존 규칙, v4, v4에서 보강 규칙 제외, v4에서 N3 제외, 기존 규칙 + 원문 11개 | 레거시 쿠폰을 할인 코드로 교체 | 30 |
| 2차 | 기존 규칙, v4, v4 + N14 | 미리보기 추가와 세 단계 배송비 | 18 |
| 전후 비교 | 변경 전 스킬, 변경 후 스킬(v5)로 실제 생성한 AGENTS.md | 1차·2차 과제 | 생성 4, 코딩 24 |
| N8 문구 | 변경 후 문서의 N8 한 줄만 행동형·정의형으로 교체 | 1차 과제 | 12 |

각 과제는 TypeScript(`tsc` 있음)와 Python(타입 검사기 없음)에서 3회씩 실행했다. 측정은 이렇게 했다.

- **diff 분석:** 결과 diff를 정규식으로 분석하고, 핵심 함정(일회용 계산 함수 이름, 중첩 삼항식, `JSON.parse` 처리)은 직접 확인했다.
- **동작 테스트와 타입 검사:** 동작 테스트(1차 8개, 2차 9개)와 타입 검사를 직접 실행했다. 일부 에이전트는 스스로 코드를 실행하다 `config/discounts.json`을 바꿔 두었다. 그래서 동작 테스트는 항상 원본 데이터로 시작했다.
- **규칙 문구 검토:** 실험 전에 Codex와 Claude 검토자 2명이 4턴에 걸쳐 검토해 합의했다.

## 한계

- 과제는 같은 쇼핑몰 코드의 두 가지 기능이고, 언어는 TypeScript와 Python뿐이다. Kotlin, Go, Rust 저장소에서는 확인하지 않았다.
- 조건마다 3회만 실행했으므로 1회 차이는 우연일 수 있다.
- 모든 실행에 Claude Sonnet만 썼다. 다른 모델에서 같은 효과가 나는지는 알 수 없다.
- 하위 에이전트에는 실행 환경의 사용자 지침(CLAUDE.md)이 함께 로드됐을 수 있다. 프롬프트로 AGENTS.md만 따르라고 지시했지만, 완전히 배제됐는지는 확인하지 못했다.
- N1(경합), N6(추상화), N9(오류), N10(정리), N13(주석)은 이번 과제에서 모든 조건이 이미 규칙대로 행동했다. 효과가 있는지 판단할 근거가 없다.

## 관련 파일

- [실측 보고서](report.html): 모든 실행의 diff, 에이전트 보고서, 신호별 판정, 코드 비교를 브라우저에서 볼 수 있다. 데이터는 압축되어 있어, `DecompressionStream`을 지원하는 최신 브라우저가 필요하다.
- [`references/working_agreements.md`](../../references/working_agreements.md): 생성 규칙의 기준 파일이다.

## 부록: 생성되는 Working Agreements 전체 목록

타입 검사기가 있는 단일 저장소 기준이다. 실제 문서에서는 응답 언어와 타입 검사 명령이 저장소에 맞게 바뀐다. 이 목록의 기준은 [`working_agreements.md`](../../references/working_agreements.md)다.

```markdown
- Respond in the user's preferred language. If none is specified, infer it from the codebase. Keep technical terms in English and never translate code blocks.
- Ask the user before introducing tests, lint, or formatter setups. Add them only on explicit request.
- Before editing, review related usages, flows, patterns, and likely impact.
- Fix the underlying cause, not only the visible symptom. Inspect affected flows and apply the narrowest complete change that resolves the root issue.
- Check side effects across callers, shared abstractions, and behavior/API boundaries. Report relevant impact and compatibility risks.
- Ask the user when decisions are needed for scope, behavior, or tradeoffs.
- Do not silently expand scope for theoretical robustness. Before adding complexity for a speculative or vanishingly unlikely race or security edge case, explain the concrete failure mode, likelihood, and complexity cost, and get the user's agreement. Fixing a confirmed root cause across affected callers is not theoretical robustness.
- Do not add parameters, configuration options, feature flags, or compatibility layers that no current caller or consumer needs.
- Add external dependencies only when necessary. Explain why each added dependency is needed.
- After code changes, run `<discovered type-check command>` to verify type safety.
- Apply the rules on function extraction, inlining, conditional expressions, abstractions, options, unpacking, validation, errors, types, and comments to code you add and to existing code the task requires you to change. Do not rewrite other code to fit them unless the user asks. If a documented or tool-enforced repository convention differs from them, follow it unless it weakens type checking.
- Extract code into a new function only when more than one place calls it, it hides a genuinely complex boundary, or it is a real concept or composable step whose name makes the caller clearer. Otherwise, keep the logic inline. Reuse an existing function that does the same job. Give each new function one purpose and place it beside related code.
- Inline a local variable used only once, unless its name explains something the expression does not, or inlining would change when or how often the expression runs or how long its result lives.
- Use at most one level of conditional expression, such as `a ? b : c` or `b if a else c`. For more branches, use `if` statements, early returns, or a lookup table.
- Do not add an interface or base class with only one implementation, or a factory with only one caller, unless a framework, a public contract, a dependency rule the language or repository enforces, an existing or requested test, or another current need requires it.
- Access values through their owner, as in `order.total`, unless correct behavior needs unpacking, the language idiom expects it, or the owner adds no meaning.
- Do not revalidate values that a schema, constructor, or internal type already guarantees. When code reads outside data, such as requests, files, environment variables, or deserialized data, check its shape where it enters the system before other code relies on it.
- Let an error propagate unless the code at that point can handle it or an established boundary converts it. If you add context, keep the error type or cause that callers check. Do not hide a failure behind a default that the function's contract does not define, even if you log it.
- Remove imports and non-public code your change leaves unused, plus debug output you added. Leave unrelated dead code alone.
- Do not weaken type checking to make code pass. Avoid escape-hatch types, unchecked casts, and checker suppressions; fix the type instead. If one is unavoidable, keep it at the narrowest point and comment why.
- Rely on type inference. Write explicit types only where the language requires them, an exported API needs them, omitting them weakens type checking, or they clarify the code.
- Comment non-obvious constraints, surprising behavior, and their reasons. Do not comment obvious assignments or control flow, or describe change history in comments.
```
