# 08 · 팩 라우팅 (Pack Router)

> **EN:** Operating instructions for `skill.pab.pack_router` — the step that takes a
> **confirmed** (or `narrowed`/edited) candidate from the confirmation gate and **promotes** it
> into exactly one of the 14 `user.*` ontology packs, owned by the **Pack Router Crab**. It does
> one thing: read the candidate's `candidate_type`, look it up in the **1:1 total router**
> (contract §6 — all 14 types map to all 14 packs, no fan-out), and write a base instance record
> into that single pack. It never decides *whether* a candidate is true (that was skill 07) and
> never extracts or scopes (skills 05/06). Above all it enforces **Gate G3 (no runtime
> activation of pending candidates)**: a candidate whose `validation_status` is `pending`,
> `rejected`, `sensitive` (blocked on a BoundaryRule), or `deferred` is **rejected at the door**
> — only `confirmed`/`narrowed`/edited candidates may enter a pack. Clean 1:1 routing is what
> keeps retrieval precise: each pack stays a single typed slice the runtime can switch on.

팩 라우팅은 [07 확인 게이트](./07-confirmation-gate.md)가 **승인한** 후보를, 그 타입이 가리키는
*정확히 하나의* `user.*` 팩으로 **승격(promote)**시키는 단계입니다. 빌더 파이프라인의
`route` 상태에 속합니다([파이프라인 §3](../spec/02-builder-pipeline.md)). 추출이 "*무엇을*
했는가"(S05), 스코프가 "*어디까지* 참인가"(S06), 게이트가 "*이걸 규칙으로 삼을까*"(S07)를
정했다면, 라우터는 그 확정된 후보를 ***어느 서랍에* 넣을지** 정하고 실제로 넣습니다.

이 문서는 마케팅이 아니라 **그대로 실행하는 운영 지침**입니다. 어휘는
[커널 스키마](../spec/01-kernel-schema.md), 라우팅 표는 [캐노니컬 계약 §6], 후보 필드는
[`candidate.schema.json`](../schemas/candidate.schema.json), 도착지 레코드 필드는
[통합 베이스 레코드](../schemas/record.base.schema.json), 팩 정의는
[03 팩 카탈로그](../spec/03-pack-catalog.md)를 따르며 새 이름을 만들지 않습니다.

---

## 1. 목적 (Purpose)

팩 라우팅은 **확정된 후보를 단 하나의 도착지 팩으로 보내고, 후보 계약을 베이스 레코드로
승격하는** 단계입니다. 라우터의 책임은 *정확히 하나의 팩 선택*과 *깨끗한 승격*, 이 둘뿐입니다.

- **단일 도착지 선택.** `candidate_type`을 [§3 라우팅 표](#3-라우팅-표-11-전수)에 넣어 *정확히
  하나의* `user.*` 팩을 얻습니다. 매핑은 1:1·전수(total)이므로 추측·분기·복수 도착지가 없습니다.
  후보가 이미 들고 있는 `proposed_target_pack`은 *제안*일 뿐, 라우터가 타입으로 다시 검산해
  불일치를 잡습니다(§5).
- **후보 → 레코드 승격.** 가벼운 후보 계약([candidate.schema.json](../schemas/candidate.schema.json))을
  도착지 팩의 베이스 레코드([record.base.schema.json](../schemas/record.base.schema.json))로
  변환합니다. 필드 매핑은 §4. 승격된 레코드는 도착지 팩의 `record_type`을 얻고, 그 팩의
  JSON Schema로 검증됩니다.

- **하는 일:** (1) `validation_status` 게이트 통과 여부 확인(G3), (2) `candidate_type`으로 단일
  도착지 팩 결정, (3) `proposed_target_pack`과의 정합 검산, (4) 후보 필드를 베이스 레코드로 매핑,
  (5) 도착지 팩 스키마로 검증, (6) `promoted_to` 엣지로 후보↔팩을 잇고 프로비넌스 보존.
- **하지 않는 일:** (1) 후보가 *참인지* 판정하지 않는다 — 그것은 [07 확인 게이트](./07-confirmation-gate.md).
  (2) 타입을 *부여/변경*하지 않는다 — 그것은 [05 후보 추출](./05-candidate-extraction.md). 도착지가
  틀렸다고 느끼면 라우팅을 멈추고 S05로 *되돌릴* 뿐, 여기서 재분류하지 않는다(§5 규칙 3). (3)
  스코프를 다시 정하지 않는다 — 그것은 [06 스코프·맥락](./06-scope-context.md). (4) **미확정 후보를
  팩에 넣지 않는다(G3).** (5) 컴파일하지 않는다 — 런타임 활성은 [10 agent_compiler](./10-agent-compiler.md).

> 한 줄 계약: **확정된 타입 지정 후보 → 정확히 한 `user.*` 팩 안의 베이스 레코드.** 출력은
> 도착지 팩 스키마를 통과하고, `id`/`statement`/`review_status`로 승격되며, `promoted_to`
> 엣지로 출처 후보를 가리킵니다. `confirmed`/`narrowed`/편집된 후보만 통과합니다(G3).

## 2. 왜 1:1 라우팅이 검색 정밀도를 지키는가

팩을 14개로 쪼개고 후보를 *정확히 하나*로 보내는 것은 행정 편의가 아니라 **검색 정밀도와
거버넌스의 핵심 장치**입니다([README 설계 원칙 5](../README.md), 마이크로 팩 분리).

- **각 팩이 단일 타입 슬라이스로 유지된다.** `user.communication_style`에는 *오직* 소통 스타일
  레코드만, `user.red_flags`에는 *오직* 위험 신호만 들어옵니다. 그래서 컴파일러
  ([10](./10-agent-compiler.md))가 맥락에 맞는 *슬라이스만* 켤 수 있습니다 — "코드 리뷰" 맥락이면
  스타일·위험·휴리스틱 팩만 로드하고 무관한 팩은 끕니다. 한 팩이 여러 타입을 섞으면 이 선택적
  로딩이 무너지고 무관한 규칙이 끌려 들어옵니다.
- **검색이 타입으로 좁혀진다.** 라우팅이 1:1이면 "위험 신호를 보여줘"는 `user.red_flags` *한
  팩*만 조회하면 됩니다. 만약 위험 신호가 세 팩에 흩어져 있으면 매 검색이 전수 스캔이 되고
  정밀도(precision)가 떨어집니다. 1:1 라우팅 = 팩 = 검색 단위.
- **거버넌스가 팩 단위로 작동한다.** 프라이버시 경계([09](./09-privacy-boundary.md)), 평가
  ([11](./11-evaluation-drift.md)), 드리프트 추적은 *팩별로* 정책을 겁니다. 타입이 한 팩에 모여
  있어야 "권한 팩(`user.boundary_authority`) 전체에 확인 게이트를 강제"같은 규칙이 성립합니다.
- **승격이 멱등(idempotent)·감사가능해진다.** 도착지가 결정적(deterministic)이면 같은 후보를 두
  번 라우팅해도 같은 팩·같은 레코드로 가고, `promoted_to` 엣지로 *어느 증거→어느 후보→어느 팩*
  경로를 역추적할 수 있습니다(추적성=1.0, [수렴 모델](../spec/06-convergence-model.md)).

요컨대 라우터가 *지루하고 결정적*일수록 시스템 전체의 검색·거버넌스·감사가 정확해집니다.
라우팅에 "판단"이 끼어드는 순간(예: 한 후보를 두 팩에 복제) 정밀도가 깨집니다.

## 3. 라우팅 표 (1:1, 전수)

아래는 [캐노니컬 계약 §6]·[커널 스키마 §6](../spec/01-kernel-schema.md#6-후보-타입--라우팅-11-전수)의
**유일한 라우팅 표**입니다. 14개 후보 타입이 14개 팩에 1:1로 전수 사상되며, 라우터는 이 표
*그대로*를 룩업할 뿐 변형하지 않습니다. 후보의 `proposed_target_pack`은 이 표로 검산됩니다.

| # | `candidate_type` | → 도착지 `user.*` 팩 | 무엇을 담는 팩인가 | 구 코드명 |
|---|------------------|---------------------|--------------------|-----------|
| 1 | `IdentityRoleCandidate` | `user.identity_roles` | 역할·정체성·맥락 | pa.roles *(신규 — 누락이었음)* |
| 2 | `PersonaTraitCandidate` | `user.persona_core` | 안정 선호/가치/우선순위 | pa.core |
| 3 | `CommunicationStyleCandidate` | `user.communication_style` | 응답 형식·언어·구조 | pa.t03 |
| 4 | `ArtifactPolicyCandidate` | `user.artifact_policy` | 선호 출력물 형태 | pa.t04 |
| 5 | `DecisionPolicyCandidate` | `user.decision_policy` | 우선순위·거부·승인 규칙 | pa.t05 |
| 6 | `TacitHeuristicCandidate` | `user.tacit_heuristics` | 암묵 판단 규칙 | t06 |
| 7 | `RedFlagCandidate` | `user.red_flags` | 위험 신호 | t07 |
| 8 | `WorkflowPatternCandidate` | `user.workflow_playbooks` | 반복 작업 시퀀스 | t08 |
| 9 | `DomainOverlayCandidate` | `user.domain_overlays` | 도메인 특화 지식 | t09 *(구 DomainSpecificCandidate)* |
| 10 | `ToolPreferenceCandidate` | `user.tool_stack` | 도구·사용 패턴 | t10 |
| 11 | `BoundaryRuleCandidate` | `user.boundary_authority` | 프라이버시·권한 규칙 | t11, .ba |
| 12 | `ProjectMemoryCandidate` | `user.memory_project_graph` | 프로젝트·목표·메모리 | x12 *(구 ProjectGoalCandidate)* |
| 13 | `EvaluationCaseCandidate` | `user.evaluation_cases` | 충실도 테스트 케이스 | x13 |
| 14 | `DriftRecordCandidate` | `user.drift_history` | 변경·버전 이력 | x14 |

규칙:

1. **전수성(totality).** 14개 타입 *모두*가 정확히 한 도착지를 가집니다 — 라우팅 실패("어디로
   보낼지 모름")가 존재하지 않습니다. 도착지를 못 찾았다면 후보의 `candidate_type`이 14개 중
   하나가 아니라는 뜻이고, 이는 라우팅이 아니라 *추출(S05)*의 결함입니다(§5 규칙 3).
2. **단사성(injectivity, 1:1).** 두 타입이 같은 팩으로 가지 않고, 한 타입이 두 팩으로 가지
   않습니다. 그래서 "팩"이 곧 "타입"이고, 검색·거버넌스 단위가 깨끗합니다(§2).
3. **이 표가 유일 진실원.** 후보가 든 `proposed_target_pack`은 *제안*입니다. 라우터는 항상
   `candidate_type`으로 표를 다시 룩업해 도착지를 정하고, `proposed_target_pack`과 다르면 라우팅을
   막습니다(§5 규칙 2). [candidate.schema.json](../schemas/candidate.schema.json)의 14개 `allOf`
   if/then 규칙이 이 짝을 스키마 차원에서 이미 강제합니다.

> 특수 경로: 모순 신호로 추출된 `DriftRecordCandidate`는 `user.drift_history`로 가고, 그 안에서
> `supersedes` 엣지로 폐기되는 옛 레코드를 가리킵니다([커널 §4](../spec/01-kernel-schema.md#4-엣지-타입-edge-types),
> [11 평가·드리프트](./11-evaluation-drift.md)). `EvaluationCaseCandidate`는 베이스 레코드가
> 아니라 케이스 필드 집합을 쓰는 `user.evaluation_cases`로 가므로, §4 매핑에서 케이스 스키마를
> 따릅니다([05 평가·드리프트](../spec/05-evaluation-drift.md)).

## 4. 작동 방식 (How it works)

팩 라우터 크랩은 다음 다섯 동작을 순서대로 실행합니다 — **게이트 검문 → 도착지 룩업 → 정합
검산 → 레코드 승격 → 검증·결속**. 어느 동작에서도 후보를 *재판정*하거나 *재분류*하지 않습니다.

```
   확정된(confirmed/narrowed/편집된) 후보 (from S07)
        │
   [A] 게이트 검문   ── validation_status 확인. pending/rejected/sensitive/deferred는 거부(G3)
        ▼
   [B] 도착지 룩업   ── candidate_type → §3 표 → 정확히 한 user.* 팩
        ▼
   [C] 정합 검산     ── proposed_target_pack == 룩업 결과인가? 불일치면 라우팅 중단
        ▼
   [D] 레코드 승격   ── 후보 필드 → 베이스 레코드 필드 매핑(§4 표), record_type 부여
        ▼
   [E] 검증·결속     ── 도착지 팩 스키마 검증 + promoted_to 엣지 + 프로비넌스 보존
        ▼
   도착지 user.* 팩 안의 베이스 레코드 → S10 컴파일 대상 풀
```

**[A] 게이트 검문 (G3).** 가장 먼저, *유일하게 거부할 수 있는* 검문입니다. `validation_status`가
`confirmed` 또는 `narrowed`(또는 사람이 편집해 확정한 상태)가 아니면 **라우팅하지 않습니다.**
구체적으로 `pending`(미검토), `rejected`(거부), `sensitive`(원칙 승인이나 `BoundaryRule` 대기,
G5), `deferred`(보류)는 모두 팩 진입이 차단됩니다(§6 표). 이것이 시스템 신뢰의 마지막 잠금장치
입니다 — 추측 후보가 런타임 규칙이 되는 경로를 *여기서* 끊습니다.

**[B] 도착지 룩업.** `candidate_type`을 [§3 표](#3-라우팅-표-11-전수)에 넣어 단일 `user.*` 팩을
얻습니다. 표는 전수이므로 룩업은 *항상* 정확히 하나를 돌려줍니다. 둘 이상이거나 0개가 나오면
그것은 라우터 버그 또는 잘못된 타입이며, 후자는 S05로 되돌립니다(§5 규칙 3).

**[C] 정합 검산.** 후보가 든 `proposed_target_pack`이 [B]의 룩업 결과와 같은지 확인합니다.
같으면 진행, 다르면 라우팅을 **중단**하고 불일치를 보고합니다 — 둘 중 하나(타입 또는 제안)가
틀렸으므로, 라우터가 임의로 고르지 않고 추출/게이트 단계로 돌려보냅니다(§5 규칙 2).

**[D] 레코드 승격.** 후보의 가벼운 계약을 도착지 팩의 베이스 레코드로 변환합니다. 핵심 필드 매핑:

| 후보 필드 (candidate) | → 베이스 레코드 필드 (record.base) | 비고 |
|------------------------|-----------------------------------|------|
| `candidate_id` | `id` | 인스턴스 id 문법 `<subject>.<recordkind>.NNN` 유지 (감사용으로 후보 id도 보존) |
| `concise_claim` | `statement` | 게이트에서 편집됐으면 *편집본*을 승격. 행동 언어 유지(G4) |
| `evidence_refs` | `evidence_refs` | 그대로 이월 (G1: ≥1개 보장) |
| `confidence` | `confidence` | 그대로 이월. **`< 0.7`이면 `counterexamples` 필수**(베이스 규칙) |
| `scope` | `scope` | 그대로 이월 (G2: 비어있지 않음). `narrowed`면 *좁혀진* 스코프 |
| `sensitivity` | `sensitivity` | 그대로 이월. `sensitive`/`restricted`는 `exception_rules` 필수 |
| `validation_status` | `review_status` | 동일 enum. `confirmed`/`narrowed`로 승격 |
| `extraction_method` | (프로비넌스로 보존) | 출처 스킬 기록 유지(추적성) |
| `reliability` | `reliability` | 그대로 이월(기본 `behavioral`). `self_reported`면 승격돼도 **draft-only** — auto-confirm 불가·여섯 수렴 지표 미산입([01 §7.1](../spec/01-kernel-schema.md), C) |
| (도착지 팩이 부여) | `record_type` | 도착지 팩 스키마의 `record_type` enum 값 |
| (승격 시각) | `created_at`, `updated_at` | 승격 타임스탬프 부여 |
| (선택 보강) | `applies_in`/`exception_rules`/`temporal_status` 등 | S06이 단 맥락·예외·시간 상태 이월 |

`label`은 후보의 `concise_claim`에서 짧은 사람용 이름을 도출하거나 게이트에서 부여된 것을 씁니다.
도착지가 `user.evaluation_cases`이면 베이스 레코드 대신 케이스 필드 집합(`case_id`, `input_task`,
`expected_behavior`, `unacceptable_behavior`, …)으로 매핑합니다([05 평가·드리프트](../spec/05-evaluation-drift.md)).

**[E] 검증·결속.** 승격된 레코드를 *도착지 팩의 JSON Schema*([`schemas/`](../schemas))로 검증합니다
— 도착지가 `user.red_flags`면 `user.red_flags.schema.json`이 통과시켜야 합니다. 검증을 통과하면
후보→팩을 `promoted_to` 엣지로 잇고([커널 §4](../spec/01-kernel-schema.md#4-엣지-타입-edge-types)),
출처 후보·증거 사슬을 보존합니다. 검증 실패는 라우팅 실패이며 레코드를 팩에 *쓰지 않습니다*.

> **쓰기 동작은 dedup 판정을 따른다(1:1은 *목적지*, dedup은 *동작*).** 라우팅 표는 *어느 팩인가*
> 만 정합니다(1:1·전수, 불변). 그 팩 *안에서* 새 레코드를 찍을지는 승격 직전 dedup judge의 판정이
> 정합니다([10 중복 억제·병합](../spec/10-dedup-and-merge.md), 액추에이터
> [`tools/pab_merge.py`](../tools/pab_merge.py)): `novel→insert`(새 베이스 레코드), `duplicate→merge`
> (새 레코드를 찍지 않고 기존 레코드에 `evidence_refs`·`repetition_count`·`confidence` upsert — §2의
> "멱등 승격"이 바로 이것), `refinement→supersede`(새 레코드 + `supersedes` 엣지, 구 레코드 은퇴).
> `conflict`(기존 *확정*과 모순) 후보는 라우터에 *도달하지 않는다* — S07/병합 층에서 사람에게
> 노출되어 보류되기 때문이다(2차 게이트, G3·G5). 즉 라우터는 판정을 *수행*할 뿐 충돌을 자동
> 해소하지 않는다.

## 5. 미확정·불일치 후보 거부 (Rejecting bad routes)

라우터의 *판단 핵심*은 "넣을까 말까"가 아니라 "이 후보가 들어올 자격이 있는가"의 *문지기* 판정
입니다. 세 가지를 거부합니다.

1. **미확정 거부 (G3 — 핵심).** `validation_status ∈ {pending, rejected, sensitive, deferred}`인
   후보는 절대 팩에 들어오지 못합니다. 특히:
   - `pending` — 아직 사람이 검토하지 않음. 라우팅은 *검토 이후* 단계입니다. 미검토 후보를
     라우팅하는 것은 추측을 규칙으로 승격하는 것이며 G3 정면 위반입니다.
   - `rejected` — 사람이 명시 거부. 팩에 넣지 않되 *감사·드리프트용으로 후보를 보존*합니다
     (왜 거부됐는지가 다음 추출의 신호가 됩니다).
   - `sensitive` — 원칙 승인이나 `BoundaryRule` 대기. **경계 규칙이 붙기 전까지 승격 차단**
     (G5). [09 프라이버시·경계](./09-privacy-boundary.md)가 경계를 붙이면 그때 라우팅이 재개됩니다.
   - `deferred` — 사람이 "나중에"로 미룸. 큐에 보류, 라우팅하지 않음.
2. **타입↔도착지 불일치 거부.** 후보의 `proposed_target_pack`이 `candidate_type`의 [§3 표] 값과
   다르면 라우팅을 중단합니다. 라우터는 *제안을 신뢰하지 않고* 항상 타입으로 표를 룩업하며,
   불일치는 상류 결함이므로 임의로 고르지 않고 보고합니다(스키마 `allOf`가 1차 방어).
3. **타입 결함은 라우팅이 아니라 추출로 되돌림.** 도착지를 못 찾았거나(타입이 14개 밖) 도착지가
   직관적으로 틀려 보이면, 라우터는 *재분류하지 않습니다.* 그것은 [05 후보 추출](./05-candidate-extraction.md)의
   소유권입니다. 라우터는 후보를 S05로 되돌리거나 게이트로 되올려 타입을 바로잡게 합니다 —
   경계를 침범해 직접 타입을 바꾸면 추출의 감사 사슬이 깨집니다.

> 거부는 *손실*이 아닙니다. 거부된·보류된 후보는 보존되어 [수렴 지표](../spec/06-convergence-model.md)의
> `confirmation_ratio` 분모에 들어가고, 거부 사유는 다음 세션의 추출 신호가 됩니다.

## 6. 입력 / 출력 (Inputs / Outputs)

### 입력

- **주 입력:** [07 확인 게이트](./07-confirmation-gate.md)가 `validation_status`를 정한 후보
  ([candidate.schema.json](../schemas/candidate.schema.json)). 라우터는 `confirmed`/`narrowed`/
  편집 확정만 처리하고 나머지는 거부합니다(§5).
- **부 입력:** 도착지 팩의 JSON Schema([`schemas/`](../schemas), [D]/[E] 검증), 도착지 팩의
  기존 레코드(id 충돌·중복 점검), [§3 라우팅 표](#3-라우팅-표-11-전수).

각 `validation_status`의 라우터 처리:

| `validation_status` | 라우터 동작 | 근거 |
|---------------------|-------------|------|
| `confirmed` | 승격 → 도착지 팩 | 정상 경로 |
| `narrowed` | 승격 → 도착지 팩 (좁혀진 `scope`로) | 정상 경로, 스코프만 더 좁음 |
| (사람이 편집 후 확정) | 승격 → 도착지 팩 (편집본 `statement`로) | 정상 경로 |
| `pending` | **거부** (라우팅 안 함) | G3 — 미검토 |
| `rejected` | **거부** (후보만 감사 보존) | 명시 거부 |
| `sensitive` | **차단** (BoundaryRule 대기) | G5 — [09](./09-privacy-boundary.md) |
| `deferred` | **보류** (큐에 둠) | 사람이 미룸 |

### 출력

도착지 `user.*` 팩 안의 *유효한 베이스 레코드 하나*. 출력은 다음을 만족합니다:

- 도착지 팩의 JSON Schema와 [record.base.schema.json](../schemas/record.base.schema.json)을 통과.
- `id`/`statement`/`review_status`로 승격됐고(§4 매핑), `record_type`이 도착지 팩 enum 값.
- `evidence_refs`·`scope`·`confidence`·`sensitivity`가 이월되어 G1·G2가 팩 안에서도 유지.
- `promoted_to` 엣지로 출처 후보를 가리켜 *증거→후보→팩* 사슬이 역추적 가능(추적성).
- 도착지가 `user.evaluation_cases`이면 케이스 필드 집합(§4 비고)으로 산출.

> 이 출력은 [10 agent_compiler](./10-agent-compiler.md)의 입력이 됩니다. 단, 팩에 들어온 것과
> *런타임 활성*은 별개입니다 — 컴파일러가 맥락에 맞는 슬라이스만 골라 어댑터로 컴파일하며,
> 라우팅은 "어느 팩에 저장"까지일 뿐 "런타임에서 사용"은 아닙니다(경계).

### 최소 예시 (확정 후보 → `user.communication_style` 레코드 승격)

```json
// 입력: 확정된 후보 (from S07)
{
  "candidate_id": "logotekton.candidate.041",
  "candidate_type": "CommunicationStyleCandidate",
  "concise_claim": "코드 리뷰 보고서 초안에서 3문단 서론을 한 줄 결론으로 교체한다",
  "evidence_refs": ["logotekton.evidence.088", "logotekton.evidence.089"],
  "proposed_target_pack": "user.communication_style",
  "confidence": 0.55,
  "scope": "코드 리뷰 보고서 초안 (내부 청중)",
  "sensitivity": "internal",
  "validation_status": "narrowed",
  "extraction_method": "diff_mining"
}
```

```json
// 출력: user.communication_style 팩 안의 베이스 레코드
{
  "id": "logotekton.style.012",
  "record_type": "StructureRecord",
  "label": "리뷰 초안: 결론 우선",
  "statement": "코드 리뷰 보고서 초안에서 3문단 서론을 한 줄 결론으로 교체하고 근거를 뒤로 옮긴다",
  "evidence_refs": ["logotekton.evidence.088", "logotekton.evidence.089"],
  "confidence": 0.55,
  "scope": "코드 리뷰 보고서 초안 (내부 청중)",
  "review_status": "narrowed",
  "sensitivity": "internal",
  "counterexamples": ["evidence.088: 동일 사용자가 외부 제안서에서는 서론을 유지했다"],
  "exception_rules": ["법적 고지·계약 문구에서는 정해진 서식을 따른다"],
  "created_at": "2026-06-28T09:12:00Z",
  "updated_at": "2026-06-28T09:12:00Z"
}
```

`candidate_type`이 `CommunicationStyleCandidate`이므로 [§3 표]가 도착지를 `user.communication_style`
*하나*로 고정했고, 후보의 `proposed_target_pack`과 일치하므로 정합 검산을 통과했습니다.
`validation_status: narrowed`라 게이트를 통과해(G3 OK) 승격됐고, `candidate_id→id`,
`concise_claim→statement`, `validation_status→review_status`로 매핑됐습니다. `confidence`가
0.7 미만이라 베이스 규칙에 따라 `counterexamples`가 채워졌고, `record_type`은 도착지 팩 스키마의
enum 값(순서 규칙이므로 `StructureRecord`)을 받았습니다. 라우터는 `statement`를 *재판정*하거나 스코프를 *재지정*하지
않았습니다 — 게이트/스코프가 준 값을 그대로 이월했을 뿐입니다.

## 7. 품질 검사 (Quality checks)

출력 전에 팩 라우터 크랩은 다음을 강제합니다. 코드 강제는
[`tools/validate_packs.py`](../tools/validate_packs.py)와 도착지 팩 스키마가 보조합니다.

- [ ] **게이트 통과(G3)** — 모든 입력이 `confirmed`/`narrowed`/편집 확정인가. `pending`/`rejected`/
  `sensitive`/`deferred` 후보를 *하나도* 팩에 넣지 않았는가(§5 규칙 1).
- [ ] **단일 도착지(1:1)** — 각 후보가 `candidate_type`으로 룩업한 *정확히 하나*의 팩으로 갔는가.
  한 후보를 둘 이상 팩에 복제하지 않았는가(§2 정밀도).
- [ ] **타입↔도착지 정합** — `proposed_target_pack`이 [§3 표]의 룩업 결과와 일치하는가. 불일치를
  임의로 봉합하지 않고 상류로 되돌렸는가(§5 규칙 2).
- [ ] **전수성** — 도착지를 못 찾은 후보가 없는가. 못 찾았다면 그것을 라우터가 추측해 메우지 않고
  타입 결함으로 S05에 되돌렸는가(§5 규칙 3).
- [ ] **승격 매핑 정확** — `candidate_id→id`, `concise_claim→statement`(편집본 반영),
  `validation_status→review_status`가 정확하고, `evidence_refs`·`scope`·`confidence`·`sensitivity`가
  손실 없이 이월됐는가(§4 표).
- [ ] **도착지 스키마 검증** — 승격된 레코드가 *도착지 팩의 JSON Schema*와 베이스 레코드 스키마를
  통과하는가. `record_type`이 도착지 팩 enum 값인가. 검증 실패 레코드를 팩에 쓰지 않았는가.
- [ ] **게이트 불변식 보존(G1·G2)** — `evidence_refs ≥ 1`(G1)·비어있지 않은 `scope`(G2)가 팩 안
  레코드에서도 유지되는가. `confidence < 0.7`인데 `counterexamples`가 누락되지 않았는가.
- [ ] **민감 차단(G5)** — `sensitive`/`restricted` 후보가 `BoundaryRule` 없이 승격되지 않았는가.
  [09 프라이버시·경계](./09-privacy-boundary.md)의 경계가 붙은 뒤에만 라우팅 재개했는가.
- [ ] **결속·프로비넌스** — `promoted_to` 엣지로 후보를 가리키고 `extraction_method`·증거 사슬을
  보존했는가. *증거→후보→팩* 경로가 역추적 가능한가(추적성=1.0).
- [ ] **경계 준수** — 후보를 *재판정*(S07)·*재분류*(S05)·*재스코프*(S06)·*컴파일*(S10)하지 않았는가.

## 8. Crab 역할 — Pack Router Crab

이 스킬의 소유 역할은 **Pack Router Crab**입니다([12 crab 오케스트레이션](./12-crab-orchestration.md),
[커널 §8](../spec/01-kernel-schema.md#8-crab-에이전트-역할-운영-모델)).

- **소유 작업:** `route` 상태에서 확정 후보의 게이트 검문(G3), `candidate_type` 기반 단일 도착지
  룩업([§3 표]), `proposed_target_pack` 정합 검산, 후보→베이스 레코드 승격(§4), 도착지 팩 스키마
  검증, `promoted_to` 결속·프로비넌스 보존.
- **받는 핸드오프:** **Confirmation Crab**(S07)이 `validation_status`를 정한 후보. 민감 후보는
  **Boundary Crab**(S09)이 `BoundaryRule`을 붙인 뒤에만 받습니다(G5).
- **넘기는 핸드오프:** 도착지 팩 안의 베이스 레코드 → **Agent Compiler**(S10)의 컴파일 대상 풀.
  타입·도착지 불일치나 타입 결함은 **Orchestrator**를 통해 **Candidate Extractor**(S05)/
  **Confirmation Crab**(S07)으로 되돌립니다(§5).
- **경계:** 후보의 *진위 판정*(S07)·*타입 부여/변경*(S05)·*스코프 지정*(S06)·*컴파일/런타임 활성*
  (S10)을 침범하지 않습니다. 미확정 후보를 팩에 넣지 않으며(G3), 한 후보를 복수 팩에 복제하지
  않고(1:1), 도착지를 추측으로 메우지 않습니다(전수성). 라우터는 *결정적·지루*해야 정확합니다.

OpenCrab 도구로 실행할 때는 `opencrab_search_packs`로 도착지 팩을 확인하고,
`opencrab_search_nodes`로 도착지 팩의 기존 레코드와 id 충돌·중복을 점검하며, 승격된 레코드를
`opencrab_pack_update`로 도착지 `user.*` 팩에 쓰고 `promoted_to` 엣지로 출처 후보를 결속합니다.
승격 전후 검증은 `opencrab_pack_qa`로, 라우팅이 막힌 민감 후보의 경계 처리는
[04 프라이버시·경계](../spec/04-privacy-boundary.md)의 권한 레벨을 따릅니다.

> 9-space 사상: 라우팅은 `claim` 공간의 후보를, 그 타입이 정한 도착지 팩으로 옮기는 동작입니다.
> 후보가 사상되던 `claim`은 승격되며 도착지 팩의 노드 타입으로 고정되고, 그 노드 타입이 9-space의
> `concept`/`policy`/`outcome` 공간으로 다시 사상됩니다(예: `policy`←`BoundaryRule`·`DecisionPolicy`·
> `RedFlag`, `concept`←`CommunicationStyleRule`·`PersonaTrait`·`DomainOverlay`). `promoted_to`
> 엣지가 `evidence`→`claim`→도착지 노드의 추적 사슬을 잇습니다([07 9-space 크로스워크](../spec/07-opencrab-9space-crosswalk.md)).

## 9. 관련 문서

- 라이프사이클·노드·엣지·게이트(특히 G3)·라우팅 표 → [01 커널 스키마](../spec/01-kernel-schema.md)
- 이 스킬이 속한 12단계 파이프라인 계약(`route`) → [02 빌더 파이프라인](../spec/02-builder-pipeline.md)
- 직전 단계(사람 검토로 `validation_status` 확정) → [07 확인 게이트](./07-confirmation-gate.md)
- 후보의 타입 부여(라우팅의 근거) → [05 후보 추출](./05-candidate-extraction.md)
- 후보의 스코프·예외·시간 상태(승격 시 이월) → [06 스코프·맥락](./06-scope-context.md)
- 직후 단계(확정 슬라이스 → 런타임 어댑터 컴파일) → [10 에이전트 컴파일러](./10-agent-compiler.md)
- 14개 도착지 팩의 정의 → [03 팩 카탈로그](../spec/03-pack-catalog.md), 기계 스키마 → [`schemas/`](../schemas)
- 후보/베이스 레코드의 기계 스키마 → [`candidate.schema.json`](../schemas/candidate.schema.json) ·
  [`record.base.schema.json`](../schemas/record.base.schema.json)
- 민감 후보의 경계·권한 처리(G5, 라우팅 차단/재개) → [04 프라이버시·경계](../spec/04-privacy-boundary.md) ·
  [09 프라이버시·경계](./09-privacy-boundary.md)
- 평가 케이스 팩의 케이스 필드(특수 매핑) → [05 평가·드리프트](../spec/05-evaluation-drift.md)
- 1:1 라우팅이 지키는 검색 정밀도·추적성·수렴 지표 → [06 수렴 모델](../spec/06-convergence-model.md)
- 팩 안 쓰기 동작을 정하는 dedup 판정(insert/merge/supersede/surface)·액추에이터 →
  [10 중복 억제·병합](../spec/10-dedup-and-merge.md) · [`tools/pab_merge.py`](../tools/pab_merge.py)
- 역할·상태·핸드오프 운영 모델 → [12 crab 오케스트레이션](./12-crab-orchestration.md)


## 트리거 (Trigger)

> 이 스킬의 발화 조건. 전체 2계층 모델·호스트(훅) 매핑·게이트 보존은
> [../spec/09-triggers.md](../spec/09-triggers.md), 머신 스키마는
> [../schemas/trigger.schema.json](../schemas/trigger.schema.json) 참고.

```yaml
trigger:
  trigger_id: pab.pack_router.on_confirmed
  skill: pack_router
  signal: candidate_confirmed
  condition: "route only confirmed or edited candidates"
  cadence: event
  host_hook: chained
  produces: routed
  requires_confirmation: false     # 스테이징만 (라이브 규칙 아님)
  default_state: enabled
  debounce: per_candidate
```

게이트를 통과한 후보만 1:1로 라우팅합니다 — pending은 절대 팩에 들어가지 않습니다(G3).
