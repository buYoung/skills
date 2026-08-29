# Google Play

## 범위와 적용

Google Play Store listing의 시각 자산만 다룬다. 제품이 앱인지 게임인지, 지원 장치(Android phone, tablet, Chromebook, Android TV, Wear OS, Automotive OS, Android XR)가 무엇인지는 출시 구성으로 확정해야 한다. 아래 기본 규격은 일반 listing에 적용하고, 장치별 조건은 해당 장치가 실제 배포 대상일 때만 적용한다. Apple App Store는 제외한다.

## 조사 상태와 공식 출처

2026-08-29에 Google Play 공식 도움말을 열어 확인했다.

- [Add preview assets to showcase your app](https://support.google.com/googleplay/android-developer/answer/9866151?hl=en) — 아이콘, feature graphic, screenshots, preview video의 규격·표시·콘텐츠 요구사항
- [Best practices for your store listing](https://support.google.com/googleplay/android-developer/answer/13393723?hl=en) — 스토어 listing 자산의 정확성·현지화·정책 권장사항
- [Deceptive Behavior](https://support.google.com/googleplay/android-developer/answer/17006354?hl=en) — 기능을 정확히 나타내야 한다는 정책

이 문서의 `필수`는 공식 자료의 Requirements, `권장`은 Highly recommended를 뜻한다. 권장은 등록 필수 조건으로 격상하지 않는다.

## 자산 인벤토리

| 자산 | 상태 | 규격·개수·형식 | 표시·관계 |
| --- | --- | --- | --- |
| App icon | 필수 | 512×512px, 32-bit PNG with alpha, 최대 1024KB | listing·검색·차트에 사용; launcher icon을 대체하지 않음 |
| Feature graphic | 필수 | 1024×500px, JPEG 또는 24-bit PNG, alpha 없음 | preview video가 있으면 cover로 사용될 수 있음 |
| Screenshots | 필수 | 서로 다른 장치 유형에 걸쳐 최소 2장; JPEG 또는 24-bit PNG, alpha 없음; 최소 320px·최대 3840px, 긴 변은 짧은 변의 2배 이하 | 최대 8장/지원 장치 유형; preview video 뒤에 표시 |
| Preview video | 선택(게임은 특정 노출면에서 요구될 수 있음) | YouTube URL 1개; public 또는 unlisted, embeddable, age restriction 없음, 광고 비활성화 | feature graphic 위 play button; 일부 면에서 최대 30초 무음 자동재생 가능 |

## 장치별 예외

- **Tablet/Chromebook:** 권장 노출 자격을 위해 최소 4장, 최소 1080px; 가로 16:9(최소 1920×1080), 세로 9:16(최소 1080×1920). 일반 large-screen 업로드는 1,080–7,680px 범위다.
- **Wear OS:** 최소 1장, 실제 Wear OS 화면만, 1:1, 최소 384×384px. 기기 프레임·추가 텍스트·배경·투명·마스킹을 넣지 않는다.
- **Android TV:** 최소 1장 이상의 Android TV 스크린샷과 1280×720px 배너가 필요하다. 배너는 JPEG 또는 24-bit PNG, alpha 없음.
- **Android Automotive OS:** 적용 카테고리에 따라 다르다. 제공 시 최소 세로 2장(800×1280)과 가로 2장(1024×768); 개별 차량/OEM이 아닌 generic system UI를 보여준다.
- **Android XR:** 4–8장, PNG 또는 JPEG, 장당 최대 8MB, 8:5; 권장 3840×2400(최소 1920×1200). 일반 preview video 외 spatial/non-spatial video를 각각 추가할 수 있다.

## 콘텐츠·정책

스크린샷과 영상은 실제 앱·게임 경험을 정확히 보여줘야 한다. 순위·수상·가격·프로모션·설치 유도 문구, 오해를 부르는 기능 표현, 무단 제3자 상표를 넣지 않는다. 스크린샷의 추가 카피는 필요할 때만 쓰고 이미지의 20%를 넘기지 않도록 권장된다. 모든 그래픽·스크린샷에는 140자 이내 대체 텍스트를 제공한다.

## 영상 조건

YouTube playlist/channel URL이 아닌 video URL을 사용한다. 광고를 끄고 public 또는 unlisted·embeddable·비연령제한 상태를 유지한다. 첫 10초 안에 실제 핵심 경험을 보여주고, 영상 대부분을 실제 경험으로 구성하며, 자막과 시장별 현지화를 제공한다. 세로·가로 모두 지원하므로 제품 경험에 맞는 방향을 선택하고 세로 영상의 양옆 검은 막대를 피한다.

## 미해결 항목

현재 제품의 배포 장치, 앱/게임 분류, 지원 언어, XR·TV·Wear OS·Automotive OS 적용 여부는 이 공통 요청만으로 확정되지 않았다. 해당 분기가 확정되면 위 조건 중 적용되는 행과 예외만 출시 체크리스트에 포함한다.
