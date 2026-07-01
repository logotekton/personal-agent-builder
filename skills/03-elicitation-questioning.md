# 03 · 구조화 질문 (Elicitation Questioning)

> **EN:** Operating instructions for `skill.pab.elicitation_questioning` — pipeline step
> **S03**, workflow state `mine_or_ask`, owned by the **Questioning Crab**. Where session
> mining (S02) and diff mining (S04) read patterns the user *already left behind*, this skill
> goes after the patterns the user has **not volunteered**: the empty packs, the ambiguous
> signals, the judgment calls that never surfaced in a log. It runs a structured,
> **episode-based** interview — anchored on a concrete recent decision, not abstract
> self-description — and captures each answer faithfully as an `EvidenceItem`. Every answer
> becomes the `evidence_refs` target a later `CandidateAssertion` will cite (Gate **G1**). It
> elicits and records; it does **not** type, score, or confirm.

이 문서는 빌더 파이프라인 3단계 [`S03 elicitation_questioning`](../spec/02-builder-pipeline.md#s02--s03--s04--상태-mine_or_ask-채굴-트리오)의
**실행 지침**입니다. 마케팅 문서가 아니라, 그대로 따라 돌릴 수 있는 운영 절차로 읽으세요.
어휘는 [01 커널 스키마](../spec/01-kernel-schema.md), 필드 규약은
[통합 베이스 레코드](../schemas/record.base.schema.json), 후보 필드는
[`candidate.schema.json`](../schemas/candidate.schema.json), 팩 정의는
[03 팩 카탈로그](../spec/03-pack-catalog.md)를 따릅니다.

---

## 1. 목적 (Purpose)

세션 마이닝(S02)과 diff 마이닝(S04)은 사용자가 **이미 남긴** 신호를 읽습니다. 하지만 사용자가
한 번도 표현하지 않은 판단 — 빈 팩, 모호한 신호, 로그에 떠오른 적 없는 경계 — 은 채굴만으로는
잡히지 않습니다. **구조화 질문**은 바로 그 *말하지 않은 패턴*을 향해 묻습니다.

이 단계의 단 하나의 책임은 **빈 영역을 겨냥한 질문으로 새 증거를 끌어내고, 그 답변을 날것 그대로
`EvidenceItem`으로 보존하는 것**입니다. 질문은 도구이고, 산출물은 *해석이 아니라 증거*입니다.

세 가지 불변식 (반드시 지킴):

1. **에피소드를 묻고, 자기소개를 묻지 않는다.** "당신은 어떤 사람입니까"는 추측을 부릅니다
   (게이트 **G4** 위반의 단골 출처). 대신 *실제로 있었던 최근 한 번의 결정*을 묻습니다 — 무엇을
   골랐고, 무엇을 버렸고, 왜인지. 일반론이 아니라 일화(episode)가 행동 증거를 만듭니다.
2. **답변을 후보로 만들지 않는다.** 이 단계는 `CandidateAssertion`을 생산하지 않습니다. 답변을
   `EvidenceItem`으로 포착할 뿐입니다. 타입 지정·스코프·점수는 [S05 candidate_extraction](../skills/05-candidate-extraction.md)의 일입니다.
3. **모든 후보는 ≥1개의 증거를 가리킨다.** 인터뷰 답변이 곧 게이트 **G1**(증거 없는 주장 금지)의
   *대상*입니다. 답변에서 나온 후보의 `evidence_refs`는 **그 답변 `EvidenceItem`의 id**입니다.

> 한 줄 계약: **빈 영역·모호 신호 → 에피소드 질문 → 인터뷰 답변 `EvidenceItem`.** 입력은
> 채워지지 않은 팩이나 해석이 갈리는 신호, 출력은 사용자의 답변을 원문 그대로 담은 증거 노드입니다.

## 2. 작동 방식 (How it works)

```
  무엇을 물을지 고른다              질문 프로토콜(§4)              답변을 보존한다
  ─────────────────              ─────────────                ─────────────
  빈 팩(coverage 낮음) ─┐
  모호한 신호(해석 갈림) │  (a) 표적: 어느 팩의 어떤 공백인가     ┌──────────────┐
  S02/S04가 못 좁힌 신호 ├─►(b) 에피소드: 최근 결정 1건 고정 ────►│ EvidenceItem │
  대조가 필요한 선호     │  (c) 탐침: 골랐다/버렸다/왜/거부 기준  │ source_type= │
  경계가 불분명한 영역  ─┘  (d) 경계: 무엇을 확인받고 싶은가      │ user_answer  │
                            (e) 검증: 답변을 사용자에게 되읽음    └──────┬───────┘
                                                                        │
                                                                        ▼
                                                S05 candidate_extraction 이 소비
```

흐름은 다섯 동작 — **표적 → 에피소드 → 탐침 → 경계 → 검증** — 으로 끝납니다. 어느 동작에서도
답변의 *의미를 확정*하지 않습니다. "이 답변이 어떤 규칙인가"는 다음 단계의 질문입니다. 이 단계의
질문은 오직 "이 사람이 실제로 한 번 어떻게 판단했는가, 그 말을 어떻게 손실 없이 보존할 것인가"입니다.

파이프라인 위치: 워크플로 상태 `mine_or_ask`에서 S02·S04와 *형제*로 동작합니다
([파이프라인 S02/S03/S04](../spec/02-builder-pipeline.md#s02--s03--s04--상태-mine_or_ask-채굴-트리오)).
오케스트레이터가 **언제 채굴 대신 질문을 부를지**(§3.3) 정하고, 산출된 인터뷰 `EvidenceItem`은
다음 상태 `extract_candidates`의 [S05](../skills/05-candidate-extraction.md)가 입력으로 받습니다.

## 3. 입력 / 출력 (Inputs / Outputs)

### 3.1 입력: 질문 트리거 (When to ask)

질문은 비싸므로(사용자의 시간을 씁니다) *아무 때나* 묻지 않습니다. 다음 신호가 있을 때만 기동합니다.

| 트리거 | 설명 | 표적 팩(예) |
|--------|------|-------------|
| **빈 팩(coverage 낮음)** | [수렴 지표](../spec/06-convergence-model.md)상 확정 레코드 <3인 팩 | 해당 팩 전부 |
| **해석이 갈리는 신호** | S02/S04가 둘 이상으로 읽힌다고 표시한 모호 신호 | 신호가 가리키는 팩 |
| **대조가 필요한 선호** | "이건 좋다"는 있는데 *왜 다른 것을 버렸는지* 증거가 없음 | `user.decision_policy`, `user.communication_style` |
| **불분명한 경계** | 무엇을 확인받고 싶은지, 무엇을 위임하는지 기록 없음 | `user.boundary_authority` |
| **빈 거부 기준** | 어떤 출력을 *거부*하는지에 대한 직접 증거 없음 | `user.red_flags`, `user.artifact_policy` |

### 3.2 출력: 인터뷰 답변 `EvidenceItem`

각 답변은 [`S01 evidence_capture`](../skills/01-evidence-capture.md)와 **같은 `EvidenceItem` 계약**으로
보존됩니다. `EvidenceItem`은 통합 베이스 레코드가 아니라 *출처 노드*입니다
([커널 §3](../spec/01-kernel-schema.md#3-노드-타입-node-types)). 질문 단계의 산출물은 다음을 채웁니다.

| 필드 | 필수 | 의미 (질문 단계 특수성) |
|------|:----:|------|
| `id` | ✓ | 안정 증거 id. 형식 `<subject>.evidence.NNN`. 이 값이 후보의 `evidence_refs`가 된다. |
| `source_type` | ✓ | 항상 **`user_answer`** (인터뷰 답변). [S01 §3.1](../skills/01-evidence-capture.md#31-입력-소스-input-sources) 열거값. |
| `source_title` | ✓ | 짧은 라벨 (예: `"인터뷰 — 6/24 보고서 포맷 결정"`). |
| `source_timestamp` | ✓ | RFC 3339. 인터뷰가 진행된 시각. |
| `source_ref` | ✓ | 인터뷰 세션·질문 id로 되돌아가는 참조 (예: `interview://2026-06-24#q3`). **반드시 어떤 질문에 대한 답인지** 식별 가능해야 함. |
| `excerpt` | ✓ | **사용자 답변 원문 그대로**. 의역·요약 금지(§5). 질문 문구는 `source_ref`/`source_title`에 두고, `excerpt`에는 *답변*만 담는다. |
| `privacy_level` | ✓ | `public` \| `internal` \| `sensitive` \| `restricted`. 인터뷰는 사적 일화를 끌어내므로 민감도 상향에 특히 주의(§5-4). |
| `extraction_status` | ✓ | 처음 포착 시 `captured`. |
| `prompt_protocol` | – | 어떤 프로토콜 질문(§4 P1–P5)에서 나온 답인지 표시 — 추출기가 후보 타입을 좁히는 힌트. |
| `related_task` / `related_project` | – | 일화가 속한 작업·프로젝트 링크 ([`user.memory_project_graph`](../schemas/user.memory_project_graph.schema.json)). |

> 한 인터뷰 = **여러 `EvidenceItem`.** 한 답변에 서로 다른 주제(포맷 선호 + 거부 기준 + 경계)가
> 섞이면, 응집된 발췌 단위로 쪼개 각각 별도 `EvidenceItem`을 만듭니다. 한 증거 = 한 응집된 답변.

### 3.3 답변이 후보가 되는 길 (evidence_ref = the interview answer)

이 단계는 후보를 만들지 않지만, *후보가 어디서 증거를 가져올지*를 결정합니다. 인터뷰 답변
`EvidenceItem`의 `id`가 곧 [S05](../skills/05-candidate-extraction.md)가 만들 후보의
`evidence_refs` 원소입니다. 즉 **evidence_ref = 그 인터뷰 답변**입니다.

```
  인터뷰 답변(EvidenceItem  logotekton.evidence.041)
        │  S05 candidate_extraction
        ▼
  CandidateAssertion { candidate_type: "ArtifactPolicyCandidate",
                       concise_claim: "긴 보고서는 1장 요약 + 부록 분리를 선호",
                       evidence_refs: ["logotekton.evidence.041"],   ← 그 답변
                       proposed_target_pack: "user.artifact_policy", ... }
```

질문 단계는 *그 화살표의 출발점*만 만듭니다. 화살표 자체(타입·`concise_claim`·`proposed_target_pack`)는
S05의 일입니다. 답변을 미리 후보처럼 해석해 적어두지 마세요 — 단계 불변식 위반입니다(§1-2, G4).

## 4. 질문 프로토콜 (Question protocol)

표준 인터뷰는 **하나의 최근 결정 에피소드**에 닻을 내리고 다섯 묶음으로 진행합니다. 일반론("당신은
어떤 스타일을 선호하세요?")은 추측·자기서사를 부르므로 **금지**입니다. 항상 *구체적 일화*로
되돌리세요("**가장 최근에** 이런 결정을 한 게 언제였죠? 그때 무엇을 골랐나요?").

### P1 — 결정 에피소드 (Decision episode) → `DecisionPolicyCandidate`

- 가장 최근에 내린 *작업상 결정* 한 건을 떠올려 주세요. 무엇에 관한 결정이었나요?
- **무엇을 선택했나요?** (the option you chose)
- **무엇을 버렸나요?** 후보에 올랐지만 택하지 않은 다른 안은? (what you rejected)
- **왜 그 선택이었나요?** 둘을 가른 결정적 기준 하나만 꼽으면? (the deciding tradeoff)
- 다시 비슷한 상황이면 같은 기준으로 판단하나요, 아니면 그때만 그랬나요? (→ S06 스코프의 단서)

### P2 — 선호 포맷 (Preferred formats) → `CommunicationStyleCandidate` · `ArtifactPolicyCandidate`

- 그 결과물을 어떤 **형태**로 받았을 때 "이거다" 싶었나요? (구조·길이·순서·매체)
- 결론과 근거 중 무엇이 먼저 와야 하나요? 표·산문·코드블록 중 무엇이 맞았나요?
- 받자마자 *그대로 쓸 수 있는* 산출물의 모습은? (→ `user.artifact_policy`)

### P3 — 거부 기준 (What makes you reject an output) → `RedFlagCandidate` · `ArtifactPolicyCandidate`

- 에이전트 출력 중 **버린 것**이 있었나요? 무엇이 마음에 안 들었나요?
- 어떤 한 가지가 보이면 *읽기도 전에* 신뢰가 깨지나요? (a single disqualifier)
- "이건 근거가 약하다/구조가 빈약하다"고 느낀 순간은? (→ `user.red_flags`)

### P4 — 경계 (Boundaries) → `BoundaryRuleCandidate`

- 그 작업에서 에이전트가 **혼자 해도 되는 것**과 **반드시 확인받아야 하는 것**의 선은 어디였나요?
- 외부 발송·되돌릴 수 없는 행동·계약/약속은 어떻게 다뤄지길 바라나요? (→ ask_confirm 기본 정책)
- 절대 저장·검색·노출되면 안 되는 종류의 정보가 닿았나요? (→ 민감도 상향, §5-4)

### P5 — 암묵 규칙·역할 (Tacit rule / role) → `TacitHeuristicCandidate` · `IdentityRoleCandidate`

- 방금 결정에서, 말로 설명한 적 없지만 *늘 그렇게 하는* 판단이 있었나요? (an unspoken rule)
- 이 일을 할 때 당신은 어떤 **역할**로서 판단하나요? (예: 리뷰어 / 설계자 / 편집자)

> 프로토콜은 *대본*이 아니라 *체크리스트*입니다. P1으로 닻을 내리고, 사용자의 답이 어느 팩의
> 공백을 메우느냐에 따라 P2–P5를 골라 깊이 파세요. 한 인터뷰가 다섯 묶음을 모두 채울 필요는 없습니다.

## 5. 포착 규칙 (Capture rules)

질문은 잘했는데 답변을 잘못 보존하면 증거가 오염됩니다. 다음 다섯 규칙은 강제입니다.

1. **에피소드를 강제하라 (Force the episode).** 사용자가 일반론("저는 보통 간결한 걸 좋아해요")으로
   답하면, *한 번의 구체적 사례*로 되돌리세요("가장 최근에 그렇게 느낀 결과물이 뭐였죠?"). 일화 없는
   선호 진술은 약한 증거이며, S05에서 `confidence`가 낮게 잡혀 반례를 요구받습니다.
2. **답변 원문을 보존하라 (Preserve the answer verbatim).** `excerpt`는 사용자가 *실제로 한 말*
   그대로입니다. 다듬거나 "정리"하지 않습니다. 질문 문구는 `excerpt`에 넣지 말고 `source_ref`/
   `source_title`에 두어, 발췌가 *답변만* 담게 합니다.
3. **유도하지 마라 (Do not lead).** "그러니까 결론부터 받는 걸 선호하신다는 거죠?"처럼 답을
   *대신 말해주는* 질문은 증거를 오염시킵니다. 열린 질문으로 사용자가 *자기 단어로* 말하게 하고,
   그 단어를 그대로 보존하세요. 해석은 절대 증거 노드에 넣지 않습니다(게이트 **G4**의 출발점).
4. **민감 항목을 표시하라 (Mark sensitive).** 인터뷰는 결정 *배경*을 끌어내므로 사적 정보(인물·
   재무·건강·계약·신원)가 답변에 섞이기 쉽습니다. 닿으면 `privacy_level`을 `sensitive`/`restricted`로
   올립니다 — 게이트 **G5**(승격 전 프라이버시)로 흘러가 [S09 privacy_boundary](../skills/09-privacy-boundary.md)가
   `BoundaryRule`을 *먼저* 부착합니다. 의심스러우면 더 높은 등급으로.
5. **답변을 되읽어 검증하라 (Read back to confirm).** 포착 전, 발췌를 사용자에게 한 번 되읽어
   "이 말이 맞나요?"로 확인합니다. 이는 *해석의 확인이 아니라 원문의 확인*입니다 — 무엇이 규칙인지의
   확정은 여전히 [S07 confirmation_gate](../skills/07-confirmation-gate.md)의 일입니다. 안정 `id`를
   부여하고 같은 답을 두 번 포착하지 않게 거릅니다(G1 토대).

## 6. 품질 검사 (Quality checks)

인터뷰 세션을 마치기 전 다음을 통과해야 합니다. 코드 강제는
[`tools/validate_packs.py`](../tools/validate_packs.py)가 보조합니다.

- [ ] **표적 정당성** — 채굴(S02/S04)으로 못 얻을 *빈 영역·모호 신호*를 겨냥했는가. 이미 증거가
  충분한 곳을 불필요하게 또 물어 사용자의 시간을 낭비하지 않았는가(§3.1 트리거).
- [ ] **에피소드 기반** — 자기소개가 아니라 *최근 결정 한 건*에 닻을 내렸는가. 일반론 답변을
  구체적 일화로 되돌렸는가(P1).
- [ ] **선택/거부/이유 포착** — *무엇을 골랐고 / 무엇을 버렸고 / 왜인지*가 발췌에 들어 있는가(P1·P3).
- [ ] **원문 보존** — `excerpt`가 사용자 답변 원문인가. 질문 문구가 발췌에 섞이지 않았는가.
- [ ] **비유도성** — 답을 대신 말해주는 유도 질문이 아니었는가. 사용자가 *자기 단어로* 말했는가.
- [ ] **해석 부재(G4)** — 발췌·라벨에 "선호한다/싫어한다/때문이다" 같은 *판단*이 섞이지 않았는가.
  타입·`concise_claim`을 미리 적어두지 않았는가(§3.3).
- [ ] **재방문 가능** — `source_ref`만으로 *어떤 질문에 대한 답*인지 되찾아갈 수 있는가.
- [ ] **민감도 표시(G5 예비)** — 사적 정보가 닿은 답변의 `privacy_level`이 상향됐는가.
- [ ] **참조 가능성(G1 예비)** — `id`가 안정적이고, 이 답변이 후보의 `evidence_refs`(= 그 답변)로
  가리켜질 수 있는가. 중복 포착이 아닌가.
- [ ] **경계 준수** — 후보를 만들지 않았는가. `source_type: user_answer`인 `EvidenceItem`만
  출력했는가(단계 불변식).

## 7. Crab 역할 — Questioning Crab

이 스킬의 소유 역할은 **Questioning Crab**입니다([12 crab 오케스트레이션](../skills/12-crab-orchestration.md)).

- **소유 작업:** 워크플로 상태 `mine_or_ask` 중 *질문 경로*. 빈 영역·모호 신호를 입력으로
  받아 에피소드 인터뷰를 진행하고 `source_type: user_answer`인 `EvidenceItem`만 생산.
- **핸드오프 (받음):** [Orchestrator Crab](../skills/12-crab-orchestration.md)가 *채굴로는 못
  메우는 공백*(coverage 낮은 팩, 해석이 갈리는 신호)을 넘길 때 기동합니다. 채굴 형제인
  [Session Miner](../skills/02-session-mining.md)·[Diff Miner](../skills/04-diff-mining.md)가
  "여기는 증거가 없다/모호하다"고 표시한 지점이 곧 질문의 표적입니다.
- **핸드오프 (넘김):** 인터뷰 `EvidenceItem`을 [Candidate Extractor](../skills/05-candidate-extraction.md)에게
  넘깁니다. 추출기는 각 답변을 타입 지정된 `CandidateAssertion`으로 바꾸며, `evidence_refs`로
  *그 답변*을 가리킵니다(§3.3).
- **하지 않는 것:** 타입 지정·스코프·점수·확인·라우팅은 이 역할의 일이 아닙니다. Questioning Crab은
  *답을 끌어내 보존*할 뿐, *답의 의미를 확정*하지 않습니다. 그 절제가 게이트 G1·G4·G5의 토대를 놓습니다.

> 9-space 사상: 인터뷰의 **출처**(인터뷰 세션)는 `resource`, **답변 발췌**는 `evidence`로
> 사상됩니다. 답변이 끌어낸 *결정 기준*은 이후 `policy`/`lever`로, *선호*는 `concept`으로
> 흐릅니다([07 9-space 크로스워크](../spec/07-opencrab-9space-crosswalk.md)).

## 8. 관련 문서

- 이 단계의 파이프라인 계약 → [02 빌더 파이프라인 · S02/S03/S04](../spec/02-builder-pipeline.md#s02--s03--s04--상태-mine_or_ask-채굴-트리오)
- 형제 채굴 스킬 → [02 session_mining](../skills/02-session-mining.md) · [04 diff_mining](../skills/04-diff-mining.md)
- 답변을 받는 다음 단계 → [05 candidate_extraction](../skills/05-candidate-extraction.md) ·
  [`candidate.schema.json`](../schemas/candidate.schema.json)
- `EvidenceItem` 계약 (공유) → [01 evidence_capture](../skills/01-evidence-capture.md)
- 노드/엣지/게이트/라이프사이클 어휘 → [01 커널 스키마](../spec/01-kernel-schema.md)
- 어떤 팩의 공백을 메우는지 → [03 팩 카탈로그](../spec/03-pack-catalog.md) · [06 수렴 모델](../spec/06-convergence-model.md)
- 민감 답변이 받는 경계 규칙 → [04 프라이버시·경계](../spec/04-privacy-boundary.md) ·
  [09 privacy_boundary](../skills/09-privacy-boundary.md)
- 역할·핸드오프 운영 모델 → [12 crab 오케스트레이션](../skills/12-crab-orchestration.md)


## 트리거 (Trigger)

> 이 스킬의 발화 조건. 전체 2계층 모델·호스트(훅) 매핑·게이트 보존은
> [../spec/09-triggers.md](../spec/09-triggers.md), 머신 스키마는
> [../schemas/trigger.schema.json](../schemas/trigger.schema.json) 참고.

```yaml
trigger:
  trigger_id: pab.elicitation_questioning.on_coverage_gap
  skill: elicitation_questioning
  signal: coverage_gap
  condition: "a pack is under-covered and an opportune moment arises, or the user runs /interview"
  cadence: event
  host_hook: [orchestrator, command]
  produces: candidate_staged
  requires_confirmation: true     # 사람 검토 필요 (게이트)
  default_state: suggested
  debounce: 1/session
```

사용자에게 직접 묻기 때문에 확인이 필요하고, 기본은 '제안' 상태입니다(끼어들지 않음).
