# 04 · diff 마이닝 (Diff Mining)

> **EN:** Operating instructions for `skill.pab.diff_mining` — the third skill of the mining
> trio, owned by the **Diff Miner Crab**. It reads *before/after correction pairs* — what the
> agent produced, and what the subject changed it into — which are the **strongest evidence**
> the pipeline has: a correction shows not what the subject says they want, but what they
> actually accept. The skill collects the before/after, classifies the correction (style vs.
> decision vs. format), mints candidate signals, attaches **both** the before and the after as
> evidence, and routes downstream. It does *not* type the final `CandidateAssertion` (that is
> skill 05) and never writes a runtime rule (Gate G3). Its discipline: do not generalize a
> global rule from a single edit unless confidence stays low, and keep *style* corrections
> separate from *decision* corrections.

diff 마이닝은 채굴 트리오([02 세션마이닝](./02-session-mining.md) · [03 질문](./03-elicitation-questioning.md) ·
[04 diff마이닝](./04-diff-mining.md))의 세 번째 스킬이며, 빌더 파이프라인의 `mine_or_ask`
상태에 속합니다([파이프라인 §3](../spec/02-builder-pipeline.md)). 세션 마이너가 *여러 세션을
가로질러 반복*을 찾고, 질문 스킬이 *빈 영역을 새로 묻는다면*, diff 마이너는 **한 번의 교정 쌍을
깊게 읽습니다.** before(에이전트가 낸 것)와 after(사용자가 바꾼 것) 사이의 차이 — 그 *델타*가
사용자의 실제 수용 기준을 가장 직접적으로 드러내기 때문입니다.

이 문서는 마케팅이 아니라 **그대로 실행하는 운영 지침**입니다. 어휘는
[커널 스키마](../spec/01-kernel-schema.md), 필드 규약은
[`candidate.schema.json`](../schemas/candidate.schema.json)과
[통합 베이스 레코드](../schemas/record.base.schema.json), 팩 정의는
[03 팩 카탈로그](../spec/03-pack-catalog.md)를 따르며 새 이름을 만들지 않습니다.

---

## 1. 목적 (Purpose)

diff 마이닝은 **before/after 교정 쌍에서 신호를 뽑는** 단계입니다. 사용자가 에이전트의 출력을
*고친* 순간 — 한 문장을 지우고, 표를 불릿으로 바꾸고, 결론을 앞으로 끌어오고, "이 방식 말고
저 방식으로" 결정을 뒤집은 순간 — 그 차이에는 어떤 인터뷰 답변보다 강한 증거가 들어 있습니다.
말로 한 선호는 이상(理想)이지만, 교정은 **실제 수용 기준**이기 때문입니다.

그래서 diff 마이닝의 단 하나의 책임은 **before와 after를 모두 보존한 채, 그 사이의 변화가
무엇을 뜻하는지 분류하고, 증거에 묶인 후보 신호로 끌어올리는 것**입니다.

- **하는 일:** before/after를 수집하고, 교정의 종류(스타일 vs 결정 vs 포맷)를 분류하고, 교정마다
  후보 신호를 만들고, **before와 after를 둘 다** `evidence_refs`로 묶고, 신뢰도를 매겨 다음
  단계로 라우팅한다.
- **하지 않는 일:** (1) 타입 지정된 `CandidateAssertion`을 만들지 않는다 — 그것은
  [05 후보 추출](./05-candidate-extraction.md)의 일이다. (2) `scope`를 확정하지 않는다 — 초안만
  제안하고 [06 스코프](./06-scope-context.md)가 확정한다. (3) 미확인 신호를 런타임 규칙으로
  올리지 않는다(게이트 G3). (4) 새 증거를 *생성*하지 않는다 — before/after의 포착은
  [01 evidence_capture](./01-evidence-capture.md)의 몫이며(`source_type` = `diff` 또는
  `correction`), diff 마이너는 이미 포착된 쌍을 읽는다.

> 한 줄 계약: **before/after 교정 쌍 → 양쪽 증거에 묶인 후보 신호.** 출력은 타입 미지정
> 후보 신호이되, *before와 after를 모두* 가리키는 `evidence_refs`를 반드시 가집니다.

## 2. 작동 방식 (How it works)

diff 마이너는 다음 다섯 동작을 순서대로 실행합니다 — **수집 → 분류 → 후보 생성 → 양쪽 증거
부착 → 라우팅**. 어느 동작에서도 추측된 심리를 단정하지 않고, 관찰된 *변화*만 기술합니다(G4).

```
   교정 쌍 EvidenceItem (before, after)
        │
   [A] 수집(collect)         ── before(에이전트 출력)와 after(사용자 교정)를 한 쌍으로 묶음
        ▼
   [B] 분류(classify)        ── 이 교정은 style / decision / format 중 무엇인가 (§3)
        ▼
   [C] 후보 생성(create)     ── 교정마다 후보 신호 + concise_claim(관찰 행동 언어) 생성
        ▼
   [D] 양쪽 부착(attach BOTH) ── before와 after를 둘 다 evidence_refs로 묶음 (G1, §4 규칙)
        ▼
   [E] 라우팅(route)         ── 후보 신호 → S05 후보 추출 → S06 스코프 → S07 확인 게이트
```

**[A] 수집.** 한 교정 쌍을 이룬다: `before`는 에이전트가 낸 산출물·답변, `after`는 사용자가
바꾼 결과입니다. 둘 다 [01](./01-evidence-capture.md)이 이미 `EvidenceItem`으로 포착한 것을
읽습니다(보통 `before`는 `source_type=artifact`, `after`는 `source_type=diff`/`correction`).
한 세션에 교정이 셋이면 쌍도 셋입니다 — 각 쌍을 독립 단위로 다룹니다.

**[B] 분류.** 변화가 *어떤 종류*인지 가린다(§3). 같은 한 줄짜리 교정이라도 "더 짧게"는 스타일,
"라이브러리 A 대신 B로"는 결정, "표 대신 불릿으로"는 포맷입니다. 이 분류가 후보 타입 가설과
목적지 팩 가설을 가릅니다. **스타일 교정과 결정 교정을 한 후보에 섞지 마세요**(§5 규칙) — 둘은
다른 팩(`user.communication_style` vs `user.decision_policy`)으로 가고, 섞이면 둘 다 오염됩니다.

**[C] 후보 생성.** 교정마다 후보 신호를 만들고 `concise_claim`을 **관찰된 변화의 언어**로 씁니다.
"사용자는 장황함을 싫어한다(추측 심리)"가 아니라 "사용자가 3문단 서론을 한 줄 결론으로 교체했다
(관찰)"로 씁니다(G4). 한 번의 교정에서 *전역 규칙*을 단정하지 않습니다 — 단일 교정은 낮은
신뢰도로만 통과합니다(§4·§5).

**[D] 양쪽 증거 부착 (핵심).** before와 after를 **둘 다** `evidence_refs`에 넣습니다. after만
넣으면 "무엇으로 바꿨는지"는 알아도 "무엇을 버렸는지"는 잃습니다 — 교정의 의미는 *델타*에
있으므로 before가 빠지면 증거가 반쪽이 됩니다. before는 흔히 후보의 `anti_examples`로, after는
`examples`로 승격 시 이어집니다. 빈 채로는 출력 금지(G1).

**[E] 라우팅.** 후보 신호를 [05 후보 추출](./05-candidate-extraction.md)로 넘깁니다. S05가
타입을 확정하면 그 `candidate_type`이 [1:1 전수 라우터](../spec/01-kernel-schema.md#6-후보-타입--라우팅-11-전수)에
따라 목적지 `user.*` 팩을 결정합니다. diff 마이너는 §3의 *제안 팩*을 힌트로 달 뿐, 팩을 직접
만들지 않습니다.

## 3. 교정 분류 (Classify the correction)

모든 교정 쌍은 다음 세 부류 중 하나(또는 한 쌍에서 분리된 여러 개)로 분류됩니다. 부류가 후보
타입 가설과 제안 팩을 가릅니다. 표의 매핑은 힌트이며 확정은 하류 단계(S05)입니다.

| 부류 | before→after에서 무엇이 바뀌었나 | 예시 | 후보 타입 가설 → 제안 팩 |
|------|----------------------------------|------|--------------------------|
| **스타일 (style)** | 같은 내용·같은 결정을 **표현·형식·톤·구조·밀도**만 바꿈 | "서론 빼고 결론부터", "존댓말로", "더 짧게", "불릿으로" | `CommunicationStyleCandidate` → `user.communication_style` (포맷이 출력물 *객체*면 `ArtifactPolicyCandidate` → `user.artifact_policy`) |
| **결정 (decision)** | **내용·선택·우선순위·트레이드오프**가 바뀜 (다른 결론) | "라이브러리 A 대신 B", "이 접근 말고 저 접근", "보안보다 속도 우선 말고 반대로" | `DecisionPolicyCandidate` → `user.decision_policy` (판단 휴리스틱이면 `TacitHeuristicCandidate` → `user.tacit_heuristics`) |
| **포맷 (format)** | 출력의 **형태·구조 객체**가 바뀜 (표↔불릿, 코드블록, 파일, 섹션 순서) | "표 대신 불릿", "코드는 별도 파일로", "TL;DR 블록 먼저" | `ArtifactPolicyCandidate` → `user.artifact_policy` (순수 텍스트 밀도면 스타일로 분류) |

분류 운영 규칙:

1. **스타일과 결정을 절대 같은 후보에 합치지 마라.** "B로 바꾸고(결정) 게다가 더 짧게(스타일)"는
   *두* 교정이 한 쌍에 들어온 것입니다. 후보를 둘로 쪼개 각각 다른 팩으로 보냅니다.
2. **포맷 vs 스타일 경계.** 출력물의 *형태 객체*(표·파일·리뷰보드)가 바뀌었으면 포맷
   →`user.artifact_policy`. 같은 텍스트의 *밀도·어순·톤*만 바뀌었으면 스타일
   →`user.communication_style`. 모호하면 둘 다 후보로 만들고 낮은 신뢰도로 게이트에 맡깁니다.
3. **경계/거부 신호 표시.** 교정이 "외부로 보내지 마", "이 표현은 빼"처럼 *경계*를 그으면
   `BoundaryRuleCandidate`(→`user.boundary_authority`) 가설을 달고 민감도를 표시합니다(G5).
   반복적으로 *같은 종류 출력을 거부*하면 `RedFlagCandidate`(→`user.red_flags`) 가설을 답니다.
4. **전이성 — 교정이 *당신의 패턴*인가 *이 프로젝트의 사실*인가([S02 §1.1](./02-session-mining.md#11-전이성-테스트--주체를-캐고-주제를-캐지-마라-mine-the-decider-not-the-topic)).**
   교정은 강한 신호지만 *전이 가능할 때만* 암묵지다. "라이브러리 A 대신 B"가 *이 프로젝트의 제약*
   (여기선 B만 호환)이면 프로젝트 사실 → 암묵지 후보 금지(필요하면 `memory_project_graph`). *프로젝트를
   바꿔도 참인 선호*("성숙도 높은 라이브러리를 선호")일 때만 `DecisionPolicyCandidate`. 프로젝트 디테일을
   벗기고 *패턴만* 후보로 만든다 — 이 게이트는 S05 체크리스트·S07 확인에서 다시 강제된다.

## 4. 신뢰도 산정 (Confidence)

각 후보 신호의 0..1 신뢰도는 [`candidate.schema.json`](../schemas/candidate.schema.json)의
`confidence_inputs`와 **동일 어휘**로 매기고, 그 근거를 투명하게 남깁니다(커널 §8). diff
마이닝에서는 `correction_strength`와 `evidence_quality`가 가장 큰 가중치를 가집니다 — 교정은
설계상 verbatim 델타라서 증거 직접성이 높기 때문입니다.

| 입력 | 의미 | diff 마이닝에서의 방향 |
|------|------|------------------------|
| `correction_strength` | 교정의 강도(0..1) — 얼마나 단호히 바꿨/뒤집었는가 | **최고 가중.** 전면 재작성·결정 번복은 ↑, 미세 손질은 ↓ |
| `evidence_quality` | 인용 증거의 직접성(0..1) | **높음.** before/after 둘 다 verbatim이면 ↑ |
| `repetition_count` | 후보를 떠받치는 서로 다른 `EvidenceItem` 수 | 단일 교정 쌍은 보통 낮음 → §5 단일-교정 규칙 적용 |
| `explicit_statement` | 사용자가 교정과 함께 *이유를 명시*했는가 | 명시 = true → ↑ ("결론부터 줘, 그게 읽기 편해") |
| `recency` | 교정의 최근성(1 = 가장 최근) | 최근 교정 ↑ (옛 패턴과 충돌하면 드리프트 후보) |
| `contradiction_count` | 후보와 충돌하는 `EvidenceItem` 수 | ↑ → 신뢰도 ↓. 교정이 기존 *확정* 레코드와 모순하면 하류 dedup judge가 `conflict`로 분류해 **사람에게 노출**(자동 적용 금지) — [10 dedup·병합](../spec/10-dedup-and-merge.md) |
| `domain_specificity` | 교정이 도메인에 얼마나 묶였는가(0..1) | 스코프 좁힘·`user.domain_overlays` 라우팅 판단에 사용 |

**가중 원칙 (운영 규칙):**

1. **교정은 가장 강한 증거다.** 사용자가 *직접 바로잡은* 델타는 세션 마이너의 추론이나 질문
   스킬의 자기보고보다 무겁습니다(`correction_strength`↑). 그것이 diff 마이닝이 트리오에서
   가장 신뢰도 높은 신호를 내는 이유입니다.
2. **단일 교정은 신뢰도를 낮게 잡되 버리지 않는다.** 한 번의 교정에서 *전역 규칙*을 단정하지
   않습니다 — 단일 교정 후보는 낮은 신뢰도로만 통과시키고, 반복(`repetition_count`↑)이나 명시
   확인을 기다립니다. 베이스 레코드 규칙상 `confidence < 0.7`이면 승격 시 `counterexamples`가
   필수이므로([record.base](../schemas/record.base.schema.json)), before(버려진 출력)가 자연스러운
   반례가 됩니다.
3. **델타의 의미는 양쪽에서 온다.** `evidence_quality`는 before와 after가 *둘 다* 인용됐을 때만
   높게 잡습니다. after만 있는 후보는 증거 반쪽으로 보고 신뢰도를 깎습니다.

## 5. 입력 / 출력 (Inputs / Outputs)

### 입력

- **주 입력:** before/after 교정 쌍 — [01 evidence_capture](./01-evidence-capture.md)가
  `source_type` `artifact`(before)와 `diff`/`correction`(after)으로 포착한 `EvidenceItem` 쌍.
  diff 마이너는 이미 포착된 쌍만 읽으며 새로 만들지 않습니다.
- **부 입력(선택):** 같은 종류의 과거 교정(반복 보강·드리프트 비교용), 이전 라운드의 확정
  레코드(중복·모순 점검용), 활성 팩 커버리지(어느 팩이 비었는지 힌트).

### 출력

각 후보 신호는 다음을 동반합니다(타입·필드 확정은 S05이지만, diff 마이너는 이 묶음을 넘깁니다):

- `concise_claim`(초안) — 관찰된 *변화*의 언어로 쓴 한 문장.
- `evidence_refs` — **before와 after를 둘 다** 가리키는 ≥1개(보통 2개) `EvidenceItem` 참조
  (게이트 G1, §2 [D]). 빈 채로 출력 금지.
- 교정 부류 라벨(§3: style / decision / format) + `proposed_target_pack` 가설.
- `confidence` + `confidence_inputs` — §4의 입력값(특히 `correction_strength`)을 채운 0..1 신뢰도.
- `scope`(초안 가설) + `sensitivity` 1차 분류(경계/민감 교정은 표시해 G5로 넘김).
- 승격 시 이어질 힌트: before → `anti_examples`, after → `examples`.
- `extraction_method = diff_mining`(프로비넌스, [candidate.schema.json](../schemas/candidate.schema.json)).

> 이 출력은 [S05 후보 추출](./05-candidate-extraction.md)의 입력 계약을 만족합니다. 거기서
> `candidate_type`이 확정되고 [1:1 전수 라우터](../spec/01-kernel-schema.md#6-후보-타입--라우팅-11-전수)가
> 목적지 팩을 결정합니다.

### 최소 예시 (후보 신호 — 타입 미확정, S05로 넘김)

```json
{
  "candidate_id": "logotekton.candidate.041",
  "concise_claim": "사용자가 3문단 배경 서론을 한 줄 결론으로 교체하고 근거를 뒤로 옮겼다(리뷰 보고서)",
  "evidence_refs": ["logotekton.evidence.088", "logotekton.evidence.089"],
  "correction_class": "style",
  "proposed_target_pack": "user.communication_style",
  "confidence": 0.55,
  "confidence_inputs": {
    "correction_strength": 0.8,
    "evidence_quality": 0.9,
    "repetition_count": 1,
    "explicit_statement": false,
    "recency": 1.0
  },
  "scope": "리뷰 보고서 초안 (가설 — S06이 확정)",
  "sensitivity": "internal",
  "extraction_method": "diff_mining"
}
```

`evidence.088`은 before(에이전트의 3문단 서론), `evidence.089`는 after(사용자의 한 줄 결론)
입니다 — 둘 다 묶여야 델타가 증거로 성립합니다. `repetition_count`가 1이라 신뢰도는 0.7 아래로
낮게 잡혔고, before는 승격 시 `anti_examples`, after는 `examples`가 됩니다.

## 6. 품질 검사 (Quality checks)

출력 전에 diff 마이너는 다음을 강제합니다. 코드 강제는
[`tools/validate_packs.py`](../tools/validate_packs.py)가 보조합니다.

- [ ] **양쪽 증거(G1)** — `evidence_refs`가 before와 after를 *둘 다* 가리키는가. after만 있으면
  델타가 반쪽이다 — 보강하거나 신뢰도를 깎는다.
- [ ] **단일 교정 과일반화 금지** — 한 번의 교정에서 *전역 규칙*을 단정하지 않았는가. 단일 교정
  후보는 **낮은 신뢰도**로만 통과하고, 넓은 일반화는 반복(`repetition_count`↑)이나 명시 확인을
  기다린다.
- [ ] **스타일 ≠ 결정 분리** — 한 쌍에 스타일 교정과 결정 교정이 섞여 있으면 *두 후보*로 쪼갰는가.
  한 후보에 합쳐 다른 팩을 오염시키지 않았는가(§3 규칙 1).
- [ ] **포맷 vs 스타일 판정** — 형태 객체 변경(→`user.artifact_policy`)과 텍스트 밀도 변경
  (→`user.communication_style`)을 올바로 가렸는가. 모호하면 양쪽 후보 + 낮은 신뢰도.
- [ ] **행동 언어만(G4)** — `concise_claim`이 *관찰된 변화*만 기술하고 추측 심리("싫어한다",
  "때문이다")를 단정하지 않는가.
- [ ] **민감/경계 표시(G5 예비)** — 경계를 긋거나 민감 정보를 건드린 교정에 `sensitivity`/
  `BoundaryRuleCandidate` 가설이 달려, [09 프라이버시 경계](./09-privacy-boundary.md)가 승격 전
  `BoundaryRule`을 붙일 수 있는가.
- [ ] **반례 준비** — `confidence < 0.7`이면 before(버려진 출력)가 승격 시 `counterexamples`/
  `anti_examples`로 이어질 수 있게 보존됐는가([record.base](../schemas/record.base.schema.json)).
- [ ] **경계 준수** — 타입 확정(S05)·스코프 확정(S06)·확인(S07)을 침범하지 않았는가. 미확인
  신호를 런타임으로 올리지 않았는가(G3).

## 7. Crab 역할 — Diff Miner Crab

이 스킬의 소유 역할은 **Diff Miner Crab**입니다([12 crab 오케스트레이션](./12-crab-orchestration.md),
[커널 §8](../spec/01-kernel-schema.md#8-crab-에이전트-역할-운영-모델)).

- **소유 작업:** `mine_or_ask` 상태에서 before/after 교정 쌍의 수집·분류·후보 생성·양쪽 증거
  부착·신뢰도 산정. 트리오 중 *교정 쌍 한 건을 깊게 읽는* 역할.
- **받는 핸드오프:** **Evidence Crab**(S01)이 만든 교정/diff `EvidenceItem` 쌍. Orchestrator가
  신호 성격이 *교정 중심*이면 세션 마이너 대신 diff 마이너로 라우팅합니다.
- **넘기는 핸드오프:** 후보 신호 → **Candidate Extractor**(S05). 교정에 *이유*가 빠져 모호하면
  **Orchestrator**가 **Questioning**(S03)에 후속 질문을 요청할 수 있습니다.
- **경계:** 타입 확정(S05)·스코프 확정(S06)·확인(S07)·라우팅(S08)을 침범하지 않습니다.
  before를 버리지 않으며(델타 보존), 미확인 신호를 런타임으로 올리지 않습니다(G3).

OpenCrab 도구로 실행할 때는 `opencrab_search_documents`/`opencrab_query`로 before/after 증거
쌍을 조회하고, 후보 신호를 `opencrab_ingest_text`로 후보 단계 노드에 적재한 뒤 S05로
핸드오프합니다. 권한·민감도 판단은 [04 프라이버시·경계](../spec/04-privacy-boundary.md)의 권한
레벨을 따릅니다.

> 9-space 사상: 교정 쌍의 **before/after 출처**는 `resource`, **발췌된 델타**는 `evidence`,
> 거기서 나온 후보 주장은 `claim`으로 사상됩니다([07 9-space 크로스워크](../spec/07-opencrab-9space-crosswalk.md)).

## 8. 관련 문서

- 라이프사이클·노드·엣지·게이트·후보 라우팅 → [01 커널 스키마](../spec/01-kernel-schema.md)
- 이 스킬이 속한 12단계 파이프라인 계약 → [02 빌더 파이프라인](../spec/02-builder-pipeline.md)
- 채굴 트리오의 다른 두 스킬 → [02 세션 마이닝](./02-session-mining.md) · [03 질문](./03-elicitation-questioning.md)
- before/after를 `EvidenceItem`으로 포착하는 단계 → [01 증거 포착](./01-evidence-capture.md)
- 후보 신호를 타입 지정 `CandidateAssertion`으로 → [05 후보 추출](./05-candidate-extraction.md)
- 후보 신호/신뢰도 입력의 기계 스키마 → [`candidate.schema.json`](../schemas/candidate.schema.json) ·
  [`record.base.schema.json`](../schemas/record.base.schema.json)
- 스코프 확정·확인 게이트 → [06 스코프](./06-scope-context.md) · [07 확인 게이트](./07-confirmation-gate.md)
- 라우팅 도착지인 14개 팩 → [03 팩 카탈로그](../spec/03-pack-catalog.md)
- 민감·경계 교정이 받는 경계 규칙 → [04 프라이버시·경계](../spec/04-privacy-boundary.md) ·
  [09 privacy_boundary](./09-privacy-boundary.md)
- 역할·상태·핸드오프 운영 모델 → [12 crab 오케스트레이션](./12-crab-orchestration.md)


## 트리거 (Trigger)

> 이 스킬의 발화 조건. 전체 2계층 모델·호스트(훅) 매핑·게이트 보존은
> [../spec/09-triggers.md](../spec/09-triggers.md), 머신 스키마는
> [../schemas/trigger.schema.json](../schemas/trigger.schema.json) 참고.

```yaml
trigger:
  trigger_id: pab.diff_mining.on_correction
  skill: diff_mining
  signal: user_correction
  condition: "agent output is edited, rejected, or followed by 'do X instead'"
  cadence: event
  host_hook: UserPromptSubmit · PostToolUse
  produces: candidate_staged
  requires_confirmation: false     # 스테이징만 (라이브 규칙 아님)
  default_state: enabled
  debounce: per_correction
```

★플래그십 — 교정은 선호 경계가 드러나는 가장 강한 신호라 1순위 트리거입니다.
