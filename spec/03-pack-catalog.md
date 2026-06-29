# 03 · 팩 카탈로그 (Pack Catalog)

> **EN:** The catalog of all 14 user ontology packs — the *shape* layer of the system.
> One subsection per pack gives its canonical name, purpose, record types (matching the
> pack's JSON Schema `record_type` enum), one short example record, the candidate type
> that routes into it (1:1, total — see [01](./01-kernel-schema.md#6-후보-타입--라우팅-11-전수)),
> and a link to its schema under [`../schemas/`](../schemas). Names and candidate types
> here are normative and must match the kernel schema exactly; old codenames are noted only
> as "구 코드명".

이 문서는 **형태(스키마) 계층**의 안내서입니다. 각 팩은 단일한 관심사를 담고, 통합 베이스
레코드([01 §7](./01-kernel-schema.md#7-통합-베이스-레코드-필드-표류-해소))를 `allOf $ref`로
확장한 뒤 자신의 `record_type` enum만 좁힙니다. 모든 인스턴스 레코드는 베이스의 필수 필드
(`id`, `record_type`, `label`, `statement`, `evidence_refs[]`, `confidence`, `scope`,
`review_status`, `sensitivity`, `created_at`, `updated_at`)를 그대로 가지므로, 아래 예제는
각 팩에서 **달라지는 부분**(주로 `record_type`·`statement`·`scope`)을 보여주는 데 집중합니다.

거버넌스 원칙: 14개 팩은 절대 섞이지 않습니다. 한 후보는 정확히 한 팩으로 라우팅되고
(라우터는 전수·1:1), 팩 간 참조는 베이스의 `related_records`/`linked_projects`/`linked_domains`
링크로만 이뤄집니다.

## 목차 (Table of Contents)

| # | 정식 이름 | 한 줄 의미 | 라우팅 후보 타입 | 스키마 |
|---|-----------|-----------|-----------------|--------|
| 1 | [`user.identity_roles`](#1-useridentity_roles) | 역할·정체성·맥락 | `IdentityRoleCandidate` | [schema](../schemas/user.identity_roles.schema.json) |
| 2 | [`user.persona_core`](#2-userpersona_core) | 안정 선호/가치/우선순위 | `PersonaTraitCandidate` | [schema](../schemas/user.persona_core.schema.json) |
| 3 | [`user.communication_style`](#3-usercommunication_style) | 응답 형식/언어/구조 | `CommunicationStyleCandidate` | [schema](../schemas/user.communication_style.schema.json) |
| 4 | [`user.artifact_policy`](#4-userartifact_policy) | 선호 출력물 형태 | `ArtifactPolicyCandidate` | [schema](../schemas/user.artifact_policy.schema.json) |
| 5 | [`user.decision_policy`](#5-userdecision_policy) | 우선순위/거부/승인 규칙 | `DecisionPolicyCandidate` | [schema](../schemas/user.decision_policy.schema.json) |
| 6 | [`user.tacit_heuristics`](#6-usertacit_heuristics) | 암묵 판단 규칙 | `TacitHeuristicCandidate` | [schema](../schemas/user.tacit_heuristics.schema.json) |
| 7 | [`user.red_flags`](#7-userred_flags) | 위험 신호 | `RedFlagCandidate` | [schema](../schemas/user.red_flags.schema.json) |
| 8 | [`user.workflow_playbooks`](#8-userworkflow_playbooks) | 반복 작업 시퀀스 | `WorkflowPatternCandidate` | [schema](../schemas/user.workflow_playbooks.schema.json) |
| 9 | [`user.domain_overlays`](#9-userdomain_overlays) | 도메인 특화 지식 | `DomainOverlayCandidate` | [schema](../schemas/user.domain_overlays.schema.json) |
| 10 | [`user.tool_stack`](#10-usertool_stack) | 도구/사용 패턴 | `ToolPreferenceCandidate` | [schema](../schemas/user.tool_stack.schema.json) |
| 11 | [`user.boundary_authority`](#11-userboundary_authority) | 프라이버시/권한 규칙 | `BoundaryRuleCandidate` | [schema](../schemas/user.boundary_authority.schema.json) |
| 12 | [`user.memory_project_graph`](#12-usermemory_project_graph) | 프로젝트·목표·메모리 | `ProjectMemoryCandidate` | [schema](../schemas/user.memory_project_graph.schema.json) |
| 13 | [`user.evaluation_cases`](#13-userevaluation_cases) | 충실도 테스트 케이스 | `EvaluationCaseCandidate` | [schema](../schemas/user.evaluation_cases.schema.json) |
| 14 | [`user.drift_history`](#14-userdrift_history) | 변경·버전 이력 | `DriftRecordCandidate` | [schema](../schemas/user.drift_history.schema.json) |

---

## 1. `user.identity_roles`

**목적.** 주체가 *누구인가* — 보유한 역할, 그 역할이 작동하는 맥락, 정체성 진술의 귀속을
담습니다. 다른 모든 팩이 "어떤 역할/맥락에서 참인가"를 가리킬 때 기준이 되는 첫 팩입니다.
대응 노드: `IdentityRole`.

**레코드 타입** (`record_type`): `RoleRecord` · `ContextRecord` · `AttributionRecord` · `ScopeRecord`.

```yaml
id: logotekton.role.001
record_type: RoleRecord
label: 온톨로지 시스템 설계자
statement: 주체는 스키마/거버넌스 결정에서 '설계자' 역할로 행동하며, 구현 세부보다 일관성·계약을 먼저 본다.
scope: 스키마·아키텍처 논의 (구현 디버깅 세션 제외)
evidence_refs: [ev.session.0142#turn7]
confidence: 0.86
review_status: confirmed
sensitivity: public
```

**라우팅 소스 후보 타입:** `IdentityRoleCandidate`.
**스키마:** [`../schemas/user.identity_roles.schema.json`](../schemas/user.identity_roles.schema.json).
(구 코드명: pa.roles.)

---

## 2. `user.persona_core`

**목적.** 주체의 **안정적** 선호·반선호·우선순위·가치·지속 작업 성향을 담습니다. 일시적 기분이
아니라 세션을 가로질러 반복되는 성향만 들어옵니다. 게이트 G4가 강하게 적용됩니다 — 추측된
심리가 아니라 **관찰된 행동**으로 기술합니다. 대응 노드: `PersonaTrait`.

> **여기서 'persona'는 행동 페르소나(behavioral mask)다 — 내면 자아가 아니다(설계자 결정 B).** 이
> 팩의 'value'·'priority'조차 *관찰된 행동으로 드러난 안정 패턴*으로만 적재되며, "이 사람의 진짜
> 가치는 X"라는 *내면 귀속*은 적재 대상이 아닙니다(그건 자기서술 → `reliability: self_reported`
> draft-only, [01 §7.1](./01-kernel-schema.md)). 즉 persona_core 는 *당신이 무엇을 느끼는가*가
> 아니라 *당신이 일관되게 어떻게 행동하는가*를 담습니다.

**레코드 타입** (`record_type`): `PreferenceRecord` · `AvoidanceRecord` · `PriorityRecord` · `ValueRecord` · `StablePatternRecord`.

```yaml
id: logotekton.trait.004
record_type: PreferenceRecord
label: 구체적 예제 선호
statement: 주체는 추상적 설명보다 동작하는 구체 예제를 먼저 보고 싶어 한다 (반복 관찰됨).
scope: 설계·문서 작성 전반
evidence_refs: [ev.session.0099#turn3, ev.session.0142#turn12, ev.diff.0031]
confidence: 0.91
review_status: confirmed
sensitivity: public
```

**라우팅 소스 후보 타입:** `PersonaTraitCandidate`.
**스키마:** [`../schemas/user.persona_core.schema.json`](../schemas/user.persona_core.schema.json).
(구 코드명: pa.core.)

---

## 3. `user.communication_style`

**목적.** 주체가 응답을 *어떻게* 받기를 원하는가 — 응답 형식, 언어, 구조, 정보 밀도, 그리고
"바꿔달라"는 신호로 작동하는 교정 큐(revision cue)를 담습니다. 대응 노드: `CommunicationStyleRule`.

**레코드 타입** (`record_type`): `ResponseFormatRecord` · `LanguageRecord` · `StructureRecord` · `DensityRecord` · `RevisionCueRecord`.

```yaml
id: logotekton.style.002
record_type: DensityRecord
label: 결론 우선·고밀도
statement: 주체는 서론 없이 결론을 먼저 제시하고 근거를 뒤에 두는 고밀도 응답을 선호한다.
scope: 기술 답변 (정서적/대화형 맥락 제외)
evidence_refs: [ev.session.0107#turn2, ev.correction.0044]
confidence: 0.88
review_status: confirmed
sensitivity: public
```

**라우팅 소스 후보 타입:** `CommunicationStyleCandidate`.
**스키마:** [`../schemas/user.communication_style.schema.json`](../schemas/user.communication_style.schema.json).
(구 코드명: pa.t03.)

---

## 4. `user.artifact_policy`

**목적.** 주체가 Personal Agent에게 **무엇을 만들어내길** 원하는가 — Markdown 형태, 파일 출력,
표·다이어그램 관습, 리뷰/산출물 구조를 담습니다. `WorkflowPattern`이 `produces` 엣지로 이 팩의
정책을 가리킵니다. 대응 노드: `ArtifactPolicy`.

**레코드 타입** (`record_type`): `ArtifactFormatRecord` · `FileOutputRecord` · `TablePolicyRecord` · `DiagramPolicyRecord` · `ReviewArtifactRecord`.

```yaml
id: logotekton.artifact.003
record_type: TablePolicyRecord
label: 비교는 표로
statement: 3개 이상의 선택지를 비교할 때는 산문 대신 정렬된 비교표를 산출한다.
scope: 설계 트레이드오프·도구 비교 문서
evidence_refs: [ev.session.0142#turn18]
confidence: 0.82
review_status: confirmed
sensitivity: public
```

**라우팅 소스 후보 타입:** `ArtifactPolicyCandidate`.
**스키마:** [`../schemas/user.artifact_policy.schema.json`](../schemas/user.artifact_policy.schema.json).
(구 코드명: pa.t04.)

---

## 5. `user.decision_policy`

**목적.** 주체가 *어떻게 결정하는가* — 우선순위 정렬, 트레이드오프 해소, 행동을 승인/거부하는
조건, 사람에게 에스컬레이션을 강제하는 임계값을 담습니다. `prioritizes`·`rejects_when` 엣지로
주체에 연결되며 `rejection_alignment`/`decision_fidelity` 평가 지표를 먹입니다. 대응 노드: `DecisionPolicy`.

**레코드 타입** (`record_type`): `PriorityRuleRecord` · `TradeoffRuleRecord` · `ApprovalConditionRecord` · `RejectionRuleRecord` · `EscalationThresholdRecord`.

```yaml
id: logotekton.decision.005
record_type: TradeoffRuleRecord
label: 일관성 > 단기 편의
statement: 스키마 결정에서 단기 편의와 장기 일관성이 충돌하면 일관성을 택한다.
scope: 스키마/계약 설계 결정
evidence_refs: [ev.session.0142#turn22, ev.diff.0031]
confidence: 0.84
review_status: confirmed
sensitivity: internal
```

**라우팅 소스 후보 타입:** `DecisionPolicyCandidate`.
**스키마:** [`../schemas/user.decision_policy.schema.json`](../schemas/user.decision_policy.schema.json).
(구 코드명: pa.t05.)

---

## 6. `user.tacit_heuristics`

**목적.** 주체가 말하지 않고 적용하는 **암묵 판단 규칙** — 반복 행동, 교정, "왜 이게 더 낫냐"는
대조 설명에서 떠오른 경험칙을 담습니다. 주로 diff_mining/elicitation으로 채굴됩니다. 게이트 G4
적용. 대응 노드: `TacitHeuristic`.

**레코드 타입** (`record_type`): `HeuristicRecord` · `ContrastiveRuleRecord` · `TriggerActionRecord`.

```yaml
id: logotekton.heuristic.006
record_type: ContrastiveRuleRecord
label: 이름 먼저 고정
statement: 새 개념을 만들 때, 구현보다 먼저 정식 이름을 고정해야 표류를 막을 수 있다고 본다.
scope: 온톨로지/스키마 어휘 설계
evidence_refs: [ev.session.0142#turn5, ev.session.0150#turn9]
confidence: 0.79
review_status: confirmed
sensitivity: public
```

**라우팅 소스 후보 타입:** `TacitHeuristicCandidate`.
**스키마:** [`../schemas/user.tacit_heuristics.schema.json`](../schemas/user.tacit_heuristics.schema.json).
(구 코드명: t06.)

---

## 7. `user.red_flags`

**목적.** 주체가 안정적으로 잡아내고 반응하는 **위험 신호** — 멈추거나 되묻거나 더 요구하게
만드는 냄새를 담습니다. 위험 신호·약한 구조·빈약한 근거를 다룹니다. `rejects_when` 엣지로 주체에
연결되고 `user.decision_policy`의 `RejectionRuleRecord`와 짝지어지며, `red_flag_recall` 지표를
직접 먹입니다. 대응 노드: `RedFlag`.

**레코드 타입** (`record_type`): `RiskSignalRecord` · `WeakStructureRecord` · `EvidenceGapRecord`.

```yaml
id: logotekton.redflag.007
record_type: EvidenceGapRecord
label: 근거 없는 단언
statement: 출처나 예제 없이 단정하는 주장은 멈추고 근거를 요구하는 신호로 취급한다.
scope: 기술 주장·설계 제안 검토
evidence_refs: [ev.correction.0051, ev.session.0150#turn14]
confidence: 0.9
review_status: confirmed
sensitivity: public
```

**라우팅 소스 후보 타입:** `RedFlagCandidate`.
**스키마:** [`../schemas/user.red_flags.schema.json`](../schemas/user.red_flags.schema.json).
(구 코드명: t07.)

---

## 8. `user.workflow_playbooks`

**목적.** 주체가 일을 끝내기 위해 돌리는 **반복 행동 시퀀스** — 순서, 진입 조건, 단계별 점검이
결과만큼 중요한 "내가 X를 실제로 하는 법"을 담습니다. `produces` 엣지로 산출물/아티팩트 정책에
연결됩니다. 대응 노드: `WorkflowPattern`.

**레코드 타입** (`record_type`): `WorkflowRecord` · `StepSequenceRecord` · `PlaybookRecord`.

```yaml
id: logotekton.workflow.008
record_type: StepSequenceRecord
label: 스키마 변경 절차
statement: 스키마를 바꿀 때 (1) 계약 문서 갱신 → (2) 베이스 정합 확인 → (3) 검증 스크립트 실행 순으로 진행한다.
scope: schemas/ 변경 작업
evidence_refs: [ev.session.0150#turn3, ev.session.0150#turn20]
confidence: 0.83
review_status: confirmed
sensitivity: internal
```

**라우팅 소스 후보 타입:** `WorkflowPatternCandidate`.
**스키마:** [`../schemas/user.workflow_playbooks.schema.json`](../schemas/user.workflow_playbooks.schema.json).
(구 코드명: t08.)

---

## 9. `user.domain_overlays`

**목적.** 주체가 특정 분야에 가져오는 **도메인 특화 지식·상시 주의 패턴·국소 어휘** — 작업이
아는 도메인으로 인식되는 순간 런타임이 알아야/주시해야/부르는 방식을 바꾸는 "오버레이"를
담습니다. 일반 성향(`user.persona_core`)이나 과정 규칙(`user.tacit_heuristics`)이 아니라,
명시된 도메인 안에서만 참인 사실/관습/용어입니다. 게이트 G2가 강하게 적용됩니다 — 한정하는
도메인이 곧 `scope`입니다. 대응 노드: `DomainOverlay`.

**레코드 타입** (`record_type`): `DomainKnowledgeRecord` · `DomainAttentionRecord` · `DomainTermRecord`.

```yaml
id: logotekton.domain.009
record_type: DomainTermRecord
label: 도메인 용어 '팩'의 의미
statement: 이 도메인에서 '팩(pack)'은 단일 관심사의 온톨로지 단위를 뜻하며 일반적 '묶음'이 아니다.
scope: 온톨로지/OpenCrab 도메인
evidence_refs: [ev.session.0142#turn1]
confidence: 0.87
review_status: confirmed
sensitivity: public
```

**라우팅 소스 후보 타입:** `DomainOverlayCandidate` *(구 후보명: DomainSpecificCandidate)*.
**스키마:** [`../schemas/user.domain_overlays.schema.json`](../schemas/user.domain_overlays.schema.json).
(구 코드명: t09.)

---

## 10. `user.tool_stack`

**목적.** 주체가 손이 가는 **도구·라이브러리·서비스·명령** — 어떤 작업에 무엇을 선호하는지,
실제로 어떻게 쓰는지, 무엇을 일부러 피하는지를 담습니다. 도구 대상은 9-space 크로스워크에서
`resource`로 떠오릅니다([07](./07-opencrab-9space-crosswalk.md)). 대응 노드: `ToolPreference`.

**레코드 타입** (`record_type`): `ToolPreferenceRecord` · `ToolUsageRecord` · `ToolAvoidanceRecord`.

```yaml
id: logotekton.tool.010
record_type: ToolPreferenceRecord
label: 검증은 python 스크립트
statement: 스키마 검증은 외부 의존성 대신 표준 라이브러리 python 스크립트로 처리하길 선호한다.
scope: 저장소 검증/CI 작업
evidence_refs: [ev.session.0150#turn11]
confidence: 0.8
review_status: confirmed
sensitivity: internal
```

**라우팅 소스 후보 타입:** `ToolPreferenceCandidate`.
**스키마:** [`../schemas/user.tool_stack.schema.json`](../schemas/user.tool_stack.schema.json).
(구 코드명: t10.)

---

## 11. `user.boundary_authority`

**목적.** 런타임이 **스스로 해도 되는 일과 사람에게 돌려줘야 하는 일**을 가르는 프라이버시·권한·
확인 규칙 — 무엇을 기억/검색/발화/행동해도 되는지, 에이전트 권한이 어디까지인지, 어떤 정보가
민감한지를 담습니다. 게이트 G5를 짊어집니다: 민감 항목은 어떤 승격·런타임 사용보다 **먼저**
경계 규칙을 받아야 합니다. `requires_confirmation` 엣지로 주체에 연결되고 9-space에서 `policy`로
떠오르며 `boundary_compliance` 지표를 먹입니다. 권한 모델 → [01 §9](./01-kernel-schema.md).
대응 노드: `BoundaryRule`.

**레코드 타입** (`record_type`): `BoundaryRuleRecord` · `AuthorityLevelRecord` · `ConfirmationRuleRecord` · `SensitivityRecord`.

```yaml
id: logotekton.boundary.011
record_type: ConfirmationRuleRecord
label: 외부 발신은 확인
statement: 외부로 나가는 메시지/커밋/발행은 보내기 전에 반드시 사람 확인(ask_confirm)을 받는다.
scope: 외부 통신·비가역 행동
evidence_refs: [ev.session.0150#turn25]
confidence: 0.95
review_status: confirmed
sensitivity: internal
exception_rules:
  - 사전 승인된 초안 저장(로컬, 미발송)은 확인 불요
```

**라우팅 소스 후보 타입:** `BoundaryRuleCandidate`.
**스키마:** [`../schemas/user.boundary_authority.schema.json`](../schemas/user.boundary_authority.schema.json).
(구 코드명: t11, .ba.)

---

## 12. `user.memory_project_graph`

**목적.** 주체의 **프로젝트·목표·지속 메모리 링크** — 흩어진 레코드를 묶어 런타임이 "주체가
실제로 무엇을 향해 일하는가"를 기억하게 하는 연결 조직입니다. 다른 팩들은 베이스의
`linked_projects`로 이 팩을 참조하고, 이 팩은 프로젝트/목표 자체와 레코드 간 링크를 기록합니다.
대응 노드: `ProjectMemory`.

> **이 팩이 *프로젝트 사실*의 유일한 귀착지다(전이성 테스트, [S02 §1.1](../skills/02-session-mining.md#11-전이성-테스트--주체를-캐고-주제를-캐지-마라-mine-the-decider-not-the-topic)).**
> "프로젝트 X는 ~한 아키텍처다 / X는 Y와 연결된다" 같은 *프로젝트를 바꾸면 거짓이 되는* 사실은 여기(또는
> 여러 프로젝트에 걸친 지속 도메인 지식이면 [`user.domain_overlays`](#9-userdomain_overlays))에만 들어옵니다.
> 페르소나·결정·암묵지 등 *암묵지 팩*은 그런 프로젝트 사실을 받지 않습니다 — 그건 *당신이 무엇을
> 만드는가*이지 *당신이 어떻게 생각하는가*가 아니기 때문입니다. 이 팩의 레코드는 런타임에서 "현재
> 프로젝트 맥락"으로 쓰이지 "당신이 누구인가"로 쓰이지 않습니다.

**레코드 타입** (`record_type`): `ProjectRecord` · `GoalRecord` · `MemoryLinkRecord`.

```yaml
id: logotekton.project.012
record_type: ProjectRecord
label: Personal Agent Builder
statement: 개인의 암묵지를 증거 기반 온톨로지 팩으로 포착해 개인 에이전트로 수렴시키는 오픈 사양 프로젝트.
scope: 2026 진행 중 공개 사양 작업
evidence_refs: [ev.session.0142#turn1, ev.session.0150#turn1]
confidence: 0.93
review_status: confirmed
sensitivity: public
linked_domains: [ontology, opencrab]
```

**라우팅 소스 후보 타입:** `ProjectMemoryCandidate` *(구 후보명: ProjectGoalCandidate)*.
**스키마:** [`../schemas/user.memory_project_graph.schema.json`](../schemas/user.memory_project_graph.schema.json).
(구 코드명: x12.)

---

## 13. `user.evaluation_cases`

**목적.** AssistantProfile이 주체가 승인할 방식대로 판단/작성/행동하는지 측정하는 **충실도 테스트
케이스**를 담습니다. 한 케이스는 입력 작업과 활성 팩 집합을 고정한 뒤, 행동 언어로 에이전트가
반드시 해야 할 것(expected_behavior)과 절대 하면 안 되는 것(unacceptable_behavior)을 채점 루브릭과
함께 명시합니다. `evaluated_by` 엣지로 프로필에 연결되고 9-space에서 `outcome`으로 떠오르며,
`decision_fidelity` 수렴 지표를 굴립니다. 필드 집합은 계약 §10을 따릅니다. 대응 노드: `EvaluationCase`.

**레코드 타입** (`record_type`): `EvaluationCaseRecord` *(단일 타입)*.

```yaml
id: logotekton.evalcase.013
record_type: EvaluationCaseRecord
label: 근거 없는 단언 거부 케이스
statement: 출처 없는 단정 주장이 입력될 때, 에이전트는 근거를 요구하고 단정을 그대로 받아들이지 않아야 한다.
scope: red_flag 충실도 평가
evidence_refs: [ev.session.0150#turn14]
confidence: 0.85
review_status: confirmed
sensitivity: internal
# 케이스 본문 필드 (계약 §10): input_task, active_pack_set,
# expected_behavior, unacceptable_behavior, scoring_rubric, result, correction_notes
```

**라우팅 소스 후보 타입:** `EvaluationCaseCandidate`.
**스키마:** [`../schemas/user.evaluation_cases.schema.json`](../schemas/user.evaluation_cases.schema.json).
(구 코드명: x13.)

---

## 14. `user.drift_history`

**목적.** 확인된 레코드의 **변경·대체·버전 이력** — 규칙이 교체되거나, 선호가 감쇠하거나, 두
레코드가 모순되거나, 값이 이동한 시점을 남기는 감사 추적입니다. 다른 레코드들에 *대한* 레코드를
담는 유일한 팩으로, 무엇이 참이었고 무엇이 대체했고 왜 그랬는지를 기억해 수렴을 가시화·가역화
합니다. `supersedes` 엣지로 바뀐 레코드에 연결되고 `drift_score` 지표와 `drift_stability` 수렴
지표를 먹입니다([06](./06-convergence-model.md)). 게이트 G4 적용. 대응 노드: `DriftRecord`.

**레코드 타입** (`record_type`): `DriftRecord` · `SupersessionRecord` · `VersionRecord`.

```yaml
id: logotekton.drift.014
record_type: SupersessionRecord
label: style.002 밀도 규칙 갱신
statement: logotekton.style.002의 '결론 우선' 규칙을 정서적 맥락 예외를 추가한 버전으로 대체했다.
scope: communication_style 갱신 이력
evidence_refs: [ev.correction.0061]
confidence: 0.9
review_status: confirmed
sensitivity: internal
supersedes: [logotekton.style.002]
```

**라우팅 소스 후보 타입:** `DriftRecordCandidate`.
**스키마:** [`../schemas/user.drift_history.schema.json`](../schemas/user.drift_history.schema.json).
(구 코드명: x14.)

---

## 관련 문서

- 노드/엣지/라이프사이클/게이트, 그리고 후보↔팩 라우팅 전체 표 → [01 커널 스키마](./01-kernel-schema.md)
- 통합 베이스 레코드 스키마(모든 팩이 확장) → [`../schemas/record.base.schema.json`](../schemas/record.base.schema.json)
- 빌더 파이프라인에서 후보가 어떻게 이 팩들로 흘러드는가 → [02 빌더 파이프라인](./02-builder-pipeline.md)
- 프라이버시/권한 모델(팩 11의 배경) → [04 프라이버시·경계](./04-privacy-boundary.md)
- 평가 지표와 케이스(팩 13/14의 배경) → [05 평가·드리프트](./05-evaluation-drift.md)
- 9-space 크로스워크(팩 ↔ OpenCrab 문법) → [07 9-space 크로스워크](./07-opencrab-9space-crosswalk.md)
