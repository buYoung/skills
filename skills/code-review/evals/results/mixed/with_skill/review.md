# 코드 리뷰

## 리뷰 대상

- 별도 리비전이 지정되지 않아 기본 범위인 모든 미커밋 변경을 검토했습니다.
- 기준은 `HEAD`의 `36dcc074deb59f5fb08da1a15f1e2d14ca2a1ca3`이며, 최종 worktree 동작을 기준으로 staged 변경(`pricing.py`), unstaged 변경(`checkout.py`, `pricing.py`), untracked 파일(`renewal.py`)을 함께 추적했습니다.
- 경로 제한은 없습니다. 변경된 세 Python 파일과 계약을 명시한 `README.md`를 모두 검토했습니다.

## 결함

### [주요] 배송비까지 할인되어 모든 할인 주문의 합계가 낮아집니다

위치: `pricing.py:2`

`README.md:1`은 할인을 소계에 한 번 적용한 뒤 배송비를 더한다고 명시합니다. 그러나 `total`은 `(subtotal_cents + shipping_cents)` 전체에 `discount_percent`를 곱합니다. 따라서 배송비가 0보다 크고 할인율이 0보다 큰 모든 호출에서 배송비도 함께 할인됩니다.

실행 경로는 두 소비자에서 모두 확인됩니다. `checkout.py:4`의 `total(1000, 500, discount_percent=10)`은 계약상 `1000 * 90 // 100 + 500 = 1400`이어야 하지만 `1350`을 반환하고, `renewal.py:4`의 동일한 10% 할인은 기대값 `1100` 대신 `1080`을 반환합니다. 이 때문에 할인 주문마다 배송비의 할인율만큼 결제 금액이 체계적으로 과소 계산됩니다.

할인을 `subtotal_cents`에만 적용한 뒤 `shipping_cents`를 더하도록 계산 순서를 바꿔야 합니다.

## 유지보수 관찰

`checkout.py:4`와 `renewal.py:4`가 동일한 10% 할인 정책을 각각 숫자 리터럴로 보관합니다. 현재처럼 두 흐름이 같은 할인율을 공유하는 동안 정책 변경 시 두 호출을 함께 찾아 수정해야 하며 한쪽만 바뀌면 동작이 조용히 갈라집니다. 할인율을 의도를 드러내는 공용 상수나 단일 정책 함수로 모으면 두 흐름의 일관성을 한 곳에서 유지할 수 있습니다.

## 검증 및 한계

- `git diff --check HEAD --`를 실행했고 공백 오류는 없었습니다.
- `PYTHONDONTWRITEBYTECODE=1 python3 -c 'from pricing import total; ...'`로 `total(1000, 500, 10)`을 실행해 실제 `1350`, 계약상 기대값 `1400`을 확인했습니다.
- `PYTHONDONTWRITEBYTECODE=1 python3 -c 'from checkout import checkout; from renewal import renewal; ...'`로 소비자 경로를 실행해 `checkout(1000) == 1350`, `renewal(1000) == 1080`을 확인했습니다.
- `ast.parse`로 `pricing.py`, `checkout.py`, `renewal.py`의 구문을 확인했습니다.
- 설치된 Python `3.14.6`에서만 동적 검증했습니다. 저장소가 명시한 최소 버전 Python 3.9에서는 실행하지 않았습니다.
- 저장소에는 테스트 파일이 없어 기존 테스트 스위트는 실행하지 못했습니다. 저장소 밖의 외부 소비자는 확인할 수 없었습니다.
