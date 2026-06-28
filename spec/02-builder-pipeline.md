# 02 · 빌더 파이프라인 (Builder Pipeline)

> **EN:** This is the 12-step, evidence-bound pipeline that turns raw session signals into
> a compiled Personal Agent, and how the 13 builder skills wire into it. Every step has an
> explicit input/output contract, a single owning skill, and a single owning Crab role.
> The pipeline runs through 9 workflow states (collect_evidence → … → record_drift_or_update)
> and is gated end-to-end by the six quality gates (G1–G6). `kernel_schema` (skill 13) is
> not a runnable step — it is the shared spine all 12 steps read first.

이 문서는 [`01 커널 스키마`](./01-kernel-schema.md)의 라이프사이클을 **실행 가능한 12단계**로
펼친 것입니다. 커널이 *어휘*를 고정한다면, 이 파이프라인은 *순서·계약·소유*를 고정합니다.
원시 신호 한 조각이 어떻게 증거에 묶이고, 스코프를 받고, 사람의 확인을 거쳐, 팩에 라우팅되고,
런타임으로 컴파일되어, 평가·드리프트 루프로 되돌아오는지를 단계별 입력/출력 계약으로 규정합니다.

핵심 규칙 세 가지:

- **13개 스킬, 12개 단계.** `kernel_schema`(스킬 13)는 단계가 아니라 모든 단계가 먼저 읽는
  *공유 척추*입니다. 실행되는 파이프라인은 스킬 01–12입니다.
- **한 단계 = 한 스킬 = 한 Crab 역할.** 채굴 단계(02 세션마이닝 / 03 질문 / 04 diff마이닝)만
  세 스킬이 한 워크플로 상태를 공유합니다.
- **모든 핸드오프는 계약이다.** 각 단계는 정해진 입력 노드를 받아 정해진 출력 노드만 내보냅니다.
  계약 위반(증거 없는 후보, 스코프 없는 레코드, 미확인 항목의 승격)은 게이트가 막습니다.

## 1. 9개 워크플로 상태와 12단계의 매핑

파이프라인은 9개의 **워크플로 상태**를 통과합니다. 상태는 *어디까지 왔는가*(오케스트레이터가
추적하는 단위)이고, 단계는 *그 상태에서 무엇을 하는가*입니다. 채굴 상태(`mine_or_ask`)는
세 스킬을 묶고, 평가·드리프트 상태(`evaluate_output` → `record_drift_or_update`)는 루프를 닫습니다.

| # | 워크플로 상태 | 포함 단계(스킬) | 라이프사이클 위치 |
|---|---------------|-----------------|-------------------|
| 1 | `collect_evidence` | S01 evidence_capture | `raw_signal` 포착 |
| 2 | `mine_or_ask` | S02 session_mining · S03 elicitation_questioning · S04 diff_mining | 원시 신호 → 후보 신호 |
| 3 | `extract_candidates` | S05 candidate_extraction | → `evidence_bound_candidate` |
| 4 | `scope_candidates` | S06 scope_context | → `scoped_candidate` |
| 5 | `review_candidates` | S07 confirmation_gate | → `user_reviewed` → `confirmed_or_rejected` |
| 6 | `route_confirmed` | S08 pack_router · S09 privacy_boundary | → `target_pack_ingested` |
| 7 | `compile_runtime` | S10 agent_compiler | → `runtime_activated` |
| 8 | `evaluate_output` | S11 evaluation_drift | 충실도·교정비용 측정 |
| 9 | `record_drift_or_update` | S11 evaluation_drift (drift 기록) → ↺ S01 | `DriftRecord` → 루프 |

> S12 `crab_orchestration`은 특정 한 상태에 속하지 않고 **9개 상태 전체를 관장**합니다(상태
> 전이·핸드오프·재시도·게이트 차단 처리). S13 `kernel_schema`는 단계가 아니라 스키마 척추입니다.

## 2. ASCII 파이프라인 다이어그램

```
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │  S12 crab_orchestration  — 모든 상태 전이·핸드오프·게이트 차단을 관장 (관제탑)  │
  └─────────────────────────────────────────────────────────────────────────────┘
        ▲          ▲          ▲          ▲          ▲          ▲          ▲
  ╔═════╪══════════╪══════════╪══════════╪══════════╪══════════╪══════════╪═════╗
  ║  [1]collect    [2]mine_or [3]extract [4]scope   [5]review  [6]route   [7]compile
  ║  _evidence     _ask       _candidates _candidates _candidates _confirmed _runtime
  ╚═════╪══════════╪══════════╪══════════╪══════════╪══════════╪══════════╪═════╝

   세션/파일 ─┐
   교정/diff ─┤  S01            S02 session_mining ┐
   인터뷰    ─┘  evidence       S03 questioning    ├─► S05            S06           S07
                 _capture  ───► S04 diff_mining    ┘   candidate ───► scope ──────► confirmation
                 (G1 증거)      (raw signals)          _extraction    _context      _gate
                    │                                   (typed         (scope+        (사람: confirm/
                    ▼                                    candidate,      exception,     edit/reject/
              EvidenceItem ──────────────────────────►  evidence_refs)  G2 스코프)     narrow/sensitive/
                                                              │                         defer; G3·G4)
                                                              ▼                              │
                                                       CandidateAssertion                    │ confirmed/
                                                                                             │ narrowed만
                                                                                             ▼
                          S08 pack_router ──► S09 privacy_boundary ──► S10 agent_compiler
                          (14 user.* 중 1개   (boundary category +      (확인 슬라이스만 →
                           1:1 라우팅)         authority level; G5)      runtime adapter; G3)
                                │                                              │
                                ▼                                              ▼
                          UserOntologypack 적재 ─────────────────────► AssistantProfile
                                                                               │ (compiled_into)
                                                                               ▼
                                                                      ┌─────────────────┐
                                                                      │  Personal Agent │ ← 작업 실행
                                                                      └────────┬────────┘
                                                                               ▼
   ┌─────────────────────────── 루프 ◄──────────────  S11 evaluation_drift  ◄┘
   │  [9]record_drift_or_update      [8]evaluate_output
   │  DriftRecord → supersedes        EvaluationCase 채점:
   │  → 새 증거로 재포착 (↺ S01)        decision_fidelity·correction_cost·drift_score
   └──────────────────────────────────────────────────────────────────────────►

  공유 척추(모든 단계가 먼저 읽음):  S13 kernel_schema  →  ./01-kernel-schema.md
  확인 게이트 확장(승격 직전):        dedup judge → merge/supersede 추천·conflict 노출 → ./10-dedup-and-merge.md
```

## 3. 단계별 입력/출력 계약

각 단계의 **입력 노드 → 출력 노드**, 소유 스킬, 소유 [Crab 역할](../skills/12-crab-orchestration.md),
강제 게이트를 규정합니다. 노드/엣지 타입은 [커널 §3·§4](./01-kernel-schema.md#3-노드-타입-node-types)를,
필드는 [통합 베이스 레코드](../schemas/record.base.schema.json)를 따릅니다.

### S01 · evidence_capture — 상태 `collect_evidence`

- **입력:** 원시 신호 — AI 세션 로그, 사용자 답변, 파일, 메시지, diff, 산출물, 노트.
- **출력:** `EvidenceItem` 노드 (출처·발췌·타임스탬프·원본 링크 포함). 이것이 *진실의 출처*.
- **소유:** 스킬 [`01-evidence-capture`](../skills/01-evidence-capture.md) · Crab 역할 **Evidence**.
- **게이트:** G1의 전제 — 이후 모든 후보가 가리킬 `evidence_refs` 대상을 여기서 만든다.
- **불변식:** 후보를 만들지 않는다. 오직 증거만 포착·정규화한다.

### S02 / S03 / S04 — 상태 `mine_or_ask` (채굴 트리오)

세 스킬이 한 워크플로 상태를 공유한다. 들어온 증거의 성격에 따라 오케스트레이터가 경로를 고른다.

| 스킬 | 입력 | 출력 | Crab 역할 |
|------|------|------|-----------|
| [`02-session-mining`](../skills/02-session-mining.md) | 누적 세션 `EvidenceItem` | 후보 신호(반복 패턴·선호·거부) | **Session Miner** |
| [`03-elicitation-questioning`](../skills/03-elicitation-questioning.md) | 빈 영역·모호 신호 | 구조화 에피소드 인터뷰 응답 → `EvidenceItem` | **Questioning** |
| [`04-diff-mining`](../skills/04-diff-mining.md) | before/after 교정 쌍 | 교정 신호(가장 강한 경계 신호) | **Diff Miner** |

- **출력 공통:** 아직 *타입이 지정되지 않은* 후보 신호 + 그 근거 `EvidenceItem`.
- **게이트:** 모든 신호는 ≥1 `EvidenceItem`에 묶인 채로만 다음 단계로 간다(G1 예비).

### S05 · candidate_extraction — 상태 `extract_candidates`

- **입력:** 채굴된 후보 신호 + `EvidenceItem`.
- **출력:** 타입 지정된 `CandidateAssertion`. 필수 필드: `candidate_id`, `candidate_type`,
  `concise_claim`, `evidence_refs`, `confidence`, `scope`(초안), `sensitivity`,
  `proposed_target_pack`, `validation_status`, `extraction_method`.
- **소유:** 스킬 [`05-candidate-extraction`](../skills/05-candidate-extraction.md) · Crab 역할 **Candidate Extractor**.
- **게이트:** G1(`evidence_refs` ≥ 1), G4(행동 언어만 — 추측된 심리 금지).
- **계약:** `candidate_type`은 [후보↔라우팅 14:14 표](./01-kernel-schema.md#6-후보-타입--라우팅-11-전수)의
  값 중 하나여야 한다(전수 매핑이므로 미분류 후보는 없다).

### S06 · scope_context — 상태 `scope_candidates`

- **입력:** `CandidateAssertion` (초안 스코프).
- **출력:** `scoped_candidate` — 비어있지 않은 `scope`, `Context`/`Condition` 연결,
  `exception_rules`, 시간적 유효성(temporal validity)이 채워진 후보.
- **소유:** 스킬 [`06-scope-context`](../skills/06-scope-context.md) · Crab 역할 **Scope**.
- **게이트:** G2(스코프 없는 휴리스틱 금지). "항상 참" 후보는 여기서 *언제/어디서*로 좁혀진다.

### S07 · confirmation_gate — 상태 `review_candidates`

- **입력:** `scoped_candidate`.
- **출력:** `review_status` ∈ {confirmed, rejected, narrowed, sensitive, deferred} 가 찍힌
  후보. `confirmed`/`narrowed`/편집본만 다음 단계로 통과.
- **소유:** 스킬 [`07-confirmation-gate`](../skills/07-confirmation-gate.md) · Crab 역할 **Confirmation**.
- **게이트:** **G3**(미확인 후보의 런타임 승격 금지)의 결정 지점. 사람이 confirm/edit/reject/
  narrow/sensitive/defer 한다 — 그리고 승격 직전 **dedup judge**가 확정 후보를 대상 팩의 기존
  레코드와 대조해 `duplicate→merge`·`refinement→supersede`를 *추천 액션*으로 더한다(여섯 기본 +
  두 dedup 액션). 기존 *확정* 레코드와 **모순(conflict)**하는 후보는 자동 적용하지 않고 사람에게
  노출된다(merge 층 = 확인 게이트 다음의 2차 관문 — [10 중복 억제·병합](./10-dedup-and-merge.md)).
  라이프사이클의 `user_reviewed → confirmed_or_rejected` 전이.

### S08 / S09 — 상태 `route_confirmed`

| 스킬 | 입력 | 출력 | Crab 역할 |
|------|------|------|-----------|
| [`08-pack-router`](../skills/08-pack-router.md) | confirmed/narrowed 후보 | 14 `user.*` 팩 중 1개로 `promoted_to` | **Pack Router** |
| [`09-privacy-boundary`](../skills/09-privacy-boundary.md) | sensitive/restricted 후보 | `BoundaryRule`(category+authority level) | **Boundary** |

- **라우팅 계약:** `candidate_type → user pack`은 [1:1 전수 표](./01-kernel-schema.md#6-후보-타입--라우팅-11-전수)로
  결정론적이다. 라우터는 새 팩을 만들지 않는다.
- **게이트:** **G5**(승격 전 프라이버시) — `sensitivity`가 sensitive/restricted면 `BoundaryRule`이
  *먼저* 부착되어야 팩에 적재된다. G6(템플릿/인스턴스 분리) — 적재 대상은 인스턴스 팩
  `personal.<subject>.*`이지 템플릿이 아니다. 라이프사이클의 `target_pack_ingested`.

### S10 · agent_compiler — 상태 `compile_runtime`

- **입력:** 확인된 인스턴스 레코드 슬라이스(작업에 필요한 팩들) + 관련 `BoundaryRule`.
- **출력:** `*.runtime_adapter`로 컴파일된 `AssistantProfile`(`compiled_into`). 이것이 작업을
  실행하는 **Personal Agent**.
- **소유:** 스킬 [`10-agent-compiler`](../skills/10-agent-compiler.md) · Crab 역할 **Agent Compiler**.
- **게이트:** **G3** 재확인 — `confirmed`/`narrowed` 레코드만 컴파일에 포함. pending은 제외.
  경계/권한은 별도 레이어로 강제([04 프라이버시·경계](./04-privacy-boundary.md)). `runtime_activated`.

### S11 · evaluation_drift — 상태 `evaluate_output` → `record_drift_or_update`

한 스킬이 루프의 두 상태를 닫는다.

- **`evaluate_output`:** `AssistantProfile`을 `EvaluationCase`로 채점 — 8개 지표
  (decision_fidelity, red_flag_recall, rejection_alignment, artifact_fit,
  boundary_compliance, evidence_traceability, correction_cost, drift_score).
- **`record_drift_or_update`:** 실패·변경·모순을 `DriftRecord`로 기록(`supersedes`로 옛 레코드
  대체) → 새 증거로 **다시 S01로 루프**.
- **소유:** 스킬 [`11-evaluation-drift`](../skills/11-evaluation-drift.md) · Crab 역할 **Evaluator**.
- **연결:** 측정값은 [05 평가·드리프트](./05-evaluation-drift.md)와 [06 수렴 모델](./06-convergence-model.md)의
  지표(`correction_cost`↓, `drift_stability`↑)로 집계된다.

### 가로지르는 두 스킬 (단계 아님)

| 스킬 | 역할 | 비고 |
|------|------|------|
| [`12-crab-orchestration`](../skills/12-crab-orchestration.md) | **Orchestrator** | 9개 상태 전이·핸드오프·재시도·게이트 차단을 관장 (관제탑) |
| [`13-kernel-schema`](../skills/13-kernel-schema.md) | **Pack Architect** | 모든 단계가 먼저 읽는 스키마 척추 (= [01 커널 스키마](./01-kernel-schema.md)) |

## 4. 단계 → 스킬 → Crab 역할 → 게이트 요약표

| 상태 | 단계(스킬) | 입력 → 출력 | Crab 역할 | 게이트 |
|------|------------|-------------|-----------|--------|
| collect_evidence | S01 [evidence_capture](../skills/01-evidence-capture.md) | 원시 신호 → `EvidenceItem` | Evidence | G1(전제) |
| mine_or_ask | S02 [session_mining](../skills/02-session-mining.md) | 세션 → 후보 신호 | Session Miner | G1 |
| mine_or_ask | S03 [elicitation_questioning](../skills/03-elicitation-questioning.md) | 빈 영역 → 인터뷰 증거 | Questioning | G1 |
| mine_or_ask | S04 [diff_mining](../skills/04-diff-mining.md) | 교정 쌍 → 교정 신호 | Diff Miner | G1 |
| extract_candidates | S05 [candidate_extraction](../skills/05-candidate-extraction.md) | 신호 → `CandidateAssertion` | Candidate Extractor | G1·G4 |
| scope_candidates | S06 [scope_context](../skills/06-scope-context.md) | 후보 → `scoped_candidate` | Scope | G2 |
| review_candidates | S07 [confirmation_gate](../skills/07-confirmation-gate.md) | 후보 → `review_status` | Confirmation | G3 |
| route_confirmed | S08 [pack_router](../skills/08-pack-router.md) | confirmed → `promoted_to` 팩 | Pack Router | G6 |
| route_confirmed | S09 [privacy_boundary](../skills/09-privacy-boundary.md) | sensitive → `BoundaryRule` | Boundary | G5 |
| compile_runtime | S10 [agent_compiler](../skills/10-agent-compiler.md) | 슬라이스 → `AssistantProfile` | Agent Compiler | G3 |
| evaluate_output | S11 [evaluation_drift](../skills/11-evaluation-drift.md) | profile → `EvaluationCase` 결과 | Evaluator | — |
| record_drift_or_update | S11 [evaluation_drift](../skills/11-evaluation-drift.md) | 변경 → `DriftRecord` → ↺S01 | Evaluator | — |
| *(전 상태)* | S12 [crab_orchestration](../skills/12-crab-orchestration.md) | 상태 전이·핸드오프 | Orchestrator | 모두 강제 |
| *(척추)* | S13 [kernel_schema](../skills/13-kernel-schema.md) | 공유 스키마 | Pack Architect | 정의 |

## 5. 파이프라인 불변식 (게이트 재확인)

이 파이프라인이 신뢰의 근거가 되는 이유는 단계 사이의 핸드오프가 게이트로 강제되기 때문입니다.
코드 강제는 [`tools/validate_packs.py`](../tools/validate_packs.py)가 담당합니다.

1. **증거 우선(G1)** — S05 출력 후보는 ≥1 `evidence_refs` 없이는 S06으로 못 간다.
2. **항상 스코프(G2)** — S06을 통과한 후보만 비어있지 않은 `scope`를 가진다.
3. **사람 승인 후 활성화(G3)** — S07에서 `confirmed`/`narrowed`가 아닌 후보는 S10 컴파일에
   포함되지 않는다. pending은 절대 런타임 규칙이 되지 않는다.
4. **행동 언어만(G4)** — S05는 관찰된 행동으로만 후보를 기술한다.
5. **승격 전 프라이버시(G5)** — S09에서 `BoundaryRule`을 먼저 받지 않은 sensitive/restricted
   항목은 S08 적재가 보류된다.
6. **템플릿/인스턴스 분리(G6)** — S08 적재 대상은 인스턴스 팩이며, 템플릿/스키마는 라이브
   레코드를 담지 않는다.

## 6. 관련 문서

- 라이프사이클·노드·엣지·게이트·베이스 레코드 → [01 커널 스키마](./01-kernel-schema.md)
- 라우팅 도착지인 14개 팩의 정의 → [03 팩 카탈로그](./03-pack-catalog.md)
- S09가 적용하는 경계 범주·권한 레벨 → [04 프라이버시·경계](./04-privacy-boundary.md)
- S11이 채점하는 지표·평가 케이스 → [05 평가·드리프트](./05-evaluation-drift.md)
- 파이프라인이 끌어올리는 수렴 지표 → [06 수렴 모델](./06-convergence-model.md)
- 각 노드의 9-space 사상 → [07 9-space 크로스워크](./07-opencrab-9space-crosswalk.md)
- S07 확인 게이트의 2차 관문(중복 억제·병합·대체) → [10 중복 억제·병합](./10-dedup-and-merge.md)
- 스킬·역할·핸드오프 운영 모델 → [12 crab 오케스트레이션](../skills/12-crab-orchestration.md)
