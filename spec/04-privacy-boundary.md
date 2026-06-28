# 04 · 프라이버시·경계 (Privacy & Boundary)

> **EN:** The privacy/authority model that decides what the Personal Agent may do on its
> own and what it must hand back to the human. Six boundary categories (memory, retrieval,
> output, action, authority, sensitivity), an eight-rung authority ladder (observe →
> blocked), and a default safe policy: the runtime may summarize/draft/classify/compare/
> recommend within confirmed scope, but must `ask_confirm` before external comms,
> irreversible actions, contractual commitments, identity-sensitive statements, and
> high-impact decisions. This layer is where Gate G5 (privacy before promotion) is paid.

경계 모델은 "에이전트가 **혼자 해도 되는 일**과 **사람에게 되물어야 하는 일**"을 가르는 층입니다.
증거에 묶이고(G1) 스코프가 지정되고(G2) 확인을 거친(G3) 레코드라도, 외부로 새거나 비가역적이거나
정체성에 닿는 행동은 자동 실행되어선 안 됩니다. 이 문서는 그 통제를 여섯 경계 범주, 여덟 권한 레벨,
하나의 기본 안전 정책으로 정의합니다. 운영 절차(스킬)는 [`../skills/09-privacy-boundary.md`](../skills/09-privacy-boundary.md),
기계 스키마는 [`../schemas/user.boundary_authority.schema.json`](../schemas/user.boundary_authority.schema.json),
이 경계가 채우는 팩은 14개 중 11번 `user.boundary_authority`입니다([03 팩 카탈로그](./03-pack-catalog.md)).

## 1. 여섯 경계 범주 (Boundary Categories)

모든 경계 규칙은 아래 여섯 범주 중 하나를 다스립니다. 스키마의 `boundary_type` 필드와 1:1로 대응합니다.

| 범주 (`boundary_type`) | 정식 키 | 무엇을 통제하는가 | 예 |
|------------------------|---------|------------------|----|
| `memory` | `memory_boundary` | 무엇이 **저장·회상**되어도 되는가 | "건강 메모는 저장하지 않음" |
| `retrieval` | `retrieval_boundary` | 무엇이 **검색·표면화**되어도 되는가 | "비공개 재무 노트는 검색 대상에서 제외" |
| `output` | `output_boundary` | 무엇이 **생성된 텍스트에 나타나도** 되는가 | "계좌번호는 출력에 절대 등장 금지" |
| `action` | `action_boundary` | 어떤 **부수효과 연산**이 허용되는가 | "파일 삭제·외부 발송은 차단" |
| `authority` | `authority_boundary` | **자율성**을 얼마나 부여하는가 (권한 사다리의 상한) | "이 작업류는 draft까지만" |
| `sensitivity` | `sensitivity_boundary` | 한 **정보 클래스**를 어떻게 다뤄야 하는가 | "고객 신원은 역할로만 지칭" |

- 처음 넷(memory/retrieval/output/action)은 **무엇을** 다루느냐의 표면을 가릅니다.
- `authority`는 **얼마나 멀리** 가도 되느냐의 천장을 정합니다(§2).
- `sensitivity`는 **어떻게** 다뤄야 하느냐를 정하며, 게이트 G5의 직접 근거가 됩니다(§5).

스키마의 `applies_to_actions`(예: `['sending messages','file writes','web fetches','memory writes']`)는
이 범주를 검증 가능한 행동 표면으로 좁혀, 비어있지 않은 `scope`(G2)를 약화시키지 않으면서 구체화합니다.

## 2. 여덟 권한 레벨 (Authority Ladder)

자율성은 단조 상승하는 사다리입니다. 스키마의 `authority_level` enum과 동일한 순서입니다.

```
observe < summarize < classify < draft < compare < recommend < ask_confirm < blocked
```

| 레벨 | 의미 | 사람 개입 |
|------|------|-----------|
| `observe` | 읽기/관찰만, 산출 없음 | 불필요 |
| `summarize` | 확인된 스코프 내 요약 | 불필요 |
| `classify` | 분류·태깅·라우팅 | 불필요 |
| `draft` | 초안 작성(미전송) | 불필요 |
| `compare` | 대안 비교·트레이드오프 제시 | 불필요 |
| `recommend` | 권고 제시(실행 아님) | 불필요 |
| `ask_confirm` | **멈추고 사람의 명시적 승인을 요구** | **필수** |
| `blocked` | 행동 자체를 금지 | — (수행 불가) |

`authority_level`은 **천장**입니다 — 런타임은 확인된 스코프 안에서 그 레벨 **이하로만** 행동합니다.
`ask_confirm`은 사람 게이트를 강제하고, `blocked`는 어떤 신뢰도에서도 행동을 막습니다. 이 사다리는
[01 커널 스키마 §9](./01-kernel-schema.md)의 정식 정의이며, [평가](./05-evaluation-drift.md)의
`boundary_compliance` 지표가 준수 여부를 점수화합니다.

## 3. 기본 안전 정책 (Default Safe Policy)

새 인스턴스가 경계 규칙을 충분히 모으기 전에도 안전하도록, 시스템은 보수적인 **기본값**을 가집니다.

> **허용 (확인된 스코프 안에서):** 런타임은 별도 확인 없이 **summarize · draft · classify ·
> compare · recommend** 할 수 있습니다.
>
> **`ask_confirm` 강제 (아래 중 하나라도 참이면 멈추고 되묻기):**
> 1. **외부 커뮤니케이션** (external comms) — 외부 수신자에게 메시지/메일 발송
> 2. **비가역적 행동** (irreversible action) — 삭제, 결제, 배포, 되돌릴 수 없는 변경
> 3. **계약적 약속** (contractual commitment) — 합의·서명·구속력 있는 약속
> 4. **정체성 민감 진술** (identity-sensitive statement) — 사용자를 대신한 신원/가치 표명
> 5. **고영향 결정** (high-impact decision) — 결과 파급이 큰 결정

이 다섯 트리거는 스키마의 `confirmation_trigger` enum과 정확히 일치합니다
(`['external comms','irreversible action','contractual commitment','identity-sensitive statement','high-impact decision']`).
`ConfirmationRuleRecord`는 그중 하나라도 참이면 `requires_confirmation=true`를 발화하고,
`requires_confirmation` 엣지로 `UserSubject`를 가리킵니다([01 커널 스키마 §4](./01-kernel-schema.md)).

기본 정책은 **하한이자 출발점**입니다. 인스턴스가 자기만의 `BoundaryRule`을 확인해 쌓으면 정책이
그 사람에 맞게 좁아지거나(더 엄격) 특정 스코프에서 넓어집니다(명시 확인 후에만). 충돌 시 **더 엄격한
규칙이 항상 이깁니다** — `blocked_actions`와 `hard` enforcement는 어떤 허용이나 약한 `DecisionPolicy`
기본값도 조용히 덮어쓸 수 없습니다.

## 4. BoundaryRule 필드 (BoundaryRule Fields)

`BoundaryRule` 노드의 레코드는 통합 베이스 레코드([01 §7](./01-kernel-schema.md))를 그대로 상속하고,
`record_type`을 이 팩의 네 타입으로 좁힌 뒤 아래 선택 필드로 구조를 더합니다. 베이스 `statement`가 항상
정식 필드이며, 아래 필드는 그것을 **검증 가능하게 만드는 패싯**입니다. 전체 스키마 →
[`../schemas/user.boundary_authority.schema.json`](../schemas/user.boundary_authority.schema.json).

**네 가지 `record_type`:**

| record_type | 무엇을 선언하는가 | 핵심 필드 |
|-------------|------------------|-----------|
| `BoundaryRuleRecord` | 여섯 범주 중 하나에 대한 제약 | `boundary_type`, `allowed_actions`, `blocked_actions` |
| `AuthorityLevelRecord` | 한 작업류의 자율성 천장 | `authority_level` |
| `ConfirmationRuleRecord` | 멈추고 되묻게 하는 트리거 | `requires_confirmation`, `confirmation_trigger` |
| `SensitivityRecord` | 한 정보 클래스의 민감성과 취급법 | `sensitivity_class`, `handling_rule` |

**팩 고유 필드 (모두 선택; required = 베이스 required + `record_type`):**

| 필드 | 타입 | 역할 |
|------|------|------|
| `boundary_type` | enum(6) | 여섯 경계 범주 중 어느 것을 다스리는가(§1) |
| `allowed_actions` | string[] | 스코프 내 **명시 허용** 연산(허용목록) — 금지만이 아니라 화이트리스트도 제공 |
| `blocked_actions` | string[] | 스코프 내 **명시 금지** 연산 — 신뢰도와 무관한 하드 스톱, 항상 우선 |
| `requires_confirmation` | boolean | 참이면 행동 전에 `ask_confirm`으로 명시적 승인 필요 |
| `confirmation_trigger` | string[] | 되묻기를 강제하는 조건(§3의 다섯 트리거) |
| `authority_level` | enum(8) | 작업류의 자율성 천장(§2 사다리) |
| `sensitivity_class` | string | 정보 클래스 라벨(예: `PII`, `client_identity`, `health`, `credentials`) |
| `handling_rule` | string | 그 클래스의 **요구 취급법**(행동 언어, G4) — G5 충족의 구성적 지시 |
| `applies_to_actions` | string[] | 경계가 발효되는 행동 종류/맥락 — `scope`를 검증 표면으로 좁힘(G2) |
| `enforcement` | enum: `hard`/`soft`/`advisory` | 얼마나 단단히 지켜야 하는가 — `confidence`(증거 강도)와 별개 |
| `on_violation` | enum: `block`/`ask_confirm`/`redact`/`warn`/`log` | 경계를 넘으려 할 때 런타임의 반응 |

> **`enforcement` vs `confidence`** — 이 둘은 다릅니다. `hard` 경계는 그 근거 증거가 아직
> 쌓이는 중이어도 강제될 수 있습니다. 안전 제약은 통계적 확신을 기다리지 않습니다.

베이스 검증은 그대로 적용됩니다: `evidence_refs` ≥ 1 (G1), 비어있지 않은 `scope` (G2),
`confidence < 0.7`이면 `counterexamples` 필수, `sensitivity` ∈ {sensitive, restricted}이면
`exception_rules` 필수.

## 5. 민감성과 라이프사이클 — 게이트 G5

경계 모델은 [라이프사이클](./01-kernel-schema.md#1-라이프사이클-the-spine)의 한 지점에 박혀 있습니다.
파이프라인의 6단계 `route_confirmed`(스킬 S09 [privacy_boundary](../skills/09-privacy-boundary.md))에서
민감 항목은 **승격되기 전에** 경계 규칙을 먼저 받습니다([02 빌더 파이프라인](./02-builder-pipeline.md)).

> **G5 (Privacy before promotion):** 어떤 항목이든 베이스 `sensitivity`가 **`sensitive` 또는
> `restricted`**이면, 대응하는 `SensitivityRecord`(또는 `BoundaryRuleRecord`)가 먼저 존재해야
> `target_pack_ingested` → `runtime_activated`로 나아갈 수 있습니다. 경계 규칙이 없으면 승격은
> 차단되고, 항목은 `review_status: deferred`로 대기합니다.

흐름으로 보면:

```
confirmed_or_rejected
      │  (sensitivity ∈ {sensitive, restricted}?)
      ├─ 예 ──► G5: SensitivityRecord/BoundaryRule 부착 필요
      │           ├─ 있음 ──► target_pack_ingested ──► runtime_activated
      │           └─ 없음 ──► 차단 (review_status: deferred, 경계 규칙 대기)
      └─ 아니오 ─► target_pack_ingested ──► runtime_activated
```

`SensitivityRecord`의 `handling_rule`이 바로 그 "먼저 받는 경계 규칙"입니다 — 예: *"고객 신원은
역할로만 지칭, 직접 인용 금지"*, *"계좌번호 redact"*, *"내부 출력에만, 외부 노출 금지"*. 이는
베이스의 per-record `sensitivity` enum(public|internal|sensitive|restricted)을 대체하지 않고
**보완**합니다: `sensitivity`는 항목의 등급, `sensitivity_class`/`handling_rule`은 그 클래스의 처리법입니다.

런타임이 경계를 넘으려 하면 `on_violation`이 반응을 결정합니다: `block`(거부), `ask_confirm`(승인
요청), `redact`(민감 부분만 제거 후 진행), `warn`(진행하되 표시), `log`(기록만). 기본 설계는 보수적이며,
이 모든 결정은 [평가](./05-evaluation-drift.md)의 `boundary_compliance` 지표로 점수화됩니다.

## 6. 다른 층과의 관계

- **DecisionPolicy와의 충돌** — `BoundaryRule`은 `DecisionPolicy`보다 우선합니다. 더 약한
  `default_action`이 `blocked_actions`나 `hard` 경계를 덮을 수 없습니다([03 팩 카탈로그](./03-pack-catalog.md)).
- **라우팅** — `BoundaryRuleCandidate`만 이 팩으로 라우팅됩니다([01 커널 스키마 §6](./01-kernel-schema.md)).
- **9-space** — 모든 경계 규칙은 OpenCrab 정식 문법의 `policy`로 사상됩니다
  ([07 크로스워크](./07-opencrab-9space-crosswalk.md)).
- **엣지** — `requires_confirmation`(BoundaryRule → UserSubject)로 사람 게이트를 명시합니다.

---

*관련: [09 프라이버시 경계 스킬](../skills/09-privacy-boundary.md) · [user.boundary_authority 스키마](../schemas/user.boundary_authority.schema.json) · [01 커널 스키마 §9](./01-kernel-schema.md) · [03 팩 카탈로그](./03-pack-catalog.md) · [05 평가·드리프트](./05-evaluation-drift.md). 구 코드명: t11, .ba.*
