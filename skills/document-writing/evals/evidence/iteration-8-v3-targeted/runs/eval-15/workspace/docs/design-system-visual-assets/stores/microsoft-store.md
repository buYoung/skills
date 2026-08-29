# Microsoft Store — Windows 11 데스크톱 MSIX

## 사용 목적

Windows 11 데스크톱 MSIX 앱의 Store listing에서 자산별 역할과 등록 계약을 빠르게 확인하기 위한 기준 문서다. 현재 대상은 Desktop이며, Xbox·Holographic 변형은 앱이 해당 디바이스 제품군을 실제로 지원할 때만 조건부로 적용한다.

## 공통 디자인 원칙

제품의 정밀함을 우선하고 장식은 핵심 기능을 설명할 때만 사용한다. 자산은 실제 UI와 기능을 정확하게 보여 주고, 과장된 마케팅 문구·불필요한 로고·장식을 넣지 않는다. Microsoft Store의 자동 텍스트 오버레이와 레이아웃별 크롭을 전제로 중요한 정보는 안전 영역 안에 둔다.

## 자산 계약 요약

| 자산 | 역할 | 공식 규격·수량 | 노출 및 조건 | 이 제품의 제작 규칙 |
| --- | --- | --- | --- | --- |
| 1:1 App tile icon | Store 여러 페이지에서 앱을 식별하는 작은 대표 이미지 | PNG, 300 × 300px, 50MB 이하 | 선택 업로드지만 강력 권장. 업로드하면 패키지 아이콘보다 우선 | 축소 시 단일 핵심 형태와 선명한 대비를 유지. 세부 장식과 작은 글자는 사용하지 않음 |
| Desktop screenshot | 고객에게 실제 앱 UI와 주요 흐름을 보여 줌 | PNG, 가로 또는 세로, 1366 × 768px 이상, 4K 3840 × 2160px 지원, 50MB 이하. Desktop 최대 10장 | 제출에는 지원 디바이스 제품군당 1장 이상. Microsoft 권장량은 지원 제품군당 최소 4장(FAQ는 5–8장 권장). Desktop 이미지는 Surface Hub에도 표시 | 핵심 시각·텍스트를 상단 2/3에 배치. 추가 로고·아이콘·마케팅 문구 금지. 기능별로 서로 다른 실제 사용 상황을 보여 줌 |
| Trailer | 제품이 동작하는 모습을 짧게 보여 줌 | 최대 15개. MOV 또는 MP4, 2GB 이하, 1920 × 1080px. 각 영상에 PNG 썸네일 1920 × 1080px와 제목(255자 이하) 필요. 자막 Web VTT 50MB 이하, 오디오 설명 MP3 500MB 이하 | 선택. Windows 10 version 1607 이상 고객에게만 표시(Xbox 포함). 제품 페이지 상단 노출은 Super hero art 조건을 따름 | 60초 이하 권장. 핵심 정보는 중앙에 배치하고 기능 증명을 우선. 접근성 파일을 함께 준비 |
| 16:9 Super hero art | 트레일러 전후와 Store의 대형·프로모션 레이아웃을 받치는 배경 artwork | PNG, 1920 × 1080px 또는 3840 × 2160px | Windows 10/11 및 Xbox 레이아웃에서 사용 가능. 트레일러를 상단에 노출하려면 필요. 앱에는 권장, 게임에는 트레일러 사용 시 필수라는 Microsoft 조건이 있음 | 제품 UI·디바이스 이미지를 넣지 않음. 텍스트·제품명 금지. 중요한 요소는 중앙, 하단 1/3과 가장자리에는 두지 않음 |
| Xbox artwork | Xbox에서 올바른 레이아웃을 구성 | Branded key art 584 × 800px(제품명·Branding Bar 필수), Titled hero art 1920 × 1080px(제품명 필수), Featured Promotional Square art 1080 × 1080px(제품명 금지) | Xbox에 게시할 때 필요. 2:3 이미지(720 × 1080 또는 1440 × 2160px)도 Store logos에 제공해야 최적 표시 | 현재 Windows 11 데스크톱 범위에서는 만들거나 업로드하지 않음. Xbox 지원 결정이 생길 때만 별도 검토 |
| Holographic image | Holographic 제품군용 대형 artwork | 2:1, 2400 × 1200px | Holographic 지원 시에만 사용하며 Microsoft는 제공을 권장 | 현재 범위에서는 만들거나 업로드하지 않음 |

## 디바이스 변형 규칙

### Desktop — 현재 대상

Desktop 스크린샷만 등록한다. 앱이 지원하는 제품군에 해당하는 이미지만 제공하며, 지원하지 않는 제품군의 스크린샷은 업로드하지 않는다. 1366 × 768px 이상을 기준으로 잡고, 4K 원본이 필요하면 3840 × 2160px를 사용한다. Store 오버레이가 하단 1/3에 나타날 수 있으므로 기능명·핵심 UI·핵심 텍스트는 상단 2/3에 둔다.

### Xbox — 조건부

Xbox 지원이 제품 범위에 추가될 때만 Xbox 전용 artwork와 2:3 Store logo를 만든다. 제목이 필요한 자산은 상단 2/3에 제목과 핵심 이미지를 배치한다. 현재 문서의 등록 대상은 데스크톱이므로 Xbox 자산은 산출하지 않는다.

### Holographic — 조건부

Holographic 지원이 확정될 때만 2:1 artwork를 추가한다. 지원하지 않는다면 문서의 규격을 참고용으로만 보관하고 업로드하지 않는다.

## 제작·검수 체크리스트

- [ ] 앱 아이콘은 300 × 300px PNG이며 축소해도 식별된다.
- [ ] Desktop 스크린샷은 실제 UI를 보여 주고 PNG·50MB 이하·1366 × 768px 이상이다.
- [ ] 스크린샷의 핵심 요소가 상단 2/3에 있고 추가 로고·아이콘·마케팅 문구가 없다.
- [ ] 지원하는 Desktop 흐름을 최소 4장의 서로 다른 스크린샷으로 설명한다. 제출 최소치는 1장이다.
- [ ] 트레일러를 쓰는 경우 영상·썸네일·제목과 선택적 자막·오디오 설명을 함께 준비한다.
- [ ] 트레일러 상단 노출이 필요하면 Super hero art의 존재와 규격을 확인한다.
- [ ] Super hero art에는 제품명·텍스트·앱 UI·디바이스 이미지를 넣지 않고, 핵심 요소를 중앙에 둔다.
- [ ] Xbox·Holographic 자산은 해당 제품군 지원이 승인된 경우에만 만든다.
- [ ] 실제 자산 파일은 이 문서 세트에 포함하지 않는다.

## 출처와 확인일

아래 Microsoft 공식 자료를 2026-08-29에 확인했다. 규격과 조건은 확인일 기준이며, 제출 시 원문을 다시 확인한다.

1. [Add app screenshots, images, and trailers for MSIX apps](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/screenshots-and-images) — 스크린샷 수량·크기·표시 지침, 앱 타일 아이콘, 트레일러, Super hero art, Xbox·Holographic artwork.
2. [Add and edit Store listing info for MSIX app](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/add-and-edit-store-listing-info) — Store listing에서 스크린샷 1장이 제출 최소 조건이며 Store logos·trailer·추가 assets가 선택 항목임을 확인.

## 확인되지 않은 항목

Microsoft 문서는 Store 레이아웃이 고객의 운영체제와 기타 조건에 따라 달라질 수 있다고 명시한다. 특정 화면에서의 정확한 크롭 위치나 실제 노출 빈도는 이 문서에서 보장하지 않는다. 제품이 Xbox 또는 Holographic을 지원하는지에 대한 결정은 현재 범위 밖이므로 조건부 규칙으로 남긴다.
