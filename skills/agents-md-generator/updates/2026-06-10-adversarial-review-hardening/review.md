---
#### 작업 정보
- 작업 agent : claude code (fable 5)
- 검증/분석 agent : 서브에이전트 3종 — 문서 품질 평가, 스크립트 실행 검증, 적대적 리뷰 (각각 독립 컨텍스트)
- 작업 유형 : 스킬 강화 (Patch 포함 — `changes.patch`)
- 리뷰 방식 : 적대적 리뷰 에이전트가 실제 픽스처를 만들어 스크립트를 실행, 파괴 경로를 실증한 항목만 채택
- 설계 결정 : "번호 없는 제목의 외부 작성 AGENTS.md" 시나리오는 결함이 아닌 의도된 범위 제한으로 확정 — 이 스킬이 생성하지 않은 AGENTS.md는 수정하지 않는다는 가드를 명문화

---

### 실증된 파괴 경로와 반영 내역

| 심각도 | 발견 | 반영 |
|---|---|---|
| 주요 | 외부 작성(번호 없는 제목) AGENTS.md 업데이트 시 표준 5개 섹션이 전부 missing 처리되어 중복 문서 생성 | 스킬 소유권 가드 신설: 표준 제목이 0개 매칭되면 수정 금지·보고, 명시적 요청 시에만 전체 재생성 (`SKILL.md` Step 5, `update_strategy.md` > Skill-Generated Files Only) |
| 주요 | 문서 타입 전환(단일↔모노레포) 시 강제 재생성으로 커스텀 섹션 무경고 소실 | 강제 재생성 시 커스텀 섹션 원문 이월 + 덮어쓰기 전 사용자 확인 의무화 |
| 주요 | 모노레포 오탐: 빈 `[workspace]`(크레이트 분리 관용구), 단일 앱 Android `include ':app'`, 주석 처리된 `include`, `"keywords": ["workspaces"]` | `detect_monorepo.py` 정밀화(JSON 파싱, 주석 제거, members 필수, include 2개 이상) + "패키지 2개 미만이면 단일 레포" 잠정 판정 규칙 신설 |
| 주요 | 예산 모순: 전체 길이 검증 vs 커스텀 섹션 바이트 보존이 동시 만족 불가 | character_limit 적용 범위를 "프리앰블 + 표준 섹션"으로 명문화, 커스텀 섹션은 한도 제외·절삭 금지 |
| 경미 | 코드 펜스 내부 `## ` 줄을 섹션 헤딩으로 오인 → 조용한 문서 손상 | `parse_sections.py`에 펜스(``` / ~~~) 상태 추적 추가 |
| 경미 | 비UTF-8 파일에서 두 스크립트 traceback 노출 | `parse_sections.py`는 깔끔한 오류 + exit 2, `detect_monorepo.py`는 `errors="replace"` |
| 경미 | git 없는 디렉터리에서 node_modules 집계로 LOC 폭증(1 → 120,001 실측) | `loc_to_limit.py` 및 측정 명령에 `node_modules`/`vendor`/`dist` 제외 추가 |
| 경미 | 타입체크 명령 포함 의무 vs 빌드 명령 금지 검증 충돌 | 안티패턴에 예외 명문화: Working Agreements의 발견된 타입체크 명령은 검증 지침 |
| 경미 | 표준 섹션 내 사용자 추가 규칙 무경고 삭제 | 업데이트 시 관리 섹션에서 제거되는 문구를 사용자에게 보고하는 검증 항목 추가 |
| 경미 | `monorepo_detection.md`에 uv/rye 마커 누락 (스크립트·SKILL.md와 불일치) | uv/rye 마커 및 Python 패키지 발견 절 추가로 3개 소스 동기화 |
| 경미 | `update_strategy.md`에 개인 머신 절대 경로 하드코딩 | 익명화 (`<project-root>/AGENTS.md`) |
| 참고 | 트리거 과확장("Use when setting up a new repository") | description을 AGENTS.md 한정으로 조정, CLAUDE.md/README 비대상 명시 |
| 참고 | 모노레포 All 모드가 Step 1을 건너뛰어 패키지별 Generate/Update 판정 누락 | 패키지별로 Step 1 판정(및 소유권 확인) 재실행 명시 |
| 참고 | `loc_measurement.md`의 "Largest section" 주석이 실제 배분(25% < 35%)과 모순 | 주석 수정 |
| 참고 | updates/README 색인 사장 + patch 필수 규정 미준수 | 색인 전체 갱신, patch는 선택 항목으로 완화 |
| 참고 | 명시적 언어 요청 무시("English only"에 예외 없음) | 사용자가 명시 요청한 언어를 따르도록 예외 추가 |
| 참고 | `--from-stdin` 경로에서 천 단위 구분자를 조용히 오파싱(`50,000` → 50) | 구분자 허용 정규식 + Total 행 부재 시 깔끔한 오류 메시지 |

### 회귀 검증

- `detect_monorepo.py`: 오탐 7종(keywords-only, 빈 workspace, 주석, 단일 include 등) 전부 false, 정탐 8종(npm 배열/객체, cargo members, gradle 다중/첫 줄/composite, latin-1, uv) 전부 true.
- `parse_sections.py`: 펜스 내부 `##` 무시·미폐쇄 펜스·latin-1 깔끔한 오류 확인, 기존 표준/커스텀/missing 판정 동작 유지.
- `loc_to_limit.py`: git 없는 node_modules 디렉터리 LOC 1로 정상화, 경계값(10000/10001/1000001) 기존과 동일, 실제 저장소 실행 정상.

### 방어 확인 (변경 불필요로 판정)

표준 섹션 재배열 보존, 제목 중복(첫 번째만 매칭), 프리앰블/HTML 주석 보존, 초소형 레포 한도(상한이지 하한 아님), 루트 무코드 모노레포 — 모두 기존 설계로 방어됨.
