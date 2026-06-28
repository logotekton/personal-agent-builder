# 05 · 후보 추출 (Candidate Extraction)

> **EN:** Operating instructions for `skill.pab.candidate_extraction` — the builder skill that
> turns upstream evidence signals (from skills 01–04) into typed, evidence-bound
> `CandidateAssertion` records. It is the pivot of the pipeline: where session-mining, the
> interview, and diff-mining produce *untyped* signals, this skill **classifies** each into one
> of the 14 candidate types, writes a behavioral `concise_claim`, attaches its `evidence_refs`
> (Gate G1), assigns `confidence` from explicit `confidence_inputs`, sets a `sensitivity` class,
> proposes the single `proposed_target_pack` fixed by the 1:1 router, and emits a record valid
> against [`candidate.schema.json`](../schemas/candidate.schema.json). It never confirms, never
> finalizes scope, and never writes a runtime rule — it hands the typed candidate to scope_context
> (skill 06) and then the confirmation_gate (skill 07).

후보 추출은 빌더 파이프라인의 **경첩(pivot)**입니다. 채굴 트리오([02 세션마이닝](./02-session-mining.md) ·
[03 질문](./03-elicitation-questioning.md) · [04 diff마이닝](./04-diff-mining.md))는 *타입 미지정
신호*를 쏟아내고, 이 스킬은 그 신호를 받아 **타입 지정된 `CandidateAssertion`**으로 정제합니다.
즉, "무언가 반복된다"를 "이것은 `CommunicationStyleCandidate`이고, `user.communication_style`로
라우팅될 것이며, 이 증거들이 떠받친다"로 바꾸는 단계입니다.

이 문서는 마케팅이 아니라 **그대로 실행하는 운영 지침**입니다. 어휘는 [커널 스키마](../spec/01-kernel-schema.md)를
따르며 새 이름을 만들지 않습니다. 기계 계약은 [`candidate.schema.json`](../schemas/candidate.schema.json)이며,
이 문서의 모든 필드는 그 스키마의 필드와 1:1로 대응합니다.

---

## 1. 목적 (Purpose)

상류(S01–S04)에서 온 증거 신호를, [커널 §6의 14개 후보 타입](../spec/01-kernel-schema.md#6-후보-타입--라우팅-11-전수)
중 정확히 하나로 분류하고, 각 후보에 증거를 묶어 신뢰도·스코프 자리표시자·민감도·제안 팩을 채운
**검증 가능한 `CandidateAssertion`**으로 내보낸다.

- **하는 일:** (1) 신호를 14개 타입 중 하나로 분류, (2) 관찰 행동 언어로 `concise_claim` 작성,
  (3) `evidence_refs` 부착(게이트 G1), (4) `confidence_inputs` → `confidence` 산정,
  (5) `sensitivity` 분류, (6) `proposed_target_pack`을 1:1 라우터로 고정, (7) `scope` 자리표시자
  설정, (8) `extraction_method` 프로비넌스 기록, (9) [S06 스코프](./06-scope-context.md)로,
  이어 [S07 확인 게이트](./07-confirmation-gate.md)로 핸드오프.
- **하지 않는 일:** (1) **확인하지 않는다** — confirm/reject/narrow는 [S07](./07-confirmation-gate.md)의 일이다.
  (2) **스코프를 확정하지 않는다** — 자리표시자만 두고 [S06](./06-scope-context.md)이 확정한다(게이트 G2).
  (3) **팩에 적재하지 않는다** — 라우팅은 [S08 pack_router](./08-pack-router.md)가, 확인된 후보에만 한다(게이트 G3).
  (4) **새 증거를 만들지 않는다** — 증거 포착은 [S01](./01-evidence-capture.md)의 몫이다.
  (5) **런타임 규칙을 만들지 않는다.**

> 출력은 **타입 지정 + 증거 결속 + 신뢰도 + 제안 팩**을 가진 후보다. `CandidateAssertion`은
> 베이스 레코드가 *아니다* — 더 가벼운 후보 계약을 쓰며 `concise_claim`/`validation_status`를
> 쓰고, 승격(S08) 때 `statement`/`review_status`로 매핑된다([candidate.schema.json](../schemas/candidate.schema.json)
> `$comment`).

## 2. 작동 방식 (How it works)

후보 추출기는 다음 7단계를 신호마다 순서대로 실행한다. 각 단계는 다음 단계 및
[`candidate.schema.json`](../schemas/candidate.schema.json)의 입력 계약을 만족시킨다.

```
   상류 신호 (S02 세션마이닝 / S03 질문 / S04 diff마이닝)
        │
   [A] 정규화 읽기(read normalized)   ── 신호 + 동반 evidence_refs + 신뢰도 입력을 읽음
        ▼
   [B] 신호 분류(classify)            ── 14개 candidate_type 중 정확히 하나로 (§3 분류 규칙)
        ▼
   [C] 타입 지정 후보 생성(create)    ── candidate_id 부여 + concise_claim(관찰 언어, G4)
        ▼
   [D] 증거 부착(attach evidence)     ── evidence_refs ≥ 1 (게이트 G1), 빈 채로는 생성 금지
        ▼
   [E] 신뢰도 + 스코프 자리표시자      ── confidence_inputs → confidence; scope 가설; sensitivity 분류
        ▼                                  proposed_target_pack = 1:1 라우터(type 고정)
   [F] 스코프로 송부(→ scope_context) ── S06이 scope를 확정 (게이트 G2)
        ▼
   [G] 확인 게이트로 송부(→ gate)      ── S07이 confirm/edit/reject/narrow/sensitive/defer
```

**[A] 정규화 읽기.** 상류 신호를 읽는다. 각 신호는 이미 `concise_claim`(초안)·`evidence_refs`·
`confidence_inputs`·제안 팩 가설·`scope` 초안을 동반한다([S02 §5 출력](./02-session-mining.md#5-입력--출력-inputs--outputs)).
추출기는 이 묶음을 *재포착*하지 않고 정제한다. `extraction_method`는 신호의 출처 스킬을 그대로
기록한다(`session_mining`/`elicitation_questioning`/`diff_mining`/`evidence_capture`/`manual`/`other`).

**[B] 신호 분류.** 신호를 14개 `candidate_type` 중 **정확히 하나**로 분류한다(§3 분류 규칙·결정
트리). 분류가 곧 라우팅을 결정한다 — `candidate_type`이 정해지면 `proposed_target_pack`은
[1:1 전수 라우터](../spec/01-kernel-schema.md#6-후보-타입--라우팅-11-전수)에 의해 *유일하게* 고정되며,
스키마의 `allOf` if/then 규칙이 둘의 불일치를 거부한다. 한 신호가 두 타입에 걸치면 §3.2의 우선순위
규칙으로 가르고, 정말로 갈라지면 두 후보로 분할한다.

**[C] 타입 지정 후보 생성.** 안정 `candidate_id`(`<subject>.<recordkind>.NNN`, 예
`logotekton.heuristic_cand.014`)를 부여하고 `concise_claim`을 한 문장으로 쓴다. **관찰된 행동
언어만** 쓴다(게이트 G4): "사용자는 장황함을 싫어한다(추측 심리)"가 아니라 "사용자가 3개 세션에서
서론 문단을 삭제하도록 교정했다(관찰)". 문장은 *스코프 가능하고 검증 가능*해야 한다 —
"짧은 걸 좋아함"이 아니라 "코드리뷰 맥락에서 불릿 위주의 간결한 답변을 선호".

**[D] 증거 부착.** 후보를 떠받치는 모든 `EvidenceItem`을 `evidence_refs`로 묶는다(`minItems: 1`,
게이트 G1). **증거를 가리키지 못하는 후보는 생성하지 않는다** — 추측은 후보가 아니다. 참조는 상류
신호의 것을 그대로 옮기되, 추출기가 같은 주장을 떠받치는 추가 증거를 발견하면 합쳐 `repetition_count`를
높인다.

**[E] 신뢰도 + 스코프 자리표시자.** §4의 7개 `confidence_inputs`를 채우고 그로부터 0..1 `confidence`를
산정한다 — 입력을 남겨 점수를 *감사 가능*하게 한다(블랙박스 숫자 금지). `sensitivity`를
{public, internal, sensitive, restricted}로 1차 분류한다(민감/제한은 G5로 표시). `scope`는
상류 가설을 옮긴 **자리표시자**로 둔다(확정은 S06, 게이트 G2). `proposed_target_pack`은 [B]의
타입에서 라우터로 채운다 — 추측이 아니라 표 조회다.

**[F] 스코프로 송부.** 타입 지정 후보를 [S06 scope_context](./06-scope-context.md)로 넘긴다. 거기서
"언제/어디서 참인가"가 확정되고 예외·시간 유효성이 붙으며, 비어있지 않은 `scope`가 강제된다(G2).

**[G] 확인 게이트로 송부.** 스코프가 확정된 후보를 [S07 confirmation_gate](./07-confirmation-gate.md)로
넘긴다. 사람이 confirm/edit/reject/narrow/sensitive/defer를 결정하며, 이것이 `validation_status`를
정한다. **확인 전엔 어떤 후보도 팩에 들어가지 않는다(게이트 G3).**

## 3. 14개 후보 타입과 분류 규칙 (Candidate types & classification)

분류는 이 스킬의 핵심 판단이다. [커널 §6](../spec/01-kernel-schema.md#6-후보-타입--라우팅-11-전수)의
14개 타입은 14개 팩에 **1:1 전수**로 라우팅되므로, 타입을 고르는 것이 곧 목적지를 고르는 것이다.

### 3.1 타입 ↔ 라우팅 표 (관찰 신호 → 타입 → 팩)

| candidate_type | 무엇을 잡는가(관찰 신호) | → proposed_target_pack |
|----------------|---------------------------|------------------------|
| `IdentityRoleCandidate` | "나는 ~로서 일한다", 역할·정체성·맥락 진술 (대개 [S03 질문](./03-elicitation-questioning.md)에서) | `user.identity_roles` |
| `PersonaTraitCandidate` | 안정적 선호/반선호/가치/작업 성향 | `user.persona_core` |
| `CommunicationStyleCandidate` | 응답 형식·언어·구조·밀도(길이·불릿·서론 유무) | `user.communication_style` |
| `ArtifactPolicyCandidate` | 결과물 *형태* 선호(표·파일·코드블록·리뷰보드) | `user.artifact_policy` |
| `DecisionPolicyCandidate` | 우선순위·트레이드오프·승인/거부 조건·에스컬레이션 | `user.decision_policy` |
| `TacitHeuristicCandidate` | 반복 행동·교정·대조에서 드러난 암묵 판단 규칙 | `user.tacit_heuristics` |
| `RedFlagCandidate` | 사용자가 위험·약한 구조·빈약한 근거로 *집어내는* 신호 | `user.red_flags` |
| `WorkflowPatternCandidate` | 같은 작업을 같은 단계 순서로 반복 수행 | `user.workflow_playbooks` |
| `DomainOverlayCandidate` | 특정 도메인에서만 나타나는 용어·검사·주의 패턴 *(구 코드명 DomainSpecificCandidate)* | `user.domain_overlays` |
| `ToolPreferenceCandidate` | 도구·언어·라이브러리·명령의 반복 선택 | `user.tool_stack` |
| `BoundaryRuleCandidate` | 외부 노출·민감 주제·비가역 행동 앞에서의 멈춤/확인 요구 | `user.boundary_authority` |
| `ProjectMemoryCandidate` | 프로젝트·목표·메모리 링크, 세션을 넘는 미해결 목표 *(구 코드명 ProjectGoalCandidate)* | `user.memory_project_graph` |
| `EvaluationCaseCandidate` | "이렇게 했어야 했다 / 이건 절대 안 된다" 형태의 충실도 기준 (대개 [S11 평가](./11-evaluation-drift.md)에서) | `user.evaluation_cases` |
| `DriftRecordCandidate` | 옛 신호와 모순되는 최근 신호, 대체·감쇠·변경 이동 | `user.drift_history` |

> `IdentityRoleCandidate`·`EvaluationCaseCandidate`·`DriftRecordCandidate`는 채굴(S02/S04)의
> *주된* 산출이 아니라 각각 질문(S03)·평가 루프(S11)에서 주로 온다([S02 §3 주석](./02-session-mining.md#3-마이닝-타깃-무엇을-찾는가)).
> 추출기는 출처와 무관하게 신호의 *내용*으로 타입을 정한다.

### 3.2 분류 결정 규칙 (경계가 모호할 때)

타입이 겹쳐 보이는 흔한 경우의 가르기 규칙:

1. **형식 vs 형태:** *어떻게 말하는가*(길이·구조·언어)는 `CommunicationStyleCandidate`,
   *무엇을 산출하는가*(표·파일·리뷰보드 객체)는 `ArtifactPolicyCandidate`.
2. **선호 vs 규칙:** 안정적 *성향*("간결을 가치로 둠")은 `PersonaTraitCandidate`,
   조건부 *판단 규칙*("테스트 없으면 머지 거부")은 `TacitHeuristicCandidate` 또는
   `DecisionPolicyCandidate`. 우선순위/트레이드오프가 핵심이면 후자.
3. **휴리스틱 vs 레드플래그:** "이럴 땐 이렇게 한다"(긍정적 행동 규칙)는 `TacitHeuristicCandidate`,
   "이건 위험 신호다"(부정적 탐지 신호)는 `RedFlagCandidate`.
4. **경계 vs 결정:** 권한·프라이버시·확인 요구(런타임이 무엇을 *해도 되는가*)는
   `BoundaryRuleCandidate`, 선택지 간 우선순위(무엇을 *고를 것인가*)는 `DecisionPolicyCandidate`.
5. **도메인 특화 우선:** `domain_specificity`가 높고(≈1) 신호가 특정 도메인에 묶이면
   일반 팩 대신 `DomainOverlayCandidate`를 우선한다.
6. **모순은 드리프트:** 신호가 기존 확정 레코드와 *모순*되면 새 타입으로 만들기 전에
   `DriftRecordCandidate`로 표시하고 `contradiction_count`를 올린다(§4·§6).
7. **정말 갈라지면 분할:** 한 신호가 두 타입을 동등하게 담으면(예: 형식 선호 + 도구 선호)
   **두 개의 후보로 분할**하고 각각 자기 증거를 가리키게 한다. 억지로 한 타입에 욱여넣지 않는다.

### 3.3 필수 필드 (Required fields)

모든 `CandidateAssertion`은 [`candidate.schema.json`](../schemas/candidate.schema.json)의 다음
10개 필수 필드를 가진다(커널 §8):

| 필드 | 의미 | 게이트/규칙 |
|------|------|-------------|
| `candidate_id` | 안정 식별자 `<subject>.<recordkind>.NNN` | 승격 시 베이스 `id`로 매핑 |
| `candidate_type` | 14개 타입 중 하나(§3.1) | 라우팅을 결정 |
| `concise_claim` | 관찰 행동 언어의 한 문장 | **G4** (추측 심리 금지); 승격 시 `statement`로 |
| `evidence_refs` | ≥1개 `EvidenceItem` 참조 | **G1** (증거 없는 후보 금지) |
| `confidence` | 0..1 추출 신뢰도 | `confidence_inputs`에서 산정(§4) |
| `scope` | 적용 범위(자리표시자) | **G2**; 확정은 [S06](./06-scope-context.md) |
| `sensitivity` | public/internal/sensitive/restricted | **G5**; 민감 시 승격 전 `BoundaryRule` |
| `proposed_target_pack` | 단일 목적지 팩 | 1:1 라우터로 고정(타입과 불일치 금지) |
| `validation_status` | 확인 게이트 상태 | 초기 `pending`; 정함은 [S07](./07-confirmation-gate.md) |
| `extraction_method` | 출처 스킬 프로비넌스 | session_mining/elicitation_questioning/diff_mining/… |

선택 필드 `confidence_inputs`(§4의 7개 신호)는 강력히 권장된다 — 신뢰도를 감사 가능하게 만들고
도구가 `confidence`를 재계산할 수 있게 한다.

## 4. 신뢰도 입력 (Confidence inputs)

`confidence`는 손으로 찍는 숫자가 아니라 **7개 입력에서 산출**되며, 입력은 `confidence_inputs`로
남겨 감사 가능하게 한다([candidate.schema.json](../schemas/candidate.schema.json) 동일 어휘, 커널 §8).

| 입력 | 의미 | 신뢰도 방향 |
|------|------|-------------|
| `explicit_statement` | 사용자가 직접 명시했는가("항상 X") vs 행동에서 추론 | 명시 = true → ↑ |
| `repetition_count` | 후보를 독립적으로 떠받치는 서로 다른 증거 수 | 반복 ↑ → ↑ |
| `correction_strength` | 교정 신호의 강도(0..1) — 얼마나 단호히 바꿨/거부했는가 | 강한 교정 ↑ → ↑ |
| `recency` | 근거 증거의 최근성(1 = 가장 최근) | 최근 ↑ → ↑ (드리프트 신호) |
| `contradiction_count` | 후보와 충돌하는 증거 수 | ↑ → ↓ (게이트에서 narrowed/deferred 유발) |
| `domain_specificity` | 후보가 도메인에 묶인 정도(0..1) | `user.domain_overlays` 라우팅·스코프 좁힘 판단 |
| `evidence_quality` | 인용 증거의 직접성/품질(0..1) | verbatim 교정 > 느슨한 추론 → 보정 |

**산정 원칙 (운영 규칙):**

1. **교정 > 수용 > 추론.** 사용자가 *바로잡은* 행동(`correction_strength`↑)이 가장 무겁다.
   [S04 diff마이닝](./04-diff-mining.md)에서 온 후보는 보통 강한 교정 신호를 동반한다.
2. **최근·명시가 최고.** 최근의 명시적 지시(`recency`≈1 + `explicit_statement`=true)는 최고
   신뢰도를 받는다. 옛 암묵 신호와 충돌하면 최근 명시를 우선하고 옛 신호는 `DriftRecordCandidate`로 표시.
3. **신뢰도 ≠ 채택 확신.** `confidence`는 "이 후보가 사용자를 충실히 반영한다"는 *추출* 신뢰도이지
   "이게 규칙이어야 한다"는 확신이 아니다 — 규칙 채택은 사람이 [S07](./07-confirmation-gate.md)에서 정한다.
4. **낮은 신뢰도는 반례를 부른다.** `confidence < 0.7`이면 승격된 베이스 레코드는 `counterexamples`가
   필수다([record.base.schema.json](../schemas/record.base.schema.json)). 추출기는 이를 내다보고
   낮은 신뢰도 후보에 반례 후보를 함께 표시한다.

## 5. 입력 / 출력 (Inputs / Outputs)

### 입력

- **주 입력:** 채굴 트리오([S02](./02-session-mining.md) / [S03](./03-elicitation-questioning.md) /
  [S04](./04-diff-mining.md))의 *타입 미지정 신호* — 각 신호는 `concise_claim`(초안)·`evidence_refs`·
  `confidence_inputs`·제안 팩 가설·`scope` 초안을 이미 동반한다. 추출기는 이를 정제하지 재포착하지 않는다.
- **부 입력(선택):** 이전 라운드의 확정 레코드(중복·모순 비교용), 활성 팩 커버리지(어느 팩이
  비었는지 → 분류 시 참고), [03 팩 카탈로그](../spec/03-pack-catalog.md)의 팩별 정의(타입 분류 근거).

### 출력

각 출력은 [`candidate.schema.json`](../schemas/candidate.schema.json)에 대해 **검증을 통과하는**
`CandidateAssertion`이다:

- `candidate_id` — 안정 식별자(§3.3).
- `candidate_type` — 14개 중 하나(§3.1).
- `concise_claim` — 관찰 행동 언어 한 문장(G4).
- `evidence_refs` — ≥1개 `EvidenceItem`(G1, 빈 채로는 출력 금지).
- `confidence` + `confidence_inputs` — §4의 7개 입력으로 산정한 0..1 신뢰도와 그 근거.
- `scope`(자리표시자) + `sensitivity` 분류(민감/제한은 G5로 표시).
- `proposed_target_pack` — 1:1 라우터로 타입에서 고정된 단일 팩.
- `validation_status = pending` — 초기 상태(정함은 S07).
- `extraction_method` — 출처 스킬 프로비넌스.

> 이 출력은 [S06 스코프](./06-scope-context.md)의 입력 계약을 만족한다. S06이 `scope`를 확정한
> 뒤 [S07 확인 게이트](./07-confirmation-gate.md)가 `validation_status`를 정하고, confirmed/narrowed
> 후보만 [S08 pack_router](./08-pack-router.md)로 승격되어 베이스 레코드가 된다(필드 매핑:
> `candidate_id`→`id`, `concise_claim`→`statement`, `validation_status`→`review_status`).

## 6. 품질 검사 (Quality checks)

출력 전, 후보 추출기는 다음을 강제한다. 위반 시 그 후보는 생성을 막거나 신뢰도를 낮춘다.
코드 강제는 [`tools/validate_packs.py`](../tools/validate_packs.py)와
[`candidate.schema.json`](../schemas/candidate.schema.json)이 보조한다.

- [ ] **단일 타입(전수성)** — 모든 후보가 14개 `candidate_type` 중 *정확히 하나*인가. 두 타입에
  걸치면 §3.2로 가르거나 분할했는가.
- [ ] **타입↔팩 정합** — `proposed_target_pack`이 `candidate_type`의 1:1 라우터 값과 일치하는가
  (스키마 `allOf`가 불일치를 거부; 추측으로 채우지 않음).
- [ ] **증거 결속(G1)** — `evidence_refs`가 ≥1개인가. 증거를 못 가리키는 후보를 만들지 않았는가.
- [ ] **행동 언어(G4)** — `concise_claim`이 *관찰된 행동*만 기술하는가. "싫어한다/때문이다" 같은
  추측 심리·동기를 단정하지 않았는가.
- [ ] **검증 가능성** — `concise_claim`이 스코프 가능하고 확인 게이트에서 *체크 가능*한가
  ("짧은 걸 좋아함" 같은 막연한 문장이 아닌가).
- [ ] **신뢰도 감사 가능(투명성)** — `confidence`가 `confidence_inputs`에서 도출됐고 입력이
  남아 있는가. 블랙박스 숫자가 아닌가.
- [ ] **낮은 신뢰도 반례** — `confidence < 0.7` 후보에 반례를 표시해 승격 시 `counterexamples`
  요건을 내다봤는가(베이스 레코드 규칙).
- [ ] **스코프 자리표시자(G2 예비)** — `scope`가 자리표시자로라도 비어있지 않은가. 확정은
  [S06](./06-scope-context.md)에 넘겼는가(여기서 확정하지 않음).
- [ ] **민감도 표시(G5 예비)** — 민감/제한 신호의 `sensitivity`가 상향됐는가. [09 프라이버시
  경계](./09-privacy-boundary.md)가 승격 전 `BoundaryRule`을 붙일 수 있게 표시했는가.
- [ ] **중복·모순 점검** — 기존 확정 레코드와 중복이면 신규 증거로 표시(`repetition_count`↑),
  모순이면 `DriftRecordCandidate`로 돌리고 `contradiction_count`↑.
- [ ] **상태 불변식** — `validation_status = pending`으로만 출력했는가. 확인/스코프 확정/라우팅을
  침범하지 않았는가(G3).

## 7. Crab 역할 — Candidate Extractor Crab

이 스킬의 소유 역할은 **Candidate Extractor Crab**입니다([12 crab 오케스트레이션](./12-crab-orchestration.md),
[커널 §8](../spec/01-kernel-schema.md#8-crab-에이전트-역할-운영-모델)).

- **소유 작업:** 상류 신호를 14개 타입 중 하나로 분류하고, `concise_claim` 작성·증거 부착·신뢰도
  산정·민감도 분류·제안 팩 고정을 거쳐 검증 가능한 `CandidateAssertion`을 생성.
- **핸드오프 (받음):** 채굴 트리오 형제 —
  [Session Miner](./02-session-mining.md)·[Questioning Crab](./03-elicitation-questioning.md)·
  [Diff Miner](./04-diff-mining.md) — 가 만든 타입 미지정 신호 + 그 `EvidenceItem` 참조.
- **핸드오프 (넘김):** 타입 지정 후보를 [Scope Crab](./06-scope-context.md)으로(스코프 확정),
  이어 [Confirmation Crab](./07-confirmation-gate.md)으로(사람 검토). 라우팅은 확인 뒤
  [Pack Router](./08-pack-router.md)가 맡는다.
- **하지 않는 것:** 확인·스코프 확정·라우팅·런타임 활성화는 이 역할의 일이 아니다. Candidate
  Extractor Crab은 *신호에 타입과 증거와 신뢰도를 부여*할 뿐, *그 의미를 확정*하지 않는다.
  그 절제가 게이트 G1·G2·G3·G4·G5의 토대를 놓는다.

> 9-space 사상: 후보가 떠받치는 **증거 발췌**는 `evidence`, 후보의 `concise_claim`(방어 가능·
> 증거 결속의 잠정 주장)은 `claim`으로 사상된다([07 9-space 크로스워크](../spec/07-opencrab-9space-crosswalk.md)).
> 확정 전이므로 아직 `concept`/`policy`로 굳지 않는다 — 그 굳힘은 확인·라우팅 뒤다.

OpenCrab 도구로 실행할 때는 `opencrab_query`/`opencrab_search_documents`로 상류 신호와 그 증거를
조회하고, 타입 지정 후보를 `opencrab_ingest_text`로 후보 단계 노드에 적재한 뒤 S06으로 핸드오프한다.
권한·민감도 판단은 [04 프라이버시·경계](../spec/04-privacy-boundary.md)의 권한 레벨을 따른다.

## 8. 관련 문서

- 14개 후보 타입·1:1 라우팅·노드·엣지·게이트·라이프사이클 어휘 → [01 커널 스키마](../spec/01-kernel-schema.md)
- 이 단계가 속한 파이프라인 계약 → [02 빌더 파이프라인](../spec/02-builder-pipeline.md)
- 후보의 기계 계약(필드·confidence_inputs·1:1 라우터 강제) → [`candidate.schema.json`](../schemas/candidate.schema.json)
- 승격 후 형태인 통합 베이스 레코드 → [`record.base.schema.json`](../schemas/record.base.schema.json) · [커널 §7](../spec/01-kernel-schema.md#7-통합-베이스-레코드-필드-표류-해소)
- 후보를 만들어주는 상류 스킬 → [02 session_mining](./02-session-mining.md) ·
  [03 elicitation_questioning](./03-elicitation-questioning.md) · [04 diff_mining](./04-diff-mining.md)
- 후보를 받는 하류 단계 → [06 scope_context](./06-scope-context.md) · [07 confirmation_gate](./07-confirmation-gate.md) · [08 pack_router](./08-pack-router.md)
- 라우팅 도착지인 14개 팩 → [03 팩 카탈로그](../spec/03-pack-catalog.md)
- 민감 후보가 받는 경계 규칙 → [04 프라이버시·경계](../spec/04-privacy-boundary.md) · [09 privacy_boundary](./09-privacy-boundary.md)
- 역할·상태·핸드오프 운영 모델 → [12 crab 오케스트레이션](./12-crab-orchestration.md)
