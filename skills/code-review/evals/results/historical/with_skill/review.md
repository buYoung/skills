# 코드 리뷰

## 검토 대상

- 요청 대상 `review-target`을 커밋 `819266bdd25bb540d8dd2a3147c680ad53df8ce1`로 해석했습니다.
- 일반 단일 커밋으로서 첫 번째 부모 `be58e699937c9c355fe8123173558349112cf442`와 비교했습니다.
- 경로 제한은 없습니다. 변경 파일은 `client.py` 한 개이며, 대상 커밋의 `README.md`, `service.py`, `transport.py`까지 소비 흐름과 계약을 확인했습니다.

## 결함

### [주요] 새 디스패치 계층이 모든 요청 옵션을 버립니다

위치: 커밋 `819266bdd25bb540d8dd2a3147c680ad53df8ce1`의 `client.py:1-2`

`service.load`는 `request`에 `timeout_ms=5000`과 호출자가 준 `signal`을 전달합니다. `request`는 이 값을 `options` 딕셔너리로 모아 새 `dispatch`에 넘기지만, `dispatch`는 `transport.send(url)`만 호출합니다. 따라서 `Transport.send`에는 두 옵션이 도달하지 않고 기본값인 `None`이 적용됩니다. 문서의 계약상 `None`은 제한 시간 없음 또는 취소 없음이므로, 이 경로의 요청은 5초 제한과 호출자 취소를 모두 잃습니다. 응답이 지연되는 경우 요청이 의도보다 오래 대기하고, 취소 신호를 보내도 기저 입출력이 계속될 수 있습니다.

실행 재현에서도 부모 커밋은 `{'url': '/items', 'timeout_ms': 5000, 'signal': 'signal-marker'}`를 반환했지만, 검토 대상은 `{'url': '/items', 'timeout_ms': None, 'signal': None}`를 반환했습니다. `dispatch`가 지원되는 옵션을 `transport.send`에 전달하도록 수정해야 합니다. 현재 계약을 유지한다면 `transport.send(url, **options)` 형태로 호출하여 값과 신호 객체를 그대로 보존할 수 있습니다.

## 검증 및 한계

- `git diff 'review-target^1' review-target -- client.py`와 대상/부모 Git blob을 비교해 이 동작이 해당 커밋에서 도입된 회귀임을 확인했습니다.
- 대상 커밋 스냅샷에서 `codemap-search`로 `request`, `dispatch`, `transport.send`의 정의와 참조를 찾고, `service.load → client.request → client.dispatch → Transport.send` 흐름을 확인했습니다.
- `/private/tmp/code-review-historical.l1nSVD/target`과 `/private/tmp/code-review-historical.l1nSVD/base`에서 동일한 `python3 -c` 호출을 실행해 위의 전후 결과를 확인했습니다. 사용한 런타임은 Python 3.14.6입니다.
- `git diff --check 'review-target^1' review-target --`는 오류 없이 완료됐습니다.
- 저장소에는 별도 테스트 파일이나 테스트 실행 명령이 없어서 기존 자동화 테스트는 실행하지 않았습니다. 저장소는 검토 전후 모두 깨끗했습니다.
