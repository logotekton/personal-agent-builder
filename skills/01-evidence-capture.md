# 01 · 증거 포착 (Evidence Capture)

> **EN:** Operating instructions for `skill.pab.evidence_capture` — pipeline step **S01**,
> workflow state `collect_evidence`, owned by the **Evidence Crab**. This skill turns a raw
> signal (a session log, a correction, a file, an interview answer) into a normalized
> `EvidenceItem` — the **source of truth** every later record points back to. It does not
> mine, interpret, type, or summarize: it preserves the source faithfully, keeps raw bytes
> separate from interpretation, marks sensitivity, and guarantees the `evidence_refs` target
> that Gate **G1** ("no evidence-free claim") will later demand.

이 문서는 빌더 파이프라인 1단계 [`S01 evidence_capture`](../spec/02-builder-pipeline.md#s01--evidence_capture--상태-collect_evidence)의
**실행 지침**입니다. 마케팅 문서가 아니라, 그대로 따라 돌릴 수 있는 운영 절차로 읽으세요.
어휘는 [01 커널 스키마](../spec/01-kernel-schema.md), 필드 규약은
[통합 베이스 레코드](../schemas/record.base.schema.json), 팩 정의는
[03 팩 카탈로그](../spec/03-pack-catalog.md)를 따릅니다.

---

## 1. 목적 (Purpose)

증거 포착은 파이프라인의 **첫 단계이자 진실의 출처**를 만드는 단계입니다. 이후 모든 단계
(채굴 → 추출 → 스코프 → 확인 → 라우팅 → 컴파일 → 평가)는 여기서 만든 `EvidenceItem`을
가리키며 동작합니다. 따라서 이 단계의 단 하나의 책임은 **원시 신호를 손실 없이, 검증 가능하게,
나중에 다시 찾아갈 수 있게 보존하는 것**입니다.

세 가지 불변식 (반드시 지킴):

1. **후보를 만들지 않는다.** 이 단계는 `CandidateAssertion`을 생산하지 않습니다. 오직
   `EvidenceItem`만 포착·정규화합니다. 타입 지정·해석은 [S05 candidate_extraction](../skills/05-candidate-extraction.md)의 일입니다.
2. **원본을 보존한다.** 발췌(`excerpt`)는 출처의 *원문 그대로*입니다. 다듬거나 요약하거나
   "정리"하지 않습니다 (§4 포착 규칙).
3. **모든 후보는 ≥1개의 증거를 가리킨다.** 이 단계가 만드는 `EvidenceItem`이 곧 게이트 **G1**
   (증거 없는 주장 금지)의 *대상*입니다. 가리킬 증거가 없으면 후보도 없습니다.

> 한 줄 계약: **원시 신호 → `EvidenceItem`.** 입력은 가공되지 않은 신호, 출력은 출처·발췌·
> 타임스탬프·원본 링크가 채워진 증거 노드 하나입니다.

## 2. 작동 방식 (How it works)

```
  입력 소스                         정규화                       출력
  ─────────                         ───────                      ────
  AI 세션 로그 ─┐
  사용자 답변   │   (a) 식별: 이 신호의 출처 종류는?              ┌──────────────┐
  교정/diff     ├─► (b) 발췌: 관련 원문을 그대로 잘라낸다  ──────►│ EvidenceItem │
  파일/산출물   │   (c) 고정: 타임스탬프·원본 참조·해시          │ (진실의 출처) │
  메시지/노트   │   (d) 표시: privacy_level / extraction_status  └──────┬───────┘
  로그/이벤트  ─┘   (e) 연결: related_task / related_project            │
                                                                        ▼
                                                          S02/03/04 채굴 트리오가 소비
```

흐름은 다섯 동작 — **식별 → 발췌 → 고정 → 표시 → 연결** — 으로 끝납니다. 어느 동작에서도
신호의 *의미를 해석*하지 않습니다. "이 발췌가 무엇을 뜻하는가"는 다음 단계의 질문입니다.
이 단계의 질문은 오직 "이 신호를 나중에 그대로 다시 보려면 무엇을 기록해야 하는가"입니다.

파이프라인 위치: 워크플로 상태 `collect_evidence` → 다음 상태 `mine_or_ask`
([S02 session_mining](../skills/02-session-mining.md) ·
[S03 elicitation_questioning](../skills/03-elicitation-questioning.md) ·
[S04 diff_mining](../skills/04-diff-mining.md))가 이 `EvidenceItem`들을 입력으로 받습니다.

## 3. 입력 / 출력 (Inputs / Outputs)

### 3.1 입력 소스 (Input sources)

| 소스 종류 (`source_type`) | 설명 | 가장 흔한 다음 단계 |
|---------------------------|------|---------------------|
| `session_log` | AI 에이전트와의 세션 전사·턴 로그 | S02 세션 마이닝 |
| `user_answer` | 인터뷰·질문에 대한 사용자의 직접 답변 | S03 질문 |
| `correction` | "아니 그거 말고", 재지시, 피드백 한 줄 | S04 diff 마이닝 |
| `diff` | before/after 산출물 쌍, 편집 차이 | S04 diff 마이닝 (가장 강한 경계 신호) |
| `file` | 사용자가 제공·승인한 문서·코드·자료 | S02 세션 마이닝 |
| `artifact` | 에이전트가 만들고 사용자가 채택/거부한 산출물 | S02 / S04 |
| `message` | 채팅·이메일·이슈 등 메시지 단편 | S02 |
| `note` | 사용자가 남긴 메모·주석 | S02 / S03 |
| `event_log` | 도구 호출·시스템 이벤트 로그 | S02 |

> 한 입력 신호는 **여러 `EvidenceItem`으로 쪼갤 수 있습니다.** 한 세션 안에 서로 다른 주제의
> 교정이 셋 있으면, 발췌가 셋이고 따라서 `EvidenceItem`도 셋입니다. 한 증거 = 한 응집된 발췌.

### 3.2 출력: `EvidenceItem` 필드

`EvidenceItem`은 노드 타입입니다([커널 §3](../spec/01-kernel-schema.md#3-노드-타입-node-types)).
이후 레코드가 `evidence_refs[]`로 가리키는 대상이며, 그 자체는 통합 베이스 레코드가 아니라
*출처 노드*입니다. 필수/선택 필드:

| 필드 | 필수 | 의미 |
|------|:----:|------|
| `id` | ✓ | 안정 증거 id. 형식 `<subject>.evidence.NNN` (예: `logotekton.evidence.001`). 이 값이 후보의 `evidence_refs`에 들어간다. |
| `source_type` | ✓ | §3.1 열거값 중 하나 (`session_log` … `event_log`). |
| `source_title` | ✓ | 사람이 알아볼 짧은 출처 이름 (예: `"2026-06-21 리뷰 세션 — 보고서 톤 교정"`). |
| `source_timestamp` | ✓ | 신호가 발생한 시각, RFC 3339 (`2026-06-21T14:03:00+09:00`). 포착 시각이 아니라 **원본 발생 시각**. |
| `source_ref` | ✓ | 원본으로 되돌아가는 참조 — URL, 파일 경로, 세션 id, 메시지 id 등. 검증·재방문의 핵심. |
| `excerpt` | ✓ | **원문 그대로의** 관련 발췌. 요약·의역 금지(§4). 길면 잘라내되 잘랐음을 표시(`… [중략] …`). |
| `privacy_level` | ✓ | 민감도. 정식 `sensitivity` enum과 동일한 값: `public` \| `internal` \| `sensitive` \| `restricted`. |
| `extraction_status` | ✓ | 후속 채굴 진행 상태: `captured` \| `mined` \| `extracted` \| `archived`. 처음 포착 시 `captured`. |
| `related_task` | – | 이 신호가 발생한 작업 식별자 (있으면). |
| `related_project` | – | [`user.memory_project_graph`](../schemas/user.memory_project_graph.schema.json)의 프로젝트 링크 (있으면). |
| `hash_or_version` | – | 발췌/원본의 무결성 지문 — 내용 해시 또는 원본 버전·리비전. 변조·재현 검증용. |

추가 규약:

- `privacy_level`은 베이스 레코드의 `sensitivity`와 **같은 어휘**를 씁니다. 그래야 이 증거에서
  추출된 후보의 `sensitivity`가 증거의 민감도를 *낮추지 않도록* 검증할 수 있습니다.
- `extraction_status`는 증거의 *수명주기*이지 후보의 `review_status`가 아닙니다. 둘을 섞지
  마세요 — 후보의 confirm/reject는 [S07 confirmation_gate](../skills/07-confirmation-gate.md)의 영역입니다.

### 3.3 최소 예시

```json
{
  "id": "logotekton.evidence.017",
  "source_type": "correction",
  "source_title": "리뷰 세션 — '결론부터' 교정",
  "source_timestamp": "2026-06-21T14:03:00+09:00",
  "source_ref": "session://2026-06-21-review#turn-42",
  "excerpt": "사용자: \"아니, 배경부터 깔지 말고 결론부터 한 줄로 줘. 근거는 그 다음.\"",
  "privacy_level": "internal",
  "extraction_status": "captured",
  "related_task": "weekly-report-draft",
  "related_project": "logotekton.project.003",
  "hash_or_version": "sha256:9f2a…c1"
}
```

이 `excerpt`는 *날것*입니다. "사용자는 결론 우선 구조를 선호한다"는 **해석**이며, 그것은
여기 들어가지 않습니다 — 그건 [S05](../skills/05-candidate-extraction.md)가 만들
`CommunicationStyleCandidate`의 `statement`이고, 이 증거 id를 `evidence_refs`로 가리킵니다.

## 4. 포착 규칙 (Capture rules)

증거 포착의 품질이 파이프라인 전체의 신뢰를 좌우합니다. 다음 다섯 규칙은 강제입니다.

1. **원본을 보존하라 (Preserve the source).** `excerpt`는 출처의 원문입니다. 오탈자·말투·
   비문도 그대로 둡니다. 잘라낼 때만 명시적으로 `… [중략] …` 표시. `source_ref`와
   `hash_or_version`으로 원본 재방문·무결성 검증이 가능해야 합니다.
2. **요약으로 지워버리지 마라 (Do not summarize away).** "사용자가 톤을 고쳤다" 같은 압축은
   증거가 아니라 *해석*입니다. 어떤 단어로 고쳤는지, 어떤 문장을 버렸는지 — 그 *질감*이
   증거의 가치입니다. 압축은 후보의 `concise_claim`에서 일어나지 여기서 일어나지 않습니다.
3. **날것과 해석을 분리하라 (Separate raw from interpretation).** `excerpt`(날것)와
   `source_title`(분류용 라벨)을 섞지 마세요. 라벨은 검색을 돕는 *메타*일 뿐, 의미 판단을
   담지 않습니다. 의미 판단(이게 무슨 규칙인지)은 절대 증거 노드에 넣지 않습니다 — 게이트
   **G4**(행동 언어만)의 출발점이 여기입니다.
4. **민감 항목을 표시하라 (Mark sensitive).** 개인정보·자격증명·건강·재무·신원·계약 등이
   발췌에 닿으면 `privacy_level`을 `sensitive` 또는 `restricted`로 올립니다. 이 표시는 게이트
   **G5**(승격 전 프라이버시)로 흘러가, [S09 privacy_boundary](../skills/09-privacy-boundary.md)가
   `BoundaryRule`을 *먼저* 부착하도록 만듭니다. 의심스러우면 더 높은 등급으로 올리세요.
5. **모든 후보는 ≥1개 증거를 가리킨다 (Every candidate references ≥1 evidence).** 이 단계는
   그 *가리킬 대상*을 만드는 단계입니다. 안정 `id`를 부여하고, 같은 신호를 두 번 포착하지 않게
   `hash_or_version`/`source_ref`로 중복을 거릅니다. 가리킬 수 없는 증거(불안정 id, 사라질
   링크)는 G1을 무력화하므로 금지입니다.

## 5. 품질 검사 (Quality checks)

포착을 마치기 전 다음을 통과해야 합니다. 코드 강제는
[`tools/validate_packs.py`](../tools/validate_packs.py)가 보조합니다.

- [ ] **필수 필드 완비** — `id`, `source_type`, `source_title`, `source_timestamp`,
  `source_ref`, `excerpt`, `privacy_level`, `extraction_status`가 모두 채워졌는가.
- [ ] **원문 보존** — `excerpt`가 요약·의역이 아니라 원문인가. 잘랐다면 표시했는가.
- [ ] **재방문 가능** — `source_ref`만으로 원본을 다시 찾아갈 수 있는가. `hash_or_version`으로
  무결성을 확인할 수 있는가.
- [ ] **시각 정확** — `source_timestamp`가 포착 시각이 아니라 **원본 발생 시각**인가 (RFC 3339).
- [ ] **해석 부재** — 발췌·라벨에 "선호한다/싫어한다/때문이다" 같은 *판단*이 섞이지 않았는가
  (G4 출발점). 판단은 후보로 미룬다.
- [ ] **민감도 표시** — 개인·재무·건강·신원·자격증명이 닿으면 `privacy_level`이 `sensitive`/
  `restricted`로 표시됐는가 (G5 예비).
- [ ] **참조 가능성(G1 예비)** — `id`가 안정적이고 후보의 `evidence_refs`에서 가리킬 수 있는가.
  중복 포착이 아닌가.
- [ ] **경계 준수** — 후보를 만들지 않았는가. `EvidenceItem`만 출력했는가 (단계 불변식).

## 6. Crab 역할 — Evidence Crab

이 스킬의 소유 역할은 **Evidence Crab**입니다([12 crab 오케스트레이션](../skills/12-crab-orchestration.md)).

- **소유 작업:** 워크플로 상태 `collect_evidence`. 입력 신호를 받아 `EvidenceItem`만 생산.
- **핸드오프 (받음):** [Orchestrator Crab](../skills/12-crab-orchestration.md)가 새 원시 신호를
  넘겨줄 때 기동합니다.
- **핸드오프 (넘김):** 정규화된 `EvidenceItem`을 채굴 트리오 —
  [Session Miner](../skills/02-session-mining.md) · [Questioning](../skills/03-elicitation-questioning.md) ·
  [Diff Miner](../skills/04-diff-mining.md) — 에게 넘깁니다. Orchestrator가 신호 성격에 따라
  경로를 고릅니다.
- **하지 않는 것:** 타입 지정·스코프·확인·라우팅은 이 역할의 일이 아닙니다. Evidence Crab은
  *의미를 만들지 않고 증거를 보존*합니다. 그 절제가 게이트 G1·G4·G5의 토대를 놓습니다.

> 9-space 사상: `EvidenceItem`의 **출처**(세션·파일·diff)는 `resource`, **발췌**는 `evidence`로
> 사상됩니다([07 9-space 크로스워크](../spec/07-opencrab-9space-crosswalk.md)).

## 7. 관련 문서

- 이 단계의 파이프라인 계약 → [02 빌더 파이프라인 · S01](../spec/02-builder-pipeline.md#s01--evidence_capture--상태-collect_evidence)
- 노드/엣지/게이트/라이프사이클 어휘 → [01 커널 스키마](../spec/01-kernel-schema.md)
- 증거를 가리키는 후보의 필드 → [05 candidate_extraction](../skills/05-candidate-extraction.md) ·
  [`candidate.schema.json`](../schemas/candidate.schema.json)
- 베이스 레코드의 `sensitivity`/`evidence_refs` 규약 → [`record.base.schema.json`](../schemas/record.base.schema.json)
- 민감 항목이 받는 경계 규칙 → [04 프라이버시·경계](../spec/04-privacy-boundary.md) ·
  [09 privacy_boundary](../skills/09-privacy-boundary.md)
- 역할·핸드오프 운영 모델 → [12 crab 오케스트레이션](../skills/12-crab-orchestration.md)


## 트리거 (Trigger)

> 이 스킬의 발화 조건. 전체 2계층 모델·호스트(훅) 매핑·게이트 보존은
> [../spec/09-triggers.md](../spec/09-triggers.md), 머신 스키마는
> [../schemas/trigger.schema.json](../schemas/trigger.schema.json) 참고.

```yaml
trigger:
  trigger_id: pab.evidence_capture.on_turn
  skill: evidence_capture
  signal: turn
  condition: "every user turn and tool result is a potential EvidenceItem"
  cadence: continuous
  host_hook: UserPromptSubmit · PostToolUse
  produces: evidence_staged
  requires_confirmation: false     # 스테이징만 (라이브 규칙 아님)
  default_state: enabled
  debounce: per_turn
```

매 턴·도구결과를 증거로 적재합니다 — 스테이징만 하므로 라이브 규칙이 되지 않습니다(G1).
