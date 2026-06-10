# 업데이트 히스토리 및 리뷰 팩트 (Update History & Review Facts)

이 디렉토리는 `agents-md-generator` 스킬의 개선 사항과 상세 리뷰 결과에 대한 팩트 정보를 관리합니다.

## 관리 구조 (Management Structure)

모든 주요 업데이트나 개선 사항은 아래 명명 규칙을 준수하여 하위 디렉토리를 생성하고 기록합니다:
`YYYY-MM-DD-[improvement-summary]`

각 폴더에는 다음과 같은 팩트 정보가 포함되어야 합니다:
- `review.md`: 업데이트의 내용, 개선된 점, 그리고 왜 그렇게 구현했는지에 대한 상세 분석 결과. (벤치마크 기록의 경우 `benchmark.md`로 대체 가능)
- `*.patch` (선택): 실제 코드 변경 사항을 증명하는 Git 패치 파일. 출력 diff가 증거의 일부일 때 포함합니다.

## 업데이트 히스토리 (History)

- [2026-02-25] 업데이트 관리 구조 초기 구축.
- [2026-02-25] [JSON 템플릿 포맷팅 리뷰](./2026-02-25-json-template-formatting-review/review.md): JSON 포맷팅 시 템플릿 문법 지원을 위한 3가지 구현 방식에 대한 기술적 팩트 비교 리뷰.
- [2026-03-11] [JSON 쿼리 설명 리뷰](./2026-03-11-json-query-explanation-review/review.md): AGENTS.md 유무에 따른 코드 설명 품질 비교 리뷰.
- [2026-03-21] [Claude Skill 2.0 적용 벤치마크](./2026-03-21-claude-skill-2_0-apply/benchmark.md): Section 3/4 분석 깊이 개선 전후 통과율 비교(36.4% → 77.3%).
- [2026-05-07] [JSON 쿼리 설명 리뷰 2차](./2026-05-07-json-query-explanation-review/review.md): AGENTS.md 없음/구버전/신버전 3안 비교 리뷰.
- [2026-06-10] [적대적 리뷰 기반 강화](./2026-06-10-adversarial-review-hardening/review.md): 서브에이전트 적대적 리뷰로 검증된 파괴 경로(외부 작성 문서 수정, 커스텀 섹션 소실, 모노레포 오탐, 예산 모순 등)에 대한 가드 및 스크립트 강화.
