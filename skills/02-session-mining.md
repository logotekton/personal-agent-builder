# 02 · 세션 마이닝 (Session Mining)

> **EN:** Operating instructions for `skill.pab.session_mining` — the builder skill that mines
> *prior* AI-agent sessions (already captured as `EvidenceItem`s by skill 01) for repeated,
> evidence-bound **candidate signals**: standing preferences, anti-preferences, correction
> patterns, decision episodes, latent boundaries, artifact/format preferences, domain attention,
> tool preferences, workflow patterns, and unresolved goals. It does *not* mint typed
> `CandidateAssertion`s (that is skill 05) and it never writes a runtime rule. Its job is to
> turn a pile of past sessions into a ranked list of *signals worth extracting*, each tied to
> the evidence that proves it, with a confidence built from repetition, recency, explicitness,
> and correction strength — then route each to its scope and confirmation step.

세션 마이닝은 채굴 트리오([02 세션마이닝](./02-session-mining.md) · [03 질문](./03-elicitation-questioning.md) ·
[04 diff마이닝](./04-diff-mining.md))의 첫 번째 스킬이며, 빌더 파이프라인의 `mine_or_ask`
상태에 속합니다([파이프라인 §1·§3](../spec/02-builder-pipeline.md#1-9개-워크플로-상태와-12단계의-매핑)).
질문 스킬이 *빈 영역을 새로 묻고*, diff 마이너가 *한 번의 교정 쌍을 깊게 읽는다면*, 세션 마이너는
**이미 쌓인 다수의 세션을 가로질러 반복을 찾습니다.** 한 번 일어난 일은 우연이지만, 세 세션에
걸쳐 같은 교정이 반복되면 그것은 신호입니다.

이 문서는 마케팅이 아니라 **그대로 실행하는 운영 지침**입니다. 입력을 받고, 정의된 절차를 돌리고,
정의된 출력을 내보냅니다. 어휘는 [커널 스키마](../spec/01-kernel-schema.md)를 따르며 새 이름을
만들지 않습니다.

---

## 1. 목적 (Purpose)

축적된 과거 세션 증거(`EvidenceItem`)를 가로질러 **반복되는 행동 신호**를 채굴하고, 각 신호에
증거를 묶어 후보 신호 목록으로 내보낸다. 한 세션에 갇혀 사라질 암묵지를, 여러 세션의 반복으로
드러나는 *후보*로 끌어올리는 것이 핵심이다.

- **하는 일:** 세션을 분절하고, 분절 간 반복을 탐지하고, 반복마다 증거 묶음을 가진 후보 신호를
  추출하고, 네 축(반복·최근성·명시성·교정강도)으로 신뢰도를 매기고, 다음 단계(스코프·확인)로 보낸다.
- **하지 않는 일:** (1) 타입 지정된 `CandidateAssertion`을 만들지 않는다 — 그것은
  [05 후보 추출](./05-candidate-extraction.md)의 일이다. (2) `scope`를 확정하지 않는다 — 초안만
  제안하고 [06 스코프](./06-scope-context.md)가 확정한다. (3) 확인되지 않은 신호를 런타임 규칙으로
  만들지 않는다(게이트 G3). (4) 새 증거를 *생성*하지 않는다 — 증거 포착은 [01](./01-evidence-capture.md)의 몫이다.

> 출력은 **타입 미지정 후보 신호 + 그 근거 `EvidenceItem` 참조**다. 타입 지정·필드 정규화는
> 하류(S05)에서 일어난다([파이프라인 §3 S02](../spec/02-builder-pipeline.md#s02--s03--s04--상태-mine_or_ask-채굴-트리오)).

## 2. 작동 방식 (How it works)

세션 마이너는 다음 6단계를 순서대로 실행한다. 각 단계는 다음 단계의 입력 계약을 만족시킨다.

```
   누적 세션 EvidenceItem
        │
   [A] 분절(segment)            ── 세션을 (요청·답변·교정·승인/거부) 에피소드 단위로 나눔
        ▼
   [B] 반복 탐지(detect)        ── 분절·세션을 가로질러 같은 행동/선호/교정이 ≥2회 나타나는지
        ▼
   [C] 후보 추출(extract)       ── 10개 마이닝 타깃별로 후보 신호 + evidence_refs 묶음 생성
        ▼
   [D] 신뢰도(score)            ── repetition · recency · explicitness · correction_strength
        ▼                             (+ contradiction · domain_specificity · evidence_quality)
   [E] 스코프 초안(propose)     ── "언제/어디서 참인가" 가설을 단다 (확정은 S06)
        ▼
   [F] 라우팅(route)            ── 후보 신호 → S05 후보 추출 → S06 스코프 → S07 확인 게이트
```

**[A] 분절.** 세션 로그를 에피소드로 나눈다. 한 에피소드 = 하나의 요청과 그에 딸린 답변·교정·
수용/거부. 분절 경계는 주제 전환, 새 요청, 명시적 교정("아니 그거 말고")에서 잡는다. 이 단계는
이후 모든 반복 탐지의 비교 단위를 만든다.

**[B] 반복 탐지.** 에피소드들을 가로질러 *같은 종류의 행동*이 둘 이상 나타나는지를 본다. 표면
문구가 달라도 같은 선호/교정이면 한 묶음으로 센다(예: "더 짧게"·"불릿으로"·"서론 빼고"는 모두
*간결 선호*의 표현). 한 번뿐인 신호도 버리지 않되 **낮은 신뢰도**로만 통과시킨다(품질 체크 §5).

**[C] 후보 추출 (증거 동반).** 반복 묶음마다 후보 신호를 만들고, 그 신호를 떠받치는 모든
`EvidenceItem`을 `evidence_refs`로 묶는다(게이트 G1). 후보 문구는 **관찰된 행동 언어**로만 쓴다
— "사용자는 X를 싫어한다(추측 심리)"가 아니라 "사용자가 3개 세션에서 X를 Y로 교정했다"(관찰)로
(게이트 G4). 후보는 §3의 10개 마이닝 타깃 중 하나로 *분류 가설*을 단다(확정 타입은 S05).

**[D] 신뢰도 산정.** §4의 네 핵심 축으로 0..1 신뢰도를 매기고, 그 근거를 `confidence_inputs`로
**투명하게** 남긴다([candidate.schema.json](../schemas/candidate.schema.json)의
`confidence_inputs`와 동일 어휘). 신뢰도는 "이게 정말 규칙이어야 한다"는 확신이 아니라 "이 신호가
사용자를 충실히 반영한다"는 추출 신뢰도다 — 규칙 채택 여부는 사람이 확인 게이트에서 정한다.

**[E] 스코프 초안.** 후보가 어디서 참인지 가설을 단다(예: "코드리뷰 세션에서만", "외부 이메일에서").
"항상 참" 후보는 표시만 하고 좁히지 않는다 — 좁히는 일은 [S06 스코프](./06-scope-context.md)가 하며,
거기서 비어있지 않은 `scope`가 강제된다(게이트 G2).

**[F] 라우팅.** 후보 신호를 [05 후보 추출](./05-candidate-extraction.md)로 넘긴다. S05가 타입을
확정하면 그 `candidate_type`이 [1:1 전수 라우팅 표](../spec/01-kernel-schema.md#6-후보-타입--라우팅-11-전수)에
따라 목적지 `user.*` 팩을 결정한다. 세션 마이너는 §3 표의 *제안 팩*을 힌트로 달 뿐, 팩을 직접 만들지
않는다.

## 3. 마이닝 타깃 (무엇을 찾는가)

세션 마이너는 다음 10개 신호 종류를 노린다. 각 타깃은 어떤 후보 타입으로 정제될지(S05), 어떤
`user.*` 팩으로 라우팅될지(S08)의 가설을 함께 가진다. 표의 매핑은 힌트이며 확정은 하류 단계다.

| # | 마이닝 타깃 | 관찰 신호(세션에서 무엇이 보이는가) | 후보 타입 가설 → 제안 팩 |
|---|-------------|--------------------------------------|--------------------------|
| 1 | **반복 선호 (repeated preference)** | 여러 세션에서 같은 형식/접근을 일관되게 요청·수용 | `CommunicationStyleCandidate` / `PersonaTraitCandidate` → `user.communication_style` / `user.persona_core` |
| 2 | **반선호 (anti-preference)** | 같은 종류의 출력을 반복적으로 거부·삭제·"이건 말고" | `PersonaTraitCandidate` → `user.persona_core` (반복 거부는 §4 교정강도↑) |
| 3 | **교정 패턴 (correction pattern)** | before→after 교정이 여러 세션에서 같은 방향 | `CommunicationStyleCandidate` / `TacitHeuristicCandidate` → 해당 팩 (교정은 최강 신호) |
| 4 | **결정 에피소드 (decision episode)** | 선택지 사이에서 무엇을 우선했는가·무엇을 트레이드오프 했는가 | `DecisionPolicyCandidate` → `user.decision_policy` |
| 5 | **잠재 경계 (latent boundary)** | 외부 노출·민감 주제·비가역 행동 앞에서 멈추거나 확인을 요구 | `BoundaryRuleCandidate` → `user.boundary_authority` (민감 시 G5) |
| 6 | **산출물 형식 선호 (artifact format pref)** | 결과물의 형태(표·파일·리뷰보드·코드블록)를 반복 선호 | `ArtifactPolicyCandidate` → `user.artifact_policy` |
| 7 | **도메인 주의 (domain attention)** | 특정 도메인에서만 나타나는 용어·검사·관심 패턴 | `DomainOverlayCandidate` → `user.domain_overlays` (도메인 특화도↑) |
| 8 | **도구 선호 (tool pref)** | 특정 도구·언어·라이브러리·명령을 반복 선택 | `ToolPreferenceCandidate` → `user.tool_stack` |
| 9 | **워크플로 패턴 (workflow pattern)** | 같은 작업을 같은 단계 순서로 반복 수행 | `WorkflowPatternCandidate` → `user.workflow_playbooks` |
| 10| **미해결 목표 (unresolved goal)** | 세션을 넘나들며 다시 언급되지만 끝나지 않은 목표·프로젝트 | `ProjectMemoryCandidate` → `user.memory_project_graph` |

> 14개 후보 타입 중 `IdentityRoleCandidate`·`EvaluationCaseCandidate`·`DriftRecordCandidate`는
> 세션 마이닝의 *주된* 산출이 아니다(역할은 보통 [03 질문](./03-elicitation-questioning.md)에서,
> 평가 케이스·드리프트는 [11 평가·드리프트](./11-evaluation-drift.md) 루프에서 나온다). 다만 세션에서
> 강한 신호가 보이면 가설로 표시해 하류로 넘길 수 있다.

## 4. 신뢰도 산정 (Confidence)

각 후보 신호의 0..1 신뢰도는 다음 입력에서 산출되며, 입력값은 `confidence_inputs`로 남겨 감사
가능하게 한다([candidate.schema.json](../schemas/candidate.schema.json) 동일 어휘, 커널 §8). 네 개의
**핵심 축**과 세 개의 보조 입력으로 구성된다.

핵심 축(세션 마이닝에서 가중치가 가장 큼):

| 입력 | 의미 | 신뢰도에 미치는 방향 |
|------|------|----------------------|
| `repetition_count` | 후보를 독립적으로 떠받치는 서로 다른 `EvidenceItem` 수 | 반복 ↑ → 신뢰도 ↑ (단일 세션은 §5 규칙 적용) |
| `recency` | 근거 증거의 최근성(1 = 가장 최근) | 최근 ↑ → 신뢰도 ↑ (오래된 행동은 가중치 ↓, 드리프트 신호) |
| `explicit_statement` | 사용자가 직접 명시했는가("항상 X 해줘") vs 행동에서 추론 | 명시 = true → 신뢰도 ↑ (최근·명시 지시는 최고 가중) |
| `correction_strength` | 교정 신호의 강도(0..1) — 얼마나 단호히 바꿨/거부했는가 | 강한 교정 ↑ → 신뢰도 ↑ (교정은 가장 강한 경계 신호) |

보조 입력:

| 입력 | 의미 | 방향 |
|------|------|------|
| `contradiction_count` | 후보와 충돌하는 `EvidenceItem` 수 | ↑ → 신뢰도 ↓ (게이트에서 narrowed/deferred 유발 가능) |
| `domain_specificity` | 후보가 도메인에 얼마나 묶였는가(0..1) | `user.domain_overlays` 라우팅·스코프 좁힘 판단에 사용 |
| `evidence_quality` | 인용 증거의 직접성/품질(0..1) | 약한 추론보다 verbatim 교정이 높음 → 신뢰도 보정 |

**가중 원칙 (운영 규칙):**

1. **교정 > 수용 > 추론.** 사용자가 *바로잡은* 행동(`correction_strength`↑)은 단순히 수용한
   행동보다, 수용은 마이너가 추론한 것보다 무겁다.
2. **최근·명시 지시가 최고.** 최근의 명시적 지시(`recency`≈1 + `explicit_statement`=true)는
   가장 높은 신뢰도를 받는다. 오래된 암묵 신호와 충돌하면 최근 명시 쪽을 우선하고, 옛 신호는
   드리프트 후보로 표시한다.
3. **반복이 일반화를 정당화한다.** 넓은(broad) 후보는 반복 지원 또는 명시 확인 없이는 높은
   신뢰도를 받지 못한다(베이스 레코드 규칙과 정합).

## 5. 입력 / 출력 (Inputs / Outputs)

### 입력

- **주 입력:** 누적된 세션 `EvidenceItem` — [01 evidence_capture](./01-evidence-capture.md)가 출처·발췌·
  타임스탬프·원본 링크와 함께 만든 것. 세션 마이너는 이미 포착된 증거만 읽으며 새로 만들지 않는다.
- **부 입력(선택):** 이전 라운드의 확정 레코드(중복·드리프트 비교용), 활성 팩 커버리지(어느 팩이
  비었는지 → 채굴 우선순위), 사용자 지정 채굴 범위(기간·프로젝트·도메인).

### 출력

각 후보 신호는 다음을 동반한다(타입·필드 확정은 S05이지만, 마이너는 이 묶음을 넘긴다):

- `concise_claim`(초안) — 관찰 행동 언어로 쓴 한 문장.
- `evidence_refs` — 이 신호를 떠받치는 ≥1개 `EvidenceItem` 참조(게이트 G1, 빈 채로는 출력 금지).
- `confidence` + `confidence_inputs` — §4의 입력값을 채운 0..1 신뢰도와 그 근거.
- 마이닝 타깃 라벨(§3) + `proposed_target_pack` 가설.
- `scope`(초안 가설) + `sensitivity` 1차 분류(민감/제한 신호는 표시해 G5로 넘김).
- `extraction_method = session_mining`(프로비넌스, [candidate.schema.json](../schemas/candidate.schema.json)).

> 이 출력은 [S05 후보 추출](./05-candidate-extraction.md)의 입력 계약을 만족한다. 거기서
> `candidate_type`이 확정되고 [1:1 전수 라우터](../spec/01-kernel-schema.md#6-후보-타입--라우팅-11-전수)가
> 목적지 팩을 결정한다.

## 6. 품질 체크 (Quality checks)

출력 전에 세션 마이너는 다음을 강제한다. 위반 시 그 신호는 신뢰도를 낮추거나 보류한다.

- **단일 세션 과일반화 금지.** 한 세션에서만 본 신호를 *넓은 규칙*으로 올리지 않는다. 단일 세션
  신호는 **반드시 낮은 신뢰도**로만 통과하며, 넓은 일반화는 반복 지원이나 명시 확인을 기다린다.
- **교정에 더 큰 가중.** 같은 무게로 보이는 신호라면 *교정*(before→after)에서 온 것을
  *수용/추론*에서 온 것보다 높게 친다(`correction_strength`).
- **최근·명시 지시 최우선.** 최근의 명시적 사용자 지시는 가장 높은 신뢰도를 받고, 오래된 암묵
  신호와 충돌하면 우선한다(옛 신호는 [05 평가·드리프트](../spec/05-evaluation-drift.md) 후보로 표시).
- **증거 없는 신호 금지(G1).** `evidence_refs`가 빈 후보는 만들지 않는다 — 추측은 신호가 아니다.
- **행동 언어만(G4).** 후보 문구는 관찰된 행동만 기술하고 추측된 심리·동기를 단정하지 않는다.
- **민감 신호 표시(G5 예비).** 민감/제한 신호는 `sensitivity`로 표시해 [09 프라이버시 경계](./09-privacy-boundary.md)가
  승격 전 `BoundaryRule`을 붙일 수 있게 한다.
- **중복·모순 점검(예비).** 기존 확정 레코드와 중복되면 신규 증거로 표시(신뢰도 보강용)하고, 모순되면
  `contradiction_count`를 올려 드리프트 후보로 넘긴다. *이 점검은 예비일 뿐* — 권위 있는 dedup
  judge(novel/duplicate/refinement/conflict → insert/merge/supersede/surface)와 conflict→사람 노출은
  하류 승격 직전(S07/병합 층)에서 일어난다([10 중복 억제·병합](../spec/10-dedup-and-merge.md),
  [`tools/pab_merge.py`](../tools/pab_merge.py)).

## 7. Crab 역할 (Crab role)

이 스킬의 소유 역할은 **Session Miner**다([crab 오케스트레이션](./12-crab-orchestration.md),
[커널 §8](../spec/01-kernel-schema.md#8-crab-에이전트-역할-운영-모델)).

- **소유 작업:** `mine_or_ask` 상태에서 누적 세션 증거의 분절·반복 탐지·후보 신호 추출·신뢰도 산정.
- **받는 핸드오프:** **Evidence** 역할(S01)이 만든 `EvidenceItem` 묶음.
- **넘기는 핸드오프:** 후보 신호 → **Candidate Extractor** 역할(S05). 빈 영역·모호 신호는
  **Orchestrator**가 **Questioning**(S03)로, 교정 쌍 중심 작업은 **Diff Miner**(S04)로 라우팅한다.
- **경계:** 타입 확정(S05)·스코프 확정(S06)·확인(S07)·라우팅(S08)을 침범하지 않는다. 미확인 신호를
  런타임으로 올리지 않는다(G3).

OpenCrab 도구로 실행할 때는 `opencrab_search_documents`/`opencrab_query`로 세션 증거를 가로질러
반복을 조회하고, 후보 신호를 `opencrab_ingest_text`로 후보 단계 노드에 적재한 뒤 S05로 핸드오프한다.
권한·민감도 판단은 [04 프라이버시·경계](../spec/04-privacy-boundary.md)의 권한 레벨을 따른다.

## 8. 관련 문서

- 라이프사이클·노드·엣지·게이트·후보 라우팅 → [01 커널 스키마](../spec/01-kernel-schema.md)
- 이 스킬이 속한 12단계 파이프라인 계약 → [02 빌더 파이프라인](../spec/02-builder-pipeline.md)
- 채굴 트리오의 다른 두 스킬 → [03 질문](./03-elicitation-questioning.md) · [04 diff 마이닝](./04-diff-mining.md)
- 후보 신호를 타입 지정 `CandidateAssertion`으로 → [05 후보 추출](./05-candidate-extraction.md)
- 후보 신호/신뢰도 입력의 기계 스키마 → [`schemas/candidate.schema.json`](../schemas/candidate.schema.json)
- 스코프 확정·확인 게이트 → [06 스코프](./06-scope-context.md) · [07 확인 게이트](./07-confirmation-gate.md)
- 라우팅 도착지인 14개 팩 → [03 팩 카탈로그](../spec/03-pack-catalog.md)
- 역할·상태·핸드오프 운영 모델 → [12 crab 오케스트레이션](./12-crab-orchestration.md)


## 트리거 (Trigger)

> 이 스킬의 발화 조건. 전체 2계층 모델·호스트(훅) 매핑·게이트 보존은
> [../spec/09-triggers.md](../spec/09-triggers.md), 머신 스키마는
> [../schemas/trigger.schema.json](../schemas/trigger.schema.json) 참고.

```yaml
trigger:
  trigger_id: pab.session_mining.on_session_end
  skill: session_mining
  signal: session_end
  condition: "mine the full transcript when a session ends"
  cadence: session_boundary
  host_hook: Stop · Cron
  produces: candidate_staged
  requires_confirmation: false     # 스테이징만 (라이브 규칙 아님)
  default_state: enabled
  debounce: batch_at_session_end
```

세션이 끝나면 트랜스크립트 전체를 일괄 마이닝해 후보를 스테이징합니다.
