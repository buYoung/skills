# Epic Games Store

## 범위와 적용성

대상은 Epic Games Store의 게임 상점 페이지 시각 자산이다. 일반 Product Details Page(PDP) 제출과 Epic이 별도로 운영하는 Featured/Discover Carousel 홍보 배치는 구분한다. 제품 패키지·기기·전체 로케일별 최신 적용성은 publisher portal에서 확인해야 한다.

## 조사 상태와 공식 출처

2026-08-29에 다음 Epic 공식 자료를 확인했다.

- [Epic Games Store distribution 안내](https://store.epicgames.com/distribution): Developer Portal이 게임 페이지·가격·오퍼·빌드·업데이트를 설정하는 도구임을 확인했고, Store Requirements 문서로 연결되는 사실을 확인했다.
- [Epic Games Store Requirements](https://dev.epicgames.com/docs/epic-games-store/requirements-guidelines/distribution-requirements/requirements-overview): 공식 요구사항 URL을 열었으나 현재 실행 환경에서는 본문을 읽을 수 없었다.
- [Epic Marcom Guidelines — Discover Carousel](https://static-assets-prod.epicgames.com/eos-docs/files/marketing-overview-files/EGS_Storefront_Merchandising_Carousel-Guidelines.pdf): Featured/Discover Carousel의 데스크톱·모바일 아트워크와 영상에 관한 시각 규격을 확인했다.

공식 publisher portal의 asset specification 페이지는 접근할 수 없었다. 따라서 아래 수치는 일반 PDP 요구사항이 아니라 위 Marcom PDF에 명시된 Carousel 홍보 배치의 확인값이다. 제3자 블로그나 기억에 의한 값은 사용하지 않았다.

## 확인된 시각 자산 규칙

| 공식 배치/자산 | 상태 | 확인된 규칙 | 출처 |
| --- | --- | --- | --- |
| Discover Carousel 데스크톱 아트워크 | 조건부 공식 확인 | `1920 x 1080`, `JPG`, 상점 페이지 상단 배치, 배경에 로고 포함 금지, 왼쪽 1/3은 텍스트·CTA 오버레이 공간, 초점은 화면 오른쪽 70%에 배치 | [Marcom PDF](https://static-assets-prod.epicgames.com/eos-docs/files/marketing-overview-files/EGS_Storefront_Merchandising_Carousel-Guidelines.pdf), p.4–5 |
| Discover Carousel 모바일 아트워크 | 조건부 공식 확인 | `1200 x 1600`, 세로, `JPG`, 배경에 로고·테두리·프레임을 포함하지 않음, 초점은 이미지 상단 50%에 배치 | [Marcom PDF](https://static-assets-prod.epicgames.com/eos-docs/files/marketing-overview-files/EGS_Storefront_Merchandising_Carousel-Guidelines.pdf), p.7 |
| Carousel 게임 로고 | 조건부 공식 확인 | 폭 `350px`, 가로 방향 최적, `PNG`, 투명 배경, 좌우 여백 없이 제출 | [Marcom PDF](https://static-assets-prod.epicgames.com/eos-docs/files/marketing-overview-files/EGS_Storefront_Merchandising_Carousel-Guidelines.pdf), p.6 |
| Carousel 영상 배경 | 조건부 공식 확인 | 6초 루프, `1920 x 1080px`, `30fps` 또는 `60fps`, `MP4`, 5MB 초과 금지; 첫 프레임 기반 커버 이미지도 요구되며 1MB 초과 금지로 안내됨 | [Marcom PDF](https://static-assets-prod.epicgames.com/eos-docs/files/marketing-overview-files/EGS_Storefront_Merchandising_Carousel-Guidelines.pdf), p.8 |
| 모바일·아랍어 변형 | 조건부 공식 확인 | 데스크톱과 모바일 최적화 자산을 모두 제공; 아랍어를 위한 데스크톱 캐러셀 좌우 반전 아트워크를 별도 제공 | [Marcom PDF](https://static-assets-prod.epicgames.com/eos-docs/files/marketing-overview-files/EGS_Storefront_Merchandising_Carousel-Guidelines.pdf), p.4, 7 |

## 미확인 요구사항

다음은 현재 문서에서 확정하지 않는다: 일반 PDP의 작은 표지·큰 홍보 이미지의 공식 자산명과 필수 여부, 최신 규격·비율·안전 영역, 파일 크기·개수·업로드 그룹, 지역·기기별 예외, 현재 publisher portal의 동영상·포스터·썸네일 요구사항. Epic Developer Portal에 접근할 수 있는 환경에서 공식 Requirements와 Asset Uploader 화면을 다시 확인해야 한다.

## 전달 전 확인

1. 자산이 일반 PDP인지 Carousel 홍보 배치인지 먼저 분류한다.
2. Carousel 배치라면 위 공식 PDF의 조건을 적용하되, 최신 portal 값과 충돌하는지 확인한다.
3. 일반 PDP라면 규격을 추정하지 않고 publisher portal의 최신 공식 값을 확보할 때까지 미해결로 표시한다.
4. 작은 표지·큰 홍보 이미지·정적·움직임에서 공통 방향 검증을 반복한다.

