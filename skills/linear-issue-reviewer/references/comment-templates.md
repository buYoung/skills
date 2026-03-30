# Review Comment Templates

## Approved

```
Linear:save_comment
  issueId: "<sub-issue-id>"
  body: |
    ## 리뷰 결과: ✅ Approved

    ### Done Criteria 검증
    - [x] Criterion 1 — 확인됨: [근거]
    - [x] Criterion 2 — 확인됨: [근거]

    ### Target Location 검증
    - 지정 파일과 변경 파일 일치

    ### 코드 품질
    - [관찰 사항, 개선 제안 등 — 승인을 막지는 않지만 참고할 점]

    → 상태 유지: Done
```

## Changes Requested

```
Linear:save_comment
  issueId: "<sub-issue-id>"
  body: |
    ## 리뷰 결과: 🔄 Changes Requested

    ### Done Criteria 검증
    - [x] 충족 항목 — 확인됨: [근거]
    - [ ] 미충족 항목 → [미충족 이유 상세 설명]

    ### 수정 필요 사항
    1. `파일경로:라인번호` — [수정 내용]
    2. `파일경로:라인번호` — [수정 내용]

    ### 스코프 이슈 (해당 시)
    - [스코프 크립이 발견된 경우 기술]

    → 상태 변경: Done → In Progress
```

Then transition the status:

```
Linear:save_issue
  id: "<sub-issue-id>"
  state: "started"
```

## Clarification Needed

```
Linear:save_comment
  issueId: "<sub-issue-id>"
  body: |
    ## 리뷰 결과: ❓ Clarification Needed

    ### Done Criteria 검증
    - [x] 확인 가능한 항목 — [근거]
    - [?] 확인 필요 항목 — [의문점]

    ### 확인 사항
    1. [구현 선택에 대한 질문]
    2. [의도 확인 필요 사항]

    → 상태 유지: Done (확인 후 판단)
```

## Final Review — All Criteria Met

```
Linear:save_comment
  issueId: "<main-issue-id>"
  body: |
    ## 📋 최종 리뷰 완료

    ### 서브이슈 리뷰 결과
    - ✅ PRI-43 — Approved
    - ✅ PRI-44 — Approved
    - ✅ PRI-45 — Approved

    ### Acceptance Criteria 검증
    - [x] Criterion 1 — PRI-43, PRI-44에서 충족
    - [x] Criterion 2 — PRI-45에서 충족

    ### 종합 의견
    [전체 작업에 대한 종합 평가]

    → 모든 Acceptance Criteria 충족. 작업 완료 승인.
```

## Final Review — Gaps Found

```
Linear:save_comment
  issueId: "<main-issue-id>"
  body: |
    ## 📋 최종 리뷰 — 추가 작업 필요

    ### 서브이슈 리뷰 결과
    - ✅ PRI-43 — Approved
    - ✅ PRI-44 — Approved

    ### Acceptance Criteria 검증
    - [x] Criterion 1 — PRI-43에서 충족
    - [ ] Criterion 2 → 커버하는 서브이슈 없음

    ### 필요 조치
    1. Criterion 2를 충족하기 위한 추가 서브이슈 필요
       - 제안: [추가 서브이슈 제목 및 내용 개요]

    → Acceptance Criteria 일부 미충족. 추가 작업 필요.
```
