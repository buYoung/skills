# Google Play store 시각 자산 규격

이 문서는 Google Play 등록에만 적용되는 현재 제출 조건이다. 2026-08-29에 공식 [Google Play Console Help: Add preview assets to showcase your app](https://support.google.com/googleplay/android-developer/answer/9866151?hl=en), [Best practices for your store listing](https://support.google.com/googleplay/android-developer/answer/13393723?hl=en), [Helpful tips for publishing](https://support.google.com/googleplay/android-developer/answer/15191715?hl=en)을 확인했다. 정책은 변경될 수 있으므로 제출 직전에 원문을 다시 확인한다.

## 제출 요약

| 자산 | 현재 필수 조건 | 이 시스템에서의 적용 |
| --- | --- | --- |
| App icon | 32-bit PNG, alpha 포함, `512 × 512 px`, 최대 `1024 KB` | 작은 크기에서도 제품 식별이 되도록 단순한 핵심 형태와 한 가지 강조색을 유지한다. 순위·가격·카테고리를 암시하는 배지나 오해를 부르는 텍스트를 넣지 않는다. |
| Screenshots | 게시를 위해 서로 다른 device type에 걸쳐 최소 `2개`; JPEG 또는 24-bit PNG, alpha 없음; 각 변 `320–3840 px`; 긴 변은 짧은 변의 `2배` 이하 | 실제 앱 화면을 보여 주며 첫 세 장은 UI를 우선한다. 앱 추천 영역의 기회를 위해 앱은 최소 `4개`, 최소 `1080 px`, 세로 `1080×1920` 또는 가로 `1920×1080`을 권장 조건으로 준비한다. |
| Preview video | 선택 사항. YouTube URL 하나(playlist/channel URL 불가); public 또는 unlisted, age restriction 없음, embeddable, 광고 monetization 비활성화 | 첫 `10초` 안에 실제 핵심 경험을 보여 주고, 첫 `30초` 자동재생·음소거 가능성을 고려한다. UI·overlay·자막·음성을 locale에 맞춘다. |
| Feature graphic | JPEG 또는 24-bit PNG, alpha 없음, `1024 × 500 px`; 게시 필수 | 핵심 경험의 맥락을 중앙에 두고 crop 영역에 잘리지 않게 한다. icon을 그대로 반복하지 않으며, 세부 장식을 가장자리에 제한한다. |

스크린샷과 feature graphic은 업로드 전 alpha 채널을 제거한다. 스크린샷에는 alt text를 제공하며, 핵심 맥락을 `140자 이하`로 설명한다.

## 정책 검수

모든 listing 그래픽과 영상은 현재 앱 기능을 정확히 반영해야 한다. 다음은 제출 전 차단 항목이다.

- 순위·성과·수상·추천을 암시하는 표현(예: “#1”, “Best”), 가격·할인·기간성 프로모션, 불필요한 call-to-action을 넣지 않는다.
- 제품과 무관한 키워드, 오해를 부르는 타사 앱·기업과의 관계, 무단 제3자 상표·캐릭터·로고를 넣지 않는다.
- 폭력적·성적으로 부적절한 표현, 모욕적 표현, 알림창의 개인정보나 통신사·알림 표시를 노출하지 않는다.
- 기기 프레임은 빠르게 구식이 되거나 사용자를 소외시킬 수 있으므로 기본적으로 사용하지 않는다.
- feature graphic의 핵심 요소는 중앙에 두고 가장자리에는 crop되어도 의미가 사라지지 않는 배경만 둔다.

Google Play는 자산을 listing 외 Google 소유 채널의 홍보에 사용할 수 있다. 외부 마케팅 노출을 제한해야 하는 경우 Play Console의 Store settings에서 관련 설정을 확인한다.

## 업로드 체크리스트

- [ ] icon이 `512 × 512 px`, 32-bit PNG, alpha 포함, `1024 KB` 이하인가?
- [ ] 서로 다른 device type의 screenshot이 최소 2개인가?
- [ ] screenshot이 JPEG/24-bit PNG, alpha 없음, 각 변 `320–3840 px`이며 비율 제한을 지키는가?
- [ ] 앱 추천 영역을 목표로 한다면 1080px 이상 screenshot 4개를 준비했는가?
- [ ] video URL이 개별 YouTube video이고 public/unlisted·embeddable·광고 비활성·연령 제한 없음인가?
- [ ] feature graphic이 `1024 × 500 px`이고 alpha가 없는가?
- [ ] 실제 앱과 기능·문구가 일치하고 모든 locale의 overlay·자막·음성이 검수되었는가?
- [ ] 정책상 순위·가격·프로모션·타사 권리·부적절한 콘텐츠가 없는가?

### 출처 및 확인일

- Google Play Console Help, “Add preview assets to showcase your app”: https://support.google.com/googleplay/android-developer/answer/9866151?hl=en — 확인일 `2026-08-29`.
- Google Play Console Help, “Best practices for your store listing”: https://support.google.com/googleplay/android-developer/answer/13393723?hl=en — 확인일 `2026-08-29`.
- Google Play Console Help, “Helpful tips for your store listing”: https://support.google.com/googleplay/android-developer/answer/15191715?hl=en — 확인일 `2026-08-29`.
