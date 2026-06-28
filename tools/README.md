# tools/ — 게이트 검증기와 수렴 리포터 (Validation & Convergence Scripts)

> **EN:** Two stdlib-first Python scripts that turn the spec's *rules* into *runnable checks*.
> [`validate_packs.py`](./validate_packs.py) **operationalizes the quality gates** — it reads
> instance records and fails the build when a record breaks the unified base contract (no
> evidence → G1, no scope → G2, pending record left runtime-active → G3, …). [`convergence_report.py`](./convergence_report.py)
> **operationalizes the convergence model** — it reads a subject's confirmed packs plus their
> evaluation and drift records and prints the six convergence indices and the current maturity
> tier (L0–L4). Together: *validate* answers "is this allowed in?", *report* answers "how close
> is this agent to convergence?". Both run on plain Python 3 (YAML needs PyYAML; JSON always works).

이 폴더의 두 스크립트는 사양(spec)의 **규칙을 실행 가능한 검사로** 바꿉니다. 하나는 *게이트*를,
다른 하나는 *수렴 모델*을 코드로 강제·측정합니다. 둘 다 외부 의존성을 최소화한 순수 Python 3로
돌아가며(JSON은 항상, YAML은 `pip install pyyaml` 시), CI나 승격(promotion) 직전 게이트키퍼로
바로 쓸 수 있습니다.

| 스크립트 | 무엇을 실행 가능하게 하나 | 답하는 질문 | 근거 사양 |
|----------|---------------------------|-------------|-----------|
| [`validate_packs.py`](./validate_packs.py) | **품질 게이트** (G1–G6 중 코드로 강제하는 부분) | "이 레코드가 들어올 자격이 되는가?" | [01 커널 스키마 §2](../spec/01-kernel-schema.md) · [베이스 레코드](../schemas/record.base.schema.json) |
| [`convergence_report.py`](./convergence_report.py) | **수렴 모델** (6개 지표 + L0–L4 성숙도) | "이 에이전트가 얼마나 수렴했는가?" | [06 수렴 모델](../spec/06-convergence-model.md) |
| [`dedup_check.py`](./dedup_check.py) | **중복/증식 신호** (redundancy_ratio·pack_cardinality·merge_rate) — *측정만* | "레코드가 중복으로 불고 있는가?" | [10 중복 억제·병합 §7](../spec/10-dedup-and-merge.md) |
| [`pab_merge.py`](./pab_merge.py) | **dedup judge + upsert actuator** — novel/duplicate/refinement/conflict → insert/**merge**/**supersede**/surface. 멱등. *측정이 아니라 수행* | "이 후보를 새로 찍을까, 기존에 흡수할까?" | [10 중복 억제·병합](../spec/10-dedup-and-merge.md) · [07 확인 게이트](../skills/07-confirmation-gate.md) |
| [`check_anchors.py`](./check_anchors.py) | **문서 링크 무결성** — 모든 교차문서 링크·`#앵커`가 실재 헤딩(GitHub 슬러그)으로 해소되는지. *게이트* | "끊긴 참조가 있는가?" | spec/skills/docs 전체 (GitHub 앵커 규약) |

> 같은 산출은 OpenCrab에서 `opencrab_pack_qa`(검증)와 `opencrab_project_run`(수렴 지표)으로도
> 재현할 수 있습니다. 이 스크립트들은 그 산출의 **의존성 없는 로컬 참조 구현**입니다.

---

## 1) `validate_packs.py` — 게이트를 코드로 (operationalize the gates)

[커널 스키마 §2](../spec/01-kernel-schema.md)의 품질 게이트는 문서로만 있으면 지켜진다는 보장이
없습니다. 이 스크립트는 그중 **레코드 단위로 코드 강제가 가능한 게이트**를, [통합 베이스
레코드](../schemas/record.base.schema.json)의 코어 계약에 비추어 검사합니다. 전체 JSON Schema
검증이 아니라 — 승격 전에 반드시 막아야 할 **빠른 게이트키퍼**입니다.

레코드별 검사 항목 (root of truth: [`../schemas/record.base.schema.json`](../schemas/record.base.schema.json)):

| 검사 | 게이트 | 위반 시 |
|------|--------|---------|
| 필수 베이스 11필드 존재 (`id`, `record_type`, `label`, `statement`, `evidence_refs`, `confidence`, `scope`, `review_status`, `sensitivity`, `created_at`, `updated_at`) | — | FAIL |
| `evidence_refs` 가 비어있지 않은 문자열 리스트 | **G1** (증거 없는 주장 금지) | FAIL |
| `scope` 가 비어있지 않음 | **G2** (스코프 없는 규칙 금지) | FAIL |
| `confidence` 가 `0..1` 범위의 숫자 | — | FAIL |
| `review_status` ∈ {pending, confirmed, rejected, narrowed, sensitive, deferred} | — | FAIL |
| `sensitivity` ∈ {public, internal, sensitive, restricted} | — | FAIL |
| `confidence < 0.7` 이면 `counterexamples`(≥1) 필수 | — | FAIL |
| 런타임 활성(`confirmed`/`narrowed`)인데 `evidence_refs` 가 빔 | **G1·G3** (대기 후보의 런타임 활성 금지) | WARN |

> G4(행동 언어), G5(승격 전 프라이버시 경계), G6(템플릿/인스턴스 분리)는 사람·리뷰·구조 차원의
> 게이트라 이 스크립트만으로 완전 자동화되지 않습니다. 이 검증기는 **G1·G2·G3와 베이스 필드
> 계약**을 기계적으로 막는 역할입니다.

입력은 세 가지 모양을 모두 허용합니다 (JSON 또는 YAML):
1. 팩 이름을 키로 하는 매핑 — `{"user.identity_roles": [rec, …], …}` (예제 파일 형태)
2. 레코드 리스트 — `[rec, rec, …]`
3. 단일 레코드 객체 — `{id: …, record_type: …, …}`

경로가 디렉터리면 그 아래 `.json/.yaml/.yml` 를 재귀 검사합니다. 오류가 하나라도 있으면 비-0
코드로 종료하므로(경고만 있으면 0) CI에 그대로 물릴 수 있습니다.

### 사용 예 — `examples/logotekton/` 검증

저장소 루트에서:

```bash
# (a) 확인된 인스턴스 레코드 한 파일 검증
python tools/validate_packs.py examples/logotekton/instance-records.yaml

# (b) 평가 케이스도 함께 (둘 다 베이스 레코드를 만족해야 함)
python tools/validate_packs.py \
    examples/logotekton/instance-records.yaml \
    examples/logotekton/evaluation-cases.yaml

# (c) 폴더 통째로 — .json/.yaml/.yml 재귀
python tools/validate_packs.py examples/logotekton/

# 도움말
python tools/validate_packs.py --help
```

기대 출력 (a):

```
────────────────────────────────────────────────────────────
요약: 8 레코드  |  PASS 8  FAIL 0  WARN 0  SKIP 0  FILE-ERROR 0
결과: PASS
```

`examples/logotekton/instance-records.yaml` 의 레코드는 모두 `review_status=confirmed`,
`evidence_refs=["current_session"]`, `confidence ≥ 0.8`(→ `counterexamples` 불필요),
`sensitivity=internal` 이라 게이트를 전부 통과합니다. 한 레코드에서 `evidence_refs` 를 비우면
즉시 `[G1]` FAIL 이, `scope` 를 비우면 `[G2]` FAIL 이 떠야 합니다 — 그게 게이트가 살아 있다는
증거입니다. PyYAML 미설치 환경에서는 YAML 파일이 `SKIP` 으로 표시되고(FAIL 아님), JSON 파일만
검사됩니다.

새 사용자가 [`templates/`](../templates) 를 채워 만든 인스턴스도 같은 방식으로 검증합니다 —
승격 전에 이 스크립트를 통과시키는 것이 [확인 게이트(skill 07)](../skills/07-confirmation-gate.md)
이후의 마지막 기계 점검입니다.

---

## 2) `convergence_report.py` — 수렴 모델을 코드로 (operationalize the convergence model)

"암묵지가 쌓이면 개인 에이전트로 수렴한다"는 명제는, [수렴 모델](../spec/06-convergence-model.md)이
정의한 **6개 지표와 5단계 성숙도(L0–L4)** 로 측정될 때 비로소 검증 가능한 주장이 됩니다. 이
스크립트는 한 주체(subject)의 확인된 인스턴스 팩 집합을 입력으로 그 숫자를 산출합니다.

| 지표 | 계산 (spec §2) | 입력 출처 | 방향 |
|------|----------------|-----------|------|
| `coverage` | 값이 채워진 팩(또는 엄격히 ≥3 확인 레코드 팩) / 14 | 인스턴스 레코드 | ↑ |
| `confirmation_ratio` | confirmed / (confirmed + pending + rejected) | 인스턴스 레코드의 `review_status` | ↑ |
| `decision_fidelity` | 통과 평가 케이스 / 전체 평가 케이스 | `user.evaluation_cases` 결과 | ↑ |
| `correction_cost` | 작업당 사용자 편집 비율(평균) | 평가 케이스 관측 | **↓** |
| `drift_stability` | 1 − (최근 대체수 / 확인 레코드수) | `user.drift_history` | ↑ |
| `traceability` | 증거 보유 활성 규칙 / 활성 규칙 | 활성 규칙의 `evidence_refs` | **= 1.0 필수** |

지표를 [수렴 모델 §3](../spec/06-convergence-model.md)의 사다리에 대입해 현재 성숙도 단계
(**L0 Seed → L1 Sketch → L2 Working → L3 Reliable → L4 Convergent**)를 판정하고, 다음 단계
게이트를 통과하려면 무엇을 더해야 하는지를 함께 보고합니다.

> `coverage`는 두 가지로 읽습니다. 표면 지표(팩에 값이 하나라도 들어갔는가, **폭**)와 엄격
> 정의(spec §2의 *≥3 확인 레코드 팩 수 / 14*, **깊이**). 이 리포터는 **두 값을 모두 출력**해,
> 게이트 통과의 실질 병목이 보통 "팩당 깊이(≥3)"임을 드러냅니다.

### 사용 예 — `examples/logotekton/` 수렴 리포트

스크립트는 **디렉터리 하나**를 받아 그 안의 인스턴스 레코드·평가 케이스·드리프트 이력을 모두 읽습니다
(파일을 따로 나열하지 않습니다):

```bash
# 한 주체의 인스턴스 + 평가 + 드리프트가 든 디렉터리 → 6개 지표와 성숙도 단계
python tools/convergence_report.py examples/logotekton
```

현재 라이브 출력(2026-06-28 — 데이터-엔진을 두 바퀴 돌린 **T2** 상태):

```
coverage             0.71   (시드폭 0.71 · 엄격 ≥3 0.07)
confirmation_ratio   1.00
decision_fidelity    1.00
correction_cost      0.08   (↓ 좋음 — #3 계측 후 NA→측정값)
drift_stability      0.89
traceability         1.00   (필수 충족)
──────────────────────────────────────────
maturity tier        L2 Working   (L3까지 남은 빗장: coverage≥0.8 하나)
```

이 숫자는 [`tests/`](../tests/README.md)가 회귀로 잠그고 있어, 도구를 바꾸면 테스트가 먼저 깨집니다.
**라이브 디렉터리는 이미 플라이휠을 두 번 돌린 T2 상태**입니다 — *맨 처음*(T0) 베이스라인은
[`convergence-report.md`](../examples/logotekton/convergence-report.md)가 보존하고, 두 번의 전이
(T0→T1→T2)는 [`revolution-01`](../examples/logotekton/revolution-01/README.md)·
[`revolution-02`](../examples/logotekton/revolution-02/README.md)가 추적합니다. 요지: `traceability=1.0`
(타협 불가)과 `decision_fidelity≥0.8`(L3 충실도 빗장)은 이미 충족, 남은 L3 병목은 `coverage`(0.71→0.8)
하나입니다.

---

## 두 스크립트의 관계 (validate → report)

```
인스턴스 레코드  ──►  validate_packs.py   ──►  PASS  ──►  convergence_report.py  ──►  6 지표 + L0–L4
 (templates를 채운 것      게이트 G1·G2·G3        들어올           수렴 모델 측정
  / 채굴·확인 산출물)      + 베이스 계약 강제      자격 확인
```

- **validate가 먼저입니다.** 게이트를 통과하지 못한 레코드(증거 없음·스코프 없음 등)는 애초에
  팩에 들어올 자격이 없고, 들어오지 않은 레코드는 수렴 지표의 분자/분모에 끼면 안 됩니다.
  특히 `traceability=1.0`(타협 불가)은 validate의 G1이 보장하는 전제입니다.
- **report는 그 다음입니다.** validate를 통과해 팩에 안착한 *확인된* 레코드들만이 수렴의 단조
  누적에 기여합니다([수렴 모델 §1](../spec/06-convergence-model.md)).

CI 권장 순서:

```bash
# 1. 게이트: 하나라도 깨지면 비-0 종료 → 빌드 실패
python tools/validate_packs.py examples/logotekton/

# 2. 리포트: 게이트 통과 후 현재 수렴 상태 출력 (정보성)
python tools/convergence_report.py examples/logotekton
```

## 크로스링크

- 게이트·라이프사이클·베이스 레코드 어휘 → [`../spec/01-kernel-schema.md`](../spec/01-kernel-schema.md)
- 통합 베이스 레코드 스키마 → [`../schemas/record.base.schema.json`](../schemas/record.base.schema.json)
- 수렴 6지표·5단계 성숙도 정의 → [`../spec/06-convergence-model.md`](../spec/06-convergence-model.md)
- 평가 지표·케이스 필드 → [`../spec/05-evaluation-drift.md`](../spec/05-evaluation-drift.md)
- 끝까지 동작하는 예제(이 스크립트들의 입력/출력) → [`../examples/logotekton/`](../examples/logotekton/README.md)
- 이 도구들의 숫자·판정을 잠그는 회귀 테스트 → [`../tests/`](../tests/README.md)
  (`python3 -m unittest discover -s tests`)
- 새 사용자 시작 양식 → [`../templates/QUICKSTART.md`](../templates/QUICKSTART.md)

> 이름 규칙: 산출물은 **Personal Agent**, 플랫폼은 **OpenCrab**, 팩은 정식 14개 이름만 씁니다.
> 구 코드명(`pa.t03`, `t06`, `x12`, `.ba` 등)은 더 이상 쓰지 않습니다
> ([`../spec/08-naming-and-ids.md`](../spec/08-naming-and-ids.md) §5).
