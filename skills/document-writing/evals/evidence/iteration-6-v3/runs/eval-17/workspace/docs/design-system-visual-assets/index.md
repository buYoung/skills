# 상점 시각 자산 디자인 시스템

## 목적과 범위

이 문서는 Play Store와 Google Play Store(동일한 공식 상점인 Google Play), Steam에 배포하는 제품의 상점 시각 자산을 위한 공통 방향과 상점별 적용 규칙을 정의한다. 실제 이미지·영상 제작, 등록 문구, 가격 정보는 범위에서 제외한다.

대상 독자는 브랜드·마케팅·아트·스토어 운영 담당자다. 공통 시각 언어는 이 세트가 소유하고, 각 상점의 공식 자산명·규격·배치는 `stores/` 아래 파일이 소유한다.

## 승인된 방향과 근거

승인된 방향은 “친근한 협동 경험을 부드러운 형태와 선명한 팀 구분으로 보여준다”이다. 작은 아이콘과 넓은 capsule, 정적 screenshot과 trailer에서 방향을 검증했으므로, 친근함과 협동의 구분은 공유하되 크기·밀도·순서는 상점 맥락에 맞게 변형한다.

방향 권위: 사용자 제공 프롬프트의 승인 문장과 검증 기록.

## 결정 소유권

| 결정 영역 | 소유 파일 |
| --- | --- |
| 공통 형태·색 역할·타이포그래피·금지 표현 | [visual-language.md](visual-language.md) |
| 상점 간 자산 개념과 매핑 | [asset-system.md](asset-system.md) |
| screenshot·preview·trailer 서사와 실제 제품 충실도 | [screenshots-and-previews.md](screenshots-and-previews.md) |
| 시각 계층·안전 영역·시각 내 문구 | [composition-and-copy.md](composition-and-copy.md) |
| 현지화·지역 변형 | [localization.md](localization.md) |
| 대비·가독성·모션 대체 | [accessibility.md](accessibility.md) |
| 소스·검증·버전·보관 | [delivery-and-versioning.md](delivery-and-versioning.md) |
| Google Play 공식 자산명과 규격 | [stores/google-play.md](stores/google-play.md) |
| Steam 공식 자산명과 규격 | [stores/steam.md](stores/steam.md) |

충돌 시 상점 운영자의 현재 공식 요구사항이 공통 표현보다 우선하며, 공통 방향을 훼손하는 경우 `delivery-and-versioning.md`의 변경 검토를 거친다.

## 대표 검증

- 작은 아이콘: 축소 상태에서도 제품 식별과 팀 구분이 유지되는지 확인했다.
- 넓은 capsule: 가로 공간에서 부드러운 형태와 로고 가독성이 함께 유지되는지 확인했다.
- 정적 screenshot: 실제 제품 화면과 협동 흐름이 오해 없이 전달되는지 확인했다.
- trailer: 움직임 속에서도 팀 구분과 친근한 인상이 유지되는지 확인했다.

## 연구 상태

Google Play와 Steamworks의 현재 공식 페이지를 2026-08-29에 열어 시각 자산 요구사항을 확인했다. 제품의 앱/게임 분류, 대상 기기, 지원 로케일은 제공되지 않았으므로 상점 파일에서 조건부 또는 미해결로 남긴다.
