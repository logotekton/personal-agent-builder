# 15 · 암묵지 채굴 (Tacit Knowledge Mining)

> **EN:** Operating instructions for `skill.pab.tacit_knowledge_mining` — the deep-mining
> skill that turns a session into the subject's **tacit decision model**, not a summary of
> the work performed. Where the mining trio (02/03/04) sweeps sessions for repetitions,
> gaps, and corrections, this skill reads the same evidence at a different altitude: it asks
> *why the subject decided as they did*, what they were **protecting**, what they rejected
> and what that rejection **contrasts** with. Its founding failure case is real: a builder
> that was asked for a personal-agent pack and returned a *task-summary pack* — topics,
> workflows, artifact lists — instead of the decider behind them. The skill exists so that
> failure mode is structurally impossible: task-summary statements are filtered (or demoted
> to `user.memory_project_graph`), every candidate carries the *verbatim user signal* it was
> mined from, and the first user-visible output is a **review board**, never a finished pack
> (Gate G3). Mirrored from the OpenCrab builder pack `skill.pab.tacit_knowledge_mining.v0.2`.

암묵지 채굴은 채굴 트리오([02 세션마이닝](./02-session-mining.md) ·
[03 질문](./03-elicitation-questioning.md) · [04 diff마이닝](./04-diff-mining.md))가 이미 포착한
증거를 **다른 고도에서 다시 읽는** 스킬입니다. 트리오가 "무엇이 반복되는가"를 찾는다면, 이 스킬은
**"왜 그렇게 결정했는가 — 주제(topic layer)가 아니라 결정자(decider layer)"**를 캡니다.
어휘는 [커널 스키마](../spec/01-kernel-schema.md), 후보 계약은
[`candidate.schema.json`](../schemas/candidate.schema.json), 전이성 테스트는
[02 §1.1](./02-session-mining.md)을 따르며 새 이름을 만들지 않습니다.

---

## 1. 목적 (Purpose)

사용자가 "이 세션 기반으로 personal agent 팩 만들어줘"라고 할 때, 채굴 대상은 **세션에서 한 일**이
아니라 **세션이 드러낸 그 사람**입니다: 결정, 교정, 거절 기준, 보호하려는 결과(protected outcome),
우선순위 트레이드오프, 증거에 대한 기대, 에이전트 행동 규칙.

- **하는 일:** 세션을 에피소드로 분해하고, 결정·교정 신호를 골라, "이게 왜 요약이 아니라
  암묵지인가"를 검증한 뒤, 대조 프레이밍을 갖춘 후보로 만들어 검토 보드에 올린다.
- **하지 않는 일:** (1) 작업 요약 팩·체인지로그 팩을 만들지 않는다. (2) 확정 팩을 직접 만들지
  않는다 — 산출물은 언제나 *검토 보드*다(G3). (3) 심리를 추측하지 않는다 — 관찰된 결정·교정만
  기술한다(G4). (4) 개인 인스턴스 데이터를 빌더 프로젝트에 넣지 않는다(G6, 3-project 토폴로지).

> 한 줄 계약: **한 세션 → 결정자(decider)의 암묵지 후보 보드.** 모든 후보는 그것을 드러낸
> *사용자 발화 원문*(`signal_text`)과 에피소드(`episode_id`)에 묶입니다.

## 2. 작동 방식 (How it works)

```
   세션 트랜스크립트 (외부 증거; 01–04가 포착한 EvidenceItem 포함)
        │
   [A] 에피소드 분해(decompose)   ── 세션을 결정 지점 단위의 에피소드로 나눔 (episode_id)
        ▼
   [B] 신호 선별(select)          ── 결정·교정·거절·반복 선호만 남김; 작업 서술은 버리거나
        │                            user.memory_project_graph 후보로 강등
        ▼
   [C] 암묵지 검증(why-tacit)     ── "프로젝트를 바꿔도 참인가?"(전이성, 02 §1.1) +
        │                            "요약이 아니라 판단 기준인가?" 둘 다 통과해야 함
        ▼
   [D] 대조 프레이밍(contrast)    ── 무엇 대신(X) 무엇을(O) 택했는가를 명시
        ▼
   [E] 후보 생성(mint)            ── 정식 14 후보 타입의 CandidateAssertion으로;
        │                            episode_id + signal_text + protected_outcome 부착
        ▼
   [F] 검토 보드(board)           ── 4컬럼 보드로 사람 검토 요청 (§4) → S07 확인 게이트
```

**[B]가 이 스킬의 심장입니다.** 신호가 되는 것: 사용자의 결정("A 말고 B로"), 교정("그게 아니라"),
거절(제안 dismiss), 명시적 금지선, 반복된 선호, 신뢰가 오르내린 순간. 신호가 아닌 것: 만든 파일
목록, 수행한 단계, 프로젝트 사실. 후자가 살아남으면 그건 이 스킬의 실패입니다 — 프로젝트 사실은
`ProjectMemoryCandidate`(→ `user.memory_project_graph`)로만 통과할 수 있습니다.

## 3. 채굴 렌즈 (Mining lenses — 분석 어휘, 새 레코드 타입 아님)

다음 여섯 렌즈로 에피소드를 읽습니다. 이것은 **분석 어휘**이며, 산출물은 언제나 정식 14 후보
타입입니다(스키마의 1:1 라우터 유지 — 새 레코드 타입을 만들지 않습니다):

| 렌즈 | 묻는 것 | 주 라우팅 (후보 타입) |
|------|---------|----------------------|
| TacitPrinciple | 결정들을 관통하는, 이름 붙인 적 없는 원리는? | PersonaTrait / TacitHeuristic |
| UserDecision | 실제로 무엇을 택하고 무엇을 물렸나? | (증거 앵커 — 모든 후보의 `signal_text`) |
| AntiPattern | 무엇을 일관되게 거부하나? | RedFlag |
| TrustCue | 무엇이 신뢰를 올리고 내리나? | CommunicationStyle / RedFlag |
| PreferredBehavior | 에이전트가 어떻게 행동하길 바라나? | DecisionPolicy / WorkflowPattern |
| FutureActionRule | 다음 에이전트가 되묻지 않아도 되게 하는 규칙은? | DecisionPolicy / BoundaryRule |

## 4. 첫 화면 계약 (First-screen review-board contract)

이 스킬이 발화되면 **첫 사용자 노출 출력은 반드시 후보 검토 보드**입니다 — 연대기 요약, 산문
분석, 팩 내용 목록으로 시작하면 계약 위반입니다.

1. 상태줄: `암묵지 후보 보드입니다. 아직 확정된 기억이 아니라 검토 대상입니다.`
2. **4컬럼 표**: `ID | 암묵지 후보 | 근거 신호 | 보호하려는 결과`
   - `근거 신호` = `signal_text`(사용자 발화 원문/에피소드 참조), `보호하려는 결과` = `protected_outcome`.
   - `라우팅 템플릿`·`검토 상태`·`확인 질문`은 필요하지만 **표 컬럼이 아니라** 표 뒤의
     `운영 메타` 절 또는 ingest 판정 블록에 둡니다.
3. (선택) 명시적 결정 vs 추론된 암묵 기준의 구분 노트.
4. 행동 요청 한 번: `확정할 ID, 수정할 ID, 제외할 ID를 말해줘.`
5. ingest 판정 블록([16 ingest 판정 게이트](./16-ingest-decision-gate.md)) — 보류 후보만 있으면
   `WAITING_FOR_CONFIRMATION`.

## 5. 품질 게이트 (Run-level quality gates)

한 런이 통과하려면 전부 성립해야 합니다:

- 모든 후보에 `evidence_refs`(G1) **그리고** `episode_id`·`signal_text`가 있다
  (스키마상 선택 필드지만 *이 스킬의 런*에서는 필수 — 신호 원문 없는 암묵지 주장은 이 스킬의
  산출물이 될 수 없다).
- 작업-요약 서술이 걸러졌거나 `user.memory_project_graph`로 강등됐다.
- 개인 데이터가 빌더 프로젝트에 들어가지 않았고, 세션 증거·pending 후보는 `personal agent evidence`,
  승인된 기억은 `personal agent`로 분리됐다(3-project 토폴로지).
- pending 후보가 승격되지 않았다(G3).
- 런이 ingest 판정(YES/NO/WAITING_FOR_CONFIRMATION)으로 끝났다(스킬 16).

**나쁜 출력 패턴(즉시 실패):** "이번 세션에서 한 일을 요약했습니다" / 빌더 프로젝트 안에 개인
팩 생성 / 증거 없이 심리 추론 / 검토 보드 생략 후 후보를 confirmed로 표기.

## 트리거 (Trigger)

> 이 스킬의 발화 조건. 전체 2계층 모델·호스트(훅) 매핑·게이트 보존은
> [../spec/09-triggers.md](../spec/09-triggers.md), 머신 스키마는
> [../schemas/trigger.schema.json](../schemas/trigger.schema.json) 참고.

```yaml
trigger:
  trigger_id: pab.tacit_knowledge_mining.on_request
  skill: tacit_knowledge_mining
  signal: command
  condition: "user asks to build personal-agent memory from a session (e.g. '이 세션 기반으로 personal agent 팩 만들어줘', '내 암묵지를 뽑아줘', '내가 내린 결정과 나도 모르는 암묵지를 추출해줘')"
  cadence: command
  host_hook: [UserPromptSubmit, command]
  produces: candidate_staged
  requires_confirmation: false     # 스테이징 + 검토 보드만 (라이브 규칙 아님, G3)
  default_state: enabled
  debounce: per_session
```

명시적 요청에만 발화합니다. 산출물은 검토 보드에 오른 pending 후보이며, 확정·라우팅은 S07/S08,
ingest 가부는 [16](./16-ingest-decision-gate.md)이 판정합니다.
