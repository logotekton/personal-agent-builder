# 09 · 프라이버시 경계 (Privacy Boundary)

> **EN:** Operating instructions for `skill.pab.privacy_boundary` — the step that attaches a
> *boundary rule* to every sensitive item before it is allowed near a pack or the runtime
> (Gate G5). It does not judge whether a claim is *true* (that was the confirmation gate,
> [S07](./07-confirmation-gate.md)); it decides what the Personal Agent may do with that claim
> on its own and what it must hand back to the human. The skill writes four kinds of record
> into `user.boundary_authority` — across **six boundary categories** (memory, retrieval,
> output, action, authority, sensitivity), an **eight-rung authority ladder** (observe →
> blocked), and a conservative **default safe policy** that forces `ask_confirm` before
> external comms, irreversible actions, contractual commitments, identity-sensitive
> statements, and high-impact decisions. Read this as a runnable checklist, not a pitch.

프라이버시 경계 스킬은 "에이전트가 **혼자 해도 되는 일**과 **사람에게 되물어야 하는 일**"을
가르는 규칙을 *짓는* 단계입니다. 확인 게이트([S07](./07-confirmation-gate.md))가 어떤 후보를
`mark_sensitive`로 표시해 넘기면, 이 스킬이 그 항목에 대응하는 **경계 규칙(`BoundaryRule`)**을
부착합니다. 규칙이 붙기 전까지 그 항목은 `target_pack_ingested` → `runtime_activated`로 한 발도
나아갈 수 없습니다 — 이것이 게이트 **G5(Privacy before promotion)**이며, 이 스킬이 그 비용을
치르는 곳입니다.

이 문서는 마케팅이 아니라 **그대로 실행하는 운영 지침**입니다. 어휘는
[커널 스키마](../spec/01-kernel-schema.md)와 [04 프라이버시·경계 사양](../spec/04-privacy-boundary.md)을
따르며 새 이름을 만들지 않습니다. 모델의 정의(여섯 범주·여덟 레벨·기본 정책)는 사양 문서에 있고,
**이 스킬 문서는 그 모델을 *어떻게 적용해 규칙을 쓰는가*의 절차**입니다. 기계 스키마는
[`user.boundary_authority.schema.json`](../schemas/user.boundary_authority.schema.json),
이 경계가 채우는 팩은 14개 중 11번 `user.boundary_authority`입니다
([03 팩 카탈로그](../spec/03-pack-catalog.md), 구 코드명 t11·.ba).

---

## 1. 목적 (Purpose)

확인 게이트가 `sensitive`로 표시했거나 기본 정책상 경계가 필요한 항목에, 여섯 경계 범주·여덟
권한 레벨·기본 안전 정책을 적용해 **검증 가능한 `BoundaryRule` 레코드**를 부착한다. 그래야
그 항목이 G5를 충족하고 승격될 수 있다. 산출은 *어떤 정보가 어떻게 다뤄져야 하는가*와 *에이전트가
어디까지 자율적으로 행동해도 되는가*를 코드로 강제 가능하게 적어 둔 규칙이다.

- **하는 일:** (1) 경계가 필요한 항목을 받아 어느 **경계 범주**(memory/retrieval/output/action/
  authority/sensitivity, §3)에 속하는지 분류, (2) 그 작업류의 **권한 천장**(`authority_level`, §4)을
  정함, (3) **기본 안전 정책**(§5)에 비춰 `confirmation_trigger`가 발화하는지 판정, (4) `BoundaryRule`
  레코드를 채움(`boundary_type`·`allowed_actions`·`blocked_actions`·`enforcement`·`on_violation` 등, §6),
  (5) `requires_confirmation` 엣지로 `UserSubject`를 가리켜 사람 게이트를 명시, (6) 규칙이 붙은
  항목만 **G5 통과**로 표시해 [S08 pack_router](./08-pack-router.md)/[S10 agent_compiler](./10-agent-compiler.md)
  하류로 흘려보냄, (7) 규칙 자체도 베이스 레코드 검증(증거·스코프·반례)을 통과하게 함.
- **하지 않는 일:** (1) **주장의 진위를 판정하지 않는다** — confirm/reject는 [S07](./07-confirmation-gate.md)의 일.
  (2) **새 후보를 만들지 않는다** — 추출은 [S05](./05-candidate-extraction.md).
  (3) **스코프를 처음부터 짓지 않는다** — 확정은 [S06](./06-scope-context.md); 경계는 그 스코프를
  *행동 표면으로 좁히기만* 한다(`applies_to_actions`).
  (4) **런타임을 활성화하지 않는다** — 컴파일은 [S10](./10-agent-compiler.md); 이 스킬은 규칙을 *쓸* 뿐
  *집행*은 런타임이 한다.
  (5) **민감 항목을 삭제하지 않는다** — 위험하면 `blocked`/`hard`로 막되, 항목은 보존한다.

> 이 스킬의 산출은 *규칙*이지 *판단*이 아니다. "이 정보가 사용자에게 맞는가"는 이미 게이트에서
> 끝났다. 여기서의 질문은 단 하나다 — **"에이전트가 이걸 혼자 다뤄도 되는가, 아니면 멈추고
> 되물어야 하는가?"** 안전 제약은 통계적 확신을 기다리지 않으므로, `enforcement: hard` 경계는
> 그 근거 증거가 아직 쌓이는 중이어도 강제될 수 있다(`enforcement` ≠ `confidence`).

## 2. 작동 방식 (How it works)

스킬은 경계가 필요한 항목 묶음을 받아 다음 순서로 처리한다. 각 단계는
[`user.boundary_authority.schema.json`](../schemas/user.boundary_authority.schema.json)과
[04 프라이버시·경계 사양](../spec/04-privacy-boundary.md)의 어휘를 만족시킨다.

```
   경계 필요 항목 (S07 confirmation_gate 의 mark_sensitive + 기본 정책 트리거)
        │
   [A] 범주 분류(categorize)     ── 여섯 boundary_type 중 하나로 (§3)
        ▼
   [B] 권한 천장 설정(authority) ── 작업류의 authority_level 상한 (§4 사다리)
        ▼
   [C] 정책 대조(policy check)   ── 기본 안전 정책의 다섯 트리거와 대조 → confirmation_trigger (§5)
        ▼
   [D] 규칙 작성(write rule)     ── BoundaryRule 레코드 채움: 네 record_type 중 하나 + 패싯 (§6)
        ▼
   [E] 베이스 검증(validate)     ── evidence_refs≥1(G1)·scope(G2)·반례·exception_rules (§6 끝)
        ▼
   [F] G5 표시 & 핸드오프        ── 규칙 부착 완료 → 항목 G5 통과; 규칙·항목 → S08/S10 하류 (§7)
```

**[A] 범주 분류.** 항목이 통제해야 할 것이 *무엇이 저장/회상되는가*(memory), *무엇이 검색/표면화
되는가*(retrieval), *무엇이 출력에 나타나는가*(output), *어떤 부수효과 연산이 허용되는가*(action),
*자율성을 얼마나 주는가*(authority), *한 정보 클래스를 어떻게 다루는가*(sensitivity) 중 무엇인지
가린다(§3). 한 항목이 여러 표면을 건드리면 **각각에 대해 규칙을 나누어** 쓴다(예: 신원 정보는
`output` 규칙 + `sensitivity` 규칙 둘 다).

**[B] 권한 천장 설정.** 그 작업류가 사다리(observe < … < blocked)에서 어디까지 올라가도 되는지
**천장**을 정한다(§4). 천장은 신뢰도가 아니라 *위험*으로 정한다 — 외부 발송·비가역 행동은 증거가
많아도 천장이 `ask_confirm`/`blocked`에 머문다.

**[C] 정책 대조.** §5 기본 안전 정책의 다섯 트리거(external comms·irreversible action·contractual
commitment·identity-sensitive statement·high-impact decision)와 대조한다. 하나라도 참이면
`requires_confirmation=true`로 두고 해당 트리거를 `confirmation_trigger`에 기록한다. 인스턴스가
자기 규칙을 쌓을수록 정책이 그 사람에 맞게 *좁아지거나*(더 엄격) 특정 스코프에서 *넓어진다*(명시
확인 후에만).

**[D] 규칙 작성.** 항목을 네 `record_type`(§6 표) 중 하나로 적고, 베이스 `statement`를 **행동
언어(G4)**로 쓴 뒤 패싯(`boundary_type`·`allowed_actions`·`blocked_actions`·`authority_level`·
`sensitivity_class`·`handling_rule`·`applies_to_actions`·`enforcement`·`on_violation`)으로 *검증
가능하게* 만든다. `allowed_actions`(허용목록)와 `blocked_actions`(금지목록)를 *둘 다* 채워, 런타임이
금지뿐 아니라 화이트리스트도 갖게 한다.

**[E] 베이스 검증.** 규칙 *자체*도 통합 베이스 레코드다. `evidence_refs` ≥ 1(G1 — 왜 이 경계가
필요한지의 증거), 비어있지 않은 `scope`(G2), `confidence < 0.7`이면 `counterexamples` 필수,
`sensitivity` ∈ {sensitive, restricted}이면 `exception_rules` 필수를 모두 만족시킨다.

**[F] G5 표시 & 핸드오프.** 규칙이 붙은 항목을 **G5 통과**로 표시하고, 규칙 레코드와 항목을
[S08 pack_router](./08-pack-router.md)(승격·라우팅)와 [S10 agent_compiler](./10-agent-compiler.md)
(런타임 컴파일)로 넘긴다. 규칙이 *없는* 민감 항목은 `review_status: deferred`로 **보류**되어 다시
게이트로 돌아가거나 다음 라운드를 기다린다 — **규칙 없이 승격은 없다(G5).**

## 3. 여섯 경계 범주 (Six boundary categories)

모든 경계 규칙은 아래 여섯 범주 중 하나를 다스린다. 스키마의 `boundary_type` enum과 1:1로 대응한다.
정식 정의는 [04 프라이버시·경계 §1](../spec/04-privacy-boundary.md#1-여섯-경계-범주-boundary-categories);
여기서는 *어떻게 분류하는가*의 결정 규칙을 둔다.

| 범주 (`boundary_type`) | 통제 대상 | "이 범주인가?" 판정 질문 | 예 |
|------------------------|-----------|--------------------------|----|
| `memory` | 저장·회상 | 이걸 **기억에 남겨도** 되나? | "건강 메모는 저장하지 않음" |
| `retrieval` | 검색·표면화 | 다음에 이걸 **꺼내 와도** 되나? | "비공개 재무 노트는 검색 대상 제외" |
| `output` | 생성 텍스트 | 이게 **출력에 나타나도** 되나? | "계좌번호는 출력에 절대 등장 금지" |
| `action` | 부수효과 연산 | 이 **행동을 실행해도** 되나? | "파일 삭제·외부 발송은 차단" |
| `authority` | 자율성 상한 | **얼마나 멀리** 혼자 가도 되나? | "이 작업류는 draft까지만" |
| `sensitivity` | 정보 클래스 취급 | 이 클래스를 **어떻게 다뤄야** 하나? | "고객 신원은 역할로만 지칭" |

- 앞 넷(memory/retrieval/output/action)은 **무엇을** 다루느냐의 표면을, `authority`는 **얼마나
  멀리** 가도 되느냐의 천장을(§4), `sensitivity`는 **어떻게** 다뤄야 하느냐를(§7, G5의 직접 근거)
  가린다.
- **한 항목이 여러 범주를 건드리면 규칙을 나눈다.** 신원 정보는 보통 `output`(말해도 되나)과
  `sensitivity`(어떻게 지칭하나) 두 규칙을 받는다. 하나의 거대한 규칙보다 *검증 가능한 작은 규칙*
  여럿이 낫다.
- `applies_to_actions`(예: `['sending messages','file writes','web fetches','memory writes']`)는
  이 범주를 검증 가능한 행동 표면으로 좁혀, 비어있지 않은 `scope`(G2)를 약화시키지 않으면서 구체화한다.

## 4. 여덟 권한 레벨 (Eight authority levels)

자율성은 단조 상승하는 사다리다. 스키마의 `authority_level` enum과 동일한 순서이며, 정식 정의는
[04 프라이버시·경계 §2](../spec/04-privacy-boundary.md#2-여덟-권한-레벨-authority-ladder)·
[커널 §9](../spec/01-kernel-schema.md)에 있다.

```
observe < summarize < classify < draft < compare < recommend < ask_confirm < blocked
```

| 레벨 | 의미 | 사람 개입 | 천장으로 둘 때 |
|------|------|-----------|----------------|
| `observe` | 읽기/관찰만, 산출 없음 | 불필요 | 최대 보수 — 보기만 |
| `summarize` | 확인된 스코프 내 요약 | 불필요 | 안전 기본 안 |
| `classify` | 분류·태깅·라우팅 | 불필요 | 안전 기본 안 |
| `draft` | 초안 작성(미전송) | 불필요 | 안전 기본 안 |
| `compare` | 대안 비교·트레이드오프 제시 | 불필요 | 안전 기본 안 |
| `recommend` | 권고 제시(실행 아님) | 불필요 | 안전 기본 안 |
| `ask_confirm` | **멈추고 사람의 명시적 승인 요구** | **필수** | 외부·비가역·고영향 작업의 천장 |
| `blocked` | 행동 자체를 금지 | — | 어떤 신뢰도에서도 수행 불가 |

**천장 설정 규칙 (운영):**

1. **`authority_level`은 상한이다.** 런타임은 확인된 스코프 안에서 그 레벨 **이하로만** 행동한다.
   천장을 `draft`로 두면 작성은 하되 전송은 못 한다.
2. **위험으로 천장을 정한다, 신뢰도로가 아니라.** 외부 발송·삭제·결제·계약 약속·정체성 진술은
   증거가 아무리 쌓여도 천장이 `ask_confirm` 이상으로 올라가지 않는다.
3. **`ask_confirm`은 사람 게이트를 강제하고, `blocked`은 행동을 봉쇄한다.** 이 둘은
   `requires_confirmation`/`blocked_actions`와 짝을 이룬다(§6).
4. **충돌 시 더 엄격한 천장이 이긴다.** 약한 `DecisionPolicy` 기본값이 낮은 천장을 덮을 수 없다(§8).

준수 여부는 [평가](../spec/05-evaluation-drift.md)의 `boundary_compliance` 지표로 점수화된다.

## 5. 기본 안전 정책 (Default safe policy)

새 인스턴스가 자기 경계 규칙을 충분히 모으기 전에도 안전하도록, 시스템은 보수적인 **기본값**을
가진다. 이 스킬은 모든 항목을 이 정책에 *먼저* 대조한 뒤 규칙을 좁힌다.

> **허용 (확인된 스코프 안에서, 별도 확인 없이):** **summarize · draft · classify · compare ·
> recommend**.
>
> **`ask_confirm` 강제 (아래 중 하나라도 참이면 멈추고 되묻기):**
> 1. **외부 커뮤니케이션** (`external comms`) — 외부 수신자에게 메시지/메일 발송
> 2. **비가역적 행동** (`irreversible action`) — 삭제, 결제, 배포, 되돌릴 수 없는 변경
> 3. **계약적 약속** (`contractual commitment`) — 합의·서명·구속력 있는 약속
> 4. **정체성 민감 진술** (`identity-sensitive statement`) — 사용자를 대신한 신원/가치 표명
> 5. **고영향 결정** (`high-impact decision`) — 결과 파급이 큰 결정

이 다섯 트리거는 스키마의 `confirmation_trigger` enum과 정확히 일치한다. 항목을 정책에 대조해
하나라도 참이면 `ConfirmationRuleRecord`를 만들어 `requires_confirmation=true`로 두고, 발화한
트리거를 `confirmation_trigger`에 기록하며, `requires_confirmation` 엣지로 `UserSubject`를 가리킨다
([커널 §4](../spec/01-kernel-schema.md)).

**기본 정책은 하한이자 출발점이다.** 인스턴스가 자기 `BoundaryRule`을 확인해 쌓으면 정책이 그
사람에 맞게 좁아지거나(더 엄격) 특정 스코프에서 넓어진다(**명시 확인 후에만**). 충돌 시 **더 엄격한
규칙이 항상 이긴다** — `blocked_actions`와 `enforcement: hard`는 어떤 허용이나 약한 `DecisionPolicy`
기본값도 조용히 덮어쓸 수 없다.

## 6. BoundaryRule 필드 (BoundaryRule fields)

규칙은 통합 베이스 레코드([커널 §7](../spec/01-kernel-schema.md#7-통합-베이스-레코드-필드-표류-해소))를
그대로 상속하고, `record_type`을 이 팩의 네 타입으로 좁힌 뒤 패싯 필드로 구조를 더한다. 베이스
`statement`가 항상 정식 필드이며, 아래 필드는 그것을 **검증 가능하게 만드는 패싯**이다. 전체 스키마 →
[`user.boundary_authority.schema.json`](../schemas/user.boundary_authority.schema.json).

**네 가지 `record_type` (어떤 항목에 무엇을 쓰나):**

| record_type | 무엇을 선언하나 | 언제 쓰나 | 핵심 필드 |
|-------------|----------------|-----------|-----------|
| `BoundaryRuleRecord` | 여섯 범주 중 하나에 대한 제약 | memory/retrieval/output/action 표면을 막거나 허용 | `boundary_type`, `allowed_actions`, `blocked_actions` |
| `AuthorityLevelRecord` | 한 작업류의 자율성 천장 | "여기까지만 혼자" 상한을 정할 때 | `authority_level` |
| `ConfirmationRuleRecord` | 멈추고 되묻게 하는 트리거 | 다섯 트리거(§5) 중 하나가 발화할 때 | `requires_confirmation`, `confirmation_trigger` |
| `SensitivityRecord` | 한 정보 클래스의 민감성·취급법 | 정보 *클래스*를 어떻게 다룰지 정할 때(G5) | `sensitivity_class`, `handling_rule` |

**팩 고유 필드 (모두 선택; required = 베이스 required + `record_type`):**

| 필드 | 타입 | 역할 |
|------|------|------|
| `boundary_type` | enum(6) | 여섯 경계 범주 중 어느 것을 다스리나(§3) |
| `allowed_actions` | string[] | 스코프 내 **명시 허용** 연산(허용목록) — 금지뿐 아니라 화이트리스트 제공 |
| `blocked_actions` | string[] | 스코프 내 **명시 금지** 연산 — 신뢰도 무관 하드 스톱, 항상 우선 |
| `requires_confirmation` | boolean | 참이면 행동 전 `ask_confirm`으로 명시적 승인 필요 |
| `confirmation_trigger` | string[] | 되묻기를 강제하는 조건(§5의 다섯 트리거) |
| `authority_level` | enum(8) | 작업류의 자율성 천장(§4 사다리) |
| `sensitivity_class` | string | 정보 클래스 라벨(예: `PII`, `client_identity`, `health`, `credentials`) |
| `handling_rule` | string | 그 클래스의 **요구 취급법**(행동 언어, G4) — G5 충족의 구성적 지시 |
| `applies_to_actions` | string[] | 경계가 발효되는 행동 종류/맥락 — `scope`를 검증 표면으로 좁힘(G2) |
| `enforcement` | enum: `hard`/`soft`/`advisory` | 얼마나 단단히 지켜야 하나 — `confidence`(증거 강도)와 별개 |
| `on_violation` | enum: `block`/`ask_confirm`/`redact`/`warn`/`log` | 경계를 넘으려 할 때 런타임의 반응 |

> **`enforcement` vs `confidence` (혼동 금지)** — 이 둘은 다르다. `hard` 경계는 그 근거 증거가
> 아직 쌓이는 중이어도 강제될 수 있다. 안전 제약은 통계적 확신을 기다리지 않는다. 규칙을 쓸 때
> `enforcement`는 *위험*으로, `confidence`는 *증거 강도*로 따로 채운다.

베이스 검증은 그대로 적용된다: `evidence_refs` ≥ 1(G1), 비어있지 않은 `scope`(G2),
`confidence < 0.7`이면 `counterexamples` 필수, `sensitivity` ∈ {sensitive, restricted}이면
`exception_rules` 필수. **규칙도 증거에 묶인다** — "왜 이 경계가 필요한가"의 근거 없이 경계를
발명하지 않는다.

## 7. 민감성과 라이프사이클 — 게이트 G5

이 스킬은 [라이프사이클](../spec/01-kernel-schema.md#1-라이프사이클-the-spine)의 한 지점에 박혀
있다. 파이프라인 6단계 `route_confirmed` 앞에서, 민감 항목은 **승격되기 전에** 경계 규칙을 먼저
받는다([02 빌더 파이프라인](../spec/02-builder-pipeline.md)).

> **G5 (Privacy before promotion):** 어떤 항목이든 베이스 `sensitivity`가 **`sensitive` 또는
> `restricted`**이면, 대응하는 `SensitivityRecord`(또는 `BoundaryRuleRecord`)가 먼저 존재해야
> `target_pack_ingested` → `runtime_activated`로 나아갈 수 있다. 경계 규칙이 없으면 승격은
> 차단되고, 항목은 `review_status: deferred`로 대기한다.

흐름으로 보면:

```
confirmed_or_rejected  (S07 confirmation_gate)
      │  (sensitivity ∈ {sensitive, restricted}?)
      ├─ 예 ──► S09 privacy_boundary: SensitivityRecord/BoundaryRule 부착 필요
      │           ├─ 부착됨 ──► G5 통과 ──► S08 라우팅 ──► S10 컴파일 ──► runtime_activated
      │           └─ 없음   ──► 차단 (review_status: deferred, 경계 규칙 대기)
      └─ 아니오 ─► 곧장 S08 라우팅 ──► … ──► runtime_activated
```

`SensitivityRecord`의 `handling_rule`이 바로 그 "먼저 받는 경계 규칙"이다 — 예: *"고객 신원은
역할로만 지칭, 직접 인용 금지"*, *"계좌번호 redact"*, *"내부 출력에만, 외부 노출 금지"*. 이는
베이스의 per-record `sensitivity` enum(public|internal|sensitive|restricted)을 대체하지 않고
**보완**한다: `sensitivity`는 항목의 등급, `sensitivity_class`/`handling_rule`은 그 클래스의 처리법.

런타임이 경계를 넘으려 하면 `on_violation`이 반응을 결정한다: `block`(거부), `ask_confirm`(승인
요청), `redact`(민감 부분만 제거 후 진행), `warn`(진행하되 표시), `log`(기록만). 이 스킬은 규칙을
*쓸* 뿐 *집행*은 런타임의 일이지만, 어떤 `on_violation`을 두느냐가 곧 집행의 보수성을 정한다. 모든
결정은 [평가](../spec/05-evaluation-drift.md)의 `boundary_compliance` 지표로 점수화된다.

## 8. 다른 층과의 충돌 해소 (Conflict resolution)

- **DecisionPolicy와의 충돌** — `BoundaryRule`은 `DecisionPolicy`보다 **우선**한다. 더 약한
  `default_action`이 `blocked_actions`나 `enforcement: hard` 경계를 덮을 수 없다
  ([03 팩 카탈로그](../spec/03-pack-catalog.md)).
- **경계끼리의 충돌** — **더 엄격한 규칙이 항상 이긴다.** 같은 행동에 허용과 금지가 겹치면
  `blocked_actions`가 이기고, 낮은 천장이 높은 천장을 이긴다. `enforcement`는 더 느슨한 형제 규칙을
  완화하는 데 쓰지 않는다.
- **상류 게이트와의 분업** — 게이트([S07](./07-confirmation-gate.md))는 `mark_sensitive`로 *표시만*
  하고, 경계 규칙 *작성*은 이 스킬의 일이다(게이트는 규칙을 발명하지 않는다).
- **라우팅** — `BoundaryRuleCandidate`만 `user.boundary_authority`로 라우팅된다
  ([커널 §6](../spec/01-kernel-schema.md#6-후보-타입--라우팅-11-전수)).

## 9. 입력 / 출력 (Inputs / Outputs)

### 입력

- **주 입력:** [S07 confirmation_gate](./07-confirmation-gate.md)에서 `mark_sensitive`로 표시되어
  넘어온 항목 — `sensitivity` ∈ {sensitive, restricted}, 비어있지 않은 `scope`, `evidence_refs`(≥1)를
  갖춘 후보/레코드. 그리고 기본 정책(§5)상 자동으로 경계가 필요한 항목(외부·비가역·고영향 행동을
  함의하는 것).
- **부 입력(선택):** [04 프라이버시·경계 사양](../spec/04-privacy-boundary.md)의 기본 정책과 enum
  정의, 기존 `BoundaryRule` 집합(중복·충돌 비교용), `user.decision_policy`의 관련 규칙(우선순위 충돌
  확인용), `user.tool_stack`의 도구 행동 표면(`applies_to_actions` 채우기용).

### 출력

각 출력은 **항목에 부착된 `BoundaryRule` 레코드**다 — 네 `record_type` 중 하나 + 패싯 + 베이스 필드:

- `record_type` ∈ {BoundaryRuleRecord, AuthorityLevelRecord, ConfirmationRuleRecord, SensitivityRecord}.
- 채워진 패싯: `boundary_type`/`authority_level`/`confirmation_trigger`/`sensitivity_class`/
  `handling_rule`/`allowed_actions`/`blocked_actions`/`applies_to_actions`/`enforcement`/`on_violation`
  중 record_type에 맞는 것.
- 베이스 필드: `evidence_refs`(≥1), `scope`, `confidence`(+ <0.7이면 `counterexamples`),
  `review_status`, `sensitivity`(+ {sensitive,restricted}이면 `exception_rules`).
- `requires_confirmation` 엣지(BoundaryRule → UserSubject)와 **G5 통과 표시**.

> **하류 계약:** 규칙이 붙은 항목만 G5를 통과해 [S08 pack_router](./08-pack-router.md)로 승격되고,
> 이후 [S10 agent_compiler](./10-agent-compiler.md)가 런타임 어댑터로 컴파일한다. 규칙이 *없는* 민감
> 항목은 `review_status: deferred`로 보류된다. 라이프사이클 전이: 경계 규칙이 `confirmed_or_rejected`와
> `target_pack_ingested` 사이의 G5 관문을 채운다([커널 §1](../spec/01-kernel-schema.md#1-라이프사이클-the-spine)).

## 10. 품질 검사 (Quality checks)

핸드오프 전, 프라이버시 경계 스킬은 다음을 강제한다. 코드 강제는
[`tools/validate_packs.py`](../tools/validate_packs.py)와
[`user.boundary_authority.schema.json`](../schemas/user.boundary_authority.schema.json)이 보조한다.

- [ ] **G5 — 민감 항목엔 규칙 선행** — `sensitivity` ∈ {sensitive, restricted}인 모든 항목이 대응
  `BoundaryRule`/`SensitivityRecord`를 *먼저* 받았는가. 규칙 없는 민감 항목이 승격 큐에 새지 않았는가.
- [ ] **범주 정확** — 각 규칙의 `boundary_type`이 여섯 범주(§3) 중 하나이고, 통제 표면과 맞는가.
  여러 표면을 건드리는 항목은 규칙을 나눴는가.
- [ ] **천장은 위험으로** — `authority_level`이 신뢰도가 아니라 *위험*으로 정해졌는가. 외부·비가역·
  고영향 작업의 천장이 `ask_confirm`/`blocked`를 넘지 않는가(§4).
- [ ] **기본 정책 대조** — 다섯 트리거(§5) 중 하나라도 참인 항목이 `requires_confirmation=true` +
  `confirmation_trigger`를 받았고, `requires_confirmation` 엣지로 `UserSubject`를 가리키는가.
- [ ] **허용 + 금지 둘 다** — `BoundaryRuleRecord`가 `allowed_actions`와 `blocked_actions`를 *둘 다*
  채워 화이트리스트와 하드 스톱을 모두 제공하는가.
- [ ] **`enforcement` ≠ `confidence`** — `hard` 경계가 증거 부족을 이유로 약화되지 않았는가. 안전
  제약이 통계적 확신을 기다리지 않았는가.
- [ ] **충돌 해소** — 같은 행동의 허용/금지 겹침에서 `blocked_actions`가 이기고, 약한
  `DecisionPolicy` 기본값이 `hard` 경계를 덮지 않았는가(§8).
- [ ] **행동 언어(G4)** — `handling_rule`·`statement`가 추측 심리가 아닌 *관찰 가능한 행동*으로
  쓰였는가("계좌번호 redact" ○, "사용자가 사생활에 예민함" ✗).
- [ ] **규칙의 증거(G1)·스코프(G2)** — 경계 규칙 *자체*가 `evidence_refs` ≥ 1과 비어있지 않은 `scope`를
  갖는가. "왜 이 경계가 필요한가"의 근거 없이 경계를 발명하지 않았는가.
- [ ] **저신뢰 반례·민감 예외** — `confidence < 0.7`이면 `counterexamples`, `sensitivity` ∈
  {sensitive, restricted}이면 `exception_rules`를 받았는가.
- [ ] **삭제 아닌 차단** — 위험 항목을 *삭제*하지 않고 `blocked`/`hard`로 *막아* 보존했는가.

## 11. Crab 역할 — Boundary Crab

이 스킬의 소유 역할은 **Boundary Crab**입니다([12 crab 오케스트레이션](./12-crab-orchestration.md),
[커널 §8](../spec/01-kernel-schema.md#8-crab-에이전트-역할-운영-모델)).

- **소유 작업:** 게이트가 `mark_sensitive`로 넘긴 항목(및 기본 정책상 경계가 필요한 항목)을 여섯
  범주로 분류하고, 권한 천장을 정하고, 기본 안전 정책에 대조해 `confirmation_trigger`를 판정하며,
  네 `record_type`의 `BoundaryRule` 레코드를 *증거에 묶어* 작성하고, `requires_confirmation` 엣지를
  걸어 G5를 충족시킨다. **규칙은 Crab이 쓰고, 집행은 런타임이, 진위 판정은 게이트가.**
- **핸드오프 (받음):** [Confirmation Crab](./07-confirmation-gate.md)이 `mark_sensitive`로 표시한 항목
  + 그 `EvidenceItem` 참조 + 제안 스코프.
- **핸드오프 (넘김):** 규칙이 붙어 G5를 통과한 항목 → [Pack Router](./08-pack-router.md)(승격·라우팅) →
  [Agent Compiler](./10-agent-compiler.md)(런타임 컴파일). 규칙 미부착 민감 항목 → `deferred`로 보류.
- **하지 않는 것:** 주장의 진위 판정·후보 생성·스코프 신규 작성·팩 직접 적재·런타임 집행은 이 역할의
  일이 아니다. Boundary Crab은 *무엇을 혼자 해도 되는지의 경계를 증거에 묶어 쓸* 뿐이다. 그 절제가
  게이트 G5의 핵심이다 — 민감한 것은 *경계를 먼저 받고서야* 에이전트의 일부가 된다.

> 9-space 사상: 모든 경계 규칙은 OpenCrab 정식 문법의 `policy`로 사상된다 — 무엇이 허용/금지되고
> 무엇이 확인을 요하는지의 통치 규칙. `requires_confirmation`이 가리키는 사람↔에이전트 관계는
> `community`, 위반 시 `on_violation`이 남기는 결과 신호는 `outcome`으로도 비친다
> ([07 9-space 크로스워크](../spec/07-opencrab-9space-crosswalk.md)).

OpenCrab 도구로 실행할 때는 `opencrab_query`/`opencrab_search_documents`로 게이트가 넘긴 민감 항목과
그 증거를 조회해 경계 범주·권한 천장을 판정하고, `BoundaryRule` 노드를 작성한 뒤 `requires_confirmation`
엣지로 `UserSubject`를 가리킨다. 규칙이 붙은 항목만 G5 통과로 표시해 S08로 핸드오프한다. 권한·기본
정책 판단은 [04 프라이버시·경계 §2 여덟 권한 레벨](../spec/04-privacy-boundary.md#2-여덟-권한-레벨-authority-ladder)·
[§3 기본 안전 정책](../spec/04-privacy-boundary.md#3-기본-안전-정책-default-safe-policy)을 따른다.

## 12. 관련 문서

- 프라이버시·권한 모델의 정식 정의(여섯 범주·여덟 레벨·기본 정책·BoundaryRule 필드) → [04 프라이버시·경계](../spec/04-privacy-boundary.md)
- 라이프사이클·게이트(G4·G5)·노드·엣지 어휘 → [01 커널 스키마](../spec/01-kernel-schema.md)
- 이 단계가 속한 파이프라인 계약 → [02 빌더 파이프라인](../spec/02-builder-pipeline.md)
- 경계 규칙의 기계 계약(네 record_type·패싯·enum) → [`user.boundary_authority.schema.json`](../schemas/user.boundary_authority.schema.json)
- 규칙이 상속하는 통합 베이스 레코드 → [`record.base.schema.json`](../schemas/record.base.schema.json) · [커널 §7](../spec/01-kernel-schema.md#7-통합-베이스-레코드-필드-표류-해소)
- 민감 항목을 이 스킬로 넘기는 상류 → [07 confirmation_gate](./07-confirmation-gate.md)
- 규칙 부착 후 흘러가는 하류 → [08 pack_router](./08-pack-router.md) · [10 agent_compiler](./10-agent-compiler.md)
- `boundary_compliance` 지표·드리프트 → [11 evaluation_drift](./11-evaluation-drift.md) · [05 평가·드리프트](../spec/05-evaluation-drift.md)
- 역할·상태·핸드오프 운영 모델 → [12 crab 오케스트레이션](./12-crab-orchestration.md)


## 트리거 (Trigger)

> 이 스킬의 발화 조건. 전체 2계층 모델·호스트(훅) 매핑·게이트 보존은
> [../spec/09-triggers.md](../spec/09-triggers.md), 머신 스키마는
> [../schemas/trigger.schema.json](../schemas/trigger.schema.json) 참고.

```yaml
trigger:
  trigger_id: pab.privacy_boundary.on_sensitivity
  skill: privacy_boundary
  signal: sensitivity_flag
  condition: "a sensitive item is detected, or before an external/irreversible tool call (pre_external_action)"
  cadence: event
  host_hook: PreToolUse
  produces: boundary_applied
  requires_confirmation: true     # 사람 검토 필요 (게이트)
  default_state: enabled
  debounce: per_action
```

항상 켜진 가드 — 승격 전 민감 항목을 잡고(G5), 외부·비가역 행동 직전 ask_confirm/block.
