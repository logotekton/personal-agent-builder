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
| **resource** | `EvidenceItem` 출처(세션·파일·diff), `ToolPreference` 대상 | 참조되는 자원·자산 |
| **evidence** | `EvidenceItem` 발췌, `evidence_refs` | 주장을 떠받치는 증거 |
| **concept** | `PersonaTrait`, `CommunicationStyleRule`, `DomainOverlay`, `WorkflowPattern`, `IdentityRole` | 사람에 관한 안정적 개념 |
| **claim** | `CandidateAssertion` / 확인된 `statement` | 증거에 묶인 가변(defeasible) 주장 |
| **community** | `AssistantProfile`↔`UserSubject` 관계, 확인 리뷰보드, 개인 에이전트 네트워크 | 행위자·관계망 |
| **outcome** | `EvaluationCase` 결과, `correction_cost`, `decision_fidelity` | 측정된 결과 |
| **lever** | `WorkflowPattern` 단계, `DecisionPolicy` 우선순위, 도구 행동 | 에이전트가 당기는 지렛대 |
| **policy** | `BoundaryRule`, `DecisionPolicy` 규칙, `RedFlag`, 프라이버시/권한 기본값 | 행동을 규율하는 정책 |

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
