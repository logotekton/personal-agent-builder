# 12 · 크랩 오케스트레이션 (Crab Orchestration)

> **EN:** Operating instructions for `skill.pab.crab_orchestration` — the **control tower**,
> owned by the **Orchestrator Crab**. It does not produce records itself. It owns the **9
> workflow states** (`collect_evidence` → … → `record_drift_or_update`), routes each unit of
> work to the **single owning Crab role** for the current state, and enforces that **every
> state has exactly one owner** and **every handoff carries an input/output contract**. When a
> Crab finishes, the Orchestrator advances the state; when a quality gate (G1–G6) or a QA
> check fails, it does **not** push forward — it routes the unit *back* to the upstream role
> that owns the defect (extraction, boundary, or schema). Think of it as a deterministic state
> machine over the pipeline, not an agent that "decides" content.

이 문서는 가로지르는 스킬 [`S12 crab_orchestration`](../spec/02-builder-pipeline.md#가로지르는-두-스킬-단계-아님)의
**실행 지침**입니다. 마케팅이 아니라 그대로 돌릴 수 있는 운영 절차로 읽으세요. 다른 11개 스킬이
*한 상태에서 무엇을 하는가*를 정의한다면, 이 스킬은 *상태 사이를 누가·언제·어떤 계약으로
넘기는가*를 정의합니다. 어휘는 [01 커널 스키마](../spec/01-kernel-schema.md), 상태·단계 매핑은
[02 빌더 파이프라인](../spec/02-builder-pipeline.md), 게이트는 커널 §2, 팩 정의는
[03 팩 카탈로그](../spec/03-pack-catalog.md)를 따르며 새 이름을 만들지 않습니다.

---

## 1. 목적 (Purpose)

크랩 오케스트레이션은 **관제탑(control tower)**입니다. 레코드를 만들지 않고, 9개 워크플로
상태 사이의 **전이·핸드오프·재시도·게이트 차단**을 관장합니다. 오케스트레이터의 책임은 단 셋입니다.

- **상태 소유권 강제.** 9개 상태 각각에 *정확히 하나*의 소유 Crab 역할이 있습니다(§3 표). 어떤
  작업 단위(work unit)든 *지금 어느 상태에 있는가*가 곧 *지금 누가 책임지는가*를 결정합니다.
  소유자 없는 상태, 소유자 둘인 상태는 존재하지 않습니다.
- **핸드오프 계약 강제.** 한 상태에서 다음으로 넘어가는 모든 핸드오프는 *정해진 입력 노드 →
  정해진 출력 노드* 계약을 만족해야 합니다(§4 표). 계약을 못 채운 핸드오프는 전진하지 않습니다.
- **게이트 차단·되돌림.** 게이트(G1–G6) 또는 단계 품질검사가 실패하면 오케스트레이터는 *전진을
  멈추고* 결함을 소유한 상류 역할로 작업을 **되돌립니다**(§5). 추측으로 봉합하거나 결함을 들고
  다음 상태로 밀지 않습니다.

오케스트레이터는 *내용을 판단하지 않습니다.* 후보가 참인지(S07), 어느 팩인지(S08), 민감한지
(S09)는 각 소유 역할의 일입니다. 오케스트레이터는 *그 판단을 누가 언제 하는지*와 *그 결과가
계약을 만족하는지*만 관장합니다.

> 한 줄 계약: **작업 단위 + 현재 상태 → (소유 역할 호출 → 계약 검증 → 다음 상태 | 되돌림).**
> 입력은 라이프사이클 어느 지점의 작업 단위, 출력은 *상태 전이 결정 하나*(전진/되돌림/보류)입니다.

## 2. 작동 방식 (How it works)

오케스트레이터는 파이프라인 위에 얹힌 **결정적 상태 기계**입니다. 각 작업 단위에 대해 다음
루프를 돕니다 — **현재 상태 확인 → 소유 역할 디스패치 → 출력 계약 검증 → 게이트 평가 →
전진 또는 되돌림**.

```
  ┌───────────────────────────────────────────────────────────────────────────┐
  │  S12 Orchestrator Crab — 9개 상태 전이·핸드오프·게이트 차단을 관장 (관제탑)  │
  └───────────────────────────────────────────────────────────────────────────┘
     │ dispatch        ▲ 출력 계약 + 게이트 통과 → 상태 전진
     ▼                 │ 실패 → 결함 소유 상류로 되돌림(↩)
  [1]collect_evidence ─► [2]mine_or_ask ─► [3]extract_candidates ─► [4]scope_candidates
        Evidence          Miner/Quest/Diff      Candidate Extractor        Scope
                                                                              │
  [7]compile_runtime ◄─ [6]route_confirmed ◄─ [5]review_candidates ◄─────────┘
     Agent Compiler        Pack Router/Boundary    Confirmation
        │
        ▼
  [8]evaluate_output ─► [9]record_drift_or_update ─► ↺ [1] (새 증거로 재포착)
     Evaluator              Evaluator (DriftRecord)
```

상태는 *어디까지 왔는가*(오케스트레이터가 추적하는 단위)이고, 단계는 *그 상태에서 무엇을
하는가*입니다([파이프라인 §1](../spec/02-builder-pipeline.md#1-9개-워크플로-상태와-12단계의-매핑)).
오케스트레이터는 9개 상태만 알면 되고, 각 상태 안의 *내용*은 소유 역할에 위임합니다.

특수 상태 두 가지를 기억하세요. (a) `mine_or_ask`는 *하나의 상태에 세 역할*(Session Miner ·
Questioning · Diff Miner)이 묶여 있어, 오케스트레이터가 들어온 증거의 성격에 따라 *경로를
고릅니다*(§4 핸드오프 H2). (b) `evaluate_output → record_drift_or_update`는 한 역할(Evaluator)이
*루프의 두 상태*를 닫고, 드리프트를 새 증거로 만들어 **S01로 되돌려 루프를 잇습니다**(§4 H8).

## 3. 13개 Crab 역할 (13 Crab roles)

파이프라인에는 **13개 Crab 역할**이 있습니다 — 9개 상태를 소유하는 12개 실행 역할과, 그 위에서
관장하는 Orchestrator입니다. 역할 어휘는 [커널 §8](../spec/01-kernel-schema.md#8-crab-에이전트-역할-운영-모델),
상태 매핑은 [파이프라인 §4](../spec/02-builder-pipeline.md#4-단계--스킬--crab-역할--게이트-요약표)와
동일하며 새 이름을 만들지 않습니다.

| # | Crab 역할 | 소유 상태 | 소유 스킬 | 강제 게이트 | 한 줄 책임 |
|---|-----------|-----------|-----------|-------------|------------|
| 0 | **Orchestrator** | *(전 상태)* | [12 crab_orchestration](./12-crab-orchestration.md) | 모두 강제 | 상태 전이·핸드오프·되돌림 관장 (관제탑) |
| 1 | **Evidence** | `collect_evidence` | [01 evidence_capture](./01-evidence-capture.md) | G1(전제) | 원시 신호 → `EvidenceItem` 포착·정규화 |
| 2 | **Session Miner** | `mine_or_ask` | [02 session_mining](./02-session-mining.md) | G1 | 누적 세션 → 반복 패턴·선호·거부 신호 |
| 3 | **Questioning** | `mine_or_ask` | [03 elicitation_questioning](./03-elicitation-questioning.md) | G1 | 빈 영역 → 구조화 에피소드 인터뷰 증거 |
| 4 | **Diff Miner** | `mine_or_ask` | [04 diff_mining](./04-diff-mining.md) | G1 | before/after 교정 쌍 → 교정 신호(최강) |
| 5 | **Candidate Extractor** | `extract_candidates` | [05 candidate_extraction](./05-candidate-extraction.md) | G1·G4 | 신호 → 타입 지정 `CandidateAssertion` |
| 6 | **Scope** | `scope_candidates` | [06 scope_context](./06-scope-context.md) | G2 | 후보 → `scoped_candidate`(언제/어디서) |
| 7 | **Confirmation** | `review_candidates` | [07 confirmation_gate](./07-confirmation-gate.md) | G3 | 사람 검토 → `review_status` 확정 |
| 8 | **Pack Router** | `route_confirmed` | [08 pack_router](./08-pack-router.md) | G6 | 확정 후보 → 14 `user.*` 중 1개로 승격 |
| 9 | **Boundary** | `route_confirmed` | [09 privacy_boundary](./09-privacy-boundary.md) | G5 | 민감 후보 → `BoundaryRule`(범주+권한) |
| 10 | **Agent Compiler** | `compile_runtime` | [10 agent_compiler](./10-agent-compiler.md) | G3 | 확인 슬라이스 → `AssistantProfile` 어댑터 |
| 11 | **Evaluator** | `evaluate_output` → `record_drift_or_update` | [11 evaluation_drift](./11-evaluation-drift.md) | — | profile 채점 + `DriftRecord` → ↺S01 |
| 12 | **Pack Architect** | *(척추, 단계 아님)* | [13 kernel_schema](./13-kernel-schema.md) | 정의 | 모든 단계가 먼저 읽는 스키마 척추 정의 |

> 소유 규칙: 한 상태 = 한 소유 역할. 예외는 `mine_or_ask`(세 역할이 *한 상태*를 공유, 경로
> 선택은 오케스트레이터)와 Evaluator(*두 상태*를 한 역할이 닫음)뿐입니다. **Pack Architect**는
> 상태를 소유하지 않는 *척추 역할*이라 9개 상태 밖에 있지만, QA가 스키마 결함을 가리키면
> 오케스트레이터가 작업을 이 역할로 되돌립니다(§5 R3).

## 4. 9개 워크플로 상태와 핸드오프 계약 (Handoff contracts)

오케스트레이터가 강제하는 핸드오프는 *상태→상태* 전이이며, 각각 **트리거 조건 · 입력 노드 ·
출력 노드**를 가집니다. 아래 표가 전이의 **유일한 계약 목록**입니다. 트리거가 만족되고
출력 계약이 검증되어야만 다음 상태로 전진합니다.

| ID | 트리거(전제 충족) | from 상태 / 역할 | → to 상태 / 역할 | 입력 노드 | 출력 노드 | 게이트 |
|----|-------------------|------------------|-------------------|-----------|-----------|--------|
| H1 | 새 원시 신호 도착 | *(외부)* → Evidence | `collect_evidence` | 원시 신호 | `EvidenceItem` | G1(전제) |
| H2 | **evidence complete** (증거 포착·정규화 완료) | `collect_evidence` / Evidence | `mine_or_ask` / **Session Miner · Questioning · Diff Miner** | `EvidenceItem` | 타입 미지정 후보 신호 + 근거 증거 | G1 |
| H3 | 채굴 신호 확보 | `mine_or_ask` / 채굴 트리오 | `extract_candidates` / Candidate Extractor | 후보 신호 + `EvidenceItem` | 타입 지정 `CandidateAssertion` | G1·G4 |
| H4 | **candidate extracted** (타입·증거·`concise_claim` 완비) | `extract_candidates` / Candidate Extractor | `scope_candidates` / **Scope** | `CandidateAssertion` | `scoped_candidate`(비어있지 않은 `scope`+예외+시간) | G2 |
| H5 | **scope assigned** (스코프·`Context`/`Condition` 연결) | `scope_candidates` / Scope | `review_candidates` / **Confirmation** | `scoped_candidate` | `review_status` 찍힌 후보 | G3(결정점) |
| H6 | **confirmed** (`confirmed`/`narrowed`/편집 확정) | `review_candidates` / Confirmation | `route_confirmed` / **Pack Router** | confirmed/narrowed 후보 | `promoted_to` (14 `user.*` 중 1) | G6 |
| H6b | 민감 후보(`sensitive`/`restricted`) | `review_candidates` / Confirmation | `route_confirmed` / **Boundary** *먼저* | 민감 후보 | `BoundaryRule`(범주+권한) → 그 뒤 Pack Router 재개 | G5 |
| H7 | **routed** (도착지 팩에 베이스 레코드 적재) | `route_confirmed` / Pack Router | `compile_runtime` / **Agent Compiler** | 확정 인스턴스 슬라이스 + `BoundaryRule` | `AssistantProfile`(`compiled_into`) | G3 재확인 |
| H8 | **runtime output** (에이전트가 작업 산출) | `compile_runtime` / Agent Compiler | `evaluate_output` / **Evaluator** | `AssistantProfile` 산출 + `EvaluationCase` | 8개 지표 채점 결과 | — |
| H9 | 변경·실패·모순 검출 | `evaluate_output` / Evaluator | `record_drift_or_update` / Evaluator | 채점 결과 | `DriftRecord`(`supersedes`) → **↺ S01** | — |

핸드오프 해설:

- **H2 (evidence complete → 채굴 트리오).** 한 상태(`mine_or_ask`)에 세 역할이 묶여 있으므로
  오케스트레이터가 *경로를 고릅니다*: 누적 세션이면 **Session Miner**, 빈 영역·모호 신호면
  **Questioning**, before/after 교정 쌍이면 **Diff Miner**(가장 강한 경계 신호). 셋 다 출력은
  ≥1 `EvidenceItem`에 묶인 후보 신호여야 합니다(G1 보존).
- **H4 (candidate extracted → scope).** 후보가 `candidate_type` 14개 중 하나로 타입 지정되고
  증거에 묶였을 때만 Scope로 넘깁니다. 타입이 14개 밖이면 H4는 *발화되지 않고*, 추출 결함으로
  되돌립니다(§5 R1).
- **H5 (scope assigned → confirmation).** 비어있지 않은 `scope`(G2)가 채워진 `scoped_candidate`만
  사람 검토로 갑니다. 여기서 라이프사이클 `user_reviewed → confirmed_or_rejected` 전이가 일어납니다.
- **H6 (confirmed → router).** `confirmed`/`narrowed`/편집 확정만 Pack Router로 전진합니다.
  `pending`/`rejected`/`deferred`는 H6가 발화되지 않습니다(G3 — 미확정의 런타임 승격 금지).
- **H6b (민감 → boundary 먼저).** `sensitivity`가 `sensitive`/`restricted`면 **Boundary가
  `BoundaryRule`을 *먼저* 붙인 뒤에만** Pack Router가 적재합니다(G5 — 승격 전 프라이버시). 경계가
  붙기 전 라우팅을 시도하면 오케스트레이터가 차단합니다.
- **H7 (routed → compiler).** 팩에 적재된 것과 *런타임 활성*은 별개입니다. 컴파일러는 작업에
  닿는 *슬라이스만* 켜고, `confirmed`/`narrowed`만 포함합니다(G3 재확인).
- **H8 (runtime output → evaluator).** 에이전트가 작업을 산출하면 `EvaluationCase`로 8개 지표
  (decision_fidelity·red_flag_recall·rejection_alignment·artifact_fit·boundary_compliance·
  evidence_traceability·correction_cost·drift_score)를 채점합니다([05 평가·드리프트](../spec/05-evaluation-drift.md)).
- **H9 (드리프트 → 루프).** 실패·변경·모순은 `DriftRecord`로 기록되고(`supersedes`로 옛 레코드
  대체), 새 증거로 **S01로 되돌아가 루프를 잇습니다**. 파이프라인은 끝나지 않고 수렴합니다.

## 5. QA 실패 시 되돌림 규칙 (Routing back on QA failure)

오케스트레이터의 *판단 핵심*은 "전진할까"가 아니라 "**이 작업 단위가 다음 상태로 갈 자격이
있는가**"입니다. 게이트(G1–G6)나 단계 품질검사가 실패하면 전진을 멈추고 **결함을 소유한 상류
역할로 되돌립니다**. 추측으로 봉합하지 않습니다. 되돌림 도착지는 결함의 *종류*가 결정합니다.

| QA 실패 종류 | 위반 게이트 | 되돌림 도착지 (소유 역할) | 근거 |
|--------------|-------------|----------------------------|------|
| 타입 결함 (타입이 14개 밖, 도착지 못 찾음, 오타입) | — / G1 | **Candidate Extractor** (`extract_candidates`) | 타입 부여는 추출의 소유권. 라우터는 재분류하지 않는다 |
| 증거 없는 후보 (`evidence_refs` < 1) | G1 | **Candidate Extractor** | 증거에 다시 묶거나 후보 폐기 |
| 행동 언어 위반 (추측된 심리) | G4 | **Candidate Extractor** | 관찰된 행동으로 재기술 |
| 스코프 없음/과도하게 넓음 | G2 | **Scope** (`scope_candidates`) | 언제/어디서로 다시 좁힘 |
| 민감 항목이 경계 없이 라우팅 시도 | G5 | **Boundary** (`route_confirmed`) | `BoundaryRule`을 먼저 부착 후 재개 |
| 미확정 후보가 팩/컴파일로 누출 | G3 | **Confirmation** (`review_candidates`) | 사람 검토로 되돌려 확정/거부 |
| 스키마 결함 (필드 표류, enum 불일치, 베이스 위반) | 정의 | **Pack Architect** (척추, [13](./13-kernel-schema.md)) | 스키마/계약 자체의 결함은 척추가 소유 |
| 템플릿에 라이브 레코드 적재 | G6 | **Pack Router** (`route_confirmed`) | 적재 대상을 인스턴스 팩으로 교정 |

되돌림 규칙(불변):

1. **결함은 소유자에게.** 오케스트레이터는 결함을 *직접 고치지 않습니다.* 타입 결함은 Candidate
   Extractor로, 스코프 결함은 Scope로, 경계 누락은 Boundary로, 스키마 결함은 Pack Architect로
   되돌립니다. 관제탑이 내용을 손대면 감사 사슬(증거→후보→팩)이 끊깁니다.
2. **전진은 계약 충족 시에만.** 출력 계약(§4 표의 출력 노드)을 못 채운 핸드오프는 발화되지
   않습니다. 게이트 실패는 *조용한 통과*가 없습니다 — 차단되거나 되돌려집니다.
3. **되돌림은 손실이 아니다.** 거부·보류·되돌림된 작업 단위는 보존되어 [수렴 지표](../spec/06-convergence-model.md)의
   `confirmation_ratio` 분모에 들어가고, 되돌림 사유는 다음 채굴 라운드의 신호가 됩니다(H9 루프와 합류).

> 교착(deadlock) 방지: 같은 작업 단위가 같은 상류로 N회 이상 되돌려지면 오케스트레이터는 무한
> 재시도 대신 `deferred`로 보류하고 갭으로 로깅합니다(추측으로 통과시키지 않음). 보류는 [11
> 평가·드리프트](./11-evaluation-drift.md)의 갭 신호가 됩니다.

## 6. 입력 / 출력 (Inputs / Outputs)

### 입력

- **주 입력:** 라이프사이클 *어느 지점*에 있는 작업 단위(원시 신호 / `EvidenceItem` / 후보 /
  레코드 / 프로필)와 그 **현재 워크플로 상태**(9개 중 하나).
- **부 입력:** 각 상태의 소유 역할 정의(§3 표), 핸드오프 계약(§4 표), 게이트 정의([커널 §2](../spec/01-kernel-schema.md)),
  단계별 품질검사 결과(각 스킬 문서의 "품질 검사" 절).

### 출력

작업 단위당 **상태 전이 결정 하나** — 전진 / 되돌림 / 보류. 출력은 다음을 만족합니다.

- 전진이면 다음 상태의 소유 역할에 *계약을 만족하는 입력 노드*가 전달됨(§4 입력 노드 열).
- 되돌림이면 결함을 소유한 상류 역할로 작업 단위 + 위반 게이트·사유가 전달됨(§5 표).
- 보류면 `deferred`로 큐에 보존되고 갭으로 로깅됨(§5 교착 방지).
- 어떤 출력도 *내용을 변형*하지 않음 — 오케스트레이터는 노드를 만들거나 고치지 않습니다(경계).

### 최소 예시 (한 작업 단위의 상태 추적)

```yaml
# 작업 단위: logotekton.candidate.041 (코드 리뷰 결론-우선 교정에서 추출)
work_unit: logotekton.candidate.041
trace:
  - state: collect_evidence      # Evidence → EvidenceItem 088,089 포착 (G1 전제)
    handoff: H2                  # evidence complete → Diff Miner (before/after 교정 쌍)
  - state: mine_or_ask           # Diff Miner → 교정 신호
    handoff: H3                  # → Candidate Extractor
  - state: extract_candidates    # CommunicationStyleCandidate 타입 지정 (G1·G4 통과)
    handoff: H4                  # candidate extracted → Scope
  - state: scope_candidates      # scope="코드 리뷰 보고서 초안(내부 청중)" (G2 통과)
    handoff: H5                  # scope assigned → Confirmation
  - state: review_candidates     # 사람: narrowed (스코프 좁힘) — G3 결정점
    handoff: H6                  # confirmed/narrowed → Pack Router
  - state: route_confirmed       # → user.communication_style 적재 (G6)
    handoff: H7                  # routed → Agent Compiler
  - state: compile_runtime       # 코드 리뷰 슬라이스에 포함 (G3 재확인)
    handoff: H8                  # runtime output → Evaluator
  - state: evaluate_output       # decision_fidelity 채점
    handoff: H9                  # (이번엔 드리프트 없음 → 루프 대기)
gate_blocks: []                  # 되돌림 없음. 모든 핸드오프가 계약 충족
```

이 추적에서 오케스트레이터는 *내용을 한 번도 만들지 않았습니다.* 각 상태의 소유 역할이 노드를
만들고, 오케스트레이터는 H2–H9 핸드오프의 *계약 충족 여부*만 검증하며 상태를 전진시켰습니다.
만약 `extract_candidates`에서 타입이 14개 밖이었다면 H4가 발화되지 않고 Candidate Extractor로
되돌아갔을 것이고(§5), `sensitivity`가 `restricted`였다면 H6 대신 H6b로 Boundary가 먼저
개입했을 것입니다.

## 7. 품질 검사 (Quality checks)

오케스트레이터가 상태를 전진시키기 전, 다음을 강제합니다. 코드 강제는
[`tools/validate_packs.py`](../tools/validate_packs.py)와 각 단계 스키마가 보조합니다.

- [ ] **모든 상태에 소유자(single owner)** — 9개 상태 각각이 §3 표의 *정확히 하나*의 Crab
  역할에 매핑됐는가. 소유자 없는 상태/소유자 둘인 상태가 없는가(`mine_or_ask`의 세 역할은
  *경로 선택*이지 공동 소유가 아님 — 한 작업 단위는 한 역할만 탄다).
- [ ] **모든 핸드오프에 입출력 계약** — 발화된 모든 핸드오프(H1–H9)가 §4 표의 *입력 노드 →
  출력 노드* 계약을 만족하는가. 계약 없는 임의 전이가 없는가.
- [ ] **게이트 차단 동작(G1–G6)** — 게이트 실패 시 전진을 *멈추고* 되돌렸는가(§5). 게이트를
  *조용히 통과*시킨 작업 단위가 하나도 없는가. 특히 G3(미확정 누출)·G5(경계 전 라우팅)·
  G1(증거 없는 후보)에서 차단했는가.
- [ ] **되돌림 도착지 정확** — QA 실패를 *결함 소유자*로 되돌렸는가(타입→Extractor, 스코프→Scope,
  경계→Boundary, 미확정→Confirmation, 스키마→Pack Architect; §5 표). 오케스트레이터가 내용을
  *직접 고치지* 않았는가(경계).
- [ ] **채굴 경로 선택** — `mine_or_ask`에서 증거 성격에 맞는 역할(세션→Session Miner,
  빈영역→Questioning, 교정쌍→Diff Miner)을 골랐는가(H2).
- [ ] **민감 우선순위(H6b)** — `sensitive`/`restricted` 후보가 Boundary의 `BoundaryRule` *뒤에만*
  Pack Router로 갔는가(G5). 경계 전 라우팅 시도를 차단했는가.
- [ ] **루프 폐쇄(H9)** — 드리프트가 `DriftRecord`로 기록되고 `supersedes`로 옛 레코드를
  대체한 뒤 **S01로 되돌아가** 루프가 닫혔는가. 파이프라인이 한 방향으로 끝나지 않고 순환하는가.
- [ ] **교착 방지** — 같은 작업 단위의 무한 되돌림 대신, N회 초과 시 `deferred` 보류 + 갭
  로깅했는가(§5 교착 방지).
- [ ] **상태 추적성** — 각 작업 단위의 *현재 상태*와 *핸드오프 이력*이 기록되어, 증거→후보→팩→
  프로필 경로가 역추적 가능한가(추적성=1.0, [수렴 모델](../spec/06-convergence-model.md)).
- [ ] **경계 준수** — 오케스트레이터가 노드를 *만들거나 변형*하지 않았는가. 내용 판단(진위·타입·
  스코프·민감도)을 소유 역할에 위임했는가(관제탑은 전이만 관장).

## 8. Crab 역할 — Orchestrator Crab

이 스킬의 소유 역할은 **Orchestrator Crab**입니다([커널 §8](../spec/01-kernel-schema.md#8-crab-에이전트-역할-운영-모델),
[파이프라인 §4](../spec/02-builder-pipeline.md#4-단계--스킬--crab-역할--게이트-요약표)). 13개 역할
중 *유일하게 상태를 소유하지 않고 9개 상태 전체를 관장*합니다.

- **소유 작업:** 9개 워크플로 상태의 전이·핸드오프(§4 H1–H9)·재시도·게이트 차단·되돌림(§5).
  각 상태를 §3 표의 단일 소유 역할에 디스패치하고, 출력 계약과 게이트를 검증해 전진/되돌림/보류를
  결정합니다.
- **받는 핸드오프:** 모든 실행 역할(Evidence … Evaluator)이 상태를 마치면 오케스트레이터에 결과를
  반환합니다. 외부에서 새 원시 신호가 들어오면 H1로 기동합니다.
- **넘기는 핸드오프:** 다음 상태의 소유 역할에 계약을 만족하는 입력 노드를 전달(전진), 또는 결함
  소유 상류 역할에 위반 사유와 함께 작업 단위를 반환(되돌림). H9에서 Evaluator가 닫은 드리프트는
  새 증거로 Evidence(S01)에 되먹입니다.
- **경계:** 노드를 *만들지도 변형하지도* 않습니다. 후보의 진위(S07)·타입(S05)·스코프(S06)·
  민감도(S09)·도착지 팩(S08)을 *직접 판정하지 않습니다* — 그 판단을 *누가 언제 하는지*와 *그
  결과가 계약을 만족하는지*만 관장합니다. 게이트를 임의로 면제하지 않고, 결함을 들고 다음 상태로
  밀지 않습니다. 오케스트레이터는 *결정적·투명*해야 파이프라인 전체가 감사 가능합니다.

OpenCrab 도구로 실행할 때는 `opencrab_list_workflows`로 정의된 워크플로 상태를 확인하고,
`opencrab_run_workflow`/`opencrab_workflow_manage`로 상태 전이를 구동하며, 각 상태의 소유
역할은 `opencrab_crab_agent`로 디스패치합니다. 상태별 노드 진척은 `opencrab_list_nodes`/
`opencrab_get_node_context`로 추적하고, 핸드오프 전후 검증은 `opencrab_pack_qa`로,
프로젝트 단위 오케스트레이션은 `opencrab_project_run`/`opencrab_project_manage`로 관장합니다.

> 9-space 사상: 오케스트레이션은 특정 한 공간이 아니라 `lever`(workflow 단계·전이) 공간에서
> 동작하며, 상태 전이 자체가 `WorkflowPattern`의 시퀀스로 사상됩니다. 게이트 차단·되돌림은
> `policy` 공간(게이트는 정책)으로, 채점·되먹임은 `outcome` 공간으로 흐릅니다([07 9-space
> 크로스워크](../spec/07-opencrab-9space-crosswalk.md)).

## 9. 관련 문서

- 9개 상태 ↔ 12단계 매핑·각 단계 입출력 계약 → [02 빌더 파이프라인](../spec/02-builder-pipeline.md)
- 라이프사이클·노드·엣지·게이트(G1–G6)·역할 목록 → [01 커널 스키마](../spec/01-kernel-schema.md)
- 각 상태의 소유 스킬(실행 지침) → [01](./01-evidence-capture.md) · [02](./02-session-mining.md) ·
  [03](./03-elicitation-questioning.md) · [04](./04-diff-mining.md) · [05](./05-candidate-extraction.md) ·
  [06](./06-scope-context.md) · [07](./07-confirmation-gate.md) · [08](./08-pack-router.md) ·
  [09](./09-privacy-boundary.md) · [10](./10-agent-compiler.md) · [11](./11-evaluation-drift.md)
- 척추(Pack Architect가 소유하는 스키마 정의) → [13 커널 스키마 스킬](./13-kernel-schema.md)
- 민감 후보의 경계·권한 우선순위(H6b, G5) → [04 프라이버시·경계](../spec/04-privacy-boundary.md)
- Evaluator가 채점하는 지표·드리프트(H8·H9) → [05 평가·드리프트](../spec/05-evaluation-drift.md)
- 되돌림·보류가 들어가는 수렴 지표(추적성=1.0) → [06 수렴 모델](../spec/06-convergence-model.md)
- 상태 전이의 9-space 사상(`lever`·`policy`·`outcome`) → [07 9-space 크로스워크](../spec/07-opencrab-9space-crosswalk.md)
