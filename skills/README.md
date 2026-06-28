# skills/ — 빌더 스킬 색인 (Builder Skills Index)

> **EN:** This is the index for the 13 builder skills of Personal Agent Builder (v0.3) — the
> `skill.pab.*` process packs that say *how* to turn raw session signals into a compiled
> Personal Agent. Skills `01`–`12` are the runnable pipeline in execution order; `13`
> (`kernel_schema`) is not a step but the shared schema spine every skill reads first. Each
> skill owns exactly one pipeline step and one Crab role; the full step→skill→role→gate
> mapping lives in [`../spec/02-builder-pipeline.md`](../spec/02-builder-pipeline.md).

이 폴더는 13개 **빌더 스킬**(`skill.pab.*`) 문서입니다. 스킬은 *방법*(HOW)을 규정합니다 —
원시 신호 한 조각을 어떻게 증거에 묶고, 스코프를 주고, 사람의 확인을 거쳐, 14개 `user.*`
팩으로 라우팅하고, 런타임으로 컴파일해, 평가·드리프트 루프로 되돌리는지의 운영 절차입니다.
각 문서는 마케팅이 아니라 **그대로 따라 돌릴 수 있는 지침**으로 작성되어 있습니다.

핵심 규칙: **13개 스킬, 12개 단계.** 스킬 `01`–`12`는 파이프라인 순서대로 실행되는 단계이고,
`13 kernel_schema`는 단계가 아니라 모든 단계가 먼저 읽는 **스키마 척추**입니다(= [`01 커널
스키마`](../spec/01-kernel-schema.md)). 한 단계 = 한 스킬 = 한 Crab 역할이며, 모든 핸드오프는
입력/출력 계약과 품질 게이트(G1–G6)로 강제됩니다. 어휘는 [커널 스키마](../spec/01-kernel-schema.md),
필드 규약은 [통합 베이스 레코드](../schemas/record.base.schema.json)를 따릅니다.

## 스킬 목록 (파이프라인 순서)

| 스킬 | 단계 / 상태 | Crab 역할 | 한 줄 설명 | EN one-liner |
|------|-------------|-----------|-----------|--------------|
| [`01-evidence-capture.md`](./01-evidence-capture.md) | S01 · `collect_evidence` | Evidence | 원시 신호(세션·교정·파일·인터뷰)를 정규화된 `EvidenceItem`으로 포착 — 모든 레코드가 가리키는 진실의 출처. | Captures raw signals into normalized `EvidenceItem` nodes — the source of truth every later record points back to. |
| [`02-session-mining.md`](./02-session-mining.md) | S02 · `mine_or_ask` | Session Miner | 누적 세션 증거에서 반복 패턴·선호·거부를 채굴해 (아직 타입 없는) 후보 신호를 낸다. | Mines accumulated session evidence for recurring patterns, preferences, and rejections into untyped candidate signals. |
| [`03-elicitation-questioning.md`](./03-elicitation-questioning.md) | S03 · `mine_or_ask` | Questioning | 빈 영역·모호 신호를 구조화 에피소드 인터뷰로 메워 새 `EvidenceItem`을 만든다. | Fills empty or ambiguous areas with structured episode interviews, producing new `EvidenceItem`s. |
| [`04-diff-mining.md`](./04-diff-mining.md) | S04 · `mine_or_ask` | Diff Miner | before/after 교정 쌍에서 가장 강한 경계 신호를 추출한다. | Extracts the strongest boundary signals from before/after correction pairs. |
| [`05-candidate-extraction.md`](./05-candidate-extraction.md) | S05 · `extract_candidates` | Candidate Extractor | 채굴 신호를 14개 타입 중 하나의 `CandidateAssertion`으로 만든다(증거·행동 언어 강제). | Turns mined signals into typed `CandidateAssertion`s, one of the 14 types, in behavioral language. |
| [`06-scope-context.md`](./06-scope-context.md) | S06 · `scope_candidates` | Scope | "항상 참" 후보를 *언제/어디서* 참인지로 좁혀 비어있지 않은 `scope`를 부여한다. | Narrows "always true" candidates into where/when they hold, assigning a non-empty `scope`. |
| [`07-confirmation-gate.md`](./07-confirmation-gate.md) | S07 · `review_candidates` | Confirmation | 사람이 confirm/edit/reject/narrow/sensitive/defer로 검토 — 미확인의 런타임 승격을 막는 결정 지점. | The human review gate (confirm/edit/reject/narrow/sensitive/defer) that blocks runtime promotion of unconfirmed candidates. |
| [`08-pack-router.md`](./08-pack-router.md) | S08 · `route_confirmed` | Pack Router | 확인된 후보를 14개 `user.*` 팩 중 하나로 1:1 결정론적 라우팅(`promoted_to`). | Routes confirmed candidates deterministically (1:1) into one of the 14 `user.*` packs. |
| [`09-privacy-boundary.md`](./09-privacy-boundary.md) | S09 · `route_confirmed` | Boundary | sensitive/restricted 항목에 경계 범주+권한 레벨의 `BoundaryRule`을 먼저 부착(승격 전 프라이버시). | Attaches a `BoundaryRule` (category + authority level) to sensitive items before promotion. |
| [`10-agent-compiler.md`](./10-agent-compiler.md) | S10 · `compile_runtime` | Agent Compiler | 확인된 레코드 슬라이스를 `*.runtime_adapter`로 컴파일해 `AssistantProfile`(= Personal Agent)을 만든다. | Compiles confirmed record slices into an `AssistantProfile` runtime adapter — the Personal Agent. |
| [`11-evaluation-drift.md`](./11-evaluation-drift.md) | S11 · `evaluate_output` → `record_drift_or_update` | Evaluator | 8개 충실도 지표로 프로필을 채점하고 변경을 `DriftRecord`로 기록해 루프를 닫는다. | Scores the profile on eight fidelity metrics and records change as `DriftRecord`s, closing the loop. |
| [`12-crab-orchestration.md`](./12-crab-orchestration.md) | *(전 상태)* · 관제탑 | Orchestrator | 9개 워크플로 상태의 전이·핸드오프·재시도·게이트 차단을 관장(레코드를 직접 만들지 않음). | The control tower governing all 9 workflow state transitions, handoffs, retries, and gate blocks. |
| [`13-kernel-schema.md`](./13-kernel-schema.md) | *(척추, 단계 아님)* | Pack Architect | 모든 스킬이 먼저 읽는 공유 스키마 척추(= [`01 커널 스키마`](../spec/01-kernel-schema.md)). | The shared schema spine every skill reads first (= [`spec/01`](../spec/01-kernel-schema.md)). |

## 파이프라인 한 장 그림

스킬이 어떻게 연결되는지 — 채굴 트리오(S02/S03/S04)는 한 상태(`mine_or_ask`)를 공유하고,
S11은 평가→드리프트의 두 상태로 루프를 닫으며, S12는 전 상태를 위에서 관장합니다. 전체 계약·
게이트 매핑은 [`02 빌더 파이프라인`](../spec/02-builder-pipeline.md)에 있습니다.

```
  ┌────────────────────────────────────────────────────────────────────────┐
  │  S12 crab_orchestration — 9개 상태 전이·핸드오프·게이트 차단 관장 (관제탑) │
  └────────────────────────────────────────────────────────────────────────┘
        ▲          ▲          ▲          ▲          ▲          ▲

   세션/파일 ─┐                 S02 session_mining ┐
   교정/diff ─┤   S01           S03 questioning    ├─► S05            S06          S07
   인터뷰    ─┘   evidence ───► S04 diff_mining    ┘   candidate ───► scope ─────► confirmation
                  _capture      (raw signals)          _extraction    _context     _gate
                  (G1 증거)                            (typed, G4)    (G2 스코프)  (사람 검토; G3)
                      │                                                                │
                      ▼                                                  confirmed/narrowed만
                 EvidenceItem ──────────────────────────────────────────────────────► │
                                                                                       ▼
                          S08 pack_router ──► S09 privacy_boundary ──► S10 agent_compiler
                          (14 user.* 1:1     (boundary+authority;      (확인 슬라이스만 →
                           라우팅; G6)        승격 전 G5)               runtime adapter; G3)
                                │                                              │
                                ▼                                              ▼
                          UserOntologyPack ───────────────────────────► AssistantProfile
                                                                               │
                                                                               ▼
                                                                      ┌─────────────────┐
                                                                      │  Personal Agent │
                                                                      └────────┬────────┘
                                                                               ▼
   ┌─────────────────────── 루프 ◄────────────  S11 evaluation_drift  ◄───────┘
   │  record_drift_or_update          evaluate_output:
   │  DriftRecord → supersedes         8개 지표 채점(decision_fidelity·correction_cost…)
   │  → 새 증거로 재포착 (↺ S01)
   └──────────────────────────────────────────────────────────────────────────►

  공유 척추(모든 단계가 먼저 읽음):  S13 kernel_schema  →  ../spec/01-kernel-schema.md
```

## 인접 폴더

- [`../spec/`](../spec) — 정규 사양. 단계별 입력/출력 계약과 게이트 매핑은
  [`02 빌더 파이프라인`](../spec/02-builder-pipeline.md), 어휘는
  [`01 커널 스키마`](../spec/01-kernel-schema.md).
- [`../schemas/`](../schemas) — 라우팅 도착지인 14개 `user.*` 팩 + 통합 베이스 레코드의
  JSON Schema. 베이스: [`../schemas/record.base.schema.json`](../schemas/record.base.schema.json).
- [`../templates/`](../templates) — 새 사용자용 빈 채우기 템플릿 + [QUICKSTART](../templates/QUICKSTART.md).
- [`../tools/`](../tools) — 게이트를 코드로 강제하는 검증·수렴 지표 스크립트.

> 규칙: 스킬 문서는 [Canonical Design Contract(v0.3)]를 따릅니다. 정식 이름(13개 스킬,
> 14개 `user.*` 팩, 14개 후보 타입)만 사용하며, 구 코드명(`pa.t03`, `t06`, `x12`, `.ba` 등)은
> [`../spec/08-naming-and-ids.md`](../spec/08-naming-and-ids.md)의 이전표에서만 언급됩니다.

> 각 스킬은 **발화 트리거**(언제 켜지는가)를 가집니다 — 문서 하단의 `## 트리거` 절. 전체 2계층
> 모델·훅 매핑은 [../spec/09-triggers.md](../spec/09-triggers.md), 스키마는
> [../schemas/trigger.schema.json](../schemas/trigger.schema.json).
