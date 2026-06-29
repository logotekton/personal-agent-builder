# 00 · 개요 (System Overview)

> **EN:** Personal Agent Builder converts a person's persona and tacit knowledge into
> evidence-bound ontology packs and compiles them into a controlled assistant — the
> Personal Agent. Four pack classes (skill / template / instance / adapter), a 12-step
> evidence-bound pipeline, 14 user ontology packs, a privacy/authority model, an
> evaluation+drift loop, and a measurable convergence model. Read order below.

## 핵심 명제 — de-averaging (왜 만드는가)

> **일차 목적은 *자기명시화*다 — "나도 모르는 나"를 증거에 묶어 *읽을 수 있는 명시적 지도*로 만드는
> 것.** 개인이 *어떻게* 결정·판단·작업하는지의 암묵 패턴은 대개 말로 못 꺼낸 채 행동에만 남는다. 이
> 시스템의 첫 산출물은 그 패턴을 명시화한 **자기지도(self-map)**다. 그 지도는 *행동하는* 개인 에이전트로
> **컴파일될 수 있지만**, 거울(자기명시화)이 먼저고 대리인 배포는 사람 검토를 요하는 별개 단계다
> ([README — 거울이냐 대리인이냐](../README.md#거울이냐-대리인이냐--자기명시화가-먼저다)).

> 그래서 목표는 *일반적으로 똑똑한* 에이전트가 아니라 **당신으로 수렴하는** 지도입니다. 그 핵심은
> **de-averaging**입니다: 지도는 **당신의 증거가 있는 곳에서만 당신을** 그리고, 증거가 없는 곳에서는
> 일반·평균값으로 둘러대지 않고 **비워 두거나 묻습니다.** 빈 영역을 인구 평균으로 채우는 순간, 그건
> *당신*이 아니라 *이름만 당신인 일반 모델*이 됩니다.

그래서 이 시스템은 (a) 모든 활성 규칙을 **증거에 결속**하고(G1·`traceability`=1.0), (b) 성숙도를
폭만이 아니라 **깊이**로 재며(한 영역을 먼저 깊게 — overfit-tiny-set-first), (c) 데이터가 없는
영역을 **off-frontier(draft-only)** 로 표시해 *모르는 곳을 아는 것*을 측정합니다. 측정·강제는
[06 수렴 모델 §8](./06-convergence-model.md#8-깊이de-averaging--모르는-곳을-아는-것이-수렴이다),
부정 증거(무엇이 *당신이 아닌가*)는 [`user.red_flags`](./03-pack-catalog.md)가 담습니다.

> **주체를 캐고, 주제를 캐지 마라.** 에이전트가 *당신*이 되는 것은 당신의 *프로젝트 데이터베이스*가
> 아니라 당신의 *판단 방식*을 증류했을 때뿐입니다. 그래서 추출의 제1 필터는 **전이성 테스트**입니다 —
> "프로젝트를 바꿔도 참인" 결정·추론·선호·휴리스틱만 암묵지 팩으로 가고, 프로젝트 고유 사실은
> `memory_project_graph`(맥락)로만 갑니다([S02 §1.1](../skills/02-session-mining.md#11-전이성-테스트--주체를-캐고-주제를-캐지-마라-mine-the-decider-not-the-topic)).
> 이것이 de-averaging 의 *입구* 형태입니다: 들어올 때부터 *당신이 무엇을 만드는가*가 아니라 *당신이
> 어떻게 생각하는가*만 들인다.

## 무엇이 *아닌가* — 위임가능한 '일하는 자아' (scope & stance)

> **EN:** What PAB builds is a *delegable working-self* — an agent that reproduces your
> judgment in the work/decision domains where it has your **behavioral evidence** — **not a
> whole-person digital twin.** This bound is a deliberate design choice and a stated stance,
> written here so the system is never read as claiming more than its evidence can earn.

PAB가 만드는 것은 **위임 가능한 '일하는 자아'**입니다 — 당신의 *행동 증거가 있는* 일·판단
영역에서 당신의 판단을 재현하는 에이전트. **전인격 디지털 트윈이 아닙니다.** 세 가지를 명시합니다.

1. **방법론적 입장 — 행동에서 만든다 (declared behavioral stance).** 에이전트는 *관찰된 행동·산출물·
   교정*에서 만들어집니다(게이트 G4). 내면·동기·정서는 *증거 계층에서 의도적으로 제외*됩니다 —
   추측한 심리를 규칙으로 굳히지 않기 위해서입니다. 이것은 "사람에게 내면이 없다"는 주장이 아니라,
   *내면은 행동 증거가 아니므로 증거 계층에 넣지 않는다*는 **선언된 방법론적 입장**입니다. 자기서술
   (self-report)이 필요하면 `reliability: self_reported` 저신뢰 채널로 *운반만* 하고(draft-only,
   auto-confirm 금지, 깊이 미산입 — [01 §7.1](./01-kernel-schema.md), 설계자 결정 C), 행동 증거로
   둔갑시키지 않습니다.

2. **채널 한계 — 증거는 주로 작업 세션에서 온다 (channel limit).** 현재 증거 채널은 대체로 *AI와의
   작업 세션*입니다. 그래서 추출이 잘 닿는 곳은 **일하는 자아**(판단·커뮤니케이션·워크플로·도구·경계)
   이고, *관계·정서·미적·서사적 자아*는 이 채널로 잘 닿지 않습니다. 이는 팩이 부족해서가 아니라
   **채널의 구조적 한계**입니다.

3. **off-ontology 기권 (honest abstention).** 닿지 않는 자아 영역은 *off-ontology*로 둡니다 —
   에이전트는 그곳에서 평균/일반값으로 당신을 흉내내지 않고 **기권하거나 묻습니다.** 이는 위 핵심
   명제의 de-averaging 을 *채널 차원*으로 확장한 것입니다: 빈 슬라이스를 채우지 않는 것이 정직이고,
   그래서 '일하는 자아'는 *과대주장 없이* 유효합니다. 채널 확대(오프라인·다중소스 적재)는 별도
   로드맵이며, 지금의 약속이 아닙니다.

## 무엇을 만드는가

세 가지를 분리해서 다룹니다 — 섞으면 신뢰가 무너지기 때문입니다(거버넌스 핵심).

1. **방법(스킬)** — 암묵지를 어떻게 포착·추출·확인·라우팅·컴파일하는가. → 13개 `skill.pab.*`
2. **형태(템플릿/스키마)** — 각 팩이 어떤 필드와 검증 규칙을 갖는가. → 14개 `user.*` 스키마
3. **데이터(인스턴스)** — 특정 개인의 확인된 레코드. → `personal.<subject>.*`
4. **런타임(어댑터)** — 확인된 슬라이스를 모아 작업별로 컴파일한 실행 프로필. → `*.runtime_adapter`

## 읽는 순서

| 문서 | 내용 |
|------|------|
| [01 커널 스키마](./01-kernel-schema.md) | 노드/엣지 타입, 라이프사이클, 6개 게이트, 베이스 레코드, 후보↔라우팅 |
| [02 빌더 파이프라인](./02-builder-pipeline.md) | 12단계 + 13개 스킬이 어떻게 연결되는가 |
| [03 팩 카탈로그](./03-pack-catalog.md) | 14개 user 온톨로지 팩의 목적·레코드 타입 |
| [04 프라이버시·경계](./04-privacy-boundary.md) | 경계 범주, 권한 레벨, 기본 안전 정책 |
| [05 평가·드리프트](./05-evaluation-drift.md) | 8개 지표, 평가 케이스, 드리프트 루프 |
| [06 수렴 모델](./06-convergence-model.md) | 6개 수렴 지표 + 5단계 성숙도 (참여 훅) |
| [07 9-space 크로스워크](./07-opencrab-9space-crosswalk.md) | OpenCrab 정식 문법과의 정합 |
| [08 네이밍·ID](./08-naming-and-ids.md) | 정식 이름, system_pack_id vs display_name |
| [09 트리거](./09-triggers.md) | 스킬 발화 조건, 훅 매핑, 스테이징/승격 경계, auto-confirm 정책 |
| [10 중복 억제·병합](./10-dedup-and-merge.md) | upsert·dedup judge·merge/supersede, redundancy/merge_rate 지표 |
| [12 확인 정책](./12-confirmation-policy.md) | 승격에 사람 확인이 언제 필요한가 — regret·네 결정 축·4계층 임계(섀도 캘리브레이션·성숙도 게이트). 07/09 심화 |

## 한눈에 보는 파이프라인

```
증거포착 → (세션마이닝 | 질문 | diff마이닝) → 후보추출 → 스코프지정
        → 확인게이트 → 팩라우팅 → 프라이버시경계 → 컴파일 → 평가/드리프트 ↺
```

각 단계는 입력/출력 계약과 담당 Crab 역할을 가집니다([02](./02-builder-pipeline.md),
[12 오케스트레이션](../skills/12-crab-orchestration.md)).

## 신뢰의 근거 (6개 게이트)

G1 증거 없는 주장 금지 · G2 스코프 없는 규칙 금지 · G3 미확인 후보의 런타임 활성화 금지 ·
G4 행동 언어만 · G5 승격 전 프라이버시 · G6 템플릿/인스턴스 분리. → [01](./01-kernel-schema.md#2-품질-게이트-quality-gates)

## OpenCrab과의 관계

OpenCrab은 **플랫폼/인프라**(온톨로지 저장·검색·QA·crab_agent 빌드)이고, **Personal Agent**는
이 위에서 만들어지는 **산출물(공식 모델명)**입니다. PA 스키마는 OpenCrab의 9-space 문법으로
사상됩니다([07](./07-opencrab-9space-crosswalk.md)).
