# 07 · 확인 게이트 (Confirmation Gate)

> **EN:** Operating instructions for `skill.pab.confirmation_gate` — the human-review checkpoint
> that stands between extracted candidates and the packs. Nothing becomes a runtime rule here
> without a person's explicit decision (Gate G3). The gate presents each scoped candidate as a
> review item (claim + evidence summary + source refs + confidence + proposed scope + proposed
> target pack) and the reviewer takes exactly one of **six review actions** — confirm, edit,
> reject, narrow_scope, mark_sensitive, defer. Only **confirmed** and **edited** candidates may
> promote; **narrowed** ones promote only within the approved scope; **sensitive** ones are held
> until a `BoundaryRule` exists (Gate G5); **rejected** ones are kept as *negative evidence*, not
> deleted. This is the lifecycle transition `user_reviewed → confirmed_or_rejected`. Read as a
> runnable checklist, not a pitch.

확인 게이트는 파이프라인에서 **사람이 결정을 내리는 단 하나의 관문**입니다. 추출기([S05](./05-candidate-extraction.md))가
타입을 붙이고 스코프([S06](./06-scope-context.md))가 "언제/어디서 참인가"를 확정한 뒤에도, 그
후보는 아직 **추측이 아닌 잠정 주장**일 뿐입니다. 여기서 사람이 `confirm`/`edit`/`reject`/
`narrow_scope`/`mark_sensitive`/`defer` 중 **정확히 하나**를 고르고, 그 결정이 `validation_status`를
정합니다. **이 게이트를 통과한 confirmed/편집본/narrowed만** [S08 pack_router](./08-pack-router.md)로
승격됩니다(게이트 G3).

이 문서는 마케팅이 아니라 **그대로 실행하는 운영 지침**입니다. 어휘는 [커널 스키마](../spec/01-kernel-schema.md)를
따르며 새 이름을 만들지 않습니다. 상태값은 [`candidate.schema.json`](../schemas/candidate.schema.json)의
`validation_status`와 [`record.base.schema.json`](../schemas/record.base.schema.json)의 `review_status`가
공유하는 단일 라이프사이클 어휘 `{pending, confirmed, rejected, narrowed, sensitive, deferred}`를
그대로 씁니다.

---

## 1. 목적 (Purpose)

스코프가 확정된 `CandidateAssertion`을 사람에게 검토 항목으로 제시하고, **여섯 검토 액션** 중
하나를 받아 후보의 `validation_status`를 정한다. confirmed/편집본만 승격을 허락하고, 나머지는
좁히거나(narrowed) 보류하거나(sensitive/deferred) 부정 증거로 보존(rejected)한다. 이로써
라이프사이클의 `user_reviewed → confirmed_or_rejected` 전이를 강제한다.

- **하는 일:** (1) 각 후보를 검토 항목(claim·증거 요약·출처·신뢰도·제안 스코프·제안 팩)으로 렌더,
  (2) 사람에게 **여섯 액션** 중 하나를 받음, (3) 액션 → `validation_status` 매핑(§4),
  (4) 편집 시 `concise_claim`·`scope`·`sensitivity`의 변경을 기록하고 감사 흔적을 남김,
  (5) narrowed는 *승인된 좁은 스코프* 안에만 머물도록 표시, (6) sensitive는 [S09 privacy_boundary](./09-privacy-boundary.md)가
  `BoundaryRule`을 붙이기 전까지 승격 차단(게이트 G5), (7) rejected를 *부정 증거*로 보존(삭제 금지),
  (8) confirmed/narrowed/편집본을 [S08 pack_router](./08-pack-router.md)로 핸드오프.
- **하지 않는 일:** (1) **새 후보를 만들지 않는다** — 추출은 [S05](./05-candidate-extraction.md)의 일.
  (2) **스코프를 처음부터 짓지 않는다** — 확정은 [S06](./06-scope-context.md); 게이트는 *좁히기만* 한다.
  (3) **팩에 적재하지 않는다** — 라우팅은 [S08](./08-pack-router.md)이 confirmed 후보에만 한다.
  (4) **경계 규칙을 발명하지 않는다** — sensitive 표시만 하고, 규칙 작성은 [S09](./09-privacy-boundary.md).
  (5) **런타임을 활성화하지 않는다** — 컴파일은 [S10](./10-agent-compiler.md).

> 게이트의 산출은 *결정이 찍힌 후보*다. 결정은 사람의 것이고, 시스템은 그 결정을 **감사 가능하게**
> 기록할 뿐이다. `confidence`(추출 신뢰도)는 **참고치이지 승인 사유가 아니다** — 높은 신뢰도가
> 자동 confirm을 뜻하지 않고, 낮은 신뢰도가 자동 reject를 뜻하지 않는다.

## 2. 작동 방식 (How it works)

게이트는 후보 묶음(보통 한 라운드 또는 한 검토 보드 분량)을 받아 다음 순서로 처리한다. 각 단계는
[`candidate.schema.json`](../schemas/candidate.schema.json)의 상태 어휘를 만족시킨다.

```
   스코프 확정 후보 (S06 scope_context 에서)
        │
   [A] 검토 항목 렌더(render)     ── 후보 → review item (§3 필드), 증거 요약 동봉
        ▼
   [B] 검토 큐 정렬(queue)        ── 민감·고임팩트·저신뢰·모순 후보를 앞으로 (§5 정렬 규칙)
        ▼
   [C] 사람 검토(human review)    ── 여섯 액션 중 정확히 하나 (§4); 빠른 승인 보드 관례 가능(§6)
        ▼
   [D] 액션 적용(apply)           ── 액션 → validation_status; 편집 diff·결정 사유·검토자·시각 기록
        ▼
   [E] 승격 규칙 적용(promote rule)── confirmed/편집본만 통과 / narrowed는 승인 스코프 내 / sensitive 보류
        ▼                            / rejected는 부정 증거로 보존 (§5)
   [F] 핸드오프(handoff)          ── 통과분 → S08 pack_router; sensitive → S09; rejected/deferred 보존
```

**[A] 검토 항목 렌더.** 각 후보를 §3의 검토 항목으로 변환한다. 핵심은 `evidence_summary` —
원시 증거 전체가 아니라 *검토자가 1분 안에 판단할 수 있는* 요약(몇 개 세션에서, 어떤 교정으로,
얼마나 최근에 떠받쳐졌는가)과 함께, 원본을 추적할 수 있는 `source_refs`(증거 id·인용)를 둔다.
이렇게 해야 검토가 빠르면서도 증거 추적성(G1)을 잃지 않는다.

**[B] 검토 큐 정렬.** 모든 후보를 같은 무게로 보지 않는다. **민감/제한**(`sensitivity` ∈
{sensitive, restricted}), **고임팩트**(`BoundaryRule`·`DecisionPolicy` 후보), **저신뢰**
(`confidence < 0.7`), **모순**(`contradiction_count > 0`, 드리프트 후보)을 큐 앞으로 올려 사람의
주의를 집중시킨다. 나머지는 빠른 승인 보드로 묶어도 된다(§6).

**[C] 사람 검토.** 검토자는 후보마다 **여섯 액션 중 정확히 하나**를 고른다(§4). 액션은 배타적이다 —
"좁히면서 민감"처럼 보이면 먼저 `narrow_scope`로 스코프를 줄이고, 그래도 민감하면 별도로
`mark_sensitive`를 적용한다(액션은 순차 적용 가능, 단일 후보에 동시 두 종결 액션은 금지).

**[D] 액션 적용.** 액션을 `validation_status`로 매핑하고(§4 표), **감사 흔적**을 남긴다:
편집이면 `concise_claim`/`scope`/`sensitivity`의 before→after diff, 결정 사유(짧은 노트),
검토자 식별자, 결정 시각. 이 흔적이 나중에 [S11 평가·드리프트](./11-evaluation-drift.md)와
[`user.drift_history`](../schemas/user.drift_history.schema.json)의 입력이 된다.

**[E] 승격 규칙 적용.** §5의 승격 규칙을 강제한다. 요지: **confirmed/편집본만** 다음 단계로
통과하고, narrowed는 *승인된 좁은 스코프 안에서만*, sensitive는 `BoundaryRule` 충족 전까지
보류, rejected는 *부정 증거로 보존*, deferred는 다음 라운드로 미룬다.

**[F] 핸드오프.** 통과한 confirmed/narrowed/편집 후보를 [S08 pack_router](./08-pack-router.md)로
넘긴다(승격 시 필드 매핑: `candidate_id`→`id`, `concise_claim`→`statement`,
`validation_status`→`review_status`). sensitive는 [S09 privacy_boundary](./09-privacy-boundary.md)로,
rejected/deferred는 보존 저장소로 보낸다. **확인 전엔 어떤 후보도 팩에 들어가지 않는다(게이트 G3).**

## 3. 검토 항목 (Review item)

게이트는 각 후보를 다음 필드를 가진 **검토 항목(review item)**으로 제시한다. 앞 9개는 후보에서
그대로 오고, `review_actions`는 검토자에게 제시되는 허용 액션 목록(§4)이다.

| 필드 | 출처/의미 | 비고 |
|------|-----------|------|
| `candidate_id` | 후보 안정 식별자 `<subject>.<recordkind>.NNN` | 승격 시 베이스 `id`로 매핑 |
| `candidate_type` | 14개 타입 중 하나([커널 §6](../spec/01-kernel-schema.md#6-후보-타입--라우팅-11-전수)) | 목적지 팩을 함의 |
| `extracted_claim` | 검토 대상 주장(후보의 `concise_claim`) | 관찰 행동 언어여야(G4); 편집 시 여기를 고침 |
| `evidence_summary` | 무엇이·몇 번·얼마나 최근에 떠받치는지의 1분 요약 | 검토 속도 + 추적성의 균형 |
| `source_refs` | 근거 `EvidenceItem` id·인용(후보의 `evidence_refs`) | ≥1개(G1); 원본 추적 경로 |
| `confidence` | 추출 신뢰도 0..1과 그 입력(`confidence_inputs`) | **참고치**; 승인 사유 아님 |
| `proposed_scope` | S06이 확정한 "언제/어디서 참인가" | `narrow_scope`로 *좁히기만* 가능 |
| `proposed_target_pack` | 1:1 라우터가 고정한 단일 팩 | 게이트는 바꾸지 않음(라우팅은 S08) |
| `review_actions` | 이 후보에 허용된 액션 목록 | 보통 여섯 전부; 정책상 일부 제한 가능 |

> `evidence_summary`는 **요약이지 결론이 아니다.** "사용자가 X를 싫어함"처럼 추측을 적지 말고
> "3개 세션에서 서론 문단을 삭제 교정, 가장 최근은 어제"처럼 *관찰*을 적는다(G4). 검토자가
> 의심스러우면 `source_refs`로 원본 증거를 직접 확인한다.

## 4. 여섯 검토 액션 (Six review actions)

검토자는 후보마다 아래 **여섯 액션 중 정확히 하나**(종결 기준)를 고른다. 각 액션은 단일
라이프사이클 어휘의 한 상태로 매핑된다.

| 액션 | 뜻 | → `validation_status` | 승격? |
|------|----|------------------------|-------|
| **confirm** | 주장·스코프·민감도가 사용자를 충실히 반영한다. 수정 없이 승인. | `confirmed` | ✅ 승격 |
| **edit** | 주장/스코프/민감도가 *거의* 맞다. 텍스트를 고쳐서 승인. before→after diff 기록. | `confirmed`(편집본) | ✅ 승격(편집된 텍스트로) |
| **reject** | 사용자를 반영하지 않는다 / 틀렸다. 승인 거부. **삭제하지 않고** 부정 증거로 보존. | `rejected` | ❌ — 부정 증거로 보존 |
| **narrow_scope** | 맞지만 *너무 넓다*. `proposed_scope`를 더 좁은 범위로 줄여 승인. | `narrowed` | ✅ 승격(좁힌 스코프 안에서만) |
| **mark_sensitive** | 맞지만 *민감*하다. `sensitivity` 상향 + `BoundaryRule` 필요로 표시. 규칙 충족 전 보류. | `sensitive` | ⏸ 보류 — `BoundaryRule` 필요(G5) |
| **defer** | 지금은 판단 불가(증거 부족·맥락 필요). 다음 라운드로 미룸. | `deferred` | ⏸ 보류 — 재검토 대기 |

**액션 규칙 (운영):**

1. **단일 종결 액션.** 한 후보는 한 종결 상태로 끝난다. `narrow_scope` 후 여전히 민감하면
   `mark_sensitive`를 *추가로* 적용할 수 있으나(스코프는 좁혀진 채 민감 보류), 두 *종결*
   상태(confirmed + rejected 등)를 동시에 둘 수 없다.
2. **편집은 감사 대상.** `edit`은 confirmed로 승격되지만, 원문→편집문 diff와 사유를 반드시
   남긴다. 편집은 "사용자가 이렇게 *고쳐서* 승인했다"는 그 자체로 강한 증거 신호다(다음 라운드의
   `correction_strength` 입력).
3. **reject는 삭제가 아니다.** 거부된 후보는 *부정 증거*로 보존된다 — 같은 잘못된 주장이 다시
   추출되면 게이트가 과거 거부를 보여 재작업을 줄이고, [S11](./11-evaluation-drift.md)의
   `rejection_alignment` 평가에 쓰인다.
4. **sensitive는 차단이지 거부가 아니다.** `mark_sensitive`는 주장을 *인정*하되 승격만 막는다.
   [S09 privacy_boundary](./09-privacy-boundary.md)가 알맞은 경계 규칙([04 프라이버시·경계 §1
   여섯 경계 범주](../spec/04-privacy-boundary.md#1-여섯-경계-범주-boundary-categories))을 붙이면
   비로소 승격 가능해진다.
5. **defer는 빚이다.** 미룬 후보는 다음 검토 라운드 큐에 자동 재등장한다. 무한 보류를 막기 위해
   defer 사유를 적고(무엇이 더 필요한가), 가능하면 필요한 후속 증거를 [S01](./01-evidence-capture.md)에
   요청으로 남긴다.

## 5. 승격 규칙 (Promotion rule)

게이트의 **계약**은 다음 한 문장이다: *오직 confirmed와 편집본만 승격한다.* 나머지는 아래 규칙을
따른다. 이 규칙은 게이트 G3·G5를 코드로도 강제한다([`tools/validate_packs.py`](../tools/validate_packs.py)).

| 상태 | 승격 여부 | 규칙 |
|------|-----------|------|
| `confirmed` | ✅ | 그대로 [S08 pack_router](./08-pack-router.md)로. `proposed_target_pack`으로 라우팅. |
| `confirmed`(편집본) | ✅ | 편집된 `concise_claim`/`scope`/`sensitivity`로 승격. diff 보존. |
| `narrowed` | ✅(제한) | **승인된 좁은 스코프 안에서만** 활성. 원래의 넓은 스코프로는 절대 일반화 금지(G2 강화). |
| `sensitive` | ⏸ | **`BoundaryRule`이 존재해야** 승격(G5). 규칙 없으면 보류; [S09](./09-privacy-boundary.md)로. |
| `rejected` | ❌ | 승격 안 함. **부정 증거로 보존**(삭제 금지). 재추출 방지·`rejection_alignment` 평가에 사용. |
| `deferred` | ⏸ | 승격 안 함. 다음 라운드 큐로 보류. 사유·필요 증거 기록. |

**불변식:**

- **G3 — pending은 절대 승격 불가.** 검토되지 않은(`pending`) 후보는 어떤 경로로도 팩·런타임에
  닿지 않는다.
- **narrowed ⊆ proposed_scope.** narrowed의 스코프는 항상 원래 `proposed_scope`의 *부분집합*이어야
  한다. 게이트는 스코프를 *좁히기만* 하고 넓히지 않는다(넓히려면 새 증거로 새 후보를 만든다).
- **sensitive ⇒ BoundaryRule 선행.** 민감/제한 후보는 대응 `BoundaryRule`이 확정되기 전엔
  승격되지 않는다([04 프라이버시·경계](../spec/04-privacy-boundary.md), 게이트 G5).
- **rejected는 보존된다.** 거부는 정보의 *손실*이 아니라 *획득*이다 — "이건 내가 아니다"라는
  경계선이 곧 페르소나의 일부다.
- **저신뢰 후보의 반례.** `confidence < 0.7`인 후보를 confirm/edit으로 승격할 땐 베이스 레코드
  규칙상 `counterexamples`가 필수다([record.base.schema.json](../schemas/record.base.schema.json)) —
  게이트는 검토자에게 반례 입력을 요구한다.

## 6. 한국식 빠른 승인 보드 관례 (Korean review-board convention)

대량의 저위험 후보를 일일이 한 항목씩 처리하면 검토 피로가 쌓이고, 피로는 무성의한 confirm을
부른다. 이를 막기 위해 게이트는 **빠른 승인 보드(quick-approval review board)** 관례를 지원한다 —
한국 팀의 *결재 보드*에서 따온 일괄 검토 방식이다.

- **저위험 묶음 일괄 승인:** `sensitivity = public/internal` + `confidence ≥ 0.7` +
  `contradiction_count = 0` + 비-`BoundaryRule`/비-`DecisionPolicy` 후보를 한 보드로 묶어
  **한 번에 훑고 일괄 confirm**할 수 있다. 단, 각 항목의 `evidence_summary`는 그대로 표시되어
  검토자가 이상치를 *즉시 빼낼* 수 있어야 한다.
- **고위험은 보드에서 제외(강제).** 민감/제한, 고임팩트(경계·결정), 저신뢰, 모순 후보는
  **일괄 보드에 올릴 수 없다** — 반드시 개별 검토한다(§2 [B] 정렬과 동일 기준). 이 분리가
  빠른 검토와 안전을 양립시킨다.
- **일괄도 감사된다.** 보드 일괄 confirm도 검토자·시각·보드 id를 남긴다. "검토 없이 통과"가
  아니라 "한 화면에서 명시적으로 함께 승인"이라는 기록이 남는다. 일괄에서 빠진(개별로 내려간)
  항목도 그 사유가 남는다.

> 빠른 승인 보드는 **G3의 예외가 아니다.** 사람이 *실제로* 봤다는 사실은 그대로다 — 단지 본 단위가
> 한 항목이 아니라 한 보드일 뿐이다. 보드에 올릴 수 있는 후보의 기준이 곧 안전장치다.

## 7. 입력 / 출력 (Inputs / Outputs)

### 입력

- **주 입력:** [S06 scope_context](./06-scope-context.md)에서 온 *스코프 확정 후보* —
  비어있지 않은 `scope`, 타입, `evidence_refs`(≥1), `confidence`+`confidence_inputs`,
  `sensitivity`, `proposed_target_pack`을 모두 갖춘 `CandidateAssertion`.
- **부 입력(선택):** 이전 라운드의 *거부 기록*(부정 증거 — 재추출 비교용), 확정 레코드 집합
  (중복·모순 비교용), [04 프라이버시·경계](../spec/04-privacy-boundary.md)의 기본 정책(어떤
  후보가 자동으로 sensitive 큐로 가는지), 활성 팩 커버리지(검토 우선순위 참고).

### 출력

각 출력은 **결정이 찍힌 후보**다 — `validation_status` ∈ {confirmed, rejected, narrowed,
sensitive, deferred} 중 하나 + 감사 흔적:

- `validation_status` — 여섯 액션 중 하나의 결과(§4).
- (편집 시) 갱신된 `concise_claim`/`scope`/`sensitivity` + before→after diff.
- (narrowed 시) `proposed_scope`의 부분집합으로 좁혀진 `scope`.
- (sensitive 시) `BoundaryRule` 필요 플래그 + [S09](./09-privacy-boundary.md) 핸드오프.
- 감사 메타: 검토자 식별자, 결정 시각, 결정 사유 노트, (일괄 시) 보드 id.

> **하류 계약:** confirmed/narrowed/편집본만 [S08 pack_router](./08-pack-router.md)의 입력이 되어
> 베이스 레코드로 승격된다(`candidate_id`→`id`, `concise_claim`→`statement`,
> `validation_status`→`review_status`). sensitive는 [S09](./09-privacy-boundary.md)로,
> rejected/deferred는 보존 저장소로 간다. 라이프사이클 전이: `user_reviewed → confirmed_or_rejected`
> ([커널 §1](../spec/01-kernel-schema.md#1-라이프사이클-the-spine)).

## 8. 품질 검사 (Quality checks)

핸드오프 전, 확인 게이트는 다음을 강제한다. 코드 강제는 [`tools/validate_packs.py`](../tools/validate_packs.py)와
[`candidate.schema.json`](../schemas/candidate.schema.json)이 보조한다.

- [ ] **사람 결정 존재(G3)** — 모든 통과 후보가 사람의 액션으로 `pending`을 벗어났는가. 자동
  confirm/승격은 없는가.
- [ ] **단일 종결 액션** — 각 후보가 여섯 액션 중 *정확히 하나*의 종결 상태인가. 두 종결 상태가
  공존하지 않는가.
- [ ] **승격 규칙 준수** — confirmed/편집본만 S08로 통과했는가. pending/rejected/deferred가
  승격 큐에 새지 않았는가.
- [ ] **narrowed ⊆ proposed_scope** — narrowed의 스코프가 원래 제안 스코프의 부분집합인가.
  게이트가 스코프를 넓히지 않았는가(G2).
- [ ] **sensitive 보류(G5)** — 민감/제한 후보가 `BoundaryRule` 없이 승격되지 않았는가.
  [S09](./09-privacy-boundary.md)로 핸드오프됐는가.
- [ ] **rejected 보존** — 거부 후보가 삭제 대신 *부정 증거*로 보존됐는가. 사유가 기록됐는가.
- [ ] **편집 감사 흔적** — 모든 `edit`이 before→after diff·사유·검토자·시각을 남겼는가.
- [ ] **저신뢰 반례** — `confidence < 0.7` 후보를 승격할 때 `counterexamples`를 받았는가
  (베이스 레코드 규칙).
- [ ] **증거 추적성(G1)** — 각 검토 항목의 `source_refs`가 ≥1개이고 원본 증거로 추적 가능한가.
  `evidence_summary`가 추측이 아닌 관찰 요약(G4)인가.
- [ ] **고위험 개별 검토** — 민감·고임팩트·저신뢰·모순 후보가 일괄 보드가 아닌 개별로 검토됐는가(§6).
- [ ] **defer 빚 관리** — 미룬 후보에 사유와 필요 증거가 적혔고, 다음 라운드 큐에 재등장하는가.

## 9. Crab 역할 — Confirmation Crab

이 스킬의 소유 역할은 **Confirmation Crab**입니다([12 crab 오케스트레이션](./12-crab-orchestration.md),
[커널 §8](../spec/01-kernel-schema.md#8-crab-에이전트-역할-운영-모델)).

- **소유 작업:** 스코프 확정 후보를 검토 항목으로 렌더하고, 검토 큐를 위험도로 정렬하며, 사람의
  여섯 액션을 받아 `validation_status`로 매핑하고, 편집·결정의 감사 흔적을 남기고, 승격 규칙(§5)을
  강제한다. **결정은 사람이, 기록과 강제는 Crab이.**
- **핸드오프 (받음):** [Scope Crab](./06-scope-context.md)이 넘긴 스코프 확정 후보 + 그
  `EvidenceItem` 참조. (그 위로 [Candidate Extractor](./05-candidate-extraction.md) → Scope
  체인에서 온다.)
- **핸드오프 (넘김):** confirmed/narrowed/편집본 → [Pack Router](./08-pack-router.md)(승격·라우팅);
  sensitive → [Boundary Crab](./09-privacy-boundary.md)(경계 규칙 부착); rejected/deferred →
  보존 저장소(부정 증거·다음 라운드 큐).
- **하지 않는 것:** 후보 생성·스코프 신규 작성·팩 적재·경계 규칙 발명·런타임 활성화는 이 역할의
  일이 아니다. Confirmation Crab은 *사람의 결정을 받아 기록하고 강제*할 뿐, *결정을 대신*하지
  않는다. 그 절제가 게이트 G3·G5의 핵심이다 — 시스템 신뢰의 마지막 잠금장치는 사람이다.

> 9-space 사상: 검토 보드와 그 결정 주체(사람↔에이전트)는 `community`로, 확정된 `statement`(이제
> 방어 가능·증거 결속의 *승인된* 주장)는 `claim`으로 사상된다. 거부 기록은 무엇이 *그 사람이
> 아닌지*를 말하는 `policy`/`outcome` 신호다([07 9-space 크로스워크](../spec/07-opencrab-9space-crosswalk.md)).

OpenCrab 도구로 실행할 때는 `opencrab_query`/`opencrab_search_documents`로 스코프 확정 후보와 그
증거를 조회해 검토 항목을 렌더하고, 사람의 액션을 받아 후보 노드의 `validation_status`를 갱신한
뒤 confirmed/narrowed만 S08로 핸드오프한다. 민감 후보의 권한·경계 판단은
[04 프라이버시·경계 §2 여덟 권한 레벨](../spec/04-privacy-boundary.md#2-여덟-권한-레벨-authority-ladder)을 따른다.

## 10. 관련 문서

- 라이프사이클·게이트(G3·G5)·노드·엣지 어휘 → [01 커널 스키마](../spec/01-kernel-schema.md)
- 이 단계가 속한 파이프라인 계약(S07 상태 `review_candidates`) → [02 빌더 파이프라인](../spec/02-builder-pipeline.md)
- 후보의 기계 계약(`validation_status` enum·필드) → [`candidate.schema.json`](../schemas/candidate.schema.json)
- 승격 후 형태인 통합 베이스 레코드(`review_status`) → [`record.base.schema.json`](../schemas/record.base.schema.json) · [커널 §7](../spec/01-kernel-schema.md#7-통합-베이스-레코드-필드-표류-해소)
- 게이트에 후보를 넘기는 상류 → [05 candidate_extraction](./05-candidate-extraction.md) · [06 scope_context](./06-scope-context.md)
- 게이트가 후보를 넘기는 하류 → [08 pack_router](./08-pack-router.md) · [09 privacy_boundary](./09-privacy-boundary.md)
- 민감 후보가 받는 경계 규칙·권한 모델 → [04 프라이버시·경계](../spec/04-privacy-boundary.md)
- 거부·드리프트·rejection_alignment 평가 → [11 evaluation_drift](./11-evaluation-drift.md) · [05 평가·드리프트](../spec/05-evaluation-drift.md)
- 역할·상태·핸드오프 운영 모델 → [12 crab 오케스트레이션](./12-crab-orchestration.md)


## 트리거 (Trigger)

> 이 스킬의 발화 조건. 전체 2계층 모델·호스트(훅) 매핑·게이트 보존은
> [../spec/09-triggers.md](../spec/09-triggers.md), 머신 스키마는
> [../schemas/trigger.schema.json](../schemas/trigger.schema.json) 참고.

```yaml
trigger:
  trigger_id: pab.confirmation_gate.on_session_end
  skill: confirmation_gate
  signal: session_end
  condition: "review staged candidates before any promotion (also queue>=K or /review)"
  cadence: session_boundary
  host_hook: Stop · command
  produces: review_requested
  requires_confirmation: true     # 사람 검토 필요 (게이트)
  default_state: enabled
  debounce: batch_at_session_end
```

유일한 사람 체크포인트입니다 — 세션 끝에 한국어 리뷰보드로 빠르게 confirm/edit/reject(comm.002).


## 중복 억제: dedup judge 와 merge / supersede (S07 확장)

> 전체 설계·정체성 키·과-제지 경계는 [../spec/10-dedup-and-merge.md](../spec/10-dedup-and-merge.md).
> 핵심: 확정된 후보를 *새 레코드로 찍지 말고* 비슷한 기존 레코드에 누적(upsert)한다.

승격(promotion) **직전**, 확정 후보를 대상 팩의 기존 레코드와 비교하는 dedup judge 한 스텝을
거칩니다(새 아키텍처가 아니라 게이트의 한 검사). 3-렌즈로 분류:

1. identity — 같은 `canonical_key`(pack·record_type·normalize(statement)·scope) 레코드가 있는가?
2. scope — 같은 스코프인가, 더 좁히는(refinement) 것인가?
3. conflict — 기존 *확정* 레코드와 모순되는가?

판정에 따라 리뷰 액션이 추가됩니다(기존 confirm/edit/reject/narrow_scope/mark_sensitive/defer에 더해):

- **`merge`** (duplicate) — 새 레코드를 만들지 않고 기존 레코드에 `evidence_refs` 추가 +
  `repetition_count`↑ + `confidence`·`updated_at` 갱신. 멱등.
- **`supersede`** (refinement) — 새 레코드 + `supersedes` 엣지, 구 레코드 은퇴 → `drift_history` 기록.
- conflict 는 사용자에게 노출(조용히 덮어쓰지 않음 — 충돌 누락 방지).
- novel 만 그대로 `confirm` → pack_router.

judge 가 미리 분류해 **추천 액션**을 리뷰보드에 제시하므로, 사용자는 한 줄로 승인만 하면 됩니다
(한국어 리뷰보드, comm.002). 병합은 G1(증거 누적)·G2(스코프 보존)·G3(여전히 게이트)·G5를 지키며
traceability 를 오히려 강화합니다.

품질 체크: 같은 스코프가 아닌 근접중복은 `merge` 가 아니라 `supersede`/별도 레코드(스코프 정밀화)로
다룬다 — 서로 다른 스코프를 뭉개지 않는다(G2). 측정은 `redundancy_ratio`·`merge_rate`
([../spec/06-convergence-model.md](../spec/06-convergence-model.md) §7).
