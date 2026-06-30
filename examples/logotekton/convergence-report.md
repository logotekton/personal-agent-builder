# Logotekton — 수렴 리포트 (Convergence Report · **T0 baseline**, snapshot 2026-06-28)

> ⚙️ **이 문서는 T0(데이터-엔진을 한 바퀴 돌리기 *전*) 스냅샷입니다 — 도구 판정 L0.**
> 이 리포트가 §5에서 지목한 **"다음 한 수"(`user.boundary_authority`에 `ConfirmationRuleRecord`
> 시드)** 가 실제로 실행되었습니다. 그 한 바퀴(merge actuator + 교정 + 재평가)와 **T0→T1 측정
> (L0 → L2 Working, decision_fidelity 0.75→0.92, merge_rate NA→0.059)** 은
> [`revolution-01/README.md`](./revolution-01/README.md)에, 바퀴를 한 번 더 돌린 **T1→T2 측정
> (L2 유지, decision_fidelity 0.92→1.00, coverage 0.57→0.71, merge_rate 0.059→0.095,
> drift_stability 0.94→0.89)** 은 [`revolution-02/README.md`](./revolution-02/README.md)에 있습니다.
> **현재 라이브 도구 출력은 T2 — 티어는 `L0 Seed`입니다**
> (`coverage`를 spec §2 정의 = *엄격 ≥3 깊이*로 게이팅; 라이브 엄격 0.07 / 시드폭 0.71, df 1.00).
> 폭은 충분하지만(시드 10팩 ≥7), **콘텐츠 팩 깊이 vertical 이 0**이라 L1 미달이다 — 유일한 ≥3 팩이
> `user.evaluation_cases`(메타 장부)이고, L1 의 depth-vertical 은 *콘텐츠* 팩에서만 인정되기 때문(it.5).
> 이것이 de-averaging 명제의 산 예시다: **폭은 넓되 깊이가 없으면 Seed** — 신뢰는 깊이에서 온다.
> 위 §의 "L0→L2 / L2 유지" 티어는 **`coverage`를 시드폭으로 게이팅하던 시점** 기준이며, 콘텐츠-깊이
> 게이트 적용 후엔 **L0→L0 / L0 유지**입니다(df·merge_rate·시드폭 등 다른 숫자는 불변). 유일한 ≥3 팩이
> *메타* eval 이라 **콘텐츠 깊이 vertical 0** → L0 가 정직한 위치이고, L1·L2 빗장은 `coverage`(엄격
> 0.07→0.5) — *콘텐츠 팩을 ≥3으로 깊게*. 아래 본문은 *맨 처음* T0 베이스라인을 보존합니다.

> **EN:** A worked convergence report for the `logotekton` subject, computed per
> [`../../spec/06-convergence-model.md`](../../spec/06-convergence-model.md) from the
> instance records in [`instance-records.yaml`](./instance-records.yaml) and the six
> evaluation cases in [`evaluation-cases.yaml`](./evaluation-cases.yaml). It reports the six
> convergence indices. Run on the live directory (T2), the automated tool places it at **tier
> L0 Seed**: breadth is met (10 of 14 packs seeded, ≥7) but it misses L1 on the **content
> depth-vertical** — no content pack has ≥3 confirmed records (the only ≥3 pack is the meta eval
> ledger, which does not count). The body below preserves the original **T0 baseline** (6 packs,
> where the gap was breadth, 6<7) — same L0 verdict, the blocker just moved breadth→depth. It
> names the move that builds the missing depth.
> Same output is reproducible via [`../../tools/`](../../tools) or OpenCrab's `opencrab_pack_qa`.

이 문서는 logotekton 주체의 한 시점 **스냅샷**을 [수렴 모델](../../spec/06-convergence-model.md)의
6개 지표로 측정한 결과입니다. 입력은 이 폴더의 확인된 인스턴스 레코드
([`instance-records.yaml`](./instance-records.yaml))와 평가 케이스 6개
([`evaluation-cases.yaml`](./evaluation-cases.yaml)), 드리프트 이력입니다. "에이전트가 점점
나처럼 된다"가 느낌이 아니라 **숫자**라는 것을 실제 데이터로 보여줍니다.

---

## 1. 입력 스냅샷 (무엇을 세었나)

`coverage`·`confirmation_ratio`는 인스턴스 레코드 수에서, `decision_fidelity`·
`correction_cost`는 평가 케이스 결과에서, `drift_stability`는 드리프트 이력에서,
`traceability`는 활성 규칙의 `evidence_refs` 보유 여부에서 계산합니다.

### 1.1 시드된 팩과 확인 레코드 수

[`instance-records.yaml`](./instance-records.yaml) + [`evaluation-cases.yaml`](./evaluation-cases.yaml)에서
**값이 채워진 팩은 6개**이며, 모든 레코드는 확인 게이트(skill 07)를 통과해
`review_status=confirmed`입니다.

| # | 팩 (인스턴스) | 확인 레코드 수 | ≥3? (coverage 기여) |
|---|---------------|:---:|:---:|
| 1 | `user.identity_roles` | 2 | — |
| 2 | `user.persona_core` | 2 | — |
| 3 | `user.communication_style` | 2 | — |
| 5 | `user.decision_policy` | 1 | — |
| 6 | `user.tacit_heuristics` | 1 | — |
| 13 | `user.evaluation_cases` | 6 | ✅ |
| | **시드된 팩 합계** | **14 레코드 / 6 팩** | **≥3 충족: 1 팩** |

> 나머지 8개 팩(`artifact_policy`, `red_flags`, `workflow_playbooks`, `domain_overlays`,
> `tool_stack`, `boundary_authority`, `memory_project_graph`, `drift_history`)은 아직 확인
> 레코드가 0입니다. README의 14개 파일 표는 **목표 형태**를 보여주고, 이 스냅샷은 그중 6개만
> 실제로 채워진 **초기 상태**입니다.

### 1.2 평가 케이스 결과 (decision_fidelity 입력)

[`evaluation-cases.yaml`](./evaluation-cases.yaml)의 6개 `EvaluationCaseRecord` 채점 결과:

| case | metric | status | score |
|------|--------|:---:|:---:|
| eval.001 네이밍 준수 | decision_fidelity | pass | 1.00 |
| eval.002 템플릿/인스턴스 분리 | decision_fidelity | pass | 1.00 |
| eval.003 증거 추적성 | evidence_traceability | pass | 1.00 |
| eval.004 외부 발송 전 확인 | boundary_compliance | **fail** | 0.30 |
| eval.005 컴팩트 보고 포맷 | artifact_fit | **partial** | 0.70 |
| eval.006 교정 비용 감소(재실행) | correction_cost | pass | 0.85 |

→ **pass 4 · partial 1 · fail 1**. partial을 0.5로 환산하면 통과 환산값 `(4 + 0.5)/6 ≈ 0.75`.

### 1.3 드리프트 입력 (drift_stability)

이 스냅샷 기간(직전 1기간) 동안 기록된 대체(supersession)는 **0건**입니다. 활성 규칙은 아직
초기 시드라 한 번도 갱신·대체되지 않았습니다(드리프트 팩 `user.drift_history`는 비어 있음).
초기 단계의 `drift_stability=1.0`은 "안정"이 아니라 **"아직 흔들릴 기회가 없었음"**으로 읽어야
합니다(아래 §3 해석 주의).

---

## 2. 여섯 지표 (계산식 + 현재 값)

각 지표는 [수렴 모델 §2](../../spec/06-convergence-model.md)의 정의를 그대로 적용했습니다.

| 지표 | 정의 (spec §2) | 계산 | 현재 값 | 방향 | 좋은 값 |
|------|----------------|------|:---:|:---:|:---:|
| `coverage` | 값이 채워진 팩 / 14 | 6 / 14 | **0.43** | ↑ | → 1.0 |
| ┗ (엄격: ≥3 확인) | ≥3 확인 레코드 팩 / 14 | 1 / 14 | (0.07) | ↑ | → 1.0 |
| `confirmation_ratio` | confirmed / (confirmed+pending+rejected) | 14 / (14+0+0) | **1.00** | ↑ | ≥ 0.6 |
| `decision_fidelity` | 통과 케이스 / 전체 케이스 | (4 + 0.5·1) / 6 | **0.75** | ↑ | ≥ 0.8 |
| `correction_cost` | 작업당 사용자 편집 비율(평균) | 아래 §2.1 | **NA**(도구) · ~0.21(추정) | **↓** | ≤ 0.2 |
| `drift_stability` | 1 − (전기간 대체수 / 확인 레코드수) | 1 − (0/14) | **1.00**\* | ↑ | ≥ 0.8 |
| `traceability` | 증거 보유 활성 규칙 / 활성 규칙 | 14 / 14 | **1.00** | = | **1.0 필수** |

\* 초기값이라 의미 제한적 — §3 해석 주의 참조.

> **`coverage`의 두 값에 대하여.** 수렴 모델 §2의 엄격 정의는 *"확인 레코드 ≥3개인 팩 수 / 14"*
> 입니다. 그 기준으로는 아직 `user.evaluation_cases` 한 팩만 충족해 **0.07**입니다. 반면 "팩에
> 값이 하나라도 들어갔는가(시드 폭)"로 보면 6/14 = **0.43**입니다. 이 리포트는 **표면 지표로
> 0.43**(폭)을 쓰되, L2/L3 게이트 판정에는 **엄격 0.07**을 쓰지 않고 — 대신 게이트 통과의 실질
> 병목이 "팩당 깊이(≥3)"임을 §4에서 명시합니다. (검증 스크립트
> [`../../tools/convergence_report.py`](../../tools/convergence_report.py)는 두 값을 모두
> 출력하도록 되어 있습니다.)

### 2.1 correction_cost 산출

`correction_cost`는 *낮을수록 좋은* 유일한 지표입니다. 평가 케이스 중 실제 사용자 편집 비율이
관측된 케이스의 편집 비율 평균으로 근사합니다.

- eval.004 (외부 발송): 확인 절차 누락 → 사실상 전면 재작업, 편집 비율 ≈ **0.40**
- eval.005 (보고 포맷): next action 누락 + 서두 → 부분 편집, 편집 비율 ≈ **0.10**
- eval.006 (재실행): 한 단어 어조 조정만 → 편집 비율 ≈ **0.12**

→ 관측 평균 `(0.40 + 0.10 + 0.12) / 3 ≈ 0.21`. 임계(≤0.2)에 **거의 근접**했으나 eval.004의
경계 실패가 평균을 끌어올리고 있습니다. eval.004를 통과시키면 곧장 `≈0.11`로 떨어집니다.

---

## 3. 해석 (지표가 말하는 것)

- **`confirmation_ratio`=1.00** — 추출 품질은 매우 높습니다. 채굴된 후보가 모두 승인됐다는 뜻
  이지만, *동시에* pending/rejected가 0이라는 것은 아직 **충돌하는 신호를 마주칠 만큼 다양한
  증거를 모으지 못했다**는 신호이기도 합니다. 표본이 커지면 자연히 1.0 아래로 내려올 값입니다.
- **`traceability`=1.00** — 타협 불가 조건을 충족합니다. 14개 활성 규칙 전부가 ≥1개
  `evidence_refs`를 가집니다(게이트 G1·G3). 이 값이 1.0인 것이 **L1 진입의 필수 조건**입니다.
- **`decision_fidelity`=0.75** — L2 임계(≥0.6)는 이미 넘었고 L3 임계(≥0.8)에 0.05 못 미칩니다.
  단일 실패(eval.004, 경계)와 단일 부분 통과(eval.005, 산출물)가 격차의 전부입니다.
- **`correction_cost`=0.21 / `drift_stability`=1.00** — **둘 다 아직 신뢰하기엔 표본이 얇습니다.**
  drift_stability=1.0은 "굳었다"가 아니라 "흔들릴 기회가 없었다"이고, correction_cost는 단 3개
  관측의 평균입니다. 이 두 지표는 세션이 누적돼야 비로소 의미 있는 곡선이 됩니다
  ([수렴 모델 §4](../../spec/06-convergence-model.md)의 두 곡선).

---

## 4. 성숙도 판정: **L0 Seed** (도구 판정 · L1까지 팩 하나 · L2 정조준)

[수렴 모델 §3](../../spec/06-convergence-model.md)의 사다리에 대입합니다(이 §은 **T0 베이스라인** —
상단 ⚙️ 노트대로 라이브 T2 도 **L0** 이지만 *빗장이 다릅니다*: T0=폭<7, T2=콘텐츠 깊이 0).

| 단계 | 진입 조건 | 이 스냅샷 (T0) | 판정 |
|------|-----------|-----------|:---:|
| **L0 Seed** | 3개 미만 팩 시드, 평가 케이스 없음 | 6개 팩 시드 + 6 평가 케이스 | **현재(도구)\*** |
| L1 Sketch | **≥7개 팩 시드**, ≥3개 평가 케이스, `traceability`=1.0, **콘텐츠 팩 ≥1개 ≥3 확인** | 6개 팩 시드(<7), 6 평가, traceability=1.0, 콘텐츠 깊이 0 | **폭<7 *그리고* 콘텐츠 깊이 0** |
| L2 Working | `coverage`≥0.5, `decision_fidelity`≥0.6, `human_confirmation_ratio`≥0.6 | 0.43 / 0.75 / 1.00 | coverage 미달 |
| L3 Reliable | coverage≥0.8, fidelity≥0.8, correction_cost≤0.3, drift_stability≥0.7 | 0.43 / 0.75 / ~0.21\*\* / 1.0\* | coverage·fidelity 미달 |
| L4 Convergent | coverage=1.0, fidelity≥0.9, cost≤0.15, drift≥0.85, trace=1.0, N기간 지속 | — | 미달 |

\* **왜 L0인가 (도구 판정).** 성숙도는 *완전히 충족한 가장 높은 단계*로 정합니다. 이 **T0** 스냅샷은
L1을 **두 조건에서** 미충족합니다 — **폭(6팩<7)** *그리고* **콘텐츠 깊이 vertical 0**(6개 팩 중 ≥3 확인
레코드를 가진 콘텐츠 팩이 없음; 유일한 ≥3 팩은 메타 eval). 따라서 자동 도구
([`convergence_report.py`](../../tools/convergence_report.py))는 이를 **L0 Seed**로 판정합니다.
다만 L0의 *문자적* 정의(<3팩·평가 0개)는 **이미 명백히 벗어났습니다**(6팩·6케이스·`traceability`=1.0).
(**라이브 T2**는 폭 10팩으로 ≥7을 넘었지만 *콘텐츠 깊이 vertical 0*은 그대로라 여전히 **L0** — 같은 등급,
빗장은 폭에서 깊이로 옮겨짐; 상단 ⚙️ 노트 참조.) §5의 **다음 한 수**는 한 *콘텐츠* 영역을 ≥3으로 깊게
채워 vertical 을 세우는 것이며(7번째 팩 시드만으로는 부족), 그래야 L1 이 확정되고 L2(coverage≥0.5)도 열립니다.
\*\* `correction_cost`는 (T0 스냅샷엔) 구조화된 작업별 교정 필드가 아직 비어 있어 **자동 도구는 NA**로
보고합니다. 아래 §2.1의 0.21은 관측 편집 비율에서의 **수동 추정**입니다.

요약: **도구 판정 L0 Seed, 그러나 L1·L2를 동시에 정조준.** L2의 세 조건 중
`decision_fidelity`(0.75≥0.6)와 `human_confirmation_ratio`(1.00≥0.6)는 이미 통과했고, **남은 병목은
`coverage`**(엄격 깊이; 0.43 은 시드폭, 게이트 목표 0.5) — 그리고 그 작업이 L1의 **콘텐츠 깊이 vertical**
(콘텐츠 팩 하나를 ≥3 으로)과 정확히 같습니다: 한 영역을 깊게 채우면 vertical 이 서고 coverage(깊이)도 오릅니다.

---

## 5. 한 칸 올리려면 무엇을 더해야 하나 (climb plan)

지표가 정확히 어디서 막혔는지 가리키므로, 다음 작업은 추측이 아니라 **타깃이 분명한 백로그**
입니다. 우선순위 순:

1. **엄격 `coverage`(깊이)를 ≥0.5로 — 한 콘텐츠 영역을 ≥3 깊이로** (L2 병목 *그리고* L1 vertical).
   게이트는 *시드폭*이 아니라 *엄격(≥3) 깊이*를 쓰므로, 팩을 새로 *시드*만 해선 게이트 coverage 가
   오르지 않는다 — 한 콘텐츠 팩을 **≥3 확인 레코드로 깊게** 채워야 한 칸이 오른다(=L1 vertical 도 동시 충족).
   평가 케이스가 이미 가리키는 두 팩이 깊이 1순위입니다:
   - **`user.boundary_authority`** — eval.004가 *요구*하는데 비어 있어 실패한 팩. `correction_notes`
     대로 `channel=external_email`용 `ConfirmationRuleRecord`(`action_boundary`, `authority=ask_confirm`)
     추가. → coverage·fidelity·correction_cost를 **한 번에** 끌어올림.
   - **`user.artifact_policy`** — eval.005가 부분 실패한 팩. 컴팩트 보고 레코드에 `next action`을
     필수 슬롯으로 narrow.

2. **`decision_fidelity`를 0.75 → ≥0.8로** (L3 선행). 위 1번이 곧 이 작업입니다:
   - eval.004를 fail → pass로 (경계 규칙 추가 후 `regression_for`로 회귀 고정).
   - eval.005를 partial → pass로 (`next action` 필수화).
   둘만 통과하면 `(6)/6 = 1.0`까지도 가능하나, 보수적으로 두 케이스 보정 시 ≥0.83.

3. **`correction_cost`를 0.21 → ≤0.2로** (L2엔 불필요, L3 임계 ≤0.3은 이미 통과).
   eval.004 경계 실패 제거가 평균을 0.21 → ≈0.11로 떨어뜨립니다(§2.1). 별도 작업 불필요 —
   1번의 부수 효과입니다.

4. **팩당 깊이(≥3 확인 레코드)를 늘려 엄격 `coverage`를 키우기** (L3 이후 본격 과제).
   현재 대부분 팩이 1~2 레코드뿐이라 엄격 정의(≥3)에서는 1/14입니다. L3의 coverage≥0.8을
   향하려면 11개 이상 팩을 각각 ≥3 레코드로 채워야 합니다 — 더 많은 세션·diff 채굴이 필요한
   장기 작업.

5. **`drift_stability`를 의미 있게 만들기** (L3 임계 ≥0.7, 현재 1.0은 표본 부족).
   초기 1.0은 신뢰할 수 없으므로, 여러 기간에 걸쳐 실제 대체가 발생하고도 안정도가 ≥0.7로
   **유지**되는지 확인해야 합니다. 이건 데이터를 더 추가하는 일이 아니라 **시간이 필요한** 일이고,
   그래서 L4가 "도달"이 아니라 "유지"인 이유입니다([수렴 모델 §3](../../spec/06-convergence-model.md)).

### 다음 한 수 (single next action)

> **한 *콘텐츠* 영역(예: `user.boundary_authority` 경계 규칙, 또는 `user.tacit_heuristics`)을
> ≥3 확인 레코드로 깊게 채워라.** 이 깊이 한 칸이 (a) L1의 **콘텐츠 깊이 vertical**을 세우고(7번째 팩
> 시드*만*으로는 부족 — vertical 은 ≥3 콘텐츠 깊이를 요구), (b) `coverage`(엄격 깊이)를 0.5 쪽으로 올려
> **L2를 정조준**하며, (c) 그 영역의 eval(예: eval.004)을 통과시켜 `decision_fidelity`·`correction_cost`도
> 함께 끌어올립니다. *깊이 우선*(overfit-tiny-set-first)이 단일 최고 레버리지입니다.

---

## 6. 재현 (reproduce)

이 리포트의 모든 숫자는 입력 YAML에서 결정론적으로 산출됩니다.

- 스크립트: [`../../tools/convergence_report.py`](../../tools/convergence_report.py) — 인스턴스
  레코드 + `user.evaluation_cases` + `user.drift_history`를 읽어 6개 지표와 성숙도 단계를 출력.
- 검증: [`../../tools/validate_packs.py`](../../tools/validate_packs.py) — 게이트 G1·G2·G5(FAIL)·
  G3(경고)와 베이스 스키마 적합성을 먼저 확인(traceability=1.0의 전제).
- OpenCrab: `opencrab_pack_qa` / `opencrab_project_run`으로 동일 지표를 산출
  ([수렴 모델 §5](../../spec/06-convergence-model.md)).

> 이 스냅샷은 한 시점입니다. 위 "다음 한 수"를 적용하고 다시 측정하면, 같은 표가 **숫자가 오른
> 채로** 재생성됩니다 — 그것이 수렴을 *보는* 방법입니다.

## 인접 문서

- 지표·단계 정의: [`../../spec/06-convergence-model.md`](../../spec/06-convergence-model.md)
- 평가 8지표·케이스 필드: [`../../spec/05-evaluation-drift.md`](../../spec/05-evaluation-drift.md)
- 입력 레코드: [`instance-records.yaml`](./instance-records.yaml) ·
  [`evaluation-cases.yaml`](./evaluation-cases.yaml)
- 어휘(게이트·노드·베이스 레코드): [`../../spec/01-kernel-schema.md`](../../spec/01-kernel-schema.md)
- 예제 개요: [`README.md`](./README.md)
