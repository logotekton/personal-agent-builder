# 06 · 수렴 모델 (Convergence Model)

> **EN:** Convergence is the monotone accumulation of confirmed, evidence-bound, scoped
> records across the 14 packs, with **falling correction cost** and **stabilizing drift**.
> We measure it with six indices and five maturity tiers (L0–L4), so "my agent is becoming
> me" is a number you can watch climb — not a feeling. This is the participation hook.

이 프로젝트의 핵심 명제는 *"암묵지가 쌓이면 개인 에이전트로 수렴한다"*입니다. 명제가
설득력을 가지려면, **수렴을 측정**할 수 있어야 합니다. 이 문서가 그 측정 도구입니다.

## 1. 수렴이란 무엇인가

수렴(convergence)은 다음의 **단조 누적**입니다:

> 14개 팩에 걸쳐, **확인되고(confirmed)**, **증거에 묶이고(evidence-bound)**,
> **스코프가 지정된(scoped)** 레코드가 쌓이면서, **교정 비용은 내려가고** **드리프트는
> 안정화**되는 과정.

즉, 단순히 "데이터가 많아짐"이 아니라 — 에이전트의 출력이 점점 **당신의 승인 없이도 당신이
승인했을 모습**에 가까워지는 것입니다. 그것을 아래 6개 지표로 본다.

## 2. 여섯 가지 수렴 지표

| 지표 | 정의 | 방향 | 좋은 값 |
|------|------|------|---------|
| `coverage` | 확인 레코드 ≥3개인 팩 수 / 14 | ↑ | → 1.0 |
| `confirmation_ratio` | confirmed / (confirmed + pending + rejected) | ↑ | ≥ 0.6 |
| `decision_fidelity` | 통과한 평가 케이스 / 전체 평가 케이스 | ↑ | ≥ 0.8 |
| `correction_cost` | 작업당 사용자 편집 비율(평균) | **↓** | ≤ 0.2 |
| `drift_stability` | 1 − (최근 기간 대체수 / 확인 레코드수) | ↑ | ≥ 0.8 |
| `traceability` | 증거를 가진 활성 규칙 / 활성 규칙 | = | **1.0 필수** |

- `coverage`는 **폭** — 자기표현이 14개 영역에 고루 퍼졌는가.
- `confirmation_ratio`는 **포착 품질** — 추출이 실제로 승인되는가, 잡음만 많은가. **단, 성숙도 게이트는
  이 값이 아니라 `human_confirmation_ratio`(auto-confirm 승격을 분자·분모에서 제외한 *사람 게이트* 흐름만)를
  쓴다** — auto-confirm 이 `confirmed` 분자를 스스로 밀어올려 *떨어졌어야 할* 성숙도를 가리는 자기인증 루프를
  막기 위해서다([12 확인 정책 §4.4](./12-confirmation-policy.md), 베이스 레코드의 `auto_confirmed` 필드).
  auto-confirm 이 0건이면 둘은 같다.
- `decision_fidelity`는 **충실도** — 에이전트가 당신이 승인할 답을 고르는가([평가](./05-evaluation-drift.md)).
- `correction_cost`는 가장 정직한 지표 — *얼마나 덜 고치게 되었는가*. 유일하게 낮을수록 좋음.
- `drift_stability`는 **수렴의 증거** — 초기엔 대체가 잦고(높은 드리프트), 수렴할수록 잦아듦이
  줄어듦. 안정화 자체가 "굳어졌다"의 신호.
- `traceability`는 **타협 불가** — 항상 1.0. 증거 없는 활성 규칙은 존재해선 안 됨(게이트 G1·G3).

## 3. 다섯 단계 성숙도 (Maturity Tiers)

각 개인 에이전트는 아래 사다리를 오릅니다. 누구나 자기 위치를 알 수 있습니다.

| 단계 | 이름 | 진입 조건 |
|------|------|-----------|
| **L0** | Seed (씨앗) | 3개 미만 팩 시드, 평가 케이스 없음 |
| **L1** | Sketch (스케치) | ≥7개 팩 시드, ≥3개 평가 케이스, `traceability`=1.0 |
| **L2** | Working (작동) | `coverage`≥0.5, `decision_fidelity`≥0.6, `human_confirmation_ratio`≥0.6 |
| **L3** | Reliable (신뢰) | `coverage`≥0.8, `decision_fidelity`≥0.8, `correction_cost`≤0.3, `drift_stability`≥0.7 |
| **L4** | Convergent (수렴) | `coverage`=1.0, `decision_fidelity`≥0.9, `correction_cost`≤0.15, `drift_stability`≥0.85, `traceability`=1.0, **N기간 이상 지속** |

> L4는 "완성"이 아니라 **유지**입니다. 사람은 변하므로, 수렴은 한 번 도달하고 끝나는 점이
> 아니라 드리프트를 흡수하며 머무는 상태입니다. 그래서 `drift_history` 팩이 14개 중 하나입니다.

## 4. 왜 수렴하는가 (직관)

각 확인 레코드는 가능한 출력 공간을 **당신이 승인하는 영역으로 좁힙니다.** 교정(diff)은 가장
강한 신호입니다 — 당신이 직접 "이게 아니라 저거"라고 경계를 그었기 때문입니다. 레코드가
쌓일수록 남은 자유도가 줄고, 새 작업에서 에이전트가 틀릴 여지가 줄어듭니다. `correction_cost`가
내려가는 것이 이 과정의 직접 측정입니다. 동시에, 한 번 굳은 패턴은 잘 바뀌지 않으므로
`drift_stability`가 올라갑니다. 두 곡선이 만나는 지점이 수렴입니다.

```
교정비용 ┐                      드리프트 안정도 ┐                ___________  ← 수렴
        │\                                     │              /
        │ \___                                 │         ____/
        │     \____                            │     ___/
        │          \_______                    │  __/
        └───────────────────► 세션 누적         └────────────────────► 세션 누적
```

## 5. 계산 방법

[`tools/convergence_report.py`](../tools/convergence_report.py)가 한 사용자의 인스턴스 팩
집합을 읽어 6개 지표와 현재 성숙도 단계를 출력합니다. 입력은 [`schemas/`](../schemas)를 따르는
인스턴스 레코드, 평가 결과는 `user.evaluation_cases`, 드리프트는 `user.drift_history`에서
가져옵니다. OpenCrab에서는 `opencrab_pack_qa`/`opencrab_project_run`으로 동일 지표를 산출할 수
있습니다.

## 6. 참여 관점 — 왜 이게 매력적인가

- **자기 정량화(self-quantification)의 새 축**: 걸음 수가 아니라 *"내 판단이 얼마나 위임
  가능해졌는가"*를 봅니다.
- **소유와 이식성**: 지표는 당신 데이터에서 나오고, 팩은 당신 것입니다. 플랫폼을 떠나도
  스키마는 열려 있어 가져갈 수 있습니다.
- **공동 발전**: 14개 팩 스키마와 지표 정의가 공개이므로, 더 나은 지표·더 나은 채굴법을
  함께 개선할 수 있습니다. 당신의 인스턴스는 비공개로 두고 방법론만 공유합니다.


## 7. 효율·중복 신호 (Efficiency & dedup signals)

> 중복이 쌓이면 *노드가 많아도 retrieval 이 나빠져* `decision_fidelity` 가 깎입니다. 그래서 수렴은
> "많이 쌓였나"만이 아니라 "**얼마나 군더더기 없이 쌓였나**"로도 봅니다. 설계는
> [10 중복 억제와 병합](./10-dedup-and-merge.md), 도구는 [`../tools/dedup_check.py`](../tools/dedup_check.py).

| 지표 | 정의 | 방향 | 의미 |
|------|------|------|------|
| `redundancy_ratio` | 근접중복 레코드 쌍 / 전체 레코드 | ↓ (→0) | 높으면 블로트 경보(검색 잡음) |
| `pack_cardinality` | 주체의 인스턴스 팩 수 / 14 | =1.0 | >1 이면 팩 증식(세션마다 새 팩 = 안티패턴) |
| `merge_rate` | 병합 / (병합+삽입) | ↑ | 재유도가 기존 레코드로 흡수되는 비율 — **성숙·수렴의 직접 신호** |

`merge_rate` 상승은 "아직 발견 중 → 채워 넣는 중"으로의 전환을 뜻합니다. 즉 중복 억제는 청소가
아니라 **수렴을 보는 또 하나의 창**입니다. 이 신호들은 §2의 6개 핵심 지표를 보완하며, 특히
`traceability`(=1.0 필수)와 `decision_fidelity`를 떠받칩니다.
