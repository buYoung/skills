# Microsoft Store

## 범위와 적용성

공식 스토어명은 Microsoft Store이며, 대상은 Windows 11 데스크톱 MSIX 앱이다. 현재 적용 디바이스는 Desktop뿐이다. Xbox와 Holographic 변형은 요청되지 않았으므로 요구사항을 적용하지 않는다. 제품 유형이 앱이므로 게임 전용 poster·box-art 조건은 적용하지 않는다.

## 조사 상태와 출처

현재 Microsoft 공식 문서를 웹에서 열어 2026-08-29에 확인했다.

| 출처 | 확인한 내용 |
| --- | --- |
| [App screenshots, images, and trailers for MSIX app](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/screenshots-and-images) | 스크린샷, Store logo, trailer, Super hero art의 역할·규격·노출 조건 |
| [Add and edit Store listing info for MSIX app](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/add-and-edit-store-listing-info) | listing에서 이미지 자산의 필수·선택 상태와 언어별 처리 |
| [Construct your Windows app's icon](https://learn.microsoft.com/en-ie/windows/apps/design/iconography/app-icon-construction) | MSIX 패키지 아이콘의 표시 크기·배율 변형 |
| [Create an app submission for your MSIX app](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/create-app-submission) | Store listing 자산의 현재 상태 표 |

## 자산 인벤토리

| 자산 | 역할·배치 | 상태 | 규격·형식 | 디바이스/변형 |
| --- | --- | --- | --- | --- |
| `1:1 App tile icon` | Store 여러 페이지의 앱 식별 | 앱에는 권장; 미제공 시 패키지 이미지 사용 | 300 x 300 px, PNG, 50 MB 이하 | Windows 10/11 및 Xbox 표면; 본 문서에서는 Desktop 소비를 우선 |
| 패키지 `AppList` 아이콘 | Windows Start·taskbar·검색 등 | 패키지 게시에 필요한 아이콘 계층 | 최소 target size 16, 24, 32, 48, 256 px; `Square44x44Logo`, `Square150x150Logo`의 배율 변형 포함 | Windows 표시 배율별 자산 |
| Desktop screenshot | 실제 앱 UI의 기능·흐름 증명 | 제출에 1개 이상; 4개 이상 권장 | PNG, landscape 또는 portrait, 50 MB 이하; Desktop 1366 x 768 px 이상, 4K 3840 x 2160 지원 | Desktop만. 최대 10개 desktop screenshot |
| Trailer | 제품 동작을 보여 주는 선택 미리보기 | 선택; 최대 15개 | MOV 또는 MP4, 최대 2 GB, 1920 x 1080; 각 항목에 thumbnail PNG 1920 x 1080과 title(255자 이하) 필요 | Windows 10 버전 1607 이상에서 표시. 상단 노출은 Super hero art 조건에 의존 |
| `16:9 Super hero art` | 큰 배치와 trailer 뒤의 artwork | 선택; 앱에는 권장 | PNG, 1920 x 1080 또는 3840 x 2160; 제목·기타 텍스트 금지 | Windows 10/11 및 Xbox의 여러 layout; trailer 상단 노출 조건 |
| Trailer closed captions | 영상의 오디오 대체 텍스트 | 선택 접근성 변형 | Web VTT, 50 MB 미만 | trailer별·언어별 검토 |
| Trailer audio description | 영상 시각 요소의 오디오 대체 | 선택 접근성 변형 | MP3, 500 MB 미만 | trailer별 검토 |

## 자산별 규칙과 예외

### 아이콘

Store의 300 x 300 `1:1 App tile icon`은 권장되며 패키지 이미지보다 우선될 수 있다. 패키지 `AppList`는 Windows가 표시 배율에 맞는 변형을 고르도록 제공한다. 공식 아이콘 안내는 최소 16, 24, 32, 48, 256 px target-size를 제시하고, `Square44x44Logo`와 `Square150x150Logo`는 100%, 200%, 400% 배율 제공을 최소 권장한다.

### Desktop screenshot

한 디바이스 제품군당 1개가 제출 최소이며, Microsoft는 지원하는 각 제품군에 최소 4개를 권장한다. Desktop은 최대 10개다. 실제 UI만 보여 주고 추가 로고·아이콘·마케팅 메시지를 넣지 않는다. 핵심 시각·텍스트는 상단 2/3에 둔다.

### Trailer와 추가 artwork

Trailers는 선택이며 video, thumbnail, title을 함께 업로드한다. 60초 이하·2 GB 미만은 권장값이며, 1920 x 1080·2 GB 이하·MOV/MP4는 요구사항이다. `16:9 Super hero art`는 앱에도 여러 layout에서 사용될 수 있는 선택 자산이며, 제공 시 trailer가 listing 상단에 표시되는 조건을 충족할 수 있다. 이 artwork에는 제품 제목이나 기타 텍스트를 넣지 않고, 중앙에 핵심 요소를 두며 하단 1/3을 비워 둔다.

### 노출과 디바이스 변형

Store는 고객 운영체제와 기타 조건에 따라 자산과 표시 방식을 달리할 수 있다. Desktop screenshot은 Surface Hub 고객에게도 표시될 수 있다. Xbox·Holographic은 현재 제품 범위 밖이며, 지원을 추가할 때 각각의 공식 변형을 재조사한다.

## 관계와 순서

스크린샷은 업로드 순서대로 listing에 표시되므로 첫 화면부터 기능 이해 흐름을 구성한다. 아이콘은 정체성, 스크린샷은 실제 기능 증거, trailer는 동작 설명, Super hero art는 큰 배치의 시각적 맥락을 담당한다. 하나의 asset이 다른 역할을 대신한다고 가정하지 않는다.

## 전달 검증

- [ ] Desktop에 해당하지 않는 screenshot을 제거했다.
- [ ] 각 screenshot이 PNG·50 MB 이하·1366 x 768 이상이다.
- [ ] screenshot은 최대 10개이고, 최소 1개를 제출하며 4개 이상을 권장 기준으로 검토했다.
- [ ] `1:1 App tile icon`이 300 x 300 PNG인지 확인했다.
- [ ] trailer를 사용할 경우 video·thumbnail·title이 함께 있고 각 공식 규격을 만족한다.
- [ ] Super hero art의 PNG·픽셀·텍스트 금지·중앙 배치를 확인했다.
- [ ] 패키지 아이콘에 필요한 배율·target-size 변형을 확인했다.

## 미해결 사항

- 실제 지원 언어와 언어별 caption·screenshot 변형은 미정이다.
- 향후 Xbox 또는 Holographic 지원 여부가 정해지면 해당 자산 규격과 노출 조건을 별도 확인해야 한다.
- 실제 자산의 내용·촬영 화면·trailer 서사는 제작 범위 밖이다.

## 범위 제외

앱 이름, 설명, search terms, 가격 및 인증 절차는 이 문서에서 다루지 않는다.
