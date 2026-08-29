# Steam

## 범위와 적용성

대상 storefront는 Valve가 운영하는 Steam이며, 대상 제품은 게임이다. 이 문서는 Steam store page와 Steam client library의 시각 자산만 다룬다. Steam의 listing metadata와 법적 제출 절차는 제외한다.

## 조사 상태와 공식 출처

2026-08-29에 Steamworks 공식 문서를 live-open해 확인했다. 현재 자산명·규격은 [Store Graphical Assets](https://partner.steamgames.com/doc/store/assets/standard?l=english), [Graphical Assets - Overview](https://partner.steamgames.com/doc/store/assets?l=english), [Graphical Asset Rules](https://partner.steamgames.com/doc/store/assets/rules?l=english), [Trailers](https://partner.steamgames.com/doc/store/trailer), [Library Assets](https://partner.steamgames.com/doc/store/assets/libraryassets?l=english&language=english)에 근거한다.

## Steam 자산 인벤토리

| 공식 이름 | 역할·노출 | 상태 | 규격 | 콘텐츠 제한·관계 |
|---|---|---|---|---|
| Header Capsule | store page 상단, Recommended For You, Big Picture browse, Daily Deals(해당 시) | Required | 920×430 | game logo와 artwork; 게임 제목 외 문구 금지 |
| Small Capsule | search results, top-sellers, new releases 등 목록 | Required | 462×174; 120×45·184×69는 자동 생성 | 가장 작은 크기에서도 logo가 읽혀야 함 |
| Main Capsule | Steam store home page 상단 Main Capsule carousel | Required | 1232×706 | game logo와 artwork; 게임 제목 외 문구 금지 |
| Vertical Capsule | seasonal sale front page 상단 및 sale page | Required | 748×896 | game logo와 artwork; 게임 제목 외 문구 금지 |
| Screenshots | store page와 Steam homepage 등 featured page | Required | 최소 1920×1080, 16:9; 최소 5개 | 실제 gameplay만. concept art, pre-rendered cinematic still, award, marketing copy 금지 |
| Trailers | store page 상단; 첫 두 유효 영상은 screenshot보다 앞, 나머지는 뒤 | Required for release process | 최대 1920×1080; 30/29.97 또는 60/59.94 fps; 5,000+ Kbps; `.mov`/`.wmv`/`.mp4`; 16:9 선호, 4:3 허용 | H.264/AAC 선호. category와 언어·국가 노출 설정 가능 |
| Poster image | trailer 로딩 전 video player | Steam이 자동 생성; custom 가능 | 자동 600×380; custom은 video frame, 1920×1080 `.jpg`/`.png` | trailer 자체 frame이어야 함 |
| Thumbnail image | store page에서 trailer 대표 | Steam이 자동 생성; custom 가능 | 자동 232×130; custom은 video frame, 1920×1080 `.jpg`/`.png` | trailer 자체 frame이어야 함 |

## 공통 capsule 규칙

Base graphical asset capsule은 game artwork, game name, official subtitle만 포함할 수 있다. review score, award, discount copy, 다른 제품 홍보, 기타 문구는 허용되지 않는다. 새 콘텐츠를 설명하는 문구는 Artwork Override로만 추가할 수 있고, 1개월 제한과 게임 지원 언어 집합으로의 현지화가 필요하다. 모든 capsule은 readable product logo/name, 정확한 dimensions, PG-13 appropriate artwork 조건을 따른다.

## 라이브러리 관계

Steam Library의 `Library Capsule`은 library overview와 collection의 주 표시 자산이며 600×900이다(300×450 PNG 자동 생성). `Library Header`는 Steam Client Library의 여러 위치와 Recent Games에 표시되며 920×430이고, 미설정 시 Store Asset Header Capsule이 사용된다. `Library Hero`는 library details page 상단의 artwork로 3840×1240 PNG이며 텍스트를 포함하지 않는다. 중앙 safe area는 860×380이다. `Library Logo`는 hero 위에 배치되는 투명 PNG logotype/logomark로 1280px wide 및/또는 720px tall 규격을 사용한다.

## Trailer 생성·노출 관계

Steam은 store page에서 첫 번째로 보이는 video를 기반으로 6초 looping `microtrailer`를 자동 생성하며 사용자 지정할 수 없다. 따라서 첫 trailer의 초반 장면은 실제 전투와 판독 가능한 플레이 관점을 대표해야 한다. 영상은 encoding 중 release할 수 없다.

## 미해결 사항

프로젝트별 파일명, 담당자, 언어별 copy, 실제 export source는 제공되지 않았으므로 결정하지 않는다. Steam 공식 문서는 변경될 수 있으므로 납품 시 현재 페이지와 템플릿을 재확인한다.
