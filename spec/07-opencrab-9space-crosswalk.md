# 07 · OpenCrab 9-Space 크로스워크

> **EN:** Personal Agent Builder uses its own domain vocabulary (UserSubject, PersonaTrait,
> BoundaryRule…). OpenCrab's MetaOntology OS uses a canonical 9-space grammar
> (subject, resource, evidence, concept, claim, community, outcome, lever, policy).
> This crosswalk maps every PA node into the 9 spaces so PA packs are first-class on the
> platform and the `opencrab_crab_agent` build path stays coherent.

OpenCrab MetaOntology OS의 정식 문법은 **9개 공간(9-space)**입니다:
`subject · resource · evidence · concept · claim · community · outcome · lever · policy`.
(`source/document/chunk/sentence/schema/task`는 온톨로지 공간이 아니라 파싱/적용 레이어입니다.)

Personal Agent 스키마의 모든 노드를 이 9개 공간에 사상(`maps_to`)하면, PA 팩이 플랫폼에서
일급 시민이 되고 `opencrab_crab_agent` 빌드 경로와 정합합니다.

## 크로스워크 표

| 9-space | PA 노드 / 개념 | 설명 |
|---------|----------------|------|
| **subject** | `UserSubject` | 에이전트의 주인인 개인 |
| **resource** | `EvidenceItem` 출처(세션·파일·diff), `ToolPreference` 대상, `ProjectMemory`(현재 프로젝트 맥락 — 피연산자) | 참조되는 자원·자산·맥락 |
| **evidence** | `EvidenceItem` 발췌, `evidence_refs` | 주장을 떠받치는 증거 |
| **concept** | `PersonaTrait`, `CommunicationStyleRule`, `DomainOverlay`, `WorkflowPattern`, `IdentityRole`, `TacitHeuristic`(안정적 *판단 방식* 패턴) | 사람에 관한 안정적 개념·판단 패턴 |
| **claim** | `CandidateAssertion` / 확인된 `statement` | 증거에 묶인 가변(defeasible) 주장 |
| **community** | `AssistantProfile`↔`UserSubject` 관계, 확인 리뷰보드, 개인 에이전트 네트워크 | 행위자·관계망 |
| **outcome** | `EvaluationCase` 결과, `correction_cost`, `decision_fidelity`, `DriftRecord`(시간에 따른 대체·드리프트) | 측정된 결과·변화 |
| **lever** | `WorkflowPattern` 단계, `DecisionPolicy` 우선순위, 도구 행동 | 에이전트가 당기는 지렛대 |
| **policy** | `BoundaryRule`, `DecisionPolicy` 규칙, `RedFlag`, `ArtifactPolicy`(산출물 형식 규율), 프라이버시/권한 기본값 | 행동·산출물을 규율하는 정책 |

## 매핑이 보장하는 것

1. **양방향 추적성** — PA의 `supported_by`(claim→evidence)는 9-space의 claim↔evidence
   관계와 일치하므로, 플랫폼 그래프에서 동일한 증거 추적이 가능합니다.
2. **정책의 일급화** — PA의 경계/권한 규칙이 9-space `policy`로 떠오르므로, 런타임 컴파일러가
   정책을 별도 레이어로 강제할 수 있습니다.
3. **결과 중심 평가** — `outcome` 공간에 평가/교정비용을 두어, 수렴 지표가 플랫폼 수준에서
   집계됩니다.
4. **커뮤니티 확장** — `community` 공간은 단일 사용자를 넘어 *검증된 개인 에이전트 네트워크*
   (OpenCanal류)로 자연스럽게 확장되는 자리입니다.

## crab_agent 빌드 시 사용법

`opencrab_crab_agent`의 `metaontology_purpose`(=`nine_grammar_purpose`)에 9-space 용어로
목적을 적을 때, 위 표의 PA→9space 매핑을 그대로 사용하면 됩니다. 예:

```
subject=개인 사용자; evidence=세션·교정·diff 발췌; concept=안정적 페르소나/스타일/도메인 개념;
claim=증거에 묶인 확인된 작업패턴 주장; policy=경계·권한·결정 규칙; outcome=충실도·교정비용;
lever=워크플로 단계·결정 우선순위; resource=도구·출처; community=주인↔에이전트·리뷰보드.
```

## 프로젝트 토폴로지 — 빌더 장치, 증거 아카이브, 개인 에이전트 (3-project)

> **EN:** On OpenCrab the four pack classes ([08 §4](./08-naming-and-ids.md#4-팩-클래스-접두사-4개-클래스--절대-섞지-않음))
> live in **three operational projects**: a reusable **builder** project (method + shape), a
> per-subject **evidence archive** project (session evidence and pending candidate boards), and a
> per-subject **personal-agent** project (confirmed data + runtime). You *mine with* the first,
> *stage evidence* in the second, and *upsert confirmed memory* into the third. This keeps the
> people-agnostic apparatus separate from both draft evidence and runtime-active memory.

PAB의 [4개 팩 클래스](./08-naming-and-ids.md#4-팩-클래스-접두사-4개-클래스--절대-섞지-않음)는
OpenCrab에서 **세 개의 운영 프로젝트**로 배치합니다:

| OpenCrab 프로젝트 | 담는 팩 클래스 | 역할 | 재사용 |
|-------------------|----------------|------|--------|
| **빌더** (예: `personal agent builder skills`) | `skill.pab.*`(방법) + `user.*`/`*.template`(형태) + 스펙·거버넌스·리뷰보드 | 추출·확인·라우팅·컴파일을 *수행하는 장치* | **사람 무관** — 모든 주인에게 동일 |
| **증거 아카이브** (예: `personal agent evidence`) | 세션 증거·후보 팩·pending 검토 보드 | 확정 전 후보와 근거를 보존하는 *비계* | **주인/세션 단위** — 검색 대상이 아니라 감사·검토 출처 |
| **개인 에이전트** (예: `personal agent`) | 승인된 `personal.<subject>.*` 14팩 + `*.runtime_adapter`(런타임) | 한 주인의 *정식 기억과 런타임* | **주인당 하나** — 사적 인스턴스 |

**흐름 (mine → stage evidence → confirm → upsert → compile):**

```
[빌더 프로젝트]  skill.pab.* + user.*.template
        │  (그 사람의 실제 세션·교정·diff = 입력 원재료)
        ▼  스킬 15로 암묵지 후보 보드 생성
[증거 아카이브 프로젝트]  세션 증거·pending 후보·검토 보드
        │  confirm/edit/reject/narrow (G3)
        ▼
[개인 에이전트 프로젝트]  승인된 personal.<subject>.* 14팩
        │  compile(S10, project-run)
        ▼
  personal.<subject>.runtime_adapter  ← 작업을 실행하는 Personal Agent
```

세 가지 불변식:

1. **빌더는 사람을 모른다.** `skill.pab.*`·`user.*` 템플릿은 *어떤 개인의 데이터도 담지 않습니다*(G6).
   그래서 한 빌더 프로젝트로 *여러 사람*의 에이전트를 만들 수 있습니다.
2. **증거 아카이브는 런타임 기억이 아니다.** 세션 팩과 pending 후보 보드는 검토·감사용 비계입니다.
   여기에 들어갔다고 개인 에이전트가 즉시 달라지지 않습니다.
3. **승인된 기억만 개인 에이전트로 간다.** confirmed/narrowed 후보만 `personal agent`의 정식 14팩에
   upsert 되고, 컴파일된 어댑터 역시 개인 에이전트 프로젝트에만 적재됩니다.

> 즉 "빌더 프로젝트*로만* 만든다"와 "승인된 팩은 개인 에이전트 프로젝트에 인제스트된다"는 둘 다 맞습니다.
> 그 사이의 `personal agent evidence`는 세션 증거와 후보를 보존하는 *비계*입니다. 런타임 기억은 오직
> 정식 14팩 upsert 이후에만 바뀝니다([01 라이프사이클](./01-kernel-schema.md): `user_reviewed` →
> `confirmed_or_rejected` → `target_pack_ingested` → `runtime_activated`).
