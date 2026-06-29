# 01 · 커널 스키마 (Kernel Schema)

> **EN:** The shared schema every builder skill and every pack reads first. Defines node
> types, edge types, the evidence-bound lifecycle, six quality gates, the unified base
> record, and the candidate-type↔pack routing (1:1, total). This is the v0.3 reconciliation
> of the earlier `skill.pab.kernel_schema` pack.

커널 스키마는 시스템의 **척추**입니다. 모든 스킬, 템플릿, 인스턴스가 이 정의를 기준으로
삼습니다. 여기서 어휘를 고정하므로, 다른 문서는 새로운 이름을 만들지 않고 이 목록을 씁니다.

## 1. 라이프사이클 (the spine)

원시 신호에서 런타임 규칙까지 모든 항목은 한 방향으로 흐릅니다:

```
raw_signal
  → evidence_bound_candidate   (증거에 묶임)
  → scoped_candidate           (적용 범위 지정)
  → user_reviewed              (사람이 검토)
  → confirmed_or_rejected      (승인/거부)
  → target_pack_ingested       (팩에 저장)
  → shadow_validated           (컴파일된 프로필을 활성 *전* NO-ACT 재생·무회귀 확인)
  → runtime_activated          (런타임에서 사용)
```

원시 사용자 발언은 **최종 규칙이 아닙니다.** 이 흐름을 강제하는 것이 시스템 신뢰의 근거입니다.
**`shadow_validated`** 는 컴파일된 슬라이스가 곧장 라이브가 되지 않도록 한 칸을 둡니다 — 새 프로필을
`regression_for` 케이스와 과거 세션에 **행동 없이(NO-ACT)** 재생해 회귀가 없을 때만 활성화합니다
([02 파이프라인 S10½](./02-builder-pipeline.md), shadow mode는 [12 확인 정책 §4.3](./12-confirmation-policy.md)).

## 2. 품질 게이트 (Quality Gates)

| ID | 규칙 | 의미 |
|----|------|------|
| G1 | No evidence-free claim | 모든 `CandidateAssertion`은 ≥1개 `EvidenceItem`에 `supported_by` |
| G2 | No unscoped heuristic | 모든 레코드는 비어있지 않은 `scope`를 가짐 |
| G3 | No runtime activation of pending | `confirmed`/`narrowed`/편집된 항목만 런타임 활성화 |
| G4 | Behavioral language only | 추측된 심리가 아니라 관찰된 행동으로 기술 |
| G5 | Privacy before promotion | 민감 항목은 경계 규칙을 먼저 받음 |
| G6 | Template/instance separation | 템플릿은 라이브 레코드를 담지 않음 |

검증 게이트는 코드로도 강제됩니다 → [`tools/validate_packs.py`](../tools/validate_packs.py).

## 3. 노드 타입 (Node Types)

| 노드 | 설명 |
|------|------|
| `UserSubject` | 원천 사용자 (에이전트의 주인) |
| `AssistantProfile` | 확인된 팩에서 생성된 통제된 런타임 프로필 |
| `EvidenceItem` | 세션·답변·교정·파일·메시지·diff·산출물·노트·로그 등 출처 |
| `CandidateAssertion` | 검토 대기 중인 타입 지정 추출물 |
| `IdentityRole` | 역할·정체성·맥락 |
| `PersonaTrait` | 안정적 선호/반선호/가치/작업 성향 |
| `CommunicationStyleRule` | 응답 형식·언어·구조·밀도 규칙 |
| `ArtifactPolicy` | 선호 출력물 형태 (Markdown, 표, 파일, 리뷰보드 등) |
| `DecisionPolicy` | 우선순위·트레이드오프·승인/거부 조건·에스컬레이션 |
| `TacitHeuristic` | 반복 행동·교정·대조 설명에서 추출한 암묵 판단 규칙 |
| `RedFlag` | 사용자가 위험/약한 구조/빈약한 근거로 취급하는 신호 |
| `WorkflowPattern` | 작업·결정을 수행하는 반복 시퀀스 |
| `DomainOverlay` | 도메인 특화 지식/주의 패턴 |
| `ToolPreference` | 도구 선택·사용 패턴 |
| `BoundaryRule` | 런타임이 무엇을 할 수 있고 무엇이 확인을 요하는가 |
| `ProjectMemory` | 프로젝트·목표·메모리 링크 |
| `EvaluationCase` | 사용자 판단 대비 충실도 측정 테스트 케이스 |
| `DriftRecord` | 변경·대체·감쇠·모순·갱신 이동 |
| `Context`, `Condition`, `Artifact`, `UserOntologyPack` | 보조 노드 |

## 4. 엣지 타입 (Edge Types)

| 엣지 | from → to |
|------|-----------|
| `supported_by` | CandidateAssertion → EvidenceItem |
| `extracted_from` | CandidateAssertion → EvidenceItem |
| `applies_in` | record → Context |
| `prioritizes` | UserSubject → DecisionPolicy |
| `rejects_when` | UserSubject → RedFlag \| Condition |
| `produces` | WorkflowPattern → Artifact \| ArtifactPolicy |
| `requires_confirmation` | Action \| BoundaryRule → UserSubject |
| `promoted_to` | CandidateAssertion → UserOntologyPack |
| `compiled_into` | UserOntologyPack → AssistantProfile |
| `supersedes` | DriftRecord → record |
| `evaluated_by` | AssistantProfile → EvaluationCase |
| `maps_to` | node → NineSpaceNode (→ [07-crosswalk](./07-opencrab-9space-crosswalk.md)) |

## 5. 14개 user 온톨로지 팩 (정식 이름)

이전 코드명(`pa.t03`, `t06`, `x12`, `.ba` 등)은 **폐기**되고 아래 정식 이름으로 통일됩니다.

| # | 정식 이름 | 의미 | 구 코드명 |
|---|-----------|------|-----------|
| 1 | `user.identity_roles` | 역할·정체성·맥락 | pa.roles |
| 2 | `user.persona_core` | 안정 선호/가치/우선순위 | pa.core |
| 3 | `user.communication_style` | 응답 형식/언어/구조 | pa.t03 |
| 4 | `user.artifact_policy` | 선호 출력물 형태 | pa.t04 |
| 5 | `user.decision_policy` | 우선순위/거부/승인 규칙 | pa.t05 |
| 6 | `user.tacit_heuristics` | 암묵 판단 규칙 | t06 |
| 7 | `user.red_flags` | 위험 신호 | t07 |
| 8 | `user.workflow_playbooks` | 반복 작업 시퀀스 | t08 |
| 9 | `user.domain_overlays` | 도메인 특화 지식 | t09 |
| 10 | `user.tool_stack` | 도구/사용 패턴 | t10 |
| 11 | `user.boundary_authority` | 프라이버시/권한 규칙 | t11, .ba |
| 12 | `user.memory_project_graph` | 프로젝트·목표·메모리 | x12 |
| 13 | `user.evaluation_cases` | 충실도 테스트 케이스 | x13 |
| 14 | `user.drift_history` | 변경·버전 이력 | x14 |

자세한 팩별 정의 → [03-pack-catalog](./03-pack-catalog.md). 각 팩의 JSON Schema → [`schemas/`](../schemas).

## 6. 후보 타입 ↔ 라우팅 (1:1, 전수)

이전 버전은 후보 타입 11개 vs 라우팅 13개로 불일치했습니다. v0.3에서 **14개 후보 타입을
14개 팩에 1:1 전수 매핑**하여 라우터를 완전(total)하게 만들었습니다.

| candidate_type | → user pack |
|----------------|-------------|
| `IdentityRoleCandidate` | `user.identity_roles` *(신규 — 누락이었음)* |
| `PersonaTraitCandidate` | `user.persona_core` |
| `CommunicationStyleCandidate` | `user.communication_style` |
| `ArtifactPolicyCandidate` | `user.artifact_policy` |
| `DecisionPolicyCandidate` | `user.decision_policy` |
| `TacitHeuristicCandidate` | `user.tacit_heuristics` |
| `RedFlagCandidate` | `user.red_flags` |
| `WorkflowPatternCandidate` | `user.workflow_playbooks` |
| `DomainOverlayCandidate` | `user.domain_overlays` *(구 DomainSpecificCandidate)* |
| `ToolPreferenceCandidate` | `user.tool_stack` |
| `BoundaryRuleCandidate` | `user.boundary_authority` |
| `ProjectMemoryCandidate` | `user.memory_project_graph` *(구 ProjectGoalCandidate)* |
| `EvaluationCaseCandidate` | `user.evaluation_cases` |
| `DriftRecordCandidate` | `user.drift_history` |

## 7. 통합 베이스 레코드 (필드 표류 해소)

v0.1은 `score`, v0.2는 `confidence`; 어떤 팩은 `statement`, 어떤 팩은 `claim`/
`rule_statement`/`instruction`/`output_rule`을 썼습니다. v0.3은 **단일 베이스 레코드**로
통일합니다. 기계 검증 스키마 → [`schemas/record.base.schema.json`](../schemas/record.base.schema.json).

**필수:** `id`, `record_type`, `label`, `statement`, `evidence_refs[]`, `confidence(0..1)`,
`scope`, `review_status`, `sensitivity`, `created_at`, `updated_at`
**선택:** `aliases`, `priority_weight`, `counterexamples`, `exception_rules`,
`related_records`, `supersedes`, `linked_projects`, `linked_domains`, `examples`, `anti_examples`,
`canonical_key`, `repetition_count`, `merge_history`, `auto_confirmed`, `review_audit`,
`reliability`(§7.1)

- `review_status` ∈ {pending, confirmed, rejected, narrowed, sensitive, deferred}
- `sensitivity` ∈ {public, internal, sensitive, restricted}
- `confidence < 0.7`이면 `counterexamples` 필수
- **병합 필드(dedup/merge, [10 중복 억제·병합](./10-dedup-and-merge.md)):** `canonical_key`(정체성 키 —
  pack·record_type·normalize(statement)·scope), `repetition_count`(같은 패턴이 재유도·병합된 횟수),
  `merge_history`(이 레코드에 병합된 후보·증거 id) — 모두 선택. `duplicate→merge` upsert가 채운다.
- 폐기 필드: `score`(→`confidence`), bare `claim`/`rule_statement`/`instruction`/`output_rule`(→`statement`)

### 7.1 reliability 채널 — 증거 계층 vs 적용/해석 계층 (claim-layer)

> **EN:** Every record carries a `reliability` channel marking WHICH CLAIM LAYER it lives in —
> the structural seam between *what your behavior shows* and *what is said/inferred about you*.
> An honest personal-agent system must not blur that seam, so the seam is a field, not a vibe.

`reliability` ∈ {`behavioral`(기본), `self_reported`} — 레코드가 **어느 클레임 계층**에 속하는지 표시.

| 채널 | 계층 | 신뢰 | 런타임 권위 | 깊이 산입 | auto-confirm |
|------|------|------|-------------|-----------|:---:|
| `behavioral` | 관찰된 행동 (OriginalClaim 에 준함) | 높음 | 예(확인 시) | 예 | 가능 |
| `self_reported` | 자기에 대한 서술 (InterpretationClaim) | 낮음 | 아니오 (draft-only) | 아니오 | **금지** |

- **왜 분리하나.** "나는 ~한 사람이다"라는 자기서술은 *행동 증거가 아니라 자기에 대한 해석*입니다.
  이를 행동 레코드와 같은 통에 넣으면 검증되지 않은 자기상이 규칙으로 굳어, 에이전트가 *실제 행동과
  다른* 당신을 연기하게 됩니다. 그래서 self_reported 는 ① auto-confirm 금지(사람만 확인 —
  `validate_packs.py`), ② draft-only — 런타임 선택 술어가 권위 컨텍스트에서 제외하고 *draft*로만
  노출(`context_select.py`; 라이브 컴파일러 배선은 #9로 진행 중), ③ **여섯 수렴 지표 전부에서 제외**
  (coverage·confirmation_ratio·decision_fidelity·correction_cost·drift_stability·traceability)와 그 게이트
  변형 `human_confirmation_ratio`·폭(seeded)까지 제외(`convergence_report.py`; 자기서술은 운반될 뿐
  수렴 대상이 아님).
- **"becoming you"는 적용주장(AIApplicationClaim)이다.** 이 프로젝트의 표어("당신으로 수렴하는
  에이전트")는 증거가 아니라 *증거를 에이전트에 적용한 주장*입니다. 그래서 그 표어는 항상 **증거
  계층 위에 얹힌, 사람 검토를 요하는(requires human review) 적용주장**으로 읽혀야 하며, 행동 레코드의
  신뢰도를 자동 상속하지 않습니다. de-averaging·off-frontier·reliability 가 그 검토를 *기계적으로*
  떠받칩니다([00 일하는 자아 스코프](./00-overview.md), [06 §8](./06-convergence-model.md)).

스키마: [`record.base.schema.json`](../schemas/record.base.schema.json) `reliability` · 강제:
[`tools/validate_packs.py`](../tools/validate_packs.py)(self_reported→auto-confirm 금지) ·
[`tools/convergence_report.py`](../tools/convergence_report.py)(깊이는 behavioral 만 산입).

## 8. Crab 에이전트 역할 (운영 모델)

Orchestrator · Pack Architect · Evidence · Session Miner · Questioning · Diff Miner ·
Candidate Extractor · Scope · Confirmation · Pack Router · Boundary · Agent Compiler ·
Evaluator. 각 역할의 소유 작업·핸드오프 → [12-crab-orchestration](../skills/12-crab-orchestration.md).

## 9. 프라이버시·권한 모델 (요약)

무엇을 스스로 해도 되고 무엇을 사람에게 되돌려야 하는가의 어휘 요약입니다. **정식 정의·표·근거는
[04 프라이버시·경계](./04-privacy-boundary.md)가 단일 진실원**이며, 이 절은 커널 어휘로서 그 이름만
고정하고 깊이는 spec/04로 미룹니다(다른 문서가 "커널 §9"로 가리키는 대상).

- **`BoundaryRule` 노드 (팩 #11 `user.boundary_authority`).** 민감 항목이 승격·런타임 사용 전 받아야
  하는 규칙. 게이트 **G5**(승격 전 프라이버시, §2)를 만족시키는 유일한 팩.
- **여섯 경계 범주** — memory · retrieval · output · action · authority · sensitivity. 정식 정의
  → [04 §1 여섯 경계 범주](./04-privacy-boundary.md#1-여섯-경계-범주-boundary-categories).
- **여덟 권한 레벨(자율성 사다리)** — `observe < summarize < classify < draft < compare <
  recommend < ask_confirm < blocked`(단조 상승). 런타임은 확정 스코프 안에서 이 천장 *이하*로만
  행동. 정식 정의 → [04 §2 여덟 권한 레벨](./04-privacy-boundary.md#2-여덟-권한-레벨-authority-ladder).
- **기본 안전 정책** — 인스턴스 `BoundaryRule`이 없을 때의 보수적 하한(외부 통신·비가역 행동·계약·
  정체성 민감 발언·고임팩트 결정 앞에서 `ask_confirm`). 정식 정의 → [04 §3 기본 안전 정책](./04-privacy-boundary.md#3-기본-안전-정책-default-safe-policy).
- 평가 지표는 `boundary_compliance`([05](./05-evaluation-drift.md)). 승격 직전 충돌은 dedup judge가
  `conflict`로 사람에게 노출([10](./10-dedup-and-merge.md), §2 G3·G5).
