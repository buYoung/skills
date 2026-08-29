# Screenshots와 Trailers

## Screenshots

Steam의 screenshot은 실제 게임플레이만 보여주는 정적 증거다. 최소 5개를 제공해야 하며, 최소 1920×1080, 16:9가 요구된다. concept art, pre-rendered cinematic still, awards, marketing copy, written product description은 넣지 않는다. 고유한 게임 구성요소가 아닌 menu screen은 피하고, in-game UI는 상호작용 방식을 이해시키는 데 도움이 될 때 포함한다. 적합한 screenshot은 Steam 노출 범위가 넓어지므로 별도 age-suitability 표시도 검토한다.

## Trailers

Steam release process에는 trailer 업로드가 요구된다. Trailer는 store page 상단에 표시되며, 첫 trailer는 gameplay 중심으로 실제 플레이어 관점을 보여주는 것을 권장한다. Steam의 trailer category는 General/Cinematic, Teaser, Gameplay, Interview/Dev Diary로 분류할 수 있다.

업로드 기준은 최대 1920×1080, 30/29.97 또는 60/59.94 fps, 5,000+ Kbps, `.mov`, `.wmv`, `.mp4` container다. H.264 video와 AAC audio가 선호되며 16:9가 선호되고 4:3도 허용된다. 여러 언어·국가 제한은 trailer별 Advanced Settings로 다룬다.

## 노출 순서와 대표 이미지

관리 화면의 순서를 기준으로 첫 두 개의 유효 trailer가 screenshot보다 먼저 표시되고, 나머지는 screenshot 뒤에 표시된다. Steam은 첫 번째 store-page video에서 6초 microtrailer를 자동 생성하며, microtrailer는 사용자 지정할 수 없다.

Steam이 trailer 처리 중 자동으로 생성하는 대표 이미지는 다음과 같다.

- `Poster image`: 600×380, video player가 재생을 시작하기 전 표시
- `Thumbnail image`: 232×130, store page에서 trailer를 대표

자동 이미지 대신 custom thumbnail/poster를 올릴 경우 video 자체의 frame이어야 하며 1920×1080 `.jpg` 또는 `.png`여야 한다. 무음 상태에서도 전투의 핵심이 이해되는지 확인한다.

## 검증 상황

- 정적·정보 밀도 높은 전투 screenshot: UI와 목표 식별이 대각선 효과보다 먼저 읽히는지 확인한다.
- 동적·시간 기반 trailer: 첫 수 초 안에 실제 플레이 관점과 전투 방향이 보이고, 자동 microtrailer로 잘려도 핵심이 남는지 확인한다.
