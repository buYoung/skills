# Google Play 상점 자산

## 범위와 식별

공식 상점명은 Google Play이며, 요청의 Play Store와 Google Play Store는 같은 상점을 가리키므로 이 파일 하나로 통합한다. 제품의 앱/게임 분류, 대상 기기, 지원 로케일은 제공되지 않았다. 따라서 앱·게임 공통 자산을 기록하고 기기별 가지는 조건부로 남긴다.

## 연구 상태와 공식 출처

2026-08-29에 Google 공식 Play Console Help 페이지를 열어 확인했다.

- [Add preview assets to showcase your app](https://support.google.com/googleplay/android-developer/answer/9866151?hl=en): App icon과 Feature graphic의 필수 형식·크기, preview video와 screenshot의 사용 맥락.
- [Best practices for your store listing](https://support.google.com/googleplay/android-developer/answer/13393723?hl=en): 그래픽의 일관성, 텍스트 최소화, 중앙 배치, 실제 기능 표현, trailer 권장.

## 자산 목록과 규칙

| 공식 자산명 | 역할·배치 | 상태 | 공식 규격·형식 | 방향 적용 |
| --- | --- | --- | --- | --- |
| App icon | listing·검색·top charts | Required | 32-bit PNG with alpha, 512×512px, 최대 1024KB | 작은 크기에서 제품 식별과 팀 구분을 우선한다. 순위·가격·카테고리를 암시하는 배지나 문구는 넣지 않는다. |
| Feature graphic | listing 및 preview video의 cover 등 | Required | JPEG 또는 24-bit PNG, alpha 없음, 1024×500px | 넓은 가로 공간에서 협동 경험을 보여주되 세부를 과밀하게 넣지 않는다. |
| Screenshots | 지원 기기별 listing 미리보기 | 운영자 요구 확인 필요 | 정확한 크기·장수·방향은 제품 분류와 기기별 공식 조건을 재확인해야 함 | 실제 제품 화면을 사용하고, 필요한 경우 짧은 문구만 사용한다. |
| Preview video | listing 및 Google 프로모션 표면 | Optional/노출 조건 확인 필요 | 이 문서에서 현재 수치 미확인 | 사용자 제공 trailer 검증 결과를 유지하고, 무음·일시정지에서도 협동 흐름이 읽히게 한다. |

## 기기·로케일 예외

Wear OS에는 1:1, 최소 384×384px screenshot과 인터페이스만 보여야 한다는 공식 조건이 있다. Android TV 배포 시 Android TV screenshot 최소 1개와 banner가 필요하다. Android Automotive OS는 카테고리에 따라 screenshot 필수 여부가 달라진다. 해당 기기 배포 여부는 미정이므로 적용 여부를 확인한 뒤 확정한다.

텍스트가 있는 screenshot과 promotional video는 지원 언어별로 별도 자산이 필요할 수 있다. 지원 로케일은 미정이다.

## 전달 검증

업로드 전 App icon과 Feature graphic의 공식 형식·크기를 검사하고, screenshot은 대상 기기에서 실제 제품 화면인지 확인한다. Google 공식 페이지는 요구사항과 권장사항을 구분하므로, 권장사항을 필수 제출 조건으로 승격하지 않는다.

## 미해결

앱/게임 분류, 대상 기기, 지원 로케일, screenshot의 적용별 크기·장수·방향, preview video의 현재 세부 요구사항을 공식 제품 조건과 함께 확정해야 한다. 등록 문구·가격 정보는 범위 밖이다.
