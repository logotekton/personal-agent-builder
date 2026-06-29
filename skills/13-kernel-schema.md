# 13 · 커널 스키마 (Kernel Schema)

> **EN:** Operating instructions for `skill.pab.kernel_schema` — the **foundational** schema
> skill, owned by the **Pack Architect Crab**. Unlike skills 01–12, it runs no pipeline step:
> it is the **shared vocabulary every other skill reads first**. Before any Crab captures
> evidence, mines, extracts, scopes, gates, routes, compiles, or evaluates, it loads this
> spine so that node types, edge types, the lifecycle, the six gates, the unified base record,
> and the 1:1 candidate→pack router all mean the same thing everywhere. This doc is a short
> index and a runnable load-and-check procedure; the **canonical kernel** lives in
> [`../spec/01-kernel-schema.md`](../spec/01-kernel-schema.md) and is the single source of truth.

이 문서는 빌더 파이프라인의 **0번째 의존성**입니다. `skill.pab.kernel_schema`는 워크플로
상태를 *소비*하지도 *생산*하지도 않습니다 — 대신 다른 13개 스킬이 동작하기 전에 *먼저 읽는*
공유 어휘를 정의합니다. 마케팅 문서가 아니라, 모든 스킬이 시작할 때 그대로 로드해 자기 출력에
대조하는 **운영 지침**으로 읽으세요.

이 문서는 커널을 **요약하고 가리킬** 뿐, 다시 정의하지 않습니다. 어휘의 *정식 정의*는 항상
[`../spec/01-kernel-schema.md`](../spec/01-kernel-schema.md)이며, 충돌 시 그쪽이 이깁니다.
필드 규약은 [통합 베이스 레코드](../schemas/record.base.schema.json), 팩 정의는
[03 팩 카탈로그](../spec/03-pack-catalog.md)를 따릅니다.

---

## 1. 목적 (Purpose)

커널 스키마는 시스템의 **척추**입니다. 14개 팩, 13개 스킬, 모든 인스턴스 레코드가 이 하나의
정의를 기준으로 어휘를 고정하므로, 어떤 문서도 새 이름을 만들지 않고 이 목록을 *재사용*합니다.
이 스킬의 단 하나의 책임은 **그 고정된 어휘를 모든 스킬이 동일하게 읽도록 보장하는 것**입니다.

세 가지 불변식 (반드시 지킴):

1. **파이프라인 단계가 아니다.** 이 스킬은 `EvidenceItem`도 `CandidateAssertion`도 레코드도
   생산하지 않습니다. 런타임 파이프라인은 [S01–S12](../spec/02-builder-pipeline.md)이며, 커널은
   그 *밑에 깔린 스키마*입니다. (계약 §8: "kernel_schema는 스키마 척추, 실행 파이프라인은 01–12".)
2. **모두가 먼저 읽는다.** 모든 다른 스킬은 자기 출력을 만들기 전에 이 커널을 로드해 노드/엣지/
   상태/게이트/필드 이름을 *여기서* 가져옵니다. 한 스킬이 새 이름을 지어내면 커널이 깨지고
   검색·라우팅·검증이 어긋납니다.
3. **정의하지 않고 가리킨다.** 정식 정의는 [`../spec/01-kernel-schema.md`](../spec/01-kernel-schema.md)에
   한 번만 존재합니다. 이 문서는 그것을 *한 화면으로 요약*하고 세부는 spec/01로 미룹니다 —
   요약과 정식 정의가 충돌하면 spec/01이 진실원입니다.

> 한 줄 계약: **입력 = 없음(읽기 전용). 출력 = 모든 스킬이 공유하는 고정 어휘.** 다른 스킬은
> 이 커널을 로드하고, 자기 노드/엣지/필드 이름이 여기 목록 안에 있는지 대조한 뒤에야 진행합니다.

## 2. 작동 방식 (How it works)

```
                        ┌───────────────────────────────────────────┐
                        │     skill.pab.kernel_schema (이 문서)       │
                        │   = spec/01 + record.base.schema.json 요약   │
                        └───────────────────────────────────────────┘
                                          │ (모든 스킬이 시작 시 로드)
        ┌───────────┬───────────┬─────────┼─────────┬───────────┬───────────┐
        ▼           ▼           ▼         ▼         ▼           ▼           ▼
     S01 증거   S02 채굴   …  S05 추출  S06 스코프  S07 게이트  S08 라우팅 …  S11 평가
     (어휘 대조) (어휘 대조)   (타입 어휘) (스코프 규칙)(상태 enum) (라우팅 표)  (지표 어휘)
```

이 스킬은 *수동(passive)* 입니다 — 동작을 수행하지 않고, 다른 스킬이 시작할 때 **읽히는**
참조입니다. 따라서 "작동"은 세 단계입니다: **로드 → 대조 → 거부/통과**. 어떤 스킬이든
(a) 커널을 로드하고, (b) 자기가 쓰려는 노드 타입·엣지·상태·필드 이름이 §3–§7 목록 안에
있는지 대조하고, (c) 목록 밖 이름이면 진행을 멈추고 추출/스코프 단계로 되돌립니다.

아래 §3–§7은 [`../spec/01-kernel-schema.md`](../spec/01-kernel-schema.md)의 한 화면 요약입니다.
*세부와 근거는 모두 spec/01에 있고, 여기서는 이름만 고정*합니다.

## 3. 라이프사이클 (한 화면)

원시 신호에서 런타임 규칙까지 모든 항목은 한 방향으로 흐릅니다. 원시 발언은 *최종 규칙이
아니며*, 이 흐름의 강제가 시스템 신뢰의 근거입니다.

```
raw_signal → evidence_bound_candidate → scoped_candidate → user_reviewed
           → confirmed_or_rejected → [dedup judge] → target_pack_ingested → runtime_activated
```

> **병합 층은 두 번째 게이트다.** `confirmed_or_rejected`와 `target_pack_ingested` 사이에서 dedup
> judge가 확정 후보를 기존 레코드와 대조해 분류한다: `novel→insert` · `duplicate→merge`(새 레코드
> 없이 upsert) · `refinement→supersede`(새 레코드+`supersedes`, 구 레코드 은퇴) · `conflict→surface`
> (기존 *확정*과 모순 → 사람에게 노출, **자동 적용 절대 금지**). 즉 *이미 확정된* 후보라도 충돌하면
> 적재되지 않는다 — G3·G5가 병합 층에서 한 번 더 강제된다([10 중복 억제·병합](../spec/10-dedup-and-merge.md),
> 액추에이터 [`tools/pab_merge.py`](../tools/pab_merge.py)).

→ 정식 정의·상태별 책임: [커널 §1](../spec/01-kernel-schema.md#1-라이프사이클-the-spine),
파이프라인 매핑: [02 빌더 파이프라인](../spec/02-builder-pipeline.md).

## 4. 품질 게이트 (G1–G6, 한 화면)

모든 스킬은 자기 출력을 이 여섯 게이트에 대조합니다. 게이트는 코드로도 강제됩니다 →
[`tools/validate_packs.py`](../tools/validate_packs.py).

| ID | 규칙 | 한 줄 의미 | 주 책임 스킬 |
|----|------|-----------|-------------|
| G1 | No evidence-free claim | 모든 후보는 ≥1 `EvidenceItem`에 `supported_by` | [01](./01-evidence-capture.md), [05](./05-candidate-extraction.md) |
| G2 | No unscoped heuristic | 모든 레코드는 비어있지 않은 `scope` | [06](./06-scope-context.md) |
| G3 | No runtime activation of pending | `confirmed`/`narrowed`/편집본만 활성화 | [07](./07-confirmation-gate.md), [08](./08-pack-router.md) |
| G4 | Behavioral language only | 추측된 심리가 아니라 관찰된 행동으로 기술 | [01](./01-evidence-capture.md), [05](./05-candidate-extraction.md) |
| G5 | Privacy before promotion | 민감 항목은 `BoundaryRule`을 먼저 받음 | [09](./09-privacy-boundary.md) |
| G6 | Template/instance separation | 템플릿은 라이브 레코드를 담지 않음 | (거버넌스 전역) |

→ 정식 정의: [커널 §2](../spec/01-kernel-schema.md#2-품질-게이트-quality-gates).

## 5. 노드·엣지 타입 (한 화면)

**노드 타입 (그래프 엔티티).** 새 노드 이름을 만들지 마세요 — 아래 목록에서 고릅니다:

`UserSubject` · `AssistantProfile` · `EvidenceItem` · `CandidateAssertion` ·
`IdentityRole` · `PersonaTrait` · `CommunicationStyleRule` · `ArtifactPolicy` ·
`DecisionPolicy` · `TacitHeuristic` · `RedFlag` · `WorkflowPattern` · `DomainOverlay` ·
`ToolPreference` · `BoundaryRule` · `ProjectMemory` · `EvaluationCase` · `DriftRecord` ·
그리고 보조 노드 `Context` · `Condition` · `Artifact` · `UserOntologyPack`.

**엣지 타입 (from → to).** 후보→증거를 잇는 `supported_by`/`extracted_from`,
승격을 잇는 `promoted_to`(Candidate→UserOntologyPack)·`compiled_into`(Pack→AssistantProfile),
맥락·정책을 잇는 `applies_in`·`prioritizes`·`rejects_when`·`produces`·`requires_confirmation`,
이력·평가·크로스워크를 잇는 `supersedes`·`evaluated_by`·`maps_to`.

→ 정식 정의(노드 설명·엣지 방향 전체): [커널 §3](../spec/01-kernel-schema.md#3-노드-타입-node-types) ·
[커널 §4](../spec/01-kernel-schema.md#4-엣지-타입-edge-types).

## 6. 14개 팩 ↔ 14개 후보 타입 라우팅 (1:1, 전수, 한 화면)

이전 코드명(`pa.t03`, `t06`, `x12`, `.ba` 등)은 **폐기**됐습니다 — 아래 정식 이름만 씁니다.
14개 후보 타입이 14개 팩에 **1:1 전수**로 사상되어 라우터를 완전(total)하게 만듭니다.

| # | 정식 팩 이름 | `candidate_type` |
|---|--------------|-------------------|
| 1 | `user.identity_roles` | `IdentityRoleCandidate` |
| 2 | `user.persona_core` | `PersonaTraitCandidate` |
| 3 | `user.communication_style` | `CommunicationStyleCandidate` |
| 4 | `user.artifact_policy` | `ArtifactPolicyCandidate` |
| 5 | `user.decision_policy` | `DecisionPolicyCandidate` |
| 6 | `user.tacit_heuristics` | `TacitHeuristicCandidate` |
| 7 | `user.red_flags` | `RedFlagCandidate` |
| 8 | `user.workflow_playbooks` | `WorkflowPatternCandidate` |
| 9 | `user.domain_overlays` | `DomainOverlayCandidate` |
| 10 | `user.tool_stack` | `ToolPreferenceCandidate` |
| 11 | `user.boundary_authority` | `BoundaryRuleCandidate` |
| 12 | `user.memory_project_graph` | `ProjectMemoryCandidate` |
| 13 | `user.evaluation_cases` | `EvaluationCaseCandidate` |
| 14 | `user.drift_history` | `DriftRecordCandidate` |

→ 정식 라우팅 표·구 코드명·전수성/단사성 규칙: [커널 §6](../spec/01-kernel-schema.md#6-후보-타입--라우팅-11-전수),
라우터 실행 절차: [08 팩 라우팅](./08-pack-router.md).

## 7. 통합 베이스 레코드 (한 화면)

모든 인스턴스 레코드는 단일 베이스 레코드를 상속합니다 — v0.1의 `score`, v0.2의 흩어진
`claim`/`rule_statement`/`instruction`/`output_rule`을 통일한 결과입니다. 기계 검증 스키마 →
[`record.base.schema.json`](../schemas/record.base.schema.json).

**필수:** `id` · `record_type` · `label` · `statement` · `evidence_refs[]` ·
`confidence(0..1)` · `scope` · `review_status` · `sensitivity` · `created_at` · `updated_at`
**선택:** `aliases` · `priority_weight` · `counterexamples` · `exception_rules` ·
`related_records` · `supersedes` · `linked_projects` · `linked_domains` · `examples` · `anti_examples` ·
`canonical_key` · `repetition_count` · `merge_history`

- `review_status` ∈ {`pending`, `confirmed`, `rejected`, `narrowed`, `sensitive`, `deferred`}
- `sensitivity` ∈ {`public`, `internal`, `sensitive`, `restricted`}
- `confidence < 0.7`이면 `counterexamples` 필수; `sensitive`/`restricted`이면 `exception_rules` 필수.
- **병합 필드(선택, [10 중복 억제·병합](../spec/10-dedup-and-merge.md)):** `canonical_key`(정체성 키) ·
  `repetition_count`(재유도·병합 횟수) · `merge_history`(병합된 후보 id) — `duplicate→merge` upsert가 채운다.
- **폐기 필드:** `score`(→`confidence`), bare `claim`/`rule_statement`/`instruction`/`output_rule`
  (→ 모두 `statement`로 통일; 팩 문서는 표시용 별칭만 기록 가능).

→ 정식 정의·검증 규칙: [커널 §7](../spec/01-kernel-schema.md#7-통합-베이스-레코드-필드-표류-해소).

## 8. 입력 / 출력 (Inputs / Outputs)

이 스킬은 *읽기 전용 참조*이므로 입출력 계약이 다른 스킬과 다릅니다.

### 입력

- **주 입력:** 없음. 이 스킬은 사용자 신호나 후보를 소비하지 않습니다. 대신 *자기 자신이*
  [`../spec/01-kernel-schema.md`](../spec/01-kernel-schema.md)과
  [`record.base.schema.json`](../schemas/record.base.schema.json)을 권위 출처로 로드합니다.
- **소비자:** 13개의 모든 다른 스킬([S01](./01-evidence-capture.md)–[S12](./12-crab-orchestration.md)).
  각 스킬이 시작 시 이 커널을 로드해 어휘를 대조합니다.

### 출력

- **고정된 공유 어휘 하나.** 라이프사이클 상태, 6개 게이트, 노드/엣지 타입, 14↔14 라우팅,
  베이스 레코드 필드·enum의 *단일하고 충돌 없는 이름 집합*. 다른 스킬은 이 집합 *안에서만*
  이름을 골라 자기 출력을 만듭니다.
- **대조 판정(읽기 시).** 어떤 스킬의 노드/엣지/상태/필드 이름이 이 집합 안에 있으면 통과,
  밖에 있으면 진행 중단 후 상류(추출/스코프)로 되돌림.

> 다른 스킬의 출력은 *전부* 이 커널의 어휘로 표현됩니다 — `EvidenceItem`(S01), 타입 지정
> `CandidateAssertion`(S05), 비어있지 않은 `scope`(S06), `validation_status`/`review_status`
> enum(S07), 14↔14 라우팅 표(S08) 모두 여기서 이름을 가져옵니다.

## 9. 품질 검사 (Quality checks)

이 스킬은 *자기 출력*을 검사하기보다, **다른 스킬이 커널과 정합한지**를 보장합니다. 코드 강제는
[`tools/validate_packs.py`](../tools/validate_packs.py)가 보조합니다.

- [ ] **단일 진실원 일치** — 이 문서의 §3–§7 요약이 [`../spec/01-kernel-schema.md`](../spec/01-kernel-schema.md)·
  [`record.base.schema.json`](../schemas/record.base.schema.json)과 *충돌하지 않는가*. 충돌 시 spec/01이 이긴다.
- [ ] **노드 어휘 폐쇄성** — 사용된 모든 노드 타입이 §5 목록 안에 있는가. 새 노드 이름을 만들지 않았는가.
- [ ] **엣지 어휘 폐쇄성** — 사용된 모든 엣지가 §5 목록 안에 있고 방향(from→to)이 맞는가.
- [ ] **상태·enum 폐쇄성** — `review_status`/`sensitivity`/라이프사이클 상태가 §3·§7 enum 안에 있는가.
- [ ] **라우팅 전수성(1:1)** — 14개 후보 타입이 §6 표에서 정확히 한 팩으로, 누락·중복 없이 사상되는가.
- [ ] **필드 규약** — 모든 레코드 필드 이름이 §7 필수/선택 목록을 따르는가. 폐기 필드
  (`score`, bare `claim`/`rule_statement`/`instruction`/`output_rule`)를 쓰지 않았는가.
- [ ] **구 코드명 부재** — `pa.t03`/`t06`/`x12`/`.ba` 등 폐기 코드명을 (정식 이름 주석 외에) 쓰지 않았는가.
- [ ] **경계 준수** — 이 스킬이 후보·레코드를 *생산*하지 않았는가. 파이프라인 단계를 침범하지 않았는가.

## 10. Crab 역할 — Pack Architect Crab

이 스킬의 소유 역할은 **Pack Architect Crab**입니다([12 crab 오케스트레이션](./12-crab-orchestration.md),
[커널 §8](../spec/01-kernel-schema.md#8-crab-에이전트-역할-운영-모델)).

- **소유 작업:** 공유 스키마 척추의 *관리와 배포* — 노드/엣지/상태/게이트/베이스 레코드 어휘를
  [`../spec/01-kernel-schema.md`](../spec/01-kernel-schema.md)·[`record.base.schema.json`](../schemas/record.base.schema.json)에
  정합 유지하고, 다른 모든 Crab이 시작 시 로드할 수 있게 합니다. 어휘 변경(새 노드 타입, 새 게이트)은
  *이 역할을 통해서만* 일어나며, 변경은 [14 드리프트 이력](../schemas/user.drift_history.schema.json) 어휘로
  버전이 남습니다.
- **받는 핸드오프:** **Orchestrator Crab**이 부트스트랩 시 모든 역할에 앞서 기동시킵니다 — 커널이
  로드되기 전에는 다른 어떤 단계도 시작하지 않습니다(0번째 의존성).
- **넘기는 핸드오프:** 고정된 어휘를 13개의 모든 다른 Crab에게 *읽기 전용으로* 제공합니다. 직접
  특정 후속 역할 하나에 넘기지 않고, *모두가 참조*합니다.
- **경계:** 후보·레코드를 *생산하지 않습니다*(파이프라인 단계가 아님). 특정 팩의 *내용*을 채우지
  않고 — 그건 [08 라우팅](./08-pack-router.md)·[10 컴파일러](./10-agent-compiler.md)의 일 — 오직 *형태*
  (스키마·어휘)만 관리합니다. 새 어휘는 임의로 늘리지 않고 spec/01 변경 절차를 통해서만 도입합니다.

OpenCrab 도구로 실행할 때는 `opencrab_search_packs`로 거버넌스/스키마 팩을 확인하고,
`opencrab_pack_qa`로 다른 팩 레코드가 베이스 레코드 어휘와 정합한지 점검하며, 어휘 변경은
`opencrab_pack_update`로 스키마 거버넌스 팩에 반영합니다.

> 9-space 사상: 커널 자체는 OpenCrab MetaOntology OS의 *문법층*에 해당합니다 — 9-space의 어떤
> 한 공간이 아니라, 노드 타입이 어느 공간으로 사상되는지를 *정의하는* 메타 규칙입니다(예:
> `concept`←`PersonaTrait`·`CommunicationStyleRule`, `policy`←`BoundaryRule`·`DecisionPolicy`·
> `RedFlag`, `claim`←`CandidateAssertion`). 사상 표 자체: [07 9-space 크로스워크](../spec/07-opencrab-9space-crosswalk.md).

## 11. 관련 문서

- **정식 커널(단일 진실원)** → [01 커널 스키마](../spec/01-kernel-schema.md)
- 베이스 레코드의 기계 스키마(필드·enum·검증) → [`record.base.schema.json`](../schemas/record.base.schema.json)
- 어휘·게이트를 강제·측정하는 결정론적 도구 → [`tools/validate_packs.py`](../tools/validate_packs.py)(게이트 G1–G6) ·
  [`tools/pab_merge.py`](../tools/pab_merge.py)(dedup/merge 액추에이터) ·
  [`tools/dedup_check.py`](../tools/dedup_check.py)(중복·merge_rate) ·
  [`tools/convergence_report.py`](../tools/convergence_report.py)(6 수렴 지표·성숙도)
- 커널이 깔린 12단계 실행 파이프라인 → [02 빌더 파이프라인](../spec/02-builder-pipeline.md)
- 14개 팩의 정의 → [03 팩 카탈로그](../spec/03-pack-catalog.md), 기계 스키마 → [`schemas/`](../schemas)
- 게이트 G5(프라이버시)·권한 모델 → [04 프라이버시·경계](../spec/04-privacy-boundary.md) · [09 privacy_boundary](./09-privacy-boundary.md)
- 평가 지표·드리프트 어휘 → [05 평가·드리프트](../spec/05-evaluation-drift.md) · [11 evaluation_drift](./11-evaluation-drift.md)
- 어휘가 떠받치는 수렴 지표(추적성=1.0 등) → [06 수렴 모델](../spec/06-convergence-model.md)
- 노드→9-space 사상 표 → [07 9-space 크로스워크](../spec/07-opencrab-9space-crosswalk.md)
- 인스턴스 id 문법·네이밍 정책 → [08 네이밍·IDs](../spec/08-naming-and-ids.md)
- 후보 추출 시 타입 어휘 사용 → [05 후보 추출](./05-candidate-extraction.md)
- 확정 후보의 1:1 라우팅 실행 → [08 팩 라우팅](./08-pack-router.md)
- 역할·상태·핸드오프 운영 모델 → [12 crab 오케스트레이션](./12-crab-orchestration.md)


## 트리거 (Trigger)

> **없음 (스키마 척추).** kernel_schema는 실행되는 단계가 아니라 다른 모든 스킬이 *먼저 읽는*
> 공유 스키마이므로 발화 트리거가 없습니다. 트리거 시스템은 이 스키마의 라이프사이클·게이트
> (G1~G6) 위에서 동작합니다 → 전체 모델 [../spec/09-triggers.md](../spec/09-triggers.md).
