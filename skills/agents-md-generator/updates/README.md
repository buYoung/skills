# 업데이트 히스토리 및 리뷰 팩트 (Update History & Review Facts)

이 디렉토리는 `agents-md-generator` 스킬의 개선 사항과 상세 리뷰 결과에 대한 팩트 정보를 관리합니다.

## 관리 구조 (Management Structure)

모든 주요 업데이트나 개선 사항은 아래 명명 규칙을 준수하여 하위 디렉토리를 생성하고 기록합니다:
`YYYY-MM-DD-[improvement-summary]`

각 폴더에는 다음과 같은 팩트 정보가 포함되어야 합니다:
- `review.md`: 업데이트의 내용, 개선된 점, 그리고 왜 그렇게 구현했는지에 대한 상세 분석 결과.
- `*.patch`: 실제 코드 변경 사항을 증명하는 Git 패치 파일.

## 업데이트 히스토리 (History)

- [2026-02-25] 업데이트 관리 구조 초기 구축.
- [2026-02-25] [JSON 템플릿 포맷팅 리뷰](./2026-02-25-json-template-formatting-review/review.md): JSON 포맷팅 시 템플릿 문법 지원을 위한 3가지 구현 방식에 대한 기술적 팩트 비교 리뷰.
