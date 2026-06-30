# 12 · 확인 정책 (Confirmation Policy — when promotion needs a human)

> **EN:** The confirmation gate ([skill 07](../skills/07-confirmation-gate.md)) asks for a human
> decision before any staged candidate becomes a runtime-active record. This document makes the
> *underlying decision rule* explicit: **when does promotion require human confirmation, and how
> are those thresholds set?** The answer is a regret-minimizing default-deny policy with four
> decision axes (impact tier · confidence · sensitivity · scope/dedup verdict), thresholds set in
> four layers (conservative default → user dial → calibration to a `target_error_rate` → a
> maturity gate). The autonomy method is grounded in publicly documented practice from Andrej
> Karpathy — Tesla **shadow mode** (validate predictions silently before they act), the
> **autonomy slider / "keep AI on a leash"** stance from his 2025 talk *Software Is Changing
> (Again)*, and the LLM-assisted-coding practices he has publicly advocated (organized here as
> four, notably *understand before accepting* — the enumeration is ours, not a fixed canon).
> Machine schema: the `auto_confirm_policy` object in
> [`../schemas/trigger.schema.json`](../schemas/trigger.schema.json).

이 문서는 [09 트리거](./09-triggers.md)와 [07 확인 게이트](../skills/07-confirmation-gate.md)가
공유하는 한 가지 질문에 **논리와 근거**를 부여합니다:

> **인스턴스 후보를 정식(런타임 활성) 레코드로 승격할 때, 어떤 조건에서 사람의 확인이
> 필요한가? 그 경계를 무엇을 근거로 정하는가?**

09는 *기본은 항상 확인, 좁은 예외만 auto-confirm*이라고 선언만 했습니다. 12는 그 예외의
**경계를 어떻게 긋고(논리) 무엇으로 정당화하는가(근거)**를 형식화합니다.

---

## 1. 핵심 원리 — 후회 최소화 (regret minimization)

승격을 자동화할지 사람에게 물을지는 **자동 승격이 틀렸을 때의 기대 후회**로 판단합니다.

```
regret(candidate) = impact(candidate) × (1 − confidence(candidate))
```

- `impact` = 그 레코드가 틀렸을 때의 **파급(blast radius)** — 에이전트의 *정체성*이나 *허용
  권한*을 바꾸는가, 아니면 표현 한 줄을 바꾸는가.
- `1 − confidence` = 추출 신뢰도의 여집합, 즉 **틀릴 확률의 대리값**.
- 규칙: **`regret`가 허용치(tolerance)를 넘으면 사람 확인을 강제**한다. 낮으면 정책이 정한
  좁은 조건에서 auto-confirm을 허용할 수 있다.

> 신뢰도 하나만으로는 부족합니다. 높은 `confidence`라도 *impact가 크면* `regret`가 커서 확인이
> 필요합니다 — 이것이 [07 §1](../skills/07-confirmation-gate.md)의 *"confidence는 참고치이지
> 승인 사유가 아니다"*를 수식으로 옮긴 형태입니다. confidence는 **필요조건의 하나**일 뿐,
> 단독 승인 사유가 아닙니다.

`regret`는 직관을 고정하는 *축*이고, 실제 게이트 결정은 이를 **네 축의 합취(AND)**로 분해합니다(§3) —
프라이버시(민감도)와 충돌(dedup)은 `regret` 수치와 무관하게 **하드 오버라이드**이기 때문입니다.

## 2. 임팩트 티어 — 14개 팩의 파급 등급

`impact`를 후보별로 매번 추정하는 대신, **목적지 팩(=후보 타입)**으로 티어를 고정합니다. 같은
팩의 레코드는 비슷한 파급을 갖기 때문입니다.

| 티어 | 의미 | 대상 팩 | 정책 |
|------|------|---------|------|
| **A — 항상 확인** | 틀리면 에이전트의 *정체성*·*결정 규칙*·*허용 경계*가 바뀜(되돌리기 비쌈) | `user.identity_roles` · `user.decision_policy` · `user.boundary_authority` · `user.red_flags` | **auto-confirm 영구 불가.** `never_auto_confirm_types`(`DecisionPolicyCandidate`·`BoundaryRuleCandidate` 등)와 동치 |
| **B — 성숙 시에만 자동** | 행동·휴리스틱·플레이북. 틀려도 회복 가능하나 잘못된 일반화 위험 | `user.persona_core` · `user.tacit_heuristics` · `user.workflow_playbooks` · `user.domain_overlays` · `user.memory_project_graph` | 성숙도 게이트(L2+) **그리고** 고신뢰일 때만 auto-confirm |
| **C — 고신뢰 시 자동** | 표현·산출물 형식·도구 선호. 파급 작고 즉시 교정 가능, 반복 잦음 | `user.communication_style` · `user.artifact_policy` · `user.tool_stack` | 고신뢰 + 비민감이면 auto-confirm 가능 |

> **나머지 2개 팩**(`user.evaluation_cases` · `user.drift_history`)은 *시스템/메타 산출물*이지
> 게이트를 거쳐 승격되는 페르소나 주장이 아닙니다 — 이 정책의 적용 대상이 아닙니다(N/A).
> (14 = 4 Tier A + 5 Tier B + 3 Tier C + 2 메타.)

**근거(Karpathy, 공개).** Tier A의 *항상 확인*은 그가 공개적으로 권한 LLM 코딩 실천(권위 있는 고정
'원칙' 목록이 아니라 여기선 4개 축으로 정리) 중 **"수용 전에 이해하라(understand before accepting)"**
를 고위험 변경에 적용한 것입니다 — *누가 에이전트인가/무엇을 해도 되는가*를 바꾸는 변경은 사람이
이해하고 받아들이기 전엔 절대 자동 승격하지 않습니다. 그의 *"AI를 목줄에 매어 두라(keep AI on a
leash)"*(2025 공개 강연 *Software Is Changing (Again)*) 입장과 동일한 보수성입니다.

## 3. 네 결정 축 (auto-confirm은 네 축이 모두 통과할 때만)

스테이징된 후보는 **아래 네 조건이 전부 참일 때에만** 사람 검토를 우회(auto-confirm)합니다.
하나라도 어기면 → [07 확인 게이트](../skills/07-confirmation-gate.md)의 사람 검토로 갑니다(기본).

| # | 축 | 통과 조건 | 게이트 |
|---|----|-----------|--------|
| 1 | **임팩트 티어** | 티어 B/C만 (A는 영구 불가) | G3 |
| 2 | **신뢰도** | `confidence ≥ per_tier_threshold[tier]` | — |
| 3 | **민감도** | `sensitivity ∈ {public, internal}` (restricted 불가, sensitive는 경계규칙 선행) | **G5** |
| 4 | **스코프·dedup 판정** | `novel`(삽입) 또는 `duplicate`(merge). **`conflict`는 항상 사람에게 노출**, `refinement`(supersede)는 정책상 검토 권장 | G2 |

- 축 3·4는 **하드 오버라이드**입니다 — `regret`가 아무리 낮아도, 민감하거나 기존 확정과
  **모순**되면 auto-confirm 불가([10 dedup·merge](./10-dedup-and-merge.md)의 `conflict`는 절대
  조용히 덮어쓰지 않음).
- 축 2의 `require_any`(강한 증거: 명시 발화 · 3회+ 반복 · 교정 기반) 조건도 함께 요구할 수
  있습니다([09 §5](./09-triggers.md)).

## 4. 경계를 정하는 법 — 4계층 (주장하지 말고 *측정*하라)

티어별 임계값을 자의적으로 박지 않습니다. 보수적 기본에서 출발해 **측정으로 좁힙니다.**

### 4.1 계층 1 — 보수적 기본 (default-deny)

정책이 없으면 **항상 사람 확인**. 자동화는 *옵트인*이며, 켜기 전까지 시스템은 [09 §4]의
스테이징/승격 경계만으로 안전합니다. 근거: Karpathy의 *vibe coding은 LLM 코딩 원칙으로
규율되어야 한다*는 공개 입장 — 무규율 자동화가 아니라 **기본은 목줄**.

### 4.2 계층 2 — 사용자 다이얼 (autonomy slider)

사용자가 자기 허용치를 정합니다. **그리고 그 설정 자체가 하나의
[`user.decision_policy`](./03-pack-catalog.md) / [`user.boundary_authority`](./03-pack-catalog.md) 레코드**입니다 —
즉 정책도 증거 결속·확인을 거친 레코드라서, "내 에이전트가 무엇을 스스로 해도 되는가"가
감사 가능하게 남습니다(자기참조적 안전장치). 이것이 Karpathy의 **자율성 슬라이더(autonomy
slider)** — 사람이 자율 폭을 손으로 쥐고 점진적으로 넓힙니다.

### 4.3 계층 3 — `target_error_rate`로의 캘리브레이션 (shadow mode)

임계값을 **단언하지 말고 보정**합니다. 목표 오류율(예: `target_error_rate ≤ 0.05`)을 정하고,
auto-confirm 정책을 **섀도 모드(shadow mode)** 로 돌립니다:

```
정책은 confirm/보류를 예측만 한다(PREDICT) — 실제로는 아무것도 승격하지 않는다(NO-ACT).
같은 후보에 대한 사람의 게이트 결정(ground truth)과 비교한다.
측정된 불일치율(disagreement rate)이 target_error_rate 이하로 안정될 때에만
그 티어에서 정책이 실제로 행동하도록 켠다.
```

- **근거(Karpathy/Tesla, 공개).** Tesla의 **shadow mode** — 새 모델 예측을 프로덕션 결정 *옆에서
  조용히* 돌려 배포 전에 검증하는 방식. 이 정책의 캘리브레이션은 그것의 1:1 차용입니다:
  auto-confirm을 *행동시키기 전에* 사람과의 일치율로 검증.
- **ground truth는 사람 흐름만.** 비교 기준은 *사람이 직접 게이트한 결정*뿐입니다 — 이미 auto-confirm된
  승격은 비교 대상에서 제외합니다(§4.4 순환 차단과 동일 원칙). 그래야 오라클이 정책 자신에 오염되지 않습니다.
- **근거(Karpathy, 공개 실천).** *자주 테스트하라* — 임계값은 측정 대상이지 가정이 아니다.
- 측정 도구는 [05 평가·드리프트](./05-evaluation-drift.md)의 충실도 지표 위에 얹습니다(불일치율 =
  정책 예측 vs 사람 결정의 오정렬).
- **정직한 한계 — 설계 단계.** 이 섀도 캘리브레이션 루프(불일치율 측정→임계 보정→행동 허용)는 *설계
  단계*다 — 라이브 런타임과 그 측정 도구가 생기면 실행된다(spec/02 S10½ 의 섀도 검증과 동일 상태).
  현재 결정론적 도구는 정적 레코드 위의 스키마·지표·선택 수학을 강제할 뿐, 라이브 불일치율을 측정하지
  않는다. 이 절은 *목표 행동의 명세*이지 구현된 자동화의 기술이 아니다.

### 4.4 계층 4 — 성숙도 게이트 (자율은 *획득*된다)

자율은 부여가 아니라 **획득**입니다. Tier B의 auto-confirm은 [06 수렴 모델](./06-convergence-model.md)의
성숙도 **L2 이상**에서, 그리고 §4.3 섀도 캘리브레이션이 그 티어에서 통과한 뒤에만 풀립니다.
**Tier C는 성숙도 게이트의 적용을 받지 않습니다**(§2) — 파급이 작고 즉시 교정 가능하므로 고신뢰·
비민감 조건만 충족하면 L0–L1에서도 auto-confirm 가능합니다. L0–L1에서 사람 검토가 기본인 것은
**Tier B**입니다(아직 캘리브레이션할 데이터가 부족).

**순환 차단 (이 게이트가 자기강화 루프가 되지 않는 이유).** 성숙도 게이트가 *그것이 통제하는
auto-confirm으로 부풀려지면* 독립적 신뢰 신호가 되지 못합니다. 그래서 게이트 신호는 auto-confirm이
**건드릴 수 없는** 것으로 둡니다:

- **사람 흐름만 센다.** auto-confirm으로 승격된 레코드는 성숙도 게이트 신호에서, 그리고 §4.3
  캘리브레이션의 ground truth에서 **제외**합니다. 게이트는 `confirmation_ratio`(분모에 auto-confirm
  포함)가 아니라 **사람이 직접 게이트한 흐름만** 센 `human_confirmation_ratio`(= 사람 게이트 confirm /
  사람 게이트 전체)를 씁니다. 그렇지 않으면 auto-confirm이 `confirmed` 분자를 스스로 밀어올려,
  *떨어졌어야 할* 성숙도를 가립니다(이것이 회피 대상 루프).
- **정책이 못 건드리는 1차 지표로 게이트한다.** Tier B 잠금해제는 [06 수렴 모델](./06-convergence-model.md)의
  `decision_fidelity`(사람 작성 평가 케이스[05](./05-evaluation-drift.md) 통과율)와 `correction_cost`를
  1차 기준으로 씁니다 — 둘 다 *런타임 행동이 사람의 정답과 얼마나 맞는가 / 교정에 얼마가 드는가*를
  재므로 auto-confirm 여부와 무관해 루프에 오염되지 않습니다. (spec/06의 L2 조건도 이미
  `decision_fidelity≥0.6`를 요구합니다.)

- **근거(Karpathy/Tesla, 공개 — 느슨한 유추).** **데이터 엔진 플라이휠**은 확정된(=레이블된) 데이터가
  쌓일수록 캘리브레이션 *재료*가 풍부해지는 흐름을 비유합니다. 단, *자율 폭을 넓히는* 주체는 데이터
  엔진 자체가 아니라 **자율성 슬라이더**(§4.2) — 데이터 엔진은 재료를 공급하고, 슬라이더가 성숙·
  캘리브레이션을 보고 자율을 *천천히* 엽니다.

## 5. 스키마 매핑 (`auto_confirm_policy` 4필드)

위 논리는 [`trigger.schema.json`](../schemas/trigger.schema.json)의 `auto_confirm_policy`에
네 필드로 직접 대응합니다(기존 `min_confidence`·`allowed_sensitivity`·`require_any`·
`never_auto_confirm_types`에 더해):

| 필드 | 타입 | 의미 | 대응 §|
|------|------|------|------|
| `impact_tier` | `"A"`/`"B"`/`"C"` (또는 팩→티어 매핑) | 이 후보/팩의 파급 등급. A는 영구 확인 | §2 |
| `per_tier_threshold` | `{ A,B,C: number }` | 티어별 `confidence` 최소 임계 (A는 사실상 불가, B 고임계, C 중임계) | §3 축2 |
| `maturity_gate` | `"L0".."L4"` | 이 정책이 *행동*해도 되는 최소 성숙도(주로 Tier B) | §4.4 |
| `target_error_rate` | `number` (0..1) | 섀도 캘리브레이션의 허용 불일치율. 측정치가 이하로 안정돼야 정책이 행동 | §4.3 |

> `per_tier_threshold`는 단일 `min_confidence`를 티어별로 **세분화**한 것입니다(하위호환:
> `min_confidence`만 있으면 모든 티어 공통 임계로 해석). 권장 기본: `{A: 1.01(불가), B: 0.95,
> C: 0.90}`, `maturity_gate: "L2"`, `target_error_rate: 0.05`.

예시(권장 보수 기본):

```yaml
auto_confirm_policy:
  impact_tier: B                       # 이 트리거가 다루는 후보의 파급 등급
  per_tier_threshold: { A: 1.01, B: 0.95, C: 0.90 }   # A는 도달 불가 → 항상 확인
  min_confidence: 0.9                  # 하위호환(티어 미지정 시 공통 임계)
  allowed_sensitivity: [public, internal]             # G5: restricted 불가
  require_any: [explicit_user_statement, repetition_ge_3, correction_backed]
  never_auto_confirm_types: [BoundaryRuleCandidate, DecisionPolicyCandidate]
  maturity_gate: L2                    # 성숙 L2+ 에서만 정책이 행동 (Tier B)
  target_error_rate: 0.05              # 섀도 불일치율 ≤5% 일 때만 실제 auto-confirm
```

## 6. 게이트 보존 (왜 안전한가)

- **G3** Tier A·미성숙·미캘리브레이션 후보는 절대 자동 승격되지 않음 — 사람 검토가 기본.
- **G5** `allowed_sensitivity`가 restricted를 영구 차단, sensitive는 경계규칙 선행. 민감도는
  `regret`와 무관한 하드 오버라이드.
- **G2** `refinement`/스코프 정밀화는 뭉개지 않고 supersede로, 다른 스코프는 다른 레코드.
- **충돌 불노출 금지** dedup `conflict`는 항상 사람에게 — 조용한 덮어쓰기 없음([10](./10-dedup-and-merge.md)).
- 따라서 정책은 프라이버시·휴먼인더루프 모델을 *약화*시키는 우회로가 아니라, **측정으로 보정된
  자율 노브**입니다. 켜기 전엔 보수적 기본, 켠 뒤에도 네 축 + 4계층이 경계를 지킵니다.

## 7. 근거 출처 (Karpathy, 공개 개념)

이 정책의 자율화 방법론은 Andrej Karpathy가 **공개적으로 제시한** 개념·실천에 근거합니다(사설
OpenCrab 팩 링크가 아니라 공개 개념의 인용이며, 일부는 흩어진 발언을 우리가 정리한 *합성*임을 밝힘):

- **Tesla shadow mode**(잘 문서화된 명명 개념) — 새 예측을 프로덕션 옆에서 조용히 돌려 *행동 전에*
  검증 → §4.3 캘리브레이션 방법론의 직접 차용.
- **Autonomy slider / "keep AI on a leash"**, *Software Is Changing (Again)*(2025 공개 강연) →
  §4.1 default-deny + §4.2 사용자 다이얼 + §4.4 점진적 자율 확대.
- **Karpathy가 공개적으로 권한 LLM 코딩 실천**(권위 있는 고정 '원칙' 목록이 아니라 우리가 4개 축으로
  정리: ① 작은 단위로 점진적 변경(컨텍스트를 작게) ② 자주 테스트 ③ 변경 인지 유지 ④ 수용 전 이해) →
  ④ = Tier A 항상 확인, ② = §4.3 측정 기반 임계, ③ = 감사 흔적(07 §4 [D]).
- **Data engine 플라이휠**(Tesla, *느슨한 유추*) → 확정(레이블)된 데이터가 쌓여 캘리브레이션 *재료*를
  공급하는 흐름. 자율을 넓히는 건 데이터 엔진이 아니라 슬라이더(§4.2)임(§4.4).

## 인접 문서
- 트리거의 2계층·스테이징/승격 경계·auto-confirm 정책 선언: [09 트리거](./09-triggers.md)
- 사람 검토 게이트의 여섯 액션·승격 규칙: [07 confirmation_gate](../skills/07-confirmation-gate.md)
- 충돌/중복 판정(축4의 dedup verdict): [10 중복 억제·병합](./10-dedup-and-merge.md)
- 성숙도 게이트(L0–L4)의 출처: [06 수렴 모델](./06-convergence-model.md)
- 캘리브레이션이 얹히는 평가 지표: [05 평가·드리프트](./05-evaluation-drift.md)
- 임팩트 티어 ↔ 팩 매핑의 원천(14팩): [03 팩 카탈로그](./03-pack-catalog.md)
- 프라이버시 하드 오버라이드(G5)의 경계 모델: [04 프라이버시·경계](./04-privacy-boundary.md)
- 머신 스키마(`auto_confirm_policy` 4필드): [`../schemas/trigger.schema.json`](../schemas/trigger.schema.json)
