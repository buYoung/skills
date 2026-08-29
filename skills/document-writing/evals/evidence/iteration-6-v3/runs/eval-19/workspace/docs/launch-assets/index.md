# 출시 자산 시각 시스템

## 목적과 범위

이 문서는 출시팀이 Linux 앱을 Flathub와 Snap Store에 등록할 때 사용하는 아이콘, 스크린샷, 미리보기 자산의 공통 시각 원칙과 상점별 적용 규칙을 정의한다. 실제 자산을 생성하거나 업로드하는 문서가 아니라, 무엇을 준비하고 어떻게 검증할지 결정하는 기준이다. Steam은 범위에서 제외한다.

## 승인된 방향과 근거

승인된 방향은 “기능을 빠르게 이해시키는 차분한 기술 제품이며 장식보다 실제 화면의 판독성을 우선한다”이다. 작은 아이콘과 큰 스크린샷, 밝은 화면과 어두운 화면에서 이 방향이 검증됐다. 공통 규칙은 [visual-language.md](visual-language.md)가 소유하고, 자산별 규칙은 [asset-system.md](asset-system.md)와 [screenshots-and-previews.md](screenshots-and-previews.md)가 소유한다.

## 적용 대상과 우선순위

| 순서 | 출처 | 적용 방식 |
| --- | --- | --- |
| 1 | 각 상점의 현재 공식 안내 | 상점별 제출 형식·크기·개수·관계에 우선 적용 |
| 2 | 이 문서 세트의 공통 원칙 | 상점 요구사항과 충돌하지 않는 범위에서 모든 자산에 적용 |
| 3 | 팀의 출시 검증 결과 | 실제 화면의 판독성 확인과 자산 선택에 적용 |

상점 요구사항이 공통 원칙보다 구체적이면 [stores/flathub.md](stores/flathub.md) 또는 [stores/snap-store.md](stores/snap-store.md)의 조건을 따른다. 공식 안내의 최신성이나 적용 범위가 불명확한 경우 해당 상점 파일의 미해결 항목을 먼저 해결한다.

## 문서 지도

- [visual-language.md](visual-language.md): 공통 시각 방향, 불변·가변·조건부·금지·검증 결정
- [asset-system.md](asset-system.md): 아이콘·스크린샷·미리보기의 공통 개념과 상점 매핑
- [screenshots-and-previews.md](screenshots-and-previews.md): 화면 선택, 순서, 실제 UI 충실도
- [accessibility.md](accessibility.md): 밝기, 어두운 화면, 대비와 판독성
- [delivery-and-versioning.md](delivery-and-versioning.md): 파일 준비, 검증, 변경 시점
- [stores/flathub.md](stores/flathub.md): Flathub 적용 규칙
- [stores/snap-store.md](stores/snap-store.md): Snap Store 적용 규칙

## 상태

방향은 승인됐고 두 가지 대조 상황에서 검증됐다. 상점의 일부 요구사항은 공식 문서와 현재 업로드 UI 사이에 차이가 보고되어 있으므로, 업로드 직전 상점별 미해결 항목을 확인해야 한다.
