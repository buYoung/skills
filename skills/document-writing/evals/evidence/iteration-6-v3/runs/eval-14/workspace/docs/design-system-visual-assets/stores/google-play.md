# Google Play

## 범위와 적용성

이 파일은 Google Play 앱 스토어 등록의 시각 자산만 다룬다. Apple App Store는 제외한다. 제품이 앱인지 게임인지, 지원 기기 유형과 locale 목록은 요청에서 확정되지 않았으므로 아래의 조건부 가지를 임의로 축소하지 않는다.

## 조사 상태와 공식 출처

2026-08-29에 Google Play 공식 Play Console Help 페이지를 열어 확인했다.

| 출처 | 확인일 | 사용 범위 |
|---|---|---|
| [Add preview assets to showcase your app](https://support.google.com/googleplay/android-developer/answer/9866151?hl=en) | 2026-08-29 | 아이콘, feature graphic, 스크린샷, preview video의 요구사항·표시 관계·콘텐츠 지침 |
| [Best practices for your store listing](https://support.google.com/googleplay/android-developer/answer/13393723?hl=en) | 2026-08-29 | 정책 준수, 실제 기능과의 일치, 과장·순위·가격·부적절 콘텐츠 방지 |

“Requirements”는 필수 조건이고 “Highly recommended”는 권장 조건으로, 이 문서에서 서로 섞지 않는다.

## 자산 인벤토리와 현재 요구사항

### App icon

- **역할/배치:** Google Play 검색, 스토어 등록, 차트 등에 사용되는 앱 식별 자산.
- **필수:** 32-bit PNG with alpha, 512px × 512px, 최대 1024KB, Google Play icon design specifications 준수.
- **금지:** 순위·가격·카테고리 또는 오해를 부르는 배지·문구.

### Feature graphic

- **역할/배치:** 제품 경험을 넓은 장면으로 전달하며 preview video가 있으면 표지 이미지로 사용된다.
- **필수:** JPEG 또는 24-bit PNG(no alpha), 1024px × 500px.
- **권장:** 핵심 시각과 초점을 중앙에 두고 중요한 요소를 잘림 영역에 두지 않는다. 배경 세부사항은 가장자리로 제한한다. 앱 아이콘과 유사한 브랜드를 반복하지 않으며, 순수 흰색·검정·짙은 회색만으로 구성하지 않는다.
- **접근성:** 각 graphic asset에 140자 이내의 맥락 중심 alt text를 제공한다.

### Screenshots

- **역할/배치:** 실제 앱 또는 게임의 기능·모양·경험을 보여준다. 지원 기기 유형별 최대 8장까지 추가할 수 있다.
- **등록 필수:** 서로 다른 기기 유형에 걸쳐 최소 2장. JPEG 또는 24-bit PNG(no alpha), 최소 변 320px, 최대 변 3840px이며 최대 변은 최소 변의 2배를 초과할 수 없다.
- **권장 노출 조건:** 앱은 추천 형식에서 최소 1080px 해상도의 스크린샷 4장(가로 16:9, 최소 1920×1080 또는 세로 9:16, 최소 1080×1920)이 필요하다. 게임은 같은 해상도의 가로 또는 세로 스크린샷 3장이 필요하다. 이는 추천 형식의 조건이며 기본 등록 최소치와 구분한다.
- **콘텐츠:** 실제 in-app/in-game 경험을 보여주며, 첫 세 장은 UI 우선이다. 텍스트 오버레이는 최소화하고 번역한다. 기기 프레임, Google Play/다른 스토어 배지, 허가 없는 제3자 상표를 넣지 않는다.
- **조건부 기기:** 태블릿/Chromebook은 최소 4장과 1,080~7,680px, 16:9 또는 9:16 조건이 별도로 있다. Wear OS와 watch face는 최소 1장, 1:1, 최소 384×384, UI만 표시하는 조건이 있다. Android TV는 최소 1장과 TV banner가 필요하다. Android Automotive OS와 Android XR은 제품 범주·기기별 별도 조건을 적용한다.
- **접근성:** 각 screenshot에 140자 이내 alt text를 제공한다.

### Preview video

- **역할/배치:** 등록 페이지에서 스크린샷보다 먼저 표시될 수 있고 feature graphic 위 재생 버튼으로 시작된다.
- **필수:** YouTube URL을 사용하며 playlist/channel URL이 아니다. 광고를 끄고, public 또는 unlisted로 설정하며, age-restricted가 아니고 Google Play에서 embed 가능해야 한다.
- **권장:** 첫 10초 안에 실제 핵심 경험을 보여주고, 전체의 약 80%를 실제 사용자 경험으로 구성한다. 첫 30초만 자동재생될 수 있으므로 짧고 명확하게 만든다. 가로·세로 모두 지원되며 portrait 영상에 검은 막대를 남기지 않는다.
- **조건부:** 게임은 Google Play의 특정 추천 영역에서 preview video가 요구될 수 있다. 제품 유형이 확정되기 전에는 이를 일반 필수 조건으로 확장하지 않는다.

## 자산 관계와 순서

preview video가 제공되면 Google Play는 이를 스크린샷보다 앞에 표시할 수 있다. feature graphic은 preview의 표지로 사용될 수 있으므로 두 자산의 중심 초점과 제품 약속이 충돌하지 않아야 한다. 실제 제품 화면은 공통 [asset-system.md](../asset-system.md)의 정본이며, Google Play의 수치·배치 예외만 이 파일이 소유한다.

## 기기·locale 변형

지원 기기별 요구사항은 위 조건부 기기 항목을 적용한다. 스크린샷이나 영상에 텍스트가 있으면 지원 언어별 별도 자산을 준비하고, 모든 번역본에도 Google Play 정책을 적용한다. 실제 지원 locale과 기기 목록은 미해결이다.

## 전달 검증

- 파일 형식·치수·용량·개수와 alpha 여부를 Play Console 업로드 전에 확인한다.
- 실제 제품 버전과 화면·영상이 일치하는지 확인한다.
- 잘림 영역, 중앙 초점, alt text, 광고·공개·embed 설정을 확인한다.
- 필수(Requirements)와 권장(Highly recommended)을 별도 결과로 기록한다.

## 미해결 요구사항

- 앱/게임 분류와 지원 기기 유형이 미확정이므로 게임 추천 조건 및 Wear OS/TV/Automotive/XR 조건의 적용 여부는 결정되지 않았다.
- 지원 locale, 실제 YouTube URL, 제품 버전, 업로드 담당자와 파일 저장 규칙은 제공되지 않았다.

