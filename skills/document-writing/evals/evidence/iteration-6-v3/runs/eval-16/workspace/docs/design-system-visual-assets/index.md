# Steam 게임 상점 시각 자산 디자인 시스템

## 목적과 범위

이 문서는 Steam 게임 상점과 Steam 라이브러리에서 사용할 시각 자산의 공통 원칙과 Steamworks 명칭·규격을 한곳에서 조회하는 결정 원천이다. 실제 이미지·영상은 이 작업에서 만들지 않는다. 대상 독자는 게임 아트, 마케팅, 캡처, 영상, QA 담당자다.

## 승인된 방향과 검증

승인된 방향은 “빠른 전투의 긴장감을 높은 대비와 대각선 흐름으로 표현하되 실제 플레이 장면의 판독성을 우선한다”이다. 이 방향은 작은 capsule과 큰 hero, 정적 screenshot과 trailer에서 검증됐다. 작은 표면에서는 로고와 핵심 실루엣의 판독성을, 큰 표면과 동영상에서는 전투의 흐름을 확장한다.

## 결정 권한과 파일 지도

- 승인된 방향과 공통 시각 원칙: [visual-language.md](visual-language.md)
- 자산 종류 간 공통 개념과 매핑: [asset-system.md](asset-system.md)
- 실제 플레이 장면, 순서, trailer 관계: [screenshots-and-previews.md](screenshots-and-previews.md)
- 구성, 안전 영역, 자산 내부 문구: [composition-and-copy.md](composition-and-copy.md)
- 언어·지역 변형: [localization.md](localization.md)
- 대비·가독성·모션 대체: [accessibility.md](accessibility.md)
- 납품·버전 관리·검증 기록: [delivery-and-versioning.md](delivery-and-versioning.md)
- Steam 공식 자산 명칭과 mutable 요구사항: [stores/steam.md](stores/steam.md)

충돌 시 사용자가 승인한 방향이 공통 시각 규칙을 정하고, 최신 Steamworks 공식 문서가 Steam 고유의 명칭·규격·노출 조건을 정한다. 팀 권장사항은 Steam 필수 요구사항과 별도로 표시한다.

## 자산 맵

| 개념 | Steam 명칭 | 정본 |
|---|---|---|
| 상점 캡슐 | Header Capsule, Small Capsule, Main Capsule, Vertical Capsule | [stores/steam.md](stores/steam.md) |
| 실제 플레이 정지 장면 | Screenshots | [screenshots-and-previews.md](screenshots-and-previews.md) |
| 영상 미리보기 | Trailers | [screenshots-and-previews.md](screenshots-and-previews.md) |
| trailer 대표 이미지 | Poster image, Thumbnail image | [stores/steam.md](stores/steam.md) |
| 라이브러리 큰 배경 | Library Hero | [stores/steam.md](stores/steam.md) |

## 제외 사항

Steam의 listing title, description, tags, categories, pricing, legal submission fields는 이 시스템의 범위가 아니다. 일반 앱 마켓의 `feature graphic` 명칭은 Steam 자산명으로 사용하지 않는다.
