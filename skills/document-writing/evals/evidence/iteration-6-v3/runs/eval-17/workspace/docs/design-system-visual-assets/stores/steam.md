# Steam 상점 자산

## 범위와 식별

공식 상점명은 Steam이며, Valve의 Steamworks 문서를 기준으로 게임 상점 및 라이브러리 시각 자산을 기록한다. Steam 배포 대상이 게임인지 여부는 사용자 문맥상 강하게 시사되지만 명시되지 않았으므로, 게임 전용·라이브러리 자산 적용은 운영자 확인이 필요하다.

## 연구 상태와 공식 출처

2026-08-29에 Steamworks 공식 문서를 열어 확인했다.

- [Graphical Assets - Overview](https://partner.steamgames.com/doc/store/assets?l=english): 현재 store·community/client·library·event 자산의 공식 명칭, 상태, 규격.
- [Store Graphical Asset Rules](https://partner.steamgames.com/doc/store/assets/rules?l=english): capsule 텍스트·콘텐츠 제한 및 Artwork Override 조건.

## Store assets

| 공식 자산명 | 역할·배치 | 상태 | 공식 규격 | 방향 적용 |
| --- | --- | --- | --- | --- |
| Header Capsule | store 상단·browse 등 | Required | 920×430px | 넓은 가로 구성에서 로고 가독성과 협동 경험을 함께 유지한다. 기본 capsule에는 게임명·공식 subtitle 외 텍스트를 넣지 않는다. |
| Small Capsule | 검색·목록 등 | Required | 462×174px | 작은 크기에서 로고가 읽히도록 단순화하고 팀 구분을 보강한다. |
| Main Capsule | Steam store home carousel | Required | 1232×706px | 핵심 경험을 즉시 전달하는 가로 대표 자산으로 사용한다. |
| Vertical Capsule | sale·신작 페이지 등 | Required | 748×896px | 세로 크롭에서도 부드러운 형태와 제품 식별을 유지한다. |
| Screenshots | store page 및 feature 표면 | Required | 최소 1920×1080px 이상, 16:9 | 실제 gameplay만 보여주고 concept art, cinematic still, marketing copy를 screenshot으로 사용하지 않는다. 최소 5개 제공 조건은 공식 페이지에서 확인했다. |
| Page Background | store page 배경 | Optional | 1438×810px | 선택 시 지나치게 밝지 않은 배경으로 제품 경험을 방해하지 않는다. |

## Community, client, library

Steamworks 공식 개요는 Shortcut Icon(Required, 256×256px `.ico` 또는 `.png`)과 App Icon(Required, 184×184px `.jpg`)을 명시한다. Library Capsule(Required, 600×900px), Library Hero(Required, 3840×1240px `.png`), Library Logo(Required, 1280px wide 및/또는 720px tall `.png`), Library Header Capsule(Required, 920×430px)도 별도 자산이다. Library Hero는 artwork만, Library Logo는 logotype과 선택적 logomark만 포함해야 한다.

## 텍스트와 예외

기본 graphical asset capsule은 artwork, 게임명, 공식 subtitle만 허용한다. review score, award, 할인 문구, 다른 제품 홍보, 기타 임의 문구는 금지한다. 새 콘텐츠를 알리는 추가 텍스트는 Artwork Override로만 올리고, 지원 언어로 현지화하며, 최대 1개월 조건을 따른다. 이는 기본 자산 규칙을 바꾸지 않는다.

모든 capsule은 읽을 수 있는 제품 로고/이름과 정확한 규격을 가져야 하며, PG-13 적합 artwork여야 한다.

## 전달 검증

업로드 전에 현재 Steamworks 규격과 CURRENT TEMPLATES를 다시 확인한다. screenshot은 최소 해상도·16:9·실제 gameplay 조건, capsule은 공식 텍스트 제한과 로고 가독성, library 자산은 자산별 콘텐츠 제한을 각각 검사한다.

## 미해결

게임 분류 및 library/community 자산 적용 범위, 지원 로케일, trailer/비디오 자산의 Steam별 현재 요구사항, 선택적 event·bundle 자산 사용 여부를 운영자와 확정해야 한다. 등록 문구·가격 정보는 범위 밖이다.
