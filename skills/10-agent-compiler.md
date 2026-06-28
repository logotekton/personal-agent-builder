# 10 · 에이전트 컴파일러 (Agent Compiler)

> **EN:** Operating instructions for `skill.pab.agent_compiler` — the step that takes the
> **confirmed, scoped** instance records sitting in the 14 `user.*` packs and compiles the
> *relevant slices* into a runtime instruction **adapter** that drives the Personal Agent for
> **one task**. It does not dump all memory. For each task it (1) identifies the task type,
> (2) selects only the packs/slices that bear on it, (3) retrieves **confirmed/narrowed only**
> (Gate G3), (4) applies the `user.boundary_authority` layer (categories + authority ladder),
> (5) generates a structured runtime adapter with eight sections (identity/role, active
> patterns, decision policy, artifact policy, heuristics+red flags, workflow, boundary rules,
> output validator), (6) sets a task-specific response policy, and (7) logs coverage gaps for
> the next mining round. The compiler reads **all 14 packs** as candidate inputs —
> `user.identity_roles` **is included** (a prior version omitted it; that is fixed here). This
> is the lifecycle transition `target_pack_ingested → runtime_activated`, owned by the **Agent
> Compiler Crab**. Read as a runnable build spec, not a pitch.

에이전트 컴파일러는 [08 팩 라우팅](./08-pack-router.md)이 14개 `user.*` 팩에 적재한 **확정 레코드**를,
*지금 이 작업에 필요한 슬라이스만* 골라 런타임 명령 **어댑터**로 컴파일하는 단계입니다. 빌더
파이프라인의 `compile_runtime` 상태에 속하며([파이프라인 §3 S10](../spec/02-builder-pipeline.md#s10--agent_compiler--상태-compile_runtime)),
라이프사이클의 `target_pack_ingested → runtime_activated` 전이를 강제합니다([커널 §1](../spec/01-kernel-schema.md#1-라이프사이클-the-spine)).
산출물은 `*.runtime_adapter`로 컴파일된 `AssistantProfile`이고(`compiled_into` 엣지), 그것이 작업을
실행하는 **Personal Agent**입니다.

이 문서는 마케팅이 아니라 **그대로 실행하는 빌드 사양**입니다. 어휘는 [커널 스키마](../spec/01-kernel-schema.md),
팩 이름은 [§2 14개 팩](#2-컴파일러-입력--14개-user-팩-모두-identity_roles-포함), 경계·권한은
[04 프라이버시·경계](../spec/04-privacy-boundary.md), 레코드 필드는 [통합 베이스 레코드](../schemas/record.base.schema.json),
팩 정의는 [03 팩 카탈로그](../spec/03-pack-catalog.md)를 따르며 새 이름을 만들지 않습니다.

---

## 1. 목적 (Purpose)

에이전트 컴파일러는 **확정된 인스턴스 레코드를 작업 단위 런타임 어댑터로 조립하는** 단계입니다.
핵심 명제는 *전체 메모리 덤프가 아니라 작업별 활성화(task-specific activation)*입니다. 사람에게
"당신은 누구다, 이 200개 규칙을 다 외워라"라고 던지는 대신, **이 작업류에 실제로 작동하는 규칙만**
켜서 좁고 정확한 실행 프로필을 만듭니다.

- **하는 일:** (1) 작업류 식별, (2) 관련 팩·슬라이스 선택, (3) `confirmed`/`narrowed`만 검색
  (G3), (4) `user.boundary_authority` 경계·권한 레이어 적용(§5), (5) **8개 섹션 런타임 어댑터**
  생성(§4), (6) 작업별 응답 정책 설정, (7) 커버리지 갭 로깅(§7). 출력은 `*.runtime_adapter`로
  컴파일된 `AssistantProfile`이며 `compiled_into` 엣지로 출처 팩들을 가리킵니다.
- **하지 않는 일:** (1) **레코드를 만들거나 편집하지 않는다** — 추출은 [05](./05-candidate-extraction.md),
  편집 승인은 [07 게이트](./07-confirmation-gate.md)의 일. 컴파일러는 *읽기 전용으로 조립*만 한다.
  (2) **미확정 후보를 켜지 않는다(G3)** — `pending`/`rejected`/`sensitive`(경계 미부착)/`deferred`는
  어댑터에 들어오지 못한다. (3) **경계 규칙을 발명하지 않는다** — 권한 레벨·트리거는 [09](./09-privacy-boundary.md)/
  [04](../spec/04-privacy-boundary.md)에서 *읽어서 강제만* 한다. (4) **충실도를 채점하지 않는다** —
  측정은 [11 평가·드리프트](./11-evaluation-drift.md). (5) **모든 팩을 항상 켜지 않는다** — 무관한
  팩을 끄는 것이 컴파일러의 본질이다(§3).

> 한 줄 계약: **작업류 + 14개 팩의 확정 레코드 → 그 작업에 필요한 슬라이스만 담은 8섹션
> 런타임 어댑터.** 어댑터는 `confirmed`/`narrowed`만 담고(G3), 경계·권한이 적용돼 있으며(G5 산물),
> `compiled_into` 엣지로 출처 팩을 가리켜 *증거→후보→팩→어댑터* 사슬이 역추적됩니다(추적성=1.0).

## 2. 컴파일러 입력 — 14개 `user.*` 팩 모두 (identity_roles 포함)

컴파일러의 **입력 풀**은 14개 팩 *전부*입니다. 특정 작업에서 *켜지는* 것은 일부지만, *후보로 고려*
되는 것은 14개 모두입니다. 특히 1번 `user.identity_roles`는 **반드시 포함**됩니다 — 이전 버전이
이 팩을 입력에서 누락했으나(라우팅 표에도 `IdentityRoleCandidate`가 없었던 것과 같은 결함, [커널 §6](../spec/01-kernel-schema.md#6-후보-타입--라우팅-11-전수)),
v0.3에서 **수정**됩니다. 정체성·역할이 빠지면 어댑터의 [§4 섹션 1](#섹션-1--identityrole-정체성역할)이
비고, 에이전트가 "누구로서" 판단하는지가 사라집니다.

| # | 입력 팩 | 어댑터에서 주로 켜지는 섹션 | 노드 타입 |
|---|---------|----------------------------|-----------|
| 1 | `user.identity_roles` | 섹션 1 (identity/role) | `IdentityRole` |
| 2 | `user.persona_core` | 섹션 1·3 (안정 선호/가치) | `PersonaTrait` |
| 3 | `user.communication_style` | 섹션 2·8 (형식·출력 검증) | `CommunicationStyleRule` |
| 4 | `user.artifact_policy` | 섹션 4 (artifact policy) | `ArtifactPolicy` |
| 5 | `user.decision_policy` | 섹션 3 (decision policy) | `DecisionPolicy` |
| 6 | `user.tacit_heuristics` | 섹션 5 (heuristics) | `TacitHeuristic` |
| 7 | `user.red_flags` | 섹션 5 (red flags) | `RedFlag` |
| 8 | `user.workflow_playbooks` | 섹션 6 (workflow) | `WorkflowPattern` |
| 9 | `user.domain_overlays` | 섹션 2·5 (도메인 주의) | `DomainOverlay` |
| 10 | `user.tool_stack` | 섹션 6 (도구 선택) | `ToolPreference` |
| 11 | `user.boundary_authority` | 섹션 7 (boundary rules) | `BoundaryRule` |
| 12 | `user.memory_project_graph` | 섹션 1·6 (프로젝트 맥락) | `ProjectMemory` |
| 13 | `user.evaluation_cases` | (컴파일 입력 아님 — [11](./11-evaluation-drift.md)이 사용) | `EvaluationCase` |
| 14 | `user.drift_history` | (활성 레코드 선별 시 `supersedes` 참조) | `DriftRecord` |

> 13·14는 *직접 어댑터 섹션을 만들지 않습니다.* `user.evaluation_cases`는 컴파일된 프로필을
> *채점*하는 [11 평가](./11-evaluation-drift.md)의 입력이고, `user.drift_history`는 어떤 레코드가
> *현재 유효한지*(폐기되지 않았는지)를 가리는 데 쓰입니다(§3 [3], `supersedes` 엣지). 11번
> `user.boundary_authority`는 섹션을 만들 뿐 아니라 **다른 모든 섹션 위에 강제 레이어로 얹힙니다**(§5).

## 3. 작동 방식 — 7단계 런타임 조립 흐름 (How it works)

에이전트 컴파일러 크랩은 작업 하나마다 다음 일곱 동작을 순서대로 실행합니다 — **작업류 식별 →
팩·슬라이스 선택 → 확정·스코프 검색 → 경계·권한 적용 → 어댑터 생성 → 응답 정책 설정 → 갭 로깅**.
어느 동작에서도 레코드를 *만들거나 편집*하지 않습니다(읽기 전용 조립).

```
   작업 요청 (지금 이 작업) + 14개 user.* 팩의 확정 레코드
        │
   [1] 작업류 식별        ── task type 판별(예: 코드 리뷰 / 외부 메일 초안 / 의사결정 메모)
        ▼
   [2] 팩·슬라이스 선택   ── 작업류에 닿는 팩만 ON, 무관 팩 OFF; scope가 작업 맥락과 겹치는 레코드만
        ▼
   [3] 확정·스코프 검색   ── review_status ∈ {confirmed, narrowed}만; pending/rejected/deferred 제외(G3)
        ▼                    ── drift_history로 supersedes된(폐기) 레코드 제외
   [4] 경계·권한 적용     ── user.boundary_authority 레이어를 모든 슬라이스 위에 강제(§5, G5 산물)
        ▼
   [5] 어댑터 생성        ── 8개 섹션으로 조립(§4); 충돌은 우선순위 규칙으로 해소(§6)
        ▼
   [6] 응답 정책 설정     ── 이 작업류에 맞는 출력 형식·자율성 천장·확인 트리거 결정
        ▼
   [7] 갭 로깅            ── 비었거나 저커버리지인 슬롯을 기록 → 다음 채굴 라운드 신호
        ▼
   *.runtime_adapter (AssistantProfile, compiled_into) → 작업 실행 → S11 평가로
```

**[1] 작업류 식별.** 들어온 작업을 *유형*으로 분류합니다 — 예: `코드 리뷰`, `외부 이메일 초안`,
`내부 의사결정 메모`, `리서치 요약`. 작업류가 곧 *어떤 팩·슬라이스가 관련 있는가*를 결정하므로,
이 단계가 틀리면 무관한 규칙이 끌려 들어옵니다. 작업류는 `user.identity_roles`의 역할 맥락과
`user.memory_project_graph`의 프로젝트 맥락으로 보강됩니다(같은 "코드 리뷰"라도 *어느 역할로, 어느
프로젝트에서*인지가 슬라이스를 바꿉니다).

**[2] 팩·슬라이스 선택.** 작업류에 닿는 팩만 켜고 나머지는 끕니다 — 1:1 라우팅이 각 팩을 단일
타입 슬라이스로 유지했기에([08 §2](./08-pack-router.md#2-왜-11-라우팅이-검색-정밀도를-지키는가))
이 선택적 로딩이 가능합니다. 같은 팩 안에서도 `scope`가 현재 작업 맥락과 *겹치는* 레코드만
당깁니다(스코프 매칭). 예: "코드 리뷰" 작업이면 스타일·휴리스틱·위험·워크플로·도구·경계 팩의
*리뷰 스코프* 레코드를 켜고, "외부 제안서" 전용 스코프 레코드는 끕니다.

**[3] 확정·스코프 검색 (G3).** 선택된 슬라이스에서 **`review_status` ∈ {`confirmed`, `narrowed`}**
인 레코드만 가져옵니다. `pending`(미검토)·`rejected`(거부)·`sensitive`(경계 미부착)·`deferred`(보류)는
*하나도* 들어오지 못합니다 — 이것이 G3의 **두 번째 잠금장치**입니다([게이트는 S07에서 한 번,
컴파일에서 다시](../spec/02-builder-pipeline.md#5-파이프라인-불변식-게이트-재확인)). `narrowed`
레코드는 *좁혀진 스코프 안에서만* 켜지고 원래의 넓은 스코프로 일반화되지 않습니다(G2 강화). 동시에
`user.drift_history`의 `supersedes` 엣지로 **폐기된 옛 레코드를 제외**하여 *현재 유효한* 버전만
컴파일합니다.

> **주의 — `narrowed`는 두 출처가 있다.** (a) 확인 게이트에서 스코프를 좁힌 *활성* 레코드와,
> (b) `refinement→supersede` 시 액추에이터([`tools/pab_merge.py`](../tools/pab_merge.py))가
> 은퇴시킨 *구* 레코드(둘 다 `review_status="narrowed"`). 따라서 `narrowed`라는 상태만으로
> 활성 여부를 판정하면 안 되고, **`supersedes` 엣지의 *대상*인 레코드는 제외**해야 한다 — 즉
> 컴파일러는 status 뿐 아니라 supersedes 이력을 *함께* 따라야 폐기된 옛 버전을 끌고 오지 않는다
> ([10 중복 억제·병합](../spec/10-dedup-and-merge.md)). 또한 기존 확정과 모순되는 후보는 병합 층이
> `conflict`로 사람에게 노출(자동 적용 금지)하므로, *충돌하는 후보는 애초에 인스턴스 팩에 들어오지
> 않아* 컴파일 입력이 되지 않는다.

**[4] 경계·권한 적용 (§5).** 검색된 슬라이스 위에 `user.boundary_authority` 레이어를 얹습니다 —
여섯 경계 범주, 여덟 권한 레벨, 확인 트리거를 어댑터의 [섹션 7](#섹션-7--boundary-rules-경계-규칙)과
[섹션 8 검증기](#섹션-8--output-validator-출력-검증기)에 묶습니다. **경계는 다른 모든 슬라이스보다
우선**합니다 — 약한 `DecisionPolicy` 기본값이 `hard`/`blocked` 경계를 덮을 수 없습니다([04 §3·§6](../spec/04-privacy-boundary.md#3-기본-안전-정책-default-safe-policy)).

**[5] 어댑터 생성 (§4).** 슬라이스를 8개 섹션으로 조립합니다. 섹션 안에서 레코드 충돌(같은 상황에
다른 규칙)이 있으면 §6 우선순위 규칙으로 결정론적으로 해소합니다 — 컴파일러가 *임의로 판단*하지
않습니다.

**[6] 응답 정책 설정.** 이 작업류에 맞는 *출력 형식·자율성 천장·확인 트리거*를 고정합니다 — 예:
"외부 이메일 초안" 작업이면 형식은 `user.communication_style`의 외부-스코프 규칙을 따르고, 자율성
천장은 `draft`(발송은 `external comms` 트리거로 `ask_confirm`)입니다([04 §3](../spec/04-privacy-boundary.md#3-기본-안전-정책-default-safe-policy)).
응답 정책은 어댑터의 섹션이 아니라 어댑터 *전체의 발화 모드*입니다.

**[7] 갭 로깅 (§7).** 어떤 슬롯이 비었거나(예: 이 작업류의 위험 신호가 0개) 저커버리지인지를
기록합니다. 갭은 *런타임을 막지 않습니다* — 어댑터는 기본 안전 정책으로 동작하되, 갭은 다음 채굴
라운드([02](./02-session-mining.md)/[03](./03-elicitation-questioning.md))와 [수렴 지표](../spec/06-convergence-model.md)의
`coverage` 신호가 됩니다.

## 4. 런타임 어댑터 — 8개 섹션 (Runtime adapter sections)

어댑터는 **8개 섹션**으로 구성됩니다. 각 섹션은 입력 팩의 *확정 슬라이스*에서 채워지며, 비면 갭으로
로깅됩니다(§7). 이것은 *작업별 활성화*이지 전체 메모리 덤프가 아닙니다 — 같은 사람이라도 작업류가
다르면 섹션 내용이 달라집니다.

### 섹션 1 — identity/role (정체성·역할)
- **출처:** `user.identity_roles`(주), `user.persona_core`(안정 가치/우선순위), `user.memory_project_graph`(프로젝트 맥락).
- **담는 것:** 에이전트가 *누구로서* 이 작업을 하는가 — 역할, 정체성, 현재 프로젝트/목표 맥락.
- **왜:** 같은 작업도 "리뷰어로서"인지 "저자로서"인지에 따라 판단이 달라집니다. **이 섹션이 비면
  안 됩니다** — identity_roles 누락이 바로 이 섹션의 공백이며(§2), 그 경우 컴파일러는 `coverage`
  갭을 강하게 로깅하고 기본 역할로만 동작합니다.

### 섹션 2 — active patterns (활성 패턴)
- **출처:** `user.communication_style`(형식·언어·구조·밀도), `user.domain_overlays`(도메인 특화 주의).
- **담는 것:** 이 작업류에서 켜진 소통/형식 규칙과 도메인 주의 패턴.
- **예:** "코드 리뷰 초안은 결론 우선, 근거는 뒤로"(스타일) + "보안 도메인이면 입력 검증 누락을
  먼저 본다"(도메인 오버레이).

### 섹션 3 — decision policy (의사결정 정책)
- **출처:** `user.decision_policy`(우선순위·트레이드오프·승인/거부), `user.persona_core`(가치 우선순위).
- **담는 것:** 트레이드오프가 생길 때 *무엇을 우선*하고 *무엇을 거부*하는가, 에스컬레이션 조건.
- **충돌 규칙:** `DecisionPolicy`는 `BoundaryRule`보다 약합니다 — 경계가 항상 이깁니다(§6, [04 §6](../spec/04-privacy-boundary.md#6-다른-층과의-관계)).

### 섹션 4 — artifact policy (산출물 정책)
- **출처:** `user.artifact_policy`.
- **담는 것:** 이 작업의 *출력 객체 형태* — Markdown/표/파일/리뷰보드 등 선호 산출물 형식.
- **연결:** `WorkflowPattern`이 `produces` 엣지로 가리키는 산출물과 정합되어야 합니다([커널 §4](../spec/01-kernel-schema.md#4-엣지-타입-edge-types)).

### 섹션 5 — heuristics + red flags (휴리스틱·위험 신호)
- **출처:** `user.tacit_heuristics`(암묵 판단 규칙), `user.red_flags`(위험 신호), `user.domain_overlays`(도메인 위험).
- **담는 것:** *작동시킬* 암묵 판단 규칙과 *잡아낼* 위험 신호. 빠른 판단의 핵심.
- **예:** 휴리스틱 "테스트 없는 리팩터는 의심한다" + 위험 신호 "근거 없는 단정·과장된 성능 주장".

### 섹션 6 — workflow (워크플로)
- **출처:** `user.workflow_playbooks`(반복 시퀀스), `user.tool_stack`(도구 선택), `user.memory_project_graph`(프로젝트 단계).
- **담는 것:** 이 작업류를 수행하는 *단계 시퀀스*와 각 단계에서 쓰는 도구.
- **예:** 리뷰 워크플로 "1. diff 훑기 → 2. 테스트 확인 → 3. 위험 신호 스캔 → 4. 결론 우선 요약".

### 섹션 7 — boundary rules (경계 규칙)
- **출처:** `user.boundary_authority`(주) — 여섯 경계 범주 + 여덟 권한 레벨 + 확인 트리거([04](../spec/04-privacy-boundary.md)).
- **담는 것:** 이 작업에서 *허용/금지* 연산, *자율성 천장*, *되묻기 트리거*.
- **강제:** 이 섹션은 §5에서 다른 모든 섹션 위에 얹히는 **레이어**입니다 — 충돌 시 항상 이깁니다.

### 섹션 8 — output validator (출력 검증기)
- **출처:** `user.communication_style`(형식 준수), `user.boundary_authority`(`output_boundary`·`on_violation`), `user.artifact_policy`(산출물 형태).
- **담는 것:** *출력을 내보내기 전* 검사하는 규칙 — 금지 출력(계좌번호 등) 미포함, 형식 준수, 민감
  클래스 취급법(redact 등), 자율성 천장 초과 여부.
- **반응:** 위반 시 `on_violation`(block/ask_confirm/redact/warn/log)으로 반응합니다([04 §5](../spec/04-privacy-boundary.md#5-민감성과-라이프사이클--게이트-g5)).

> 응답 정책(§3 [6])은 9번째 섹션이 아니라 어댑터 *전체*에 걸린 발화 모드입니다 — 형식·자율성
> 천장·확인 트리거를 작업류에 맞춰 한 번 고정합니다.

## 5. 경계·권한 레이어 (Boundary & authority layer)

`user.boundary_authority`는 *하나의 섹션*(섹션 7)을 만들 뿐 아니라, **다른 일곱 섹션 위에 강제
레이어로 얹힙니다**. 이것이 컴파일러가 G5의 결과를 런타임에 *집행*하는 방식입니다.

- **여섯 경계 범주.** `memory`/`retrieval`/`output`/`action`/`authority`/`sensitivity` 각각이
  무엇을 저장·검색·출력·실행·허가·취급해도 되는지를 가립니다([04 §1](../spec/04-privacy-boundary.md#1-여섯-경계-범주-boundary-categories)).
  컴파일러는 작업 맥락에 발효되는(`applies_to_actions`) 경계만 켭니다.
- **여덟 권한 레벨(천장).** `observe < summarize < classify < draft < compare < recommend <
  ask_confirm < blocked`. 어댑터의 자율성 천장은 이 작업류에 적용되는 `AuthorityLevelRecord`로
  정해지고, 런타임은 천장 *이하로만* 행동합니다([04 §2](../spec/04-privacy-boundary.md#2-여덟-권한-레벨-authority-ladder)).
- **다섯 확인 트리거.** `external comms`·`irreversible action`·`contractual commitment`·
  `identity-sensitive statement`·`high-impact decision` 중 하나라도 참이면 `ask_confirm`으로
  멈추고 사람에게 되묻습니다([04 §3](../spec/04-privacy-boundary.md#3-기본-안전-정책-default-safe-policy)).
  경계 레코드가 부족한 새 인스턴스에서도 이 **기본 안전 정책**이 보수적 하한으로 작동합니다.
- **경계 우선 + 더 엄격한 규칙 승리.** `hard` 강제·`blocked_actions`는 어떤 허용이나 약한
  `DecisionPolicy` 기본값도 덮을 수 없습니다. `enforcement`(얼마나 단단히)와 `confidence`(증거
  강도)는 별개입니다 — 안전 제약은 통계적 확신을 기다리지 않습니다([04 §4 노트](../spec/04-privacy-boundary.md#4-boundaryrule-필드-boundaryrule-fields)).

> 컴파일러는 경계를 *발명하지 않습니다.* `user.boundary_authority`에 이미 확정된 `BoundaryRule`을
> *읽어서 레이어로 묶을* 뿐입니다. 민감 항목이 경계 없이 새는 것은 컴파일이 아니라 라우팅/게이트
> 단계에서 이미 차단됐어야 합니다(G5, [09](./09-privacy-boundary.md)).

## 6. 충돌 해소 — 결정론적 우선순위 (Conflict resolution)

한 작업에 같은 상황을 다르게 지시하는 두 레코드가 켜질 수 있습니다. 컴파일러는 *임의 판단* 대신
다음 **결정론적 우선순위**로 해소합니다(같은 입력 → 같은 어댑터, 멱등·감사가능).

1. **경계 > 그 외 전부.** `BoundaryRule`(특히 `hard`/`blocked`)은 스타일·결정·휴리스틱 무엇보다
   우선합니다([04 §6](../spec/04-privacy-boundary.md#6-다른-층과의-관계)).
2. **더 좁은 스코프 > 더 넓은 스코프.** 현재 작업 맥락에 *더 구체적으로* 매칭되는 레코드가 일반
   규칙을 이깁니다(`narrowed` 레코드는 그 좁은 스코프 안에서 특히 강함).
3. **더 엄격 > 더 느슨.** 두 규칙이 같은 스코프·같은 층이면 더 보수적인 쪽(더 낮은 자율성 천장,
   더 강한 확인 트리거)을 택합니다.
4. **더 최근·고신뢰 > 옛·저신뢰.** 위가 다 같으면 `drift_history`상 더 최근(폐기되지 않은) 레코드,
   그다음 더 높은 `confidence`를 택합니다. 그래도 충돌이면 **갭으로 로깅하고 `ask_confirm`으로
   되묻습니다** — 컴파일러가 몰래 한쪽을 고르지 않습니다.

## 7. 갭 로깅 (Gap logging)

컴파일러는 *완전한 어댑터를 강요하지 않습니다.* 어떤 작업류에서 슬롯이 비거나 저커버리지면 그것을
**기록**하되 런타임은 기본 안전 정책으로 계속 동작합니다. 갭은 실패가 아니라 *다음에 무엇을
포착할지*의 신호입니다.

- **무엇을 로깅하나:** 빈 섹션(예: 이 작업류의 `red_flags` 0개), 저커버리지 팩(확정 레코드 < 3개,
  [수렴 모델 `coverage`](../spec/06-convergence-model.md)), 충돌로 `ask_confirm`에 떨어진 슬롯(§6 규칙 4),
  스코프 미스매치(작업 맥락에 닿는 확정 레코드가 없어 기본값으로 동작한 슬롯).
- **어디로 가나:** 갭 로그는 [11 평가·드리프트](./11-evaluation-drift.md)의 **`coverage`**(시드 폭/
  깊이) 집계와 다음 채굴 라운드([02 세션 마이닝](./02-session-mining.md)·[03 질문](./03-elicitation-questioning.md))의
  타깃이 됩니다 — "이 작업류엔 위험 신호가 없으니 다음 세션에서 캐자". (컴파일러는 `coverage` 신호만
  낸다. `correction_cost`는 컴파일 갭이 아니라 **RUN 단계에서 케이스별 `result.edit_fraction`**으로
  관측되는 별개 지표다 — [05 평가·드리프트 §1](../spec/05-evaluation-drift.md)·[06 수렴 모델](../spec/06-convergence-model.md).)
- **무엇을 하지 않나:** 갭을 *추측으로 메우지 않습니다.* 빈 섹션을 그럴듯한 규칙으로 채우면 G1(증거)·
  G3(확인)을 정면 위반합니다. 컴파일러는 비면 *비운 채로 두고 로깅*합니다.

## 8. 입력 / 출력 (Inputs / Outputs)

### 입력

- **주 입력:** 14개 `user.*` 팩의 **확정 인스턴스 레코드**(`review_status` ∈ {confirmed, narrowed},
  [record.base.schema.json](../schemas/record.base.schema.json)) + **현재 작업 요청**(작업류 판별의 근거).
  `user.identity_roles`를 포함한 14개 *모두*가 입력 풀입니다(§2).
- **부 입력:** `user.boundary_authority`의 경계·권한 레코드(§5 레이어), `user.drift_history`의
  `supersedes`(폐기 레코드 제외), 작업 맥락(역할·프로젝트)으로 스코프 매칭에 쓰이는 `Context`/`Condition`.

각 `review_status`의 컴파일러 처리:

| `review_status` | 컴파일러 동작 | 근거 |
|-----------------|---------------|------|
| `confirmed` | 어댑터에 포함(스코프 매칭 시) | 정상 경로 |
| `narrowed` | 포함하되 **좁혀진 스코프 안에서만** | 정상 경로, G2 강화 |
| `pending` | **제외** | G3 — 미검토 |
| `rejected` | **제외** | 명시 거부 |
| `sensitive` | **제외** (경계 미부착) — 경계 부착 후 `confirmed`면 포함 | G5 — [09](./09-privacy-boundary.md) |
| `deferred` | **제외** (보류) | 사람이 미룸 |
| *(supersedes된 레코드)* | **제외** | `drift_history`상 폐기됨 |

### 출력

`*.runtime_adapter`로 컴파일된 **`AssistantProfile` 하나** — 이것이 작업을 실행하는 Personal Agent입니다. 출력은 다음을 만족합니다:

- **8개 섹션**(§4)으로 구조화되고, 각 섹션은 *확정·스코프 매칭 슬라이스*로만 채워짐.
- **`confirmed`/`narrowed`만** 포함(G3 재확인). pending/rejected/sensitive(미부착)/deferred/폐기 레코드 없음.
- `user.boundary_authority` 레이어가 모든 섹션 위에 적용(§5) + **작업별 응답 정책**(형식·자율성 천장·확인 트리거) 고정.
- `compiled_into` 엣지로 출처 `UserOntologyPack`들을 가리켜 *증거→후보→팩→어댑터* 사슬이 역추적 가능(추적성=1.0).
- **갭 로그**(빈/저커버리지 슬롯) 동봉 → [11 평가](./11-evaluation-drift.md)·[수렴 지표](../spec/06-convergence-model.md)·다음 채굴 라운드 입력.

> **하류 계약:** 컴파일된 `AssistantProfile`은 [11 평가·드리프트](./11-evaluation-drift.md)가
> `user.evaluation_cases`로 채점합니다(`evaluated_by` 엣지) — `decision_fidelity`·`boundary_compliance`·
> `correction_cost`·`drift_score` 등 8개 지표. 평가 결과와 갭은 새 증거로 [S01](./01-evidence-capture.md)에
> 루프됩니다. 라이프사이클 전이: `target_pack_ingested → runtime_activated`([커널 §1](../spec/01-kernel-schema.md#1-라이프사이클-the-spine)).

### 최소 예시 ("코드 리뷰" 작업 → 부분 어댑터)

```yaml
# 입력: 작업 요청
task: "이 PR diff를 리뷰해줘"
task_type: code_review
role_context: reviewer            # user.identity_roles (섹션 1)
project_context: payments-svc     # user.memory_project_graph

# 출력(발췌): *.runtime_adapter (confirmed/narrowed 슬라이스만)
adapter:
  identity_role:                  # 섹션 1 — identity_roles + persona_core
    role: "결제 서비스 코드 리뷰어"
    stable_values: ["정확성 > 속도", "테스트 없는 변경 불신"]   # confidence 높음, confirmed
  active_patterns:                # 섹션 2 — communication_style + domain_overlays
    style: "리뷰 코멘트는 결론 우선, 근거는 뒤로 (scope: 코드 리뷰)"   # narrowed
    domain: "결제 도메인: 멱등성·금액 반올림·재시도 누락을 먼저 본다"
  decision_policy:                # 섹션 3 — decision_policy (BoundaryRule보다 약함)
    on_tradeoff: "보안/정확성과 속도가 충돌하면 정확성을 택하고 사유를 단다"
  artifact_policy:                # 섹션 4 — artifact_policy
    output_shape: "리뷰보드 코멘트 + 한 줄 종합 결론"
  heuristics_red_flags:           # 섹션 5 — tacit_heuristics + red_flags
    heuristics: ["테스트 없는 리팩터는 의심", "TODO/주석 처리된 코드 플래그"]
    red_flags: ["근거 없는 성능 단정", "에러 무시(swallow)", "하드코딩된 시크릿"]
  workflow:                       # 섹션 6 — workflow_playbooks + tool_stack
    steps: ["diff 훑기", "테스트 커버리지 확인", "위험 신호 스캔", "결론 우선 요약"]
  boundary_rules:                 # 섹션 7 — boundary_authority (레이어로 모든 섹션 위)
    authority_ceiling: recommend  # 리뷰는 권고까지; 코드 직접 수정/머지는 차단
    blocked_actions: ["머지", "force-push", "시크릿 출력"]
    confirmation_triggers: ["irreversible action"]
  output_validator:               # 섹션 8 — output_boundary + style + artifact
    checks: ["시크릿/계좌번호 미포함(redact)", "결론 우선 형식 준수", "권고 천장 초과 금지"]
response_policy:                  # 어댑터 전체 발화 모드
  format: "리뷰보드 코멘트"
  autonomy_ceiling: recommend
  ask_confirm_on: ["머지 제안 실행", "외부 공유"]
gaps_logged:                      # §7 — 다음 채굴 라운드 신호
  - "user.tool_stack: 이 리포의 정적분석 도구 선호 미확정(저커버리지)"
```

이 어댑터는 14개 팩을 다 덤프하지 않고 *코드 리뷰에 닿는 슬라이스만* 켰습니다. `confirmed`/`narrowed`
레코드만 들어왔고(G3), 경계 레이어가 `authority_ceiling: recommend`로 머지/force-push/시크릿 출력을
막았으며(§5), 미확정 슬롯("정적분석 도구 선호")은 추측으로 메우지 않고 갭으로 로깅됐습니다(§7).

## 9. 품질 검사 (Quality checks)

어댑터를 내보내기 전, 에이전트 컴파일러 크랩은 다음을 강제합니다. 코드 강제는
[`tools/validate_packs.py`](../tools/validate_packs.py)와 입력 팩 스키마가 보조합니다.

- [ ] **확정만 포함(G3 재확인)** — 어댑터의 *모든* 레코드가 `confirmed`/`narrowed`인가.
  `pending`/`rejected`/`sensitive`(미부착)/`deferred`/폐기 레코드가 *하나도* 새지 않았는가(§3 [3]).
- [ ] **14개 팩 입력(identity_roles 포함)** — 입력 풀에서 `user.identity_roles`를 누락하지 않았는가.
  섹션 1(identity/role)이 채워졌거나, 비었다면 강한 `coverage` 갭으로 로깅됐는가(§2).
- [ ] **작업별 활성화** — 전체 메모리 덤프가 아니라 *작업류에 닿는 슬라이스만* 켰는가. 무관 팩을
  껐는가(§3 [2]). 스코프가 작업 맥락과 겹치지 않는 레코드를 끌어오지 않았는가.
- [ ] **8개 섹션 구조** — 어댑터가 8개 섹션(§4)으로 조립됐는가. 빈 섹션은 추측으로 메우지 않고
  갭으로 남겼는가(§7).
- [ ] **경계 레이어 적용(G5 산물)** — `user.boundary_authority`가 섹션 7뿐 아니라 *모든 섹션 위에*
  레이어로 강제됐는가. 자율성 천장·확인 트리거·`blocked_actions`가 묶였는가(§5).
- [ ] **경계 우선 충돌 해소** — `hard`/`blocked` 경계가 약한 `DecisionPolicy`·스타일에 덮이지
  않았는가. 충돌을 §6 결정론적 우선순위로 해소했고, 미해소 시 `ask_confirm`/갭으로 떨어뜨렸는가.
- [ ] **narrowed ⊆ 스코프** — `narrowed` 레코드를 *좁혀진 스코프 안에서만* 켰는가. 넓은 스코프로
  일반화하지 않았는가(G2 강화).
- [ ] **폐기 제외** — `drift_history`상 `supersedes`된 옛 레코드를 컴파일에서 제외했는가(현재 유효
  버전만).
- [ ] **응답 정책 설정** — 작업류에 맞는 출력 형식·자율성 천장·확인 트리거가 고정됐는가(§3 [6]).
- [ ] **출력 검증기 동작** — 섹션 8이 금지 출력·형식·민감 클래스 취급·천장 초과를 검사하고
  `on_violation`으로 반응하도록 묶였는가(§4 섹션 8).
- [ ] **추적성·결속** — `compiled_into` 엣지로 출처 팩을 가리켜 *증거→후보→팩→어댑터* 역추적이
  되는가(추적성=1.0). 갭 로그가 [11](./11-evaluation-drift.md)·[수렴 지표](../spec/06-convergence-model.md)로 향하는가.
- [ ] **경계 준수(읽기 전용)** — 레코드를 *생성/편집*(S05/S07)하거나 *경계를 발명*(S09)하거나
  *충실도를 채점*(S11)하지 않았는가. 컴파일러는 *읽어서 조립*만 한다.

## 10. Crab 역할 — Agent Compiler Crab

이 스킬의 소유 역할은 **Agent Compiler Crab**입니다([12 crab 오케스트레이션](./12-crab-orchestration.md),
[커널 §8](../spec/01-kernel-schema.md#8-crab-에이전트-역할-운영-모델)).

- **소유 작업:** `compile_runtime` 상태에서 작업류 식별, 14개 팩(identity_roles 포함)에서 관련
  팩·슬라이스 선택, `confirmed`/`narrowed` 검색(G3 재확인) + 폐기 제외, `user.boundary_authority`
  레이어 적용(§5), 8섹션 어댑터 생성(§4) + 충돌 해소(§6), 작업별 응답 정책 설정, 갭 로깅(§7),
  `compiled_into` 결속·프로비넌스 보존.
- **받는 핸드오프:** **Pack Router**(S08)가 14개 `user.*` 팩에 적재한 확정 레코드, **Boundary
  Crab**(S09)이 부착한 `BoundaryRule`(경계 레이어의 출처). 작업 요청은 **Orchestrator**(S12)가 전달.
- **넘기는 핸드오프:** 컴파일된 `AssistantProfile`(`*.runtime_adapter`) → **Evaluator**(S11)가
  `user.evaluation_cases`로 채점. 갭 로그 → **Orchestrator**를 통해 다음 채굴 라운드(**Session
  Miner**/**Questioning**, S02/S03)와 [수렴 지표](../spec/06-convergence-model.md)로.
- **경계:** 레코드의 *생성/편집*(S05/S07), *경계 규칙 발명*(S09), *충실도 채점*(S11)을 침범하지
  않습니다. 미확정 후보를 어댑터에 넣지 않으며(G3), 빈 슬롯을 추측으로 메우지 않고(G1), 모든 팩을
  무차별 덤프하지 않습니다(작업별 활성화). 컴파일러는 *읽기 전용·결정론적*이어야 정확합니다.

OpenCrab 도구로 실행할 때는 `opencrab_search_packs`로 작업류에 관련된 14개 `user.*` 팩을 식별하고,
`opencrab_query`/`opencrab_search_nodes`로 각 팩의 `confirmed`/`narrowed` 레코드를 스코프 매칭으로
검색하며(폐기·미확정 제외), `opencrab_get_node_context`로 `BoundaryRule`·`supersedes` 맥락을 끌어와
경계 레이어를 묶습니다. 컴파일된 어댑터(`AssistantProfile`)는 `compiled_into` 엣지로 출처 팩에
결속하고, 검증·갭 점검은 `opencrab_pack_qa`로 보조합니다.

> 9-space 사상: 컴파일은 `concept`(PersonaTrait·CommunicationStyleRule·DomainOverlay·WorkflowPattern·
> IdentityRole)·`policy`(BoundaryRule·DecisionPolicy·RedFlag)·`lever`(WorkflowPattern 단계·도구 행동)
> 공간의 확정 노드를, `community`로 사상되는 `AssistantProfile`로 조립하는 동작입니다. `compiled_into`
> 엣지가 `evidence`→`claim`→팩 노드→`AssistantProfile`의 추적 사슬을 잇고, 그 프로필의 실행 결과는
> `outcome`(EvaluationCase 결과·correction_cost·decision_fidelity)로 사상됩니다([07 9-space 크로스워크](../spec/07-opencrab-9space-crosswalk.md)).

## 11. 관련 문서

- 라이프사이클(`target_pack_ingested → runtime_activated`)·노드·엣지·게이트(특히 G3)·베이스 레코드 → [01 커널 스키마](../spec/01-kernel-schema.md)
- 이 스킬이 속한 12단계 파이프라인 계약(`compile_runtime`, S10) → [02 빌더 파이프라인](../spec/02-builder-pipeline.md)
- 직전 단계(확정 레코드를 14개 팩에 적재) → [08 팩 라우팅](./08-pack-router.md) · [09 프라이버시·경계](./09-privacy-boundary.md)
- 컴파일러가 강제하는 경계 범주·권한 사다리·확인 트리거 → [04 프라이버시·경계](../spec/04-privacy-boundary.md)
- 직후 단계(컴파일된 프로필 채점 + 드리프트) → [11 평가·드리프트](./11-evaluation-drift.md) · [05 평가·드리프트](../spec/05-evaluation-drift.md)
- 14개 입력 팩의 정의 → [03 팩 카탈로그](../spec/03-pack-catalog.md), 기계 스키마 → [`schemas/`](../schemas)
- 확정 레코드의 기계 스키마(어댑터 입력) → [`record.base.schema.json`](../schemas/record.base.schema.json)
- 갭·평가가 끌어올리는 수렴 지표(`coverage`·`correction_cost`·`traceability`) → [06 수렴 모델](../spec/06-convergence-model.md)
- 각 노드의 9-space 사상 → [07 9-space 크로스워크](../spec/07-opencrab-9space-crosswalk.md)
- 역할·상태·핸드오프 운영 모델 → [12 crab 오케스트레이션](./12-crab-orchestration.md)
- **이 스킬이 실제로 만든 산출물(worked example)** → [`runtime-adapter.md`](../examples/logotekton/runtime-adapter.md)
  (logotekton의 컴파일된 어댑터), 그리고 그 입력 레코드가 병합·대체로 진화하는 한 바퀴
  → [`revolution-01`](../examples/logotekton/revolution-01/) · [`revolution-02`](../examples/logotekton/revolution-02/)


## 트리거 (Trigger)

> 이 스킬의 발화 조건. 전체 2계층 모델·호스트(훅) 매핑·게이트 보존은
> [../spec/09-triggers.md](../spec/09-triggers.md), 머신 스키마는
> [../schemas/trigger.schema.json](../schemas/trigger.schema.json) 참고.

```yaml
trigger:
  trigger_id: pab.agent_compiler.on_session_start
  skill: agent_compiler
  signal: session_start
  condition: "compile confirmed, scoped slices into the runtime adapter"
  cadence: session_boundary
  host_hook: SessionStart
  produces: compiled
  requires_confirmation: false     # 스테이징만 (라이브 규칙 아님)
  default_state: enabled
  debounce: per_session
```

세션 시작 시 확인된 슬라이스만 어댑터로 컴파일합니다 — 작업별 활성화, 전체 메모리 덤프 아님.
