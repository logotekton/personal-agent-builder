# 06 · 스코프·맥락 (Scope & Context)

> **EN:** Operating instructions for `skill.pab.scope_context` — the gate that turns a typed
> but *unscoped* candidate into a **scoped candidate**, owned by the **Scope Crab**. Its single
> job is to attach four things to every candidate: a non-empty `scope` (where/when it is true),
> an `applies_in` context, `exception_rules` (where it is *not* true), and a `temporal_status`
> (current / decaying / expired). An unscoped rule is the most dangerous artifact in the
> pipeline — a single accepted edit silently becomes a law applied everywhere — so this skill
> enforces **Gate G2 (no unscoped heuristic)** and actively fights over-generalization by
> narrowing breadth to the evidence actually on hand. It does *not* type the candidate (that is
> skill 05), does *not* confirm it (skill 07), and never writes a runtime rule (Gate G3).

스코프·맥락 지정은 [05 후보 추출](./05-candidate-extraction.md)이 만든 *타입은 정해졌지만 적용
범위가 비어 있는* 후보를, [07 확인 게이트](./07-confirmation-gate.md)로 넘기기 직전에
**언제·어디서 참인지를 못박는** 단계입니다. 빌더 파이프라인의 `scope_assign` 상태에 속합니다
([파이프라인 §3](../spec/02-builder-pipeline.md)). 추출이 "사용자가 *무엇을* 했는가"를 정했다면,
스코프는 "그게 *어디까지* 참인가"를 정합니다.

이 문서는 마케팅이 아니라 **그대로 실행하는 운영 지침**입니다. 어휘는
[커널 스키마](../spec/01-kernel-schema.md), 필드 규약은
[통합 베이스 레코드](../schemas/record.base.schema.json)와
[`candidate.schema.json`](../schemas/candidate.schema.json), 팩 정의는
[03 팩 카탈로그](../spec/03-pack-catalog.md)를 따르며 새 이름을 만들지 않습니다.

---

## 1. 목적 (Purpose)

스코프·맥락 지정은 **모든 후보에 적용 범위·맥락·예외·시간적 유효성을 붙이는** 단계입니다. 후보가
타입을 얻고도 *"항상, 어디서나 참"*인 채로 게이트를 통과하면, 한 번의 우연한 교정이 **전역 법칙**이
되어 무관한 맥락에까지 적용됩니다. "결론부터 써라"가 *리뷰 보고서*에서 나온 교정인데 스코프가
비어 있으면, 에이전트는 *법률 면책 고지*에서도 서론을 지웁니다. 그래서 스코프 지정의 단 하나의
책임은 **증거가 실제로 지지하는 범위만큼만 후보를 넓히는 것** — 즉 과일반화를 막는 것입니다.

후보마다 다음 네 가지를 붙입니다:

- **`scope`** — 이 규칙이 참인 *영역*. 비어 있으면 출력 금지(G2). 베이스 레코드 필수 필드.
- **`applies_in` (context)** — 어떤 *맥락 노드*(작업 종류·청중·산출물·도메인·채널)에서 켜지는가.
  [커널 §4](../spec/01-kernel-schema.md#4-엣지-타입-edge-types)의 `applies_in` 엣지로 표현.
- **`exception_rules`** — *명시적으로 참이 아닌* 경계. "단, ~일 때는 제외." 베이스 선택 필드이며,
  민감도가 `sensitive`/`restricted`이면 필수가 됩니다([record.base](../schemas/record.base.schema.json)).
- **`temporal_status`** — `current` / `decaying` / `expired`. 시간이 지나며 약해지거나 폐기될
  규칙의 유효성. 감쇠·폐기는 [11 평가·드리프트](./11-evaluation-drift.md)·`user.drift_history`로 잇습니다.

- **하는 일:** 후보의 증거를 읽어 *가장 좁은 정직한 범위*를 정하고, `scope`·`applies_in`·
  `exception_rules`·`temporal_status`를 채우고, 과일반화를 좁히고(narrow), 스코프를 확정해
  S07로 넘긴다.
- **하지 않는 일:** (1) 후보의 *타입*을 바꾸지 않는다 — 그것은 [05](./05-candidate-extraction.md).
  (2) 후보를 *승인/거부*하지 않는다 — 그것은 [07 확인 게이트](./07-confirmation-gate.md)이며,
  스코프는 사람이 검토하기 *쉽게* 만들 뿐이다. (3) 새 증거를 만들지 않는다. (4) 미확정 후보를
  런타임으로 올리지 않는다(G3).

> 한 줄 계약: **타입 지정된 미스코프 후보 → 스코프 지정된 후보.** 출력은 비어 있지 않은 `scope`,
> ≥1개 `applies_in` 맥락, 명시된 `exception_rules`(또는 "예외 없음" 근거), `temporal_status`를
> 반드시 가집니다.

## 2. 왜 미스코프 규칙이 위험한가 (G2)

게이트 **G2 — No unscoped heuristic**는 장식이 아니라 시스템 신뢰의 핵심입니다. 미스코프 규칙이
위험한 이유는 *조용하기* 때문입니다 — 어디서 깨지는지 아무도 모르는 채 전역에 적용됩니다.

- **단일 사례의 전역화.** 한 번의 교정·한 번의 발언은 *한 맥락의 증거*입니다. 스코프가 비면
  그 한 점이 *모든 맥락*의 법칙이 됩니다. 증거는 1점인데 적용 범위는 무한대 — 증거-적용 비율이
  깨집니다(G1의 정신을 G2가 공간 축에서 지킵니다).
- **충돌의 은폐.** 두 규칙이 서로 다른 맥락에서 참인데(예: "코드 리뷰엔 직설적으로" vs "고객
  메일엔 완곡하게") 둘 다 스코프가 비면, 런타임에서 충돌하고 *임의로* 하나가 이깁니다. 스코프가
  있으면 둘은 *다른 맥락*에 살며 충돌하지 않습니다.
- **드리프트의 비가시화.** 시간 한정이 없으면 *낡은* 규칙이 영원히 현역으로 남습니다. 사용자가
  6개월 전 선호를 바꿨는데 `temporal_status`가 없으면 폐기를 추적할 수 없습니다(§5).
- **검토 부담의 폭증.** 확인 게이트(S07)의 사람은 "이게 *어디서* 참인가"를 알아야 confirm할 수
  있습니다. 스코프가 비면 검토자가 매번 범위를 *상상*해야 하고, 그 추측이 곧 미검증 규칙이 됩니다.

그래서 이 스킬의 기본 자세는 **넓게 시작해 좁히는** 것이 아니라 **증거가 닿는 만큼만 좁게 시작해
필요할 때만 넓히는** 것입니다. 넓힘은 *반복 증거*나 *명시 확인*을 요구합니다(§4).

## 3. 작동 방식 (How it works)

스코프 크랩은 다음 다섯 동작을 순서대로 실행합니다 — **증거 범위 읽기 → 스코프 초안 → 맥락
사상 → 예외 추출 → 시간 유효성 판정**. 어느 동작에서도 증거를 넘어 범위를 확장하지 않습니다(G2).

```
   타입 지정된 미스코프 후보 (from S05)
        │
   [A] 증거 범위 읽기   ── evidence_refs가 실제로 닿는 맥락이 어디까지인가
        ▼
   [B] 스코프 초안     ── 가장 좁은 정직한 scope 문장 작성 (비어 있으면 금지, G2)
        ▼
   [C] 맥락 사상       ── applies_in Context 노드 연결 (작업·청중·산출물·도메인·채널)
        ▼
   [D] 예외 추출       ── exception_rules: 규칙이 깨지는 경계 + 반례 (counterexamples)
        ▼
   [E] 시간 유효성     ── temporal_status = current / decaying / expired 판정
        ▼
   스코프 지정된 후보 → S07 확인 게이트
```

**[A] 증거 범위 읽기.** 후보의 `evidence_refs`를 펼쳐 *그 증거가 실제로 관찰된 맥락*을 봅니다.
세 건의 교정이 전부 *코드 리뷰* 세션에서 나왔다면, 증거가 지지하는 범위는 "코드 리뷰"이지 "모든
글쓰기"가 아닙니다. **범위는 증거에서 읽어내는 것이지 후보 문장에서 추론하는 것이 아닙니다.**

**[B] 스코프 초안.** *가장 좁은 정직한 범위*를 한 문장으로 씁니다. 좁힘의 축은 보통: 작업 종류
(리뷰/초안/요약/결정), 청중(내부/고객/공개), 산출물(코드/보고서/메일), 도메인(`linked_domains`와
정렬), 채널, 단계. 비어 있으면 출력 금지(G2). "항상"·"모든"·"언제나" 같은 전역 양화사는 *증거가
정말 전역적일 때만* 허용하고, 그때도 §4의 넓힘 조건을 만족해야 합니다.

**[C] 맥락 사상.** 스코프를 *기계가 켜고 끌 수 있는* `Context` 노드로 사상해 `applies_in` 엣지로
연결합니다([커널 §4](../spec/01-kernel-schema.md#4-엣지-타입-edge-types)). `scope`가 사람용 산문이라면
`applies_in`은 런타임용 스위치입니다 — 컴파일러([10 agent_compiler](./10-agent-compiler.md))가 이
맥락 매칭으로 *어떤 슬라이스를 켤지* 결정합니다. 한 후보가 여러 맥락에 걸치면 다중 `applies_in`을
달되, 그 자체가 *과일반화 신호*이니 쪼갤 수 있는지 검토합니다(§4 규칙 2).

**[D] 예외 추출.** 규칙이 *깨지는* 경계를 `exception_rules`로 명시합니다. "결론부터 — 단,
*법적 고지·계약 문구*에서는 정해진 서식을 따름." 예외는 두 곳에서 옵니다: (1) 증거 안의 반례
([04 diff 마이닝](./04-diff-mining.md)의 `anti_examples`/버려진 before), (2) 충돌하는 다른 후보
와의 경계. 예외를 *명시*하면 충돌이 런타임이 아니라 *여기서* 해소됩니다. 민감
(`sensitive`/`restricted`) 후보는 `exception_rules`가 필수입니다([record.base](../schemas/record.base.schema.json)).

**[E] 시간 유효성 판정.** `temporal_status`를 셋 중 하나로 정합니다(§5). 갓 들어온 후보는 대개
`current`, 더 최근 증거와 충돌하는 옛 패턴은 `decaying`, 사용자가 명시적으로 철회했거나 후속
레코드가 `supersedes`한 것은 `expired`. `expired`는 런타임 비활성이며 `user.drift_history`로 이관
사유를 남깁니다([11 평가·드리프트](./11-evaluation-drift.md)).

## 4. 스코프 좁힘 (Narrowing — 과일반화 방지)

이 스킬의 *판단 핵심*은 "이 후보를 얼마나 넓게 잡을 것인가"입니다. 원칙은 **증거가 지지하는
만큼만**. 넓힘은 비용을 요구하고, 좁힘은 기본값입니다.

| 좁힘 축 | 질문 | 좁히는 방향 |
|---------|------|-------------|
| **작업 종류** | 어떤 작업에서 관찰됐나 (리뷰/초안/요약/결정)? | 한 작업 종류에서만 봤으면 그 작업으로 한정 |
| **청중/노출** | 내부·고객·공개 중 어디인가? | 내부 교정을 고객 채널로 확장하지 말 것 |
| **산출물** | 코드·보고서·메일·표 중 무엇에 대한 규칙인가? | 산출물 객체로 한정 (artifact_policy 정렬) |
| **도메인** | 도메인 특화인가 범용인가 (`domain_specificity`)? | 높으면 `user.domain_overlays`로 한정·라우팅 |
| **시간** | 최근 패턴인가 옛 패턴인가 (`recency`)? | 옛것이면 `decaying`, 철회됐으면 `expired` |

**넓힘 조건 (운영 규칙):**

1. **기본은 좁게.** 한 점의 증거에서 전역 규칙을 만들지 않습니다. 단일 증거 후보는 *그 증거의
   맥락*으로 스코프를 한정합니다. 넓힘은 (a) 서로 다른 맥락의 **반복 증거**(`repetition_count`↑)나
   (b) 검토자의 **명시 확인**(S07)이 있을 때만 허용합니다.
2. **다중 맥락은 쪼갬 신호.** 한 후보가 너무 많은 `applies_in`을 요구하면, 그것은 *하나의 넓은
   규칙*이 아니라 *여러 좁은 규칙*일 가능성이 큽니다. 쪼갤 수 있으면 쪼개 각 맥락에 정확한 스코프를
   답니다. 못 쪼개면 신뢰도를 낮춰 게이트에 `narrowed` 후보로 넘깁니다.
3. **충돌은 좁힘으로 해소.** 두 후보가 상충하면 보통 *둘 다 참이되 다른 맥락*입니다. 스코프를
   좁혀 서로 다른 `applies_in`에 살게 하면 충돌이 사라집니다 — 한쪽을 버릴 필요가 없습니다.
4. **반례 보존.** `confidence < 0.7`인 후보는 승격 시 `counterexamples`가 필수입니다
   ([record.base](../schemas/record.base.schema.json)). 좁힘 과정에서 발견한 "여기선 안 통함"
   사례를 그대로 `counterexamples`/`exception_rules`로 남깁니다 — 좁힘의 부산물이 곧 반례입니다.

## 5. 시간적 유효성 (Temporal status)

`temporal_status`는 규칙이 *시간 축에서* 얼마나 살아 있는지를 표시합니다. 공간 스코프(`scope`)가
"어디서 참인가"라면 시간 상태는 "아직도 참인가"입니다.

| 상태 | 의미 | 트리거 | 런타임 효과 |
|------|------|--------|-------------|
| **`current`** | 현재 유효, 최근 증거와 정합 | 갓 확정됐거나 최근 증거가 재확인 | 정상 활성 (스코프 안에서) |
| **`decaying`** | 약해지는 중, 더 최근 증거와 부분 충돌 | `recency`↓ + `contradiction_count`↑, 부분 모순 | 활성이되 신뢰도↓·재확인 대기, 충돌 시 양보 |
| **`expired`** | 폐기, 더는 적용 안 함 | 사용자 명시 철회 또는 후속 레코드가 `supersedes` | 런타임 **비활성**, 이력만 보존 |

운영 규칙:

1. **감쇠는 삭제가 아니다.** `decaying`은 후보를 버리지 않습니다 — 신뢰도를 낮추고 재확인을
   기다립니다. 옛 선호도 *그 시기*에는 참이었으므로 이력으로 가치가 있습니다.
2. **폐기는 이력을 남긴다.** `expired`로 넘길 때는 *왜* 폐기됐는지(철회·대체)를
   `user.drift_history`의 `DriftRecord`로 남기고 `supersedes`로 후속 레코드와 잇습니다
   ([커널 §4](../spec/01-kernel-schema.md#4-엣지-타입-edge-types) `supersedes`,
   [11 평가·드리프트](./11-evaluation-drift.md)).
3. **드리프트는 스코프 크랩이 *표시*만 한다.** 실제 감쇠/폐기 *판정과 측정*은
   [11 평가·드리프트](./11-evaluation-drift.md)의 `drift_score`가 담당합니다. 스코프 크랩은 후보를
   넘길 때 1차 시간 상태를 달 뿐, 드리프트 지표를 계산하지 않습니다(경계).

## 6. 입력 / 출력 (Inputs / Outputs)

### 입력

- **주 입력:** [05 후보 추출](./05-candidate-extraction.md)이 만든 *타입 지정된 미스코프*
  `CandidateAssertion` — `candidate_type`, `concise_claim`, `evidence_refs`, 1차 `confidence`,
  `proposed_target_pack`을 가지되 `scope`가 초안이거나 비어 있는 후보.
- **부 입력(선택):** 같은 맥락의 기존 확정 레코드(스코프 정합·충돌 점검), 활성 `Context` 노드
  목록(맥락 재사용), 충돌 후보(좁힘으로 분리), `user.drift_history`(옛 패턴과의 비교).

### 출력

각 후보는 다음 네 필드가 채워진 채 S07로 넘어갑니다:

- `scope` — 비어 있지 않은, *가장 좁은 정직한* 범위 문장(G2). 베이스 레코드 필수 필드.
- `applies_in` — ≥1개 `Context` 노드로의 `applies_in` 엣지(런타임 스위치).
- `exception_rules` — 규칙이 깨지는 경계 목록(또는 "예외 없음"의 명시적 근거). 민감 후보는 필수.
- `temporal_status` — `current` / `decaying` / `expired`(§5).
- (보강) `counterexamples` — 좁힘 중 발견한 반례. `confidence < 0.7`이면 필수.
- (보강) `linked_domains` — 도메인 특화 시 `user.domain_overlays` 정렬·라우팅 힌트.
- `extraction_method`/프로비넌스는 보존하며 변경하지 않습니다([candidate.schema.json](../schemas/candidate.schema.json)).

> 이 출력은 [S07 확인 게이트](./07-confirmation-gate.md)의 입력 계약을 만족합니다. 거기서 사람이
> confirm / edit / reject / **narrow** / sensitive / defer를 정하며, `narrow`는 스코프 크랩이
> 준비한 범위를 사람이 *더* 좁히는 동작입니다.

### 최소 예시 (스코프 지정된 후보 — S07로 넘김)

```json
{
  "candidate_id": "logotekton.candidate.041",
  "candidate_type": "CommunicationStyleCandidate",
  "concise_claim": "사용자가 3문단 배경 서론을 한 줄 결론으로 교체하고 근거를 뒤로 옮겼다",
  "evidence_refs": ["logotekton.evidence.088", "logotekton.evidence.089"],
  "proposed_target_pack": "user.communication_style",
  "confidence": 0.55,
  "scope": "코드 리뷰 보고서 초안 (내부 청중)",
  "applies_in": ["context.task.code_review", "context.audience.internal"],
  "exception_rules": [
    "법적 고지·계약 문구에서는 정해진 서식을 따른다",
    "고객 대면 요약에서는 1문장 맥락 서론을 허용한다"
  ],
  "temporal_status": "current",
  "counterexamples": ["evidence.088: 동일 사용자가 외부 제안서에서는 서론을 유지했다"],
  "extraction_method": "diff_mining"
}
```

증거 두 건이 모두 *코드 리뷰* 맥락에서 나왔으므로 `scope`를 "모든 글쓰기"가 아니라 "코드 리뷰
보고서 초안"으로 한정했습니다. `applies_in`은 그 범위를 런타임 스위치로 사상하고,
`exception_rules`는 규칙이 깨지는 두 경계를 못박아 다른 맥락의 후보와 충돌하지 않게 합니다.
`confidence`가 0.7 미만이라 `counterexamples`가 채워졌고, 옛 패턴과 충돌이 없으므로
`temporal_status`는 `current`입니다.

## 7. 품질 검사 (Quality checks)

출력 전에 스코프 크랩은 다음을 강제합니다. 코드 강제는
[`tools/validate_packs.py`](../tools/validate_packs.py)가 보조합니다.

- [ ] **비어 있지 않은 스코프(G2)** — 모든 후보가 비어 있지 않은 `scope`를 가지는가. "항상/모든"
  같은 전역 양화사를 *증거 없이* 쓰지 않았는가.
- [ ] **증거가 범위를 지지하는가** — `scope`의 넓이가 `evidence_refs`가 실제로 닿는 맥락을 넘지
  않는가. 단일·동일 맥락 증거로 전역 규칙을 만들지 않았는가(§4 규칙 1).
- [ ] **맥락 사상** — ≥1개 `applies_in` `Context`로 연결돼 런타임이 켜고 끌 수 있는가. 과도한
  다중 맥락이면 쪼갬을 검토했는가(§4 규칙 2).
- [ ] **예외 명시** — 규칙이 깨지는 경계가 `exception_rules`에 있는가. 충돌하는 후보가 *다른
  맥락*으로 분리됐는가(§4 규칙 3). 민감 후보(`sensitive`/`restricted`)는 `exception_rules`가
  채워졌는가([record.base](../schemas/record.base.schema.json)).
- [ ] **시간 상태** — `temporal_status`가 셋 중 하나로 정해졌는가. `expired`이면 `supersedes`/
  `DriftRecord`로 이력이 남는가(§5).
- [ ] **반례 준비** — `confidence < 0.7`이면 `counterexamples`가 채워졌는가. 좁힘 중 발견한
  "여기선 안 통함" 사례를 보존했는가.
- [ ] **행동 언어만(G4)** — `scope`·`exception_rules`가 *관찰된 맥락*으로 기술되고 추측 심리를
  단정하지 않는가.
- [ ] **경계 준수** — 타입(S05)·승인/거부(S07)·라우팅(S08)을 침범하지 않았는가. 미확정 후보를
  런타임으로 올리지 않았는가(G3). 드리프트 *측정*은 [11](./11-evaluation-drift.md)에 맡겼는가.

## 8. Crab 역할 — Scope Crab

이 스킬의 소유 역할은 **Scope Crab**입니다([12 crab 오케스트레이션](./12-crab-orchestration.md),
[커널 §8](../spec/01-kernel-schema.md#8-crab-에이전트-역할-운영-모델)).

- **소유 작업:** `scope_assign` 상태에서 타입 지정된 후보에 `scope`·`applies_in`·
  `exception_rules`·`temporal_status` 부착, 과일반화 좁힘, 충돌 후보의 맥락 분리.
- **받는 핸드오프:** **Candidate Extractor**(S05)가 타입을 확정한 미스코프 후보. 채굴 트리오
  (S02·S03·S04)가 단 *스코프 초안 가설*을 입력으로 받아 정제합니다.
- **넘기는 핸드오프:** 스코프 지정된 후보 → **Confirmation Crab**(S07). 후보가 옛 패턴과
  충돌해 감쇠/폐기로 보이면 **Orchestrator**가 **Evaluator**(S11)에 드리프트 측정을 요청할 수
  있습니다.
- **경계:** 타입(S05)·승인/거부(S07)·라우팅(S08)을 침범하지 않습니다. 증거를 넘어 범위를
  확장하지 않으며(G2), 드리프트 *지표*를 계산하지 않고(S11에 위임), 미확정 후보를 런타임으로
  올리지 않습니다(G3).

OpenCrab 도구로 실행할 때는 `opencrab_get_node_context`/`opencrab_query`로 후보의 증거 맥락을
조회해 가장 좁은 범위를 읽고, 기존 `Context` 노드는 `opencrab_search_nodes`로 재사용하며,
스코프·맥락을 채운 후보를 `opencrab_pack_update`로 후보 단계에 반영한 뒤 S07로 핸드오프합니다.
민감 후보의 처리는 [04 프라이버시·경계](../spec/04-privacy-boundary.md)의 권한 레벨을 따릅니다.

> 9-space 사상: 후보가 사상되는 `claim`은 *방어가능(defeasible)*하며, 그 방어가능성의 핵심이
> 바로 스코프입니다. `scope`/`applies_in`은 `concept`·`policy` 공간의 적용 경계를,
> `exception_rules`는 `policy`의 예외를, `temporal_status`는 `outcome`/드리프트로의 다리를
> 이룹니다([07 9-space 크로스워크](../spec/07-opencrab-9space-crosswalk.md)).

## 9. 관련 문서

- 라이프사이클·노드·엣지·게이트(특히 G2)·맥락 사상 → [01 커널 스키마](../spec/01-kernel-schema.md)
- 이 스킬이 속한 12단계 파이프라인 계약(`scope_assign`) → [02 빌더 파이프라인](../spec/02-builder-pipeline.md)
- 직전 단계(타입 지정 후보 생성) → [05 후보 추출](./05-candidate-extraction.md)
- 직후 단계(사람 검토: confirm/edit/reject/narrow/sensitive/defer) → [07 확인 게이트](./07-confirmation-gate.md)
- 스코프 초안 가설을 다는 채굴 트리오 → [02 세션 마이닝](./02-session-mining.md) ·
  [03 질문](./03-elicitation-questioning.md) · [04 diff 마이닝](./04-diff-mining.md)
- 후보/필드의 기계 스키마 → [`candidate.schema.json`](../schemas/candidate.schema.json) ·
  [`record.base.schema.json`](../schemas/record.base.schema.json)
- 시간 감쇠·폐기의 측정·이력 → [11 평가·드리프트](./11-evaluation-drift.md) (`user.drift_history`)
- 라우팅 도착지인 14개 팩 → [03 팩 카탈로그](../spec/03-pack-catalog.md)
- 민감·경계 후보의 권한·경계 처리 → [04 프라이버시·경계](../spec/04-privacy-boundary.md) ·
  [09 privacy_boundary](./09-privacy-boundary.md)
- 역할·상태·핸드오프 운영 모델 → [12 crab 오케스트레이션](./12-crab-orchestration.md)
