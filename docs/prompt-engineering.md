# 프롬프트 엔지니어링 마스터 레퍼런스

> 범용 프롬프트 작성 시 참고하는 통합 가이드. 공식 문서(Anthropic / OpenAI / Microsoft / Google)와 주요 학술 논문을 기반으로 하되, 과장된 수치성 주장은 1차 출처 재확인 후 보정했다.

---

## 0. 한 줄 요약

좋은 프롬프트는 **"마법 주문"이 아니라 "작업 명세서(specification)"**다. 모델이 추측해야 할 영역을 줄이는 구조화가 본질이다.

**핵심 공식:**

```
역할 + 목표 + 맥락 + 구분된 입력 + 단계별 작업 + 제약 조건 + 출력 형식 + 검증 기준
```

가장 중요한 마지막 한 문장: **프롬프트는 "좋아 보이는지"가 아니라 "테스트셋에서 더 잘 작동하는지"로 판단한다.**

---

## 1. 7가지 보편 원칙 (모든 공식 문서 공통)

| # | 원칙 | 핵심 |
|---|---|---|
| 1 | **명확성 + 구체성** | 모호한 지시는 출력 변동성과 환각을 증가시킨다 |
| 2 | **구조화** | `###`, `"""`, XML 태그로 지시 / 맥락 / 입력 / 예제를 명시적으로 분리 |
| 3 | **긍정형 지시** | "하지 마라" 대신 "이렇게 하라" |
| 4 | **예시 기반(Few-shot)** | Zero-shot으로 시작, 부족하면 2~5개 예시 추가 |
| 5 | **역할 부여** | 도메인 / 관점 / 톤 지정 (단, ⚠️ 5절 참고) |
| 6 | **출력 형식 고정** | JSON / 표 / bullet 등 구체적으로 명시 |
| 7 | **불확실성 처리 규칙** | "모르면 모른다고 말하라"를 명시 |

---

## 2. 권장 표준 구조

### 2.1 범용 템플릿 (실무 베이스)

```text
# Role
너는 {역할/전문성}이다.

# Objective
목표는 {최종 산출물}을 만드는 것이다.

# Context
배경:
- {도메인 정보}
- {사용자 상황}
- {중요 제약}

# Input
아래 입력만 근거로 사용한다.
"""
{입력 데이터}
"""

# Task
1. {해야 할 일 1}
2. {해야 할 일 2}
3. {해야 할 일 3}

# Rules
- 입력에 없는 사실은 추측하지 않는다.
- 불확실하면 "정보 부족"이라고 표시한다.
- 판단에는 근거를 붙인다.
- {하지 말 것} 대신 {대체 행동}을 수행한다.
- 길이 / 톤 / 언어 / 독자: {지정}

# Output Format
## 결론
## 근거
## 상세 분석
## 리스크 / 한계
## 다음 액션
```

### 2.2 Claude 계열 (XML 태그)

```xml
<role>너는 B2B SaaS 제품 전략 컨설턴트다.</role>

<context>
우리 제품은 개발자용 로그 분석 도구다.
주요 고객은 50~500인 규모의 SaaS 기업이다.
</context>

<task>아래 고객 피드백을 분석해 기능 우선순위를 정하라.</task>

<input>{feedback}</input>

<output_format>
1. 핵심 인사이트
2. 기능 요청
3. 우선순위
4. 근거
</output_format>
```

**Anthropic 공식 권장사항** (Claude API Docs 기준):
- Claude는 XML 태그를 프롬프트 구조화 메커니즘으로 인식하도록 훈련됨 (단, "특별한 마법 태그"는 없음 — 일관된 태그 이름이면 무엇이든 가능)
- 일관되고 서술적인 태그 이름 사용, 자연스러운 계층은 태그 중첩으로 표현
- 다중 문서 입력 시 `<document>` 내부에 `<document_content>`, `<source>` 등으로 메타데이터 분리 권장
- 긴 문서를 다룰 때는 문서 본문을 위쪽에 두고 질문을 아래에 두는 패턴 고려

### 2.3 OpenAI 계열 (구분자 + 섹션)

```text
다음 문서를 5개 bullet로 요약하라.

문서:
"""
{document}
"""
```

OpenAI 공식 가이드: 지시를 먼저 쓰고, `###` 또는 `"""`로 지시와 데이터를 분리. 길이는 "fairly short" 같은 모호한 표현 대신 "3~5문장"처럼 구체화.

---

## 3. 구성 요소별 최적화

### 3.1 Role / 역할

⚠️ **중요 단서**: Zheng et al. (EMNLP 2024)이 162개 페르소나·2,410개 사실 질문으로 실험한 결과, 페르소나 추가는 사실성 작업의 정확도를 **일관되게 향상시키지 않는다**. 효과는 거의 랜덤에 가깝다.

그러나 역할은 다음에서는 여전히 유용하다:
- **톤 / 스타일 / 어휘 통제** (어조, 격식 수준)
- **판단 기준 명시** (역할에 따라 어떤 기준을 적용할지)
- **출력 범위 한정** (전문 영역 제한)

**나쁜 예:**
```
너는 세계 최고의 전문가야. 완벽하게 해줘.
```

**좋은 예:**
```
너는 B2B SaaS 제품 전략 컨설턴트다.
목표는 아래 고객 피드백에서 기능 우선순위를 도출하는 것이다.
판단 기준은 매출 영향, 구현 난이도, 반복 빈도, 고객 등급이다.
```

역할만으로는 부족하다. **역할 + 목표 + 판단 기준**이 세트가 되어야 효과가 있다.

### 3.2 Context / 맥락

"왜 이 작업을 하는지"와 "무엇을 기준으로 판단해야 하는지"를 명시한다.

```text
배경:
- 이 문서는 신규 입사 개발자를 위한 온보딩 문서다.
- 독자는 React와 Node.js는 알지만 우리 내부 아키텍처는 모른다.
- 목표는 30분 안에 전체 흐름을 이해시키는 것이다.
```

### 3.3 Input 분리

입력과 지시를 섞으면 모델이 "어디까지가 데이터고 어디까지가 명령인지" 혼동한다.

```text
아래 텍스트를 요약하라.

텍스트:
"""
{document}
"""
```

Claude에서는 XML이 더 깔끔하다:

```xml
<instructions>아래 문서를 근거로 리스크를 요약하라.</instructions>
<document>{document}</document>
```

### 3.4 Task — 동사 중심으로

| 애매한 표현 | 검증 가능한 표현 |
|---|---|
| 잘 정리해줘 | 핵심 주장 5개를 bullet로 요약해줘 |
| 분석해줘 | 원인 / 영향 / 리스크 / 대응책으로 나눠 분석해줘 |
| 예쁘게 써줘 | 20대 사용자 대상, 친근한 톤, 500자 이내로 작성해줘 |
| 알아서 해줘 | 누락된 정보는 가정하지 말고 질문 목록으로 분리해줘 |
| 짧게 | 200~300자, 핵심 3가지 |
| 자세히 | 800자 이내, 근거 3개와 예시 1개 포함 |
| 적절히 | 기준 A, B, C를 적용해 우선순위를 매겨줘 |

### 3.5 Rules / 제약 조건

성능에 큰 영향을 준다. 좋은 규칙 예시:

```text
규칙:
- 제공된 문서에 없는 내용은 추측하지 않는다.
- 근거가 없으면 "문서에서 확인 불가"라고 표시한다.
- 상충되는 정보가 있으면 둘 다 제시하고 충돌 지점을 설명한다.
- 최종 답변 전에 요구사항 충족 여부를 점검한다.
```

Microsoft 공식 가이드: 모델이 답을 지어내지 않도록 "답이 없으면 not found라고 답하라" 같은 **escape path**를 주는 것이 환각 감소에 효과적.

### 3.6 Output Format / 출력 형식

출력 형식을 지정하지 않으면 결과가 흔들린다.

**비추천:** "이거 정리해줘."

**추천:**
```text
다음 표로 출력하라.

| 항목 | 요약 | 근거 | 리스크 | 권장 액션 |
|---|---|---|---|---|
```

정형 데이터가 필요하면 프롬프트 문구로 "JSON으로 줘" 하는 것보다 OpenAI **Structured Outputs** 또는 function calling `strict: true`가 더 안정적. JSON Schema로 enum, required key 보장 가능.

---

## 4. 작업 유형별 패턴

### 4.1 리서치 / 사실 검증

```text
너는 사실 검증 리서처다.

목표: {주제}에 대해 근거 기반으로 정리한다.

규칙:
- 최신 정보가 필요한 항목은 최신 출처를 우선한다.
- 출처가 없는 내용은 추측하지 않는다.
- 서로 다른 출처가 충돌하면 충돌 지점을 명시한다.
- 결론, 근거, 불확실성을 분리한다.

출력:
## 결론
## 확인된 사실
## 불확실하거나 추가 검증 필요한 내용
## 참고 출처
```

**Chain-of-Verification (CoVe)** 4단계 적용 가능:
1. 초안 작성
2. 검증 질문 계획
3. 독립 답변
4. 최종 검증 답변

검증된 효과 (Dhuliawala et al. 2023, Llama 65B 기준): Wikidata 리스트 정밀도 0.17→0.36, MultiSpanQA F1 +23%, FACTSCORE 63.7→71.4. 단, 일부 작업에서는 정확한 답을 잘못 수정할 수 있음.

### 4.2 복잡 추론 / 수학

- **CoT**: "단계별로 풀어라" (Wei et al. 2022, NeurIPS)
- **Zero-shot CoT**: "Let's think step by step" 한 줄 (Kojima et al. 2022)
- 단, 추론 특화 모델(o-series, Claude extended thinking)에서는 과도한 명시 지시가 오히려 역효과 — 고수준 목표만 제시

### 4.3 매우 어려운 문제 분해

**Least-to-Most Prompting** (Zhou et al. 2022): 복잡한 문제를 하위 문제로 분해 → 이전 답을 활용해 순차 해결.
- 검증 효과: GPT-3 code-davinci-002 + SCAN 벤치마크에서 99.7% vs CoT 16.2% (14개 예시만으로)
- 단, SCAN은 합성 언어 기반 인공 태스크라 실제 자연어 태스크로의 전이는 제한적

### 4.4 정형 데이터 추출 / 분류

```text
작업: 고객 문의를 다음 카테고리 중 하나로 분류한다.

카테고리:
- billing
- technical_issue
- sales
- cancellation
- other

예시:
<example>
<input>결제가 두 번 됐어요.</input>
<output>{"category":"billing","confidence":0.94}</output>
</example>

<example>
<input>로그인하면 흰 화면만 나와요.</input>
<output>{"category":"technical_issue","confidence":0.91}</output>
</example>

입력: {user_message}

출력 JSON schema:
{
  "category": "...",
  "confidence": 0.0,
  "reason": "..."
}
```

프로덕션 환경에서는 프롬프트로 JSON 요구하기보다 **Structured Outputs** 또는 `strict: true` function calling 사용 권장.

### 4.5 코딩 / Agentic 작업

**OpenAI GPT-4.1 Prompting Guide 공식 권장 3종**:

1. **Persistence** (지속성): "You are an agent — please keep going until the user's query is completely resolved, before ending your turn and yielding back to the user. Only terminate your turn when you are sure that the problem is solved."
2. **Tool-calling** (도구 사용): "If you are not sure about file content or codebase structure pertaining to the user's request, use your tools to read files and gather the relevant information: do NOT guess or make up an answer."
3. **Planning** (계획): "You MUST plan extensively before each function call, and reflect extensively on the outcomes of the previous function calls. DO NOT do this entire process by making function calls only."

**OpenAI 자체 측정 효과** (SWE-bench Verified):
- 세 가지 합산: 약 +20% 향상
- Planning만 추가: +4%

### 4.6 문서 요약 (긴 컨텍스트)

```text
너는 기술 문서 요약가다.

목표: 아래 문서를 신규 개발자가 10분 안에 이해할 수 있게 요약한다.

규칙:
- 핵심 개념, 시스템 흐름, 주의사항을 분리한다.
- 원문에 없는 내용은 추가하지 않는다.
- 각 섹션은 5개 bullet 이내.

문서:
"""
{document}
"""

출력:
## 한 줄 요약
## 핵심 개념
## 시스템 흐름
## 주의사항
## 더 읽어야 할 부분
```

Anthropic 권장: 긴 문서는 프롬프트 **상단**, 질문은 **하단** 배치가 다중 문서 입력에서 응답 품질에 유리할 수 있음.

---

## 5. 학술 검증된 5대 기법 (현실적 단서 포함)

| 기법 | 핵심 | 검증된 효과 | 한계 / 단서 |
|---|---|---|---|
| Chain-of-Thought (Wei 2022) | 중간 추론 단계 생성 | 산술/상식/상징 추론 성능 향상 | 추론 모델에서는 역효과 가능 |
| Zero-shot CoT (Kojima 2022) | "Let's think step by step" | 예시 없이 추론 성능 향상 | 작업에 따라 효과 편차 |
| Self-Consistency | 여러 추론 경로 → 다수결 | 추론 정확도 향상 | Prompt Report에서는 효과 제한적이라 보고 |
| Least-to-Most (Zhou 2022) | 분해 → 순차 해결 | SCAN 99.7% (CoT는 16.2%) | 합성 태스크 기반, 자연어 일반화 제한 |
| Chain-of-Verification (Dhuliawala 2023) | 자기 검증 4단계 | F1 +23% 등 | 모델 / 태스크 의존 |

---

## 6. 모델별 최신 권장사항 (2026년 5월 기준)

### Claude (Anthropic, Opus 4.7 등)
- **XML 태그 권장** (`<instructions>`, `<context>`, `<input>` 등 — 다만 "특별한 마법 태그"는 없으며, 일관된 구조가 핵심)
- 최신 Claude는 지시를 더 문자 그대로 해석 — 범용 적용을 원하면 범위를 명시
- 공격적 표현("CRITICAL: You MUST use this tool")은 과잉 트리거 유발 → "Use this tool when..." 같은 일반 언어로 조정
- 출력 형식 제어 시 "마크다운 금지" 대신 "부드럽게 흐르는 산문 문단으로 구성"처럼 긍정형으로
- Extended thinking 모드: 과도한 step-by-step 지시 대신 "think deeply"로 자율성 부여

### OpenAI GPT 계열
- Markdown + XML 혼용 가능 (GPT-4.1 테스트에서 문서 검색은 XML이 우수)
- Developer role 활용
- Structured Outputs로 스키마 강제
- 명시적·상세 지시 권장 (Claude 대비)
- 긴 컨텍스트: 중요 지시는 프롬프트 **시작 + 끝** 양쪽에 배치

### 추론 특화 모델 (o-series 등)
- 고수준 목표만 제시
- 과도한 CoT 명시 지시 자제 (내부적으로 자동 수행)

---

## 7. 안티패턴 (피해야 할 표현)

```text
❌ "너는 세계 최고의 전문가야. 완벽하게 해줘."
   → 역할만 있고 목표/입력/출력 기준 없음

❌ "고급스럽고 세련되고 전문적으로, 너무 길지 않게, 잘 써줘."
   → 모호한 품질어 남발

❌ "이거 분석해줘."
   → 출력 형식 미지정

❌ "개인정보 묻지 마. 반복하지 마. 쓸데없는 말 하지 마."
   → 부정문만으로는 대체 행동을 학습시킬 수 없음
```

**회피 단어**: `가능하면`, `적절히`, `자유롭게`, `너무 길지 않게`, `잘 써줘`, `세련되게` — 사람마다 기준이 다르므로 모델도 추측에 의존.

**올바른 대안:**
```text
✅ 대상 독자: B2B 의사결정권자
✅ 톤: 차분하고 전문적
✅ 문장 길이: 평균 20자 내외
✅ 핵심 이점 3개를 먼저 제시, 그 다음 근거
✅ 개인정보가 필요한 상황에서는 고객센터 도움말 링크로 안내
```

---

## 8. 12대 최종 원칙

1. **지시와 입력을 분리하라.** `"""`, `###`, XML 태그 사용.
2. **목표를 산출물 기준으로 써라.** "분석해줘" 대신 "리스크 5개와 대응책을 표로 작성하라".
3. **출력 형식을 고정하라.** 표, JSON, bullet, 섹션 제목, 글자 수 명시.
4. **모호한 형용사를 숫자로 바꿔라.** "짧게" → "3~5문장".
5. **부정 지시보다 대체 행동을 써라.** "하지 마" 대신 "이 상황에서는 이렇게 하라".
6. **예시는 실제 케이스와 가까워야 한다.** 관련성 낮은 few-shot은 오히려 잘못된 패턴 학습.
7. **복잡한 문제는 분해하라.** Least-to-Most 또는 prompt chaining.
8. **근거 기반 작업에는 '모르면 모른다' 규칙을 넣어라.** 환각 방지.
9. **긴 문서 작업은 배치 순서를 신경 써라.** 긴 데이터는 상단, 질문은 하단.
10. **추론 작업에는 단계적 사고 또는 검증 루프를 붙여라.** CoT / CoVe.
11. **정형 출력은 schema를 써라.** 프롬프트로 "JSON으로 줘"보다 Structured Outputs / function calling이 안정적.
12. **프롬프트 변경은 반드시 eval로 검증하라.** 가장 중요한 원칙.

---

## 9. 자체 점검 10대 체크리스트

프롬프트 작성 후 다음을 확인:

1. 목표가 한 문장으로 명확한가?
2. 입력 데이터와 지시문이 구분되어 있는가?
3. 출력 형식이 고정되어 있는가?
4. 길이, 톤, 대상 독자가 지정되어 있는가?
5. 예시가 필요한 작업에 Few-shot 예시(3~5개)가 있는가?
6. 모르면 어떻게 행동할지 적혀 있는가?
7. "하지 말라"보다 "해야 할 행동"이 적혀 있는가?
8. 복잡한 문제는 분해 절차가 있는가?
9. 사실 기반 작업은 출처/근거 규칙이 있는가?
10. **실제 테스트셋으로 eval을 돌려봤는가?** ⭐ 가장 중요

Anthropic 공식 가이드도 동일: **성공 기준을 먼저 정의 → 평가 설계 → 프롬프트 작성 → 측정 → 개선**이라는 사이클이 프롬프트 엔지니어링의 중심이다.

---

## 10. 폐기 / 보류 / 보정한 주장들 (투명성 섹션)

원본 자료에 있던 주장 중 1차 출처 재확인 후 **수정/보류/폐기**한 내용:

| 원본 주장 | 처리 | 근거 |
|---|---|---|
| "원칙별 +100%, +85% 향상" (Principled Instructions 원칙별 수치) | ⚠️ **신뢰도 격하** | ATLAS 벤치마크 baseline이 약하다는 비판이 PromptHub 등에서 제기됨. 전체 평균(+57.7% 품질, +67.3% 정확도)은 1차 출처에 있으나, 원칙별 수치를 일반화하면 안 됨 |
| "Take a deep breath = 보편 효과 문구" | ❌ **폐기** | OPRO 논문은 PaLM 2 + GSM8K 한정. AI가 그 벤치마크에 맞춰 자동 생성한 문구로, 다른 모델/태스크에서는 효과 다름 |
| "역할 부여로 정확도 +60%/86.7%" | ⚠️ **수정** | Zheng et al. (EMNLP 2024): 페르소나는 사실성 작업 정확도를 일관되게 향상시키지 않음. 역할은 톤/스타일/판단 기준 통제 용도로 한정 |
| "You will be penalized 핵심 문구" | ⚠️ **보류** | Principled Instructions에는 있으나, 최신 모델/UX에서는 공격적 표현이 부작용 유발 가능. 권장 안 함 |
| "Claude는 XML에 특별 fine-tuning" | ⚠️ **수정** | Anthropic 공식: Claude는 XML 구조를 인식하도록 훈련됐지만 "특별한 마법 태그"는 없음. 일관된 태그 이름이면 무엇이든 가능 |
| "정중한 표현은 항상 불필요" | ⚠️ **수정** | 성능 측면에서는 직접성이 유리할 수 있으나, 고객-facing UX에서는 톤이 중요. 컨텍스트 의존 |
| "CoVe는 모든 환각을 줄임" | ⚠️ **수정** | 사실 정확성에는 효과 검증되지만, 일부 작업에서 정답을 잘못 수정할 수 있음. 또한 발산적 창의성과 트레이드오프 가능 |

**핵심 교훈**: 특정 벤치마크에서 측정된 수치(특히 단일 모델·단일 태스크 결과)를 보편 규칙으로 사용하면 안 된다. 자기 태스크에서 eval로 직접 확인하는 것이 유일한 검증 방법이다.

---

## 11. 즉시 사용 가능한 범용 템플릿

```text
너는 {역할}이다.

[목표]
{최종적으로 얻고 싶은 결과를 1문장으로}

[맥락]
{왜 이 작업이 중요한지, 결과물이 어디에 쓰일지}

[입력]
"""
{사용자 입력 / 문서 / 코드 / 데이터}
"""

[작업]
1. {해야 할 일 1}
2. {해야 할 일 2}
3. {해야 할 일 3}

[규칙]
- 입력에 없는 사실은 추측하지 않는다.
- 불확실하면 "정보 부족"이라고 표시한다.
- 중요한 판단에는 근거를 붙인다.
- {금지사항} 대신 {대체 행동}을 수행한다.
- 길이/톤/언어: {지정}

[출력 형식]
## 결론
{1-3문장}

## 근거
- {근거 1}
- {근거 2}

## 상세 분석
{필요 시}

## 다음 액션
- {액션 1}
- {액션 2}
```

---

## 12. 참고 자료 (검증 완료)

**공식 문서**
- Anthropic Claude Prompting Best Practices: https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/claude-prompting-best-practices
- OpenAI Prompt Engineering Guide: https://developers.openai.com/api/docs/guides/prompt-engineering
- OpenAI GPT-4.1 Prompting Guide: https://cookbook.openai.com/examples/gpt4-1_prompting_guide
- OpenAI Structured Outputs: https://developers.openai.com/api/docs/guides/structured-outputs
- Microsoft Azure OpenAI Prompt Engineering: https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/prompt-engineering
- Google Gemini Prompting Strategies: https://ai.google.dev/gemini-api/docs/prompting-strategies

**핵심 논문**
- Chain-of-Thought (Wei et al. 2022): https://arxiv.org/abs/2201.11903
- Zero-shot CoT (Kojima et al. 2022): https://arxiv.org/abs/2205.11916
- Least-to-Most (Zhou et al. 2022): https://arxiv.org/abs/2205.10625
- Chain-of-Verification (Dhuliawala et al. 2023): https://arxiv.org/abs/2309.11495
- Principled Instructions (Bsharat et al. 2023): https://arxiv.org/abs/2312.16171
- The Prompt Report (Schulhoff et al. 2024): https://arxiv.org/abs/2406.06608
- Prompt Pattern Catalog (White et al. 2023): https://arxiv.org/abs/2302.11382
- **When "A Helpful Assistant" Is Not Really Helpful** (Zheng et al. 2024, EMNLP Findings): https://arxiv.org/abs/2311.10054

**종합 정리 사이트**
- Prompting Guide: https://www.promptingguide.ai/
- Learn Prompting: https://learnprompting.org/

---

## 13. 최종 한 줄 정리

프롬프트 엔지니어링의 핵심은 **특정 마법 문구를 외우는 것**이 아니라, 모델에게 주는 작업을 **명세서처럼 구조화**하는 것이다.

가장 안전한 공식:

```
역할 + 목표 + 맥락 + 구분된 입력 + 단계별 작업 + 제약 조건 + 출력 형식 + 검증 기준
```

그리고 실무의 진짜 결론:

> **프롬프트는 "좋아 보이는지"가 아니라 "테스트셋에서 더 잘 작동하는지"로 판단한다.**
