# QUICKSTART — 첫 세션에서 내 Personal Agent 시작하기

> **EN:** A new-user onboarding guide: build your own *Personal Agent* in your very first
> session. You start from one real session you already had with an AI agent, capture 3–5
> `EvidenceItem`s, extract typed candidates, confirm them yourself in a quick Korean-style
> review board, route the confirmed ones into 2–3 packs to reach the **L1 Sketch** tier, and
> check the numbers with `tools/convergence_report.py`. Nothing here becomes a runtime rule
> without **your** explicit confirmation — the whole flow is fenced by six quality gates
> (G1–G6) and your data is private by default.

이 문서는 처음 온 사람을 위한 **30~60분짜리 첫 세션 안내서**입니다. 거창한 설정 없이, 당신이
*이미 했던* AI 에이전트 세션 하나에서 출발해 — 증거를 줍고, 후보를 뽑고, **당신이 직접 확인**해서,
2~3개 팩에 채워 넣고, 수렴 지표로 현재 위치(L1 스케치)를 확인하는 데까지 갑니다.

핵심 약속 두 가지를 먼저 못 박습니다:

- **당신의 데이터는 당신 것입니다.** 인스턴스 레코드는 기본 비공개이며, 어떤 라이선스에도
  묶이지 않습니다([README 라이선스](../README.md)). 공개되는 것은 *방법론(스키마·스킬·지표)*이지
  *당신의 인스턴스*가 아닙니다.
- **당신이 확인하기 전엔 아무것도 활성화되지 않습니다.** 추출된 후보는 추측일 뿐이며, 당신의
  명시적 확인(`confirm`/`edit`/`narrow_scope`)을 거쳐야만 에이전트의 규칙이 됩니다(게이트 G3).

어휘는 모두 [커널 스키마](../spec/01-kernel-schema.md)를 따릅니다. 새 이름을 만들지 않습니다.

---

## 0. 그 전에: 6개 게이트 (한눈에)

이 7단계 내내 시스템이 당신을 지키는 여섯 개의 잠금장치입니다. 외울 필요는 없지만, *왜 이렇게까지
하나*가 궁금할 때 돌아오세요([커널 §2](../spec/01-kernel-schema.md#2-품질-게이트-quality-gates)).

| ID | 규칙 | 첫 세션에서 당신이 체감하는 곳 |
|----|------|--------------------------------|
| **G1** | 증거 없는 주장 없음 | 모든 후보가 ≥1개 증거에 묶임 (단계 2–3) |
| **G2** | 스코프 없는 규칙 없음 | "언제/어디서 참인가"를 항상 적음 (단계 4) |
| **G3** | 미확인 항목은 런타임 활성화 금지 | 당신이 confirm해야만 규칙이 됨 (단계 4) |
| **G4** | 행동 언어만 | 추측 심리("X를 싫어함") 금지, 관찰("서론을 3번 지움")만 (단계 2) |
| **G5** | 승격 전 프라이버시 | 민감 항목은 경계 규칙을 먼저 받음 (단계 4–5) |
| **G6** | 템플릿/인스턴스 분리 | 빈 템플릿과 당신의 레코드는 절대 섞이지 않음 (단계 5) |

---

## 1단계 · 프라이버시 먼저 (Privacy first)

만들기 전에, 당신이 무엇을 통제하는지부터 확인합니다.

- **소유:** 당신이 만든 인스턴스 레코드(`personal.<당신>.*`)는 당신 것입니다. 기본 `sensitivity`는
  보수적으로 잡습니다 — 개인적·식별 가능 항목은 `internal` 이상으로 시작하세요. 공개해도 되는
  순수 작업 선호만 `public`으로 둡니다.
- **민감도 4단계:** `public` · `internal` · `sensitive` · `restricted`
  ([record.base](../schemas/record.base.schema.json)). `sensitive`/`restricted` 항목은 **경계
  규칙(`BoundaryRule`)을 먼저 받기 전엔 승격되지 않습니다**(게이트 G5).
- **기본 안전 정책:** 런타임은 확인된 스코프 안에서 요약·초안·분류·비교·추천까지만 자유롭게 하고,
  외부 발신·비가역 행동·계약·신원 민감 발언·고임팩트 결정 앞에서는 **항상 확인을 요구**합니다
  ([04 프라이버시·경계](../spec/04-privacy-boundary.md)).

> 한 줄 점검: *"이 항목이 유출되면 곤란한가?"* 그렇다면 지금 `sensitivity`를 올려 두세요. 나중에
> 경계 규칙을 붙이며 다시 검토합니다. 의심되면 높게.

---

## 2단계 · 실제 세션 하나에서 시작, 증거 3~5개 줍기

새로 무언가를 꾸며내지 마세요. **이미 있었던 진짜 세션**에서 출발합니다 — 가장 신호가 강한 곳은
*당신이 결과를 고친 순간*입니다.

좋은 1차 출처(`EvidenceItem`):

- 에이전트의 출력을 **당신이 고친 교정/diff** — 가장 강한 증거(당신이 직접 경계를 그었으므로).
- "아니 그거 말고 이렇게" 같은 **명시적 지시 발언**.
- 받아들인 출력 vs 버린 출력의 **대조**.
- 반복해서 요구한 **포맷·구조 선호**.

**3~5개**의 짧은 증거 조각을 고릅니다. 각 조각은 [01 증거 포착](../skills/01-evidence-capture.md)을
따라 *관찰된 행동*으로만 적습니다(게이트 G4) — 추측 심리는 적지 않습니다.

| `EvidenceItem` 예 (행동 언어 ✅) | 적지 말 것 (추측 ❌) |
|----------------------------------|----------------------|
| "보고서 초안의 서론 문단을 3개 세션에서 삭제 교정함" | "사용자는 장황한 글을 싫어함" |
| "마크다운 표를 요청, 산문 단락 답변을 표로 다시 시킴" | "사용자는 표를 좋아하는 성격" |
| "외부 이메일 초안에 항상 '보내기 전 확인' 요구" | "사용자는 신중한 사람" |

> 팁: 증거마다 **출처 참조**(세션 id·인용·시각)를 남기세요. 이게 나중에 G1(증거 추적성)을
> 자동으로 만족시킵니다. 첫 세션엔 3개면 충분합니다 — 완벽보다 *실재*가 중요합니다.

---

## 3단계 · 후보 추출 (Extract candidates)

증거에서 **타입이 붙은 후보**(`CandidateAssertion`)를 뽑습니다([05 후보 추출](../skills/05-candidate-extraction.md)).
각 후보는 14개 후보 타입 중 **정확히 하나**이고, 그 타입이 목적지 팩을 1:1로 정합니다
([커널 §6 라우팅](../spec/01-kernel-schema.md#6-후보-타입--라우팅-11-전수)).

위 세 증거에서 자연스럽게 나오는 후보:

| 증거 | → 후보 타입 | → 목적지 팩 |
|------|-------------|-------------|
| 서론을 반복 삭제 | `CommunicationStyleCandidate` | `user.communication_style` |
| 표로 다시 시킴 | `ArtifactPolicyCandidate` | `user.artifact_policy` |
| 외부 발신 전 확인 요구 | `BoundaryRuleCandidate` | `user.boundary_authority` |

각 후보에는 최소한 다음을 채웁니다(스킬 05의 필수 필드): `candidate_type`, `concise_claim`(관찰
행동 언어), `evidence_refs`(≥1, **게이트 G1**), `confidence`(0..1), `proposed_target_pack`.

> `confidence`는 *추출 자신감*일 뿐, 승인 사유가 아닙니다. 첫 세션엔 대부분 0.5~0.7 사이로 나옵니다.
> `confidence < 0.7`이면 4단계에서 **반례(`counterexamples`)를 하나 적어야** 승격됩니다
> ([record.base](../schemas/record.base.schema.json)). 이건 부담이 아니라 정직함입니다.

---

## 4단계 · 빠른 한국식 검토 보드에서 확인 (Review & confirm)

여기가 **당신이 결정하는 단 하나의 관문**입니다([07 확인 게이트](../skills/07-confirmation-gate.md)).
시스템은 후보를 *제시*하고 *기록*할 뿐, **결정은 당신이** 내립니다(게이트 G3).

각 후보에 대해 **여섯 액션 중 정확히 하나**를 고릅니다:

| 액션 | 언제 | 결과 |
|------|------|------|
| **confirm** | 그대로 나를 충실히 반영 | 승격 ✅ |
| **edit** | 거의 맞다, 문구만 손봄 | 승격 ✅ (편집본, diff 기록) |
| **narrow_scope** | 맞지만 너무 넓다 | 승격 ✅ (좁힌 스코프 안에서만) |
| **reject** | 내가 아니다 / 틀림 | 부정 증거로 보존 ❌ (삭제 아님) |
| **mark_sensitive** | 맞지만 민감 | 보류 ⏸ — 경계 규칙 필요(G5) |
| **defer** | 지금은 판단 불가 | 다음 라운드로 미룸 ⏸ |

이때 각 후보에 **스코프**를 확정합니다 — "언제/어디서 참인가"(게이트 G2). 예: *"긴 형식 보고서
초안에 한함, 짧은 채팅 답변엔 비적용"*. 빈 스코프는 통과할 수 없습니다.

**빠른 승인 보드 관례.** 저위험 후보(`public`/`internal` + `confidence ≥ 0.7` + 모순 없음 +
비-경계/비-결정)는 한 화면에 묶어 **일괄 confirm**할 수 있습니다 — 한국 팀의 *결재 보드* 방식입니다.
단, 민감·고임팩트·저신뢰·모순 후보는 **반드시 개별 검토**합니다([07 §6](../skills/07-confirmation-gate.md)).
일괄도 "본 단위가 한 보드일 뿐, 안 본 게 아니다" — 그래서 G3의 예외가 아닙니다.

> 첫 세션 목표는 **3~4개 confirm**입니다. 위 예시라면: 통신 스타일 1개와 산출물 정책 1개를
> `confirm`, 경계 규칙 1개는 `mark_sensitive`로 보류해 5단계에서 경계 규칙을 붙입니다.

---

## 5단계 · 2~3개 팩에 라우팅 → L1 스케치 도달

확인된 후보를 [08 팩 라우터](../skills/08-pack-router.md)가 **목적지 팩**으로 보냅니다. 승격되면
후보 필드가 통합 베이스 레코드로 매핑됩니다: `candidate_id` → `id`, `concise_claim` → `statement`,
`validation_status` → `review_status`([record.base](../schemas/record.base.schema.json)).

첫 세션이라면 보통 **2~3개 팩**이 채워집니다. 예:

- `user.communication_style` — "긴 보고서 초안에서 서론 문단을 생략한다" (1개 confirmed)
- `user.artifact_policy` — "구조화된 데이터는 산문 대신 마크다운 표로 출력한다" (1개 confirmed)
- `user.boundary_authority` — "외부 이메일은 발신 전 항상 확인을 요구한다" (경계 규칙 부착 후 confirmed)

세 번째 항목은 민감했으므로 [09 프라이버시·경계](../skills/09-privacy-boundary.md)가 먼저
`BoundaryRule`(여섯 경계 범주 중 `output_boundary`/`action_boundary`)을 붙인 뒤에야 승격됩니다(G5).

**템플릿 ≠ 인스턴스(G6).** `templates/`의 빈 채우기 양식은 *스키마*입니다. 당신의 confirmed
레코드는 *인스턴스*(`personal.<당신>.*`)로, 절대 섞이지 않습니다.

### 지금 당신은 어디인가 — 성숙도 사다리

[수렴 모델](../spec/06-convergence-model.md)의 5단계 사다리에서 첫 세션의 목표는 **L1 Sketch**입니다.

| 단계 | 이름 | 진입 조건 | 첫 세션 |
|------|------|-----------|---------|
| **L0** | Seed | 3개 미만 팩 시드, 평가 케이스 없음 | 출발점 |
| **L1** | **Sketch** | **≥7개 팩 시드, ≥3개 평가 케이스, `traceability`=1.0** | ← 목표 |
| L2 | Working | `coverage`≥0.5, `decision_fidelity`≥0.6, `confirmation_ratio`≥0.6 | 다음 |
| L3 | Reliable | `coverage`≥0.8, `decision_fidelity`≥0.8, `correction_cost`≤0.3 … | 이후 |
| L4 | Convergent | 전 지표 충족 + N기간 지속 (도달이 아니라 *유지*) | 장기 |

> 솔직히: **한 세션으로 7개 팩 전부를 채우긴 어렵습니다.** L1의 핵심 진입 조건인
> **`traceability`=1.0**(증거 가진 활성 규칙 / 활성 규칙)은 첫날부터 만족시킬 수 있습니다 — 모든
> 레코드가 증거에 묶여 있으니까요(G1). 나머지 팩 시드와 평가 케이스 3개는 다음 1~2세션에서
> 채웁니다. 첫 세션의 진짜 성과는 *L0를 벗어나 사다리에 발을 올린 것*입니다.

---

## 6단계 · 수렴 확인 (`tools/convergence_report.py`)

채웠으면, *느낌*이 아니라 *숫자*로 봅니다. 한 사용자의 인스턴스 팩 집합을 읽어 6개 지표와 현재
성숙도 단계를 출력합니다([수렴 모델 §5](../spec/06-convergence-model.md#5-계산-방법)).

```bash
python tools/convergence_report.py <당신의-인스턴스-폴더>   # 인스턴스 레코드·평가 케이스가 든 디렉터리 하나
# 번들 예제로 먼저 감을 잡고 싶다면:
python tools/convergence_report.py examples/logotekton
```

첫 세션 직후 보게 될 대략의 모습:

| 지표 | 방향 | 첫 세션 예상 | 의미 |
|------|------|--------------|------|
| `coverage` | ↑ | ~0.14 (2/14) | 폭 — 아직 좁음, 정상 |
| `confirmation_ratio` | ↑ | ~0.75 | 포착 품질 — 추출이 실제로 승인됨 |
| `decision_fidelity` | ↑ | n/a | 평가 케이스가 생기면 측정 |
| `correction_cost` | **↓** | 기준선 | 다음 세션부터 내려가는지 봄 |
| `drift_stability` | ↑ | n/a | 대체가 생기면 측정 |
| `traceability` | **= 1.0 필수** | **1.0** | 증거 없는 활성 규칙 0개 — 첫날부터 만족 |

> `traceability`가 1.0이 아니면 **무언가 증거 없이 활성화된 것**입니다 — 게이트 위반이므로 즉시
> 고치세요(증거를 붙이거나, 규칙을 비활성화). 나머지 지표는 *낮은 게 정상*입니다. 첫 세션의
> 목적은 높은 점수가 아니라 **올바른 곡선의 시작점**을 찍는 것입니다.

OpenCrab에서 운영한다면 동일 지표를 `opencrab_pack_qa` / `opencrab_project_run`으로 산출할 수
있습니다.

---

## 7단계 · 반복 (Iterate)

수렴은 **단조 누적**입니다 — 한 번에 끝나지 않고, 세션마다 조금씩 좁혀집니다
([수렴 모델 §4](../spec/06-convergence-model.md#4-왜-수렴하는가-직관)). 다음 세션의 가장 가성비
높은 행동:

1. **고친 순간을 다시 줍는다.** 매 세션 당신이 출력을 고친 곳이 곧 다음 증거입니다. `diff`가
   가장 강한 신호입니다([04 diff 마이닝](../skills/04-diff-mining.md)).
2. **빈 팩을 메운다.** 7개 팩 시드로 가는 길 — 결정 정책·암묵 휴리스틱·레드플래그·워크플로 등을
   2~3세션에 걸쳐 채웁니다([03 팩 카탈로그](../spec/03-pack-catalog.md)).
3. **평가 케이스 3개를 만든다.** "이 입력엔 이렇게 답해야 나답다"를 적어두면 `decision_fidelity`가
   측정되기 시작합니다([11 평가·드리프트](../skills/11-evaluation-drift.md)). L1의 마지막 조건입니다.
4. **`correction_cost`가 내려가는지 본다.** 이게 *가장 정직한 지표*입니다 — 에이전트가 점점 덜
   고쳐지는가. 이 곡선이 내려가고 `drift_stability`가 올라가면, 그게 **당신으로 수렴**한다는 증거입니다.

```
   세션 1   ── L0를 벗어나 사다리에 발을 올림 (이 문서)
   세션 2~3 ── 7개 팩 시드 + 평가 케이스 3개 → L1 Sketch 완성
   세션 N   ── coverage·fidelity 상승, correction_cost 하강 → L2 → L3 → …
                         └──────► 매 세션 다시 증거로 (루프)
```

> 변하는 자신을 두려워 마세요. 사람은 변하므로 `user.drift_history` 팩이 14개 중 하나로 존재합니다
> ([커널 §5](../spec/01-kernel-schema.md#5-14개-user-온톨로지-팩-정식-이름)). 수렴(L4)은 *완성*이
> 아니라 드리프트를 흡수하며 머무는 *유지* 상태입니다.

---

## 한 화면 체크리스트 (첫 세션)

- [ ] **(1) 프라이버시** — 민감 항목 `sensitivity`를 보수적으로 설정했는가.
- [ ] **(2) 증거** — 실제 세션에서 3~5개 `EvidenceItem`을 *행동 언어*로 줍고 출처를 남겼는가(G1·G4).
- [ ] **(3) 추출** — 각 후보에 타입·`evidence_refs`(≥1)·`confidence`·목적지 팩을 채웠는가.
- [ ] **(4) 확인** — 후보마다 여섯 액션 중 하나를 고르고 **스코프를 확정**했는가(G2·G3). 저신뢰
  후보엔 반례를 적었는가.
- [ ] **(5) 라우팅** — confirmed 후보를 2~3개 팩에 넣었는가. 민감 항목은 경계 규칙을 먼저 받았는가(G5·G6).
- [ ] **(6) 수렴** — `tools/convergence_report.py`로 지표를 확인했고 **`traceability`=1.0**인가.
- [ ] **(7) 반복** — 다음 세션 계획(빈 팩·평가 케이스 3개)을 적었는가.

---

## 관련 문서

- 어휘·라이프사이클·6 게이트·14 팩 → [01 커널 스키마](../spec/01-kernel-schema.md)
- 12단계 파이프라인 전체 계약 → [02 빌더 파이프라인](../spec/02-builder-pipeline.md)
- 14개 팩별 정의 → [03 팩 카탈로그](../spec/03-pack-catalog.md)
- 프라이버시·경계·권한 모델 → [04 프라이버시·경계](../spec/04-privacy-boundary.md)
- 평가·드리프트·평가 케이스 → [05 평가·드리프트](../spec/05-evaluation-drift.md)
- 수렴 지표·성숙도 사다리(L0–L4) → [06 수렴 모델](../spec/06-convergence-model.md)
- 통합 베이스 레코드(기계 계약) → [`schemas/record.base.schema.json`](../schemas/record.base.schema.json)
- 단계별 실행 스킬 → [01 증거 포착](../skills/01-evidence-capture.md) · [05 후보 추출](../skills/05-candidate-extraction.md) · [07 확인 게이트](../skills/07-confirmation-gate.md) · [08 팩 라우터](../skills/08-pack-router.md) · [09 프라이버시·경계](../skills/09-privacy-boundary.md)
