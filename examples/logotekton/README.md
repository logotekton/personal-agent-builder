# examples/logotekton/ — 끝까지 동작하는 실제 인스턴스 예제 (Worked End-to-End Example)

> ⚙️ **성숙도 게이트 결함 수정 노트.** 이 문서 곳곳의 라이브 티어 표기(**L2 Working**)는 `coverage`를
> *시드폭*으로 게이팅하던 시점 기준입니다. 이후 게이트가 spec §2 정의(*엄격 ≥3 깊이*)를 쓰도록
> 수정되어 — "Working"을 폭으로 따는 자기기만을 막기 위해 — **현재 라이브 티어는 `L1 Sketch`**입니다
> (깊은 팩이 `evaluation_cases` 1개뿐: coverage 엄격 **0.07** / 시드폭 0.71, df 1.00). 다른 숫자
> (df·merge_rate·시드폭 전이)는 모두 불변이고, 남은 L2 빗장은 `coverage`(엄격 0.07→0.5) 하나입니다.
> 아래 본문의 "L2"는 이 노트를 전제로 읽어주세요.

> **EN:** This is the one fully worked example of Personal Agent Builder, for the subject
> **Logotekton** — the person who *founded the Personal Agent project* (the product's
> official model name is **Personal Agent**). Unlike the blank `templates/`, the records
> here are **real, confirmed, evidence-bound** records mined from actual AI-agent sessions,
> then run once through the full pipeline: evidence → candidates → scope → confirmation
> gate → routing into the `user.*` packs → compiled runtime adapter → evaluation and a
> convergence report. **9 of the 14 instance packs are seeded** (plus the evaluation cases —
> 10 packs by the convergence count) at maturity **L1 Sketch** (the gate keys on strict ≥3-depth
> coverage per spec §2; broad-but-shallow = Sketch — see the ⚙️ note above), after the data-engine wheel was
> turned **twice** on real records: `revolution-01` (merge actuator + the eval.004 correction →
> `decision_fidelity` 0.75→0.92) and `revolution-02` (a second turn → `decision_fidelity`
> 0.92→**1.00**, `coverage` 0.57→0.71, `merge_rate` 0.059→0.095 — and, honestly, the tier *held*
> at L2, with the report naming the two remaining L3 blockers). See
> [`revolution-01/README.md`](./revolution-01/README.md) and
> [`revolution-02/README.md`](./revolution-02/README.md). Spec ground truth:
> [`../../spec/01-kernel-schema.md`](../../spec/01-kernel-schema.md) and
> [`../../spec/03-pack-catalog.md`](../../spec/03-pack-catalog.md).

이 폴더는 시스템 전체를 **한 사람에게 실제로 한 번 적용한** 유일한 완성 예제입니다. 주체는
**Logotekton** — 이 프로젝트(공식 모델명 **Personal Agent**)를 시작한 사람입니다. 빈
[`templates/`](../../templates)와 달리, 여기 레코드는 **추측이 아니라 실제 세션에서 채굴되어
사람이 확인한, 증거에 묶인 진짜 인스턴스 레코드**입니다. `user.*` 팩이 어떻게 채워지고, 어떻게
하나의 런타임으로 컴파일되며, 수렴 지표가 실제로 어떤 값을 내는지를 처음부터 끝까지 보여줍니다.

> **창립자 귀속(Founder attribution).** Logotekton은 Personal Agent 프로젝트를 시작했습니다
> (*"Logotekton founded the Personal Agent project."*). 이 사실은 `user.identity_roles` 팩의
> `AttributionRecord` 타입으로 보존됩니다. 단, 귀속은 **증거 게이트의 예외가 아닙니다** —
> 다른 모든 레코드와 똑같이 ≥1개 `evidence_refs`(G1)와 비어 있지 않은 `scope`(G2)를 가지며,
> 다른 사용자의 인스턴스(`personal.<other>.*`)에 대한 어떤 권한도 부여하지 않습니다. 규칙
> 전문 → [`../../spec/08-naming-and-ids.md`](../../spec/08-naming-and-ids.md) §6.

## 무엇이 "실제"인가 (왜 templates와 다른가)

| | [`templates/`](../../templates) | **`examples/logotekton/` (여기)** |
|--|--|--|
| 팩 클래스 | 템플릿(SHAPE) — 빈 양식 | **인스턴스(DATA)** — `personal.logotekton.*` |
| 값 | 비어 있음, 예제는 주석 처리 | **채워진 실제 값** (확인된 레코드) |
| `review_status` | `pending`으로 시작 | 전부 `confirmed` (런타임 활성) |
| 출처 | 가상 | **실제 세션·교정·결정 기록에서 채굴** |
| 검증 시 | "데이터 없음"으로 분리 | "스키마 통과 + 게이트 충족" |

핵심: 템플릿은 *형태*를, 이 폴더는 *데이터*를 보여줍니다. 둘은 절대 섞이지 않습니다(게이트
G6). 여기 레코드의 ID는 모두 인스턴스 형식 `<subject>.<recordkind>.NNN`을 따릅니다 — 예:
`logotekton.role.001`, `logotekton.heuristic.001`
([`../../spec/08-naming-and-ids.md`](../../spec/08-naming-and-ids.md) §3).

## 파이프라인을 한 번 적용한 결과 (the spine, applied once)

이 예제는 [빌더 파이프라인](../../spec/02-builder-pipeline.md)을 Logotekton의 실제 증거에
**한 번 통과**시킨 스냅샷입니다. 라이프사이클의 각 단계가 이 폴더의 산출물로 남아 있습니다.

```
실제 세션/교정/diff ─► (S01) 증거 포착        EvidenceItem            current_session
                          │  G1: 모든 후보는 증거에 묶임
                          ▼
                  (S02–S05) 채굴·추출         CandidateAssertion ×N    (14개 타입 중 하나)
                          │  G4: 행동 언어로만 기술
                          ▼
                  (S06) 스코프 지정           "언제/어디서 참인가"      G2: 비어있지 않은 scope
                          │
                          ▼
                  (S07) 확인 게이트           사람 검토: confirm/edit/  ← 여기서 진짜가 됨
                          │                   narrow/reject/...         G3
                          ▼ confirmed/narrowed만
                  (S08) 팩 라우팅             user.* 1:1               ── instance-records.yaml
                          │  (민감 항목은 S09에서 BoundaryRule 먼저, G5)
                          ▼
                  (S10) 컴파일                확인 슬라이스 →           runtime-adapter.md
                          │                   AssistantProfile         (= Personal Agent)
                          ▼
                  (S11) 평가 & 드리프트       8개 지표 + 수렴 측정      convergence-report.md
                          └────────────► 루프: 새 증거로 재포착
```

게이트(G1–G6)·노드/엣지 어휘는 [커널 스키마](../../spec/01-kernel-schema.md)를, 단계별
입력/출력 계약은 [빌더 파이프라인](../../spec/02-builder-pipeline.md)을 그대로 따릅니다.

## 이 폴더의 파일

### 1) [`instance-records.yaml`](./instance-records.yaml) — 확인된 레코드 (`personal.logotekton.*`)

정식 팩 이름을 **키로 하는 단일 YAML 매핑**입니다. 현재 **14개 중 9개 인스턴스 팩이 시드**(+
평가케이스 팩 = 수렴 기준 10팩)되어 있고(revolution-01 에서 `boundary_authority`·`drift_history`,
revolution-02 에서 `artifact_policy`·`tool_stack` 추가), 각 레코드는 동일 이름의
[`user.*` 스키마](../../schemas)와 [통합 베이스 레코드](../../schemas/record.base.schema.json)를
동시에 만족합니다 ([팩 카탈로그](../../spec/03-pack-catalog.md)와 1:1 대응).

| # | 팩 (매핑 키) | 시드 | 담는 것 | id 토큰 | 스키마 |
|---|--------------|------|---------|---------|--------|
| 1 | `user.identity_roles` | ✅ 2건 (창립자 `AttributionRecord` 포함) | 역할·정체성·맥락 | `role` | [schema](../../schemas/user.identity_roles.schema.json) |
| 2 | `user.persona_core` | ✅ 2건 | 안정 선호/가치/우선순위 | `trait` | [schema](../../schemas/user.persona_core.schema.json) |
| 3 | `user.communication_style` | ✅ 2건 | 응답 형식/언어/구조 | `style` | [schema](../../schemas/user.communication_style.schema.json) |
| 4 | `user.artifact_policy` | ✅ 1건 (revolution-02 교정 산물: 보고 `next action` 필수 `ReviewArtifactRecord`) | 산출물 형식/리뷰 구조 | `artifact` | [schema](../../schemas/user.artifact_policy.schema.json) |
| 5 | `user.decision_policy` | ✅ 1건 | 우선순위·승인/거부 | `decision` | [schema](../../schemas/user.decision_policy.schema.json) |
| 6 | `user.tacit_heuristics` | ✅ 1건 (rev-01+rev-02 **2회 병합**: `repetition_count`=3) | 암묵 판단 규칙 | `heuristic` | [schema](../../schemas/user.tacit_heuristics.schema.json) |
| 10 | `user.tool_stack` | ✅ 1건 (revolution-02 시드: 결정론적 도구 선호 `ToolPreferenceRecord`) | 도구 선택/사용/회피 | `tool` | [schema](../../schemas/user.tool_stack.schema.json) |
| 11 | `user.boundary_authority` | ✅ 1건 (revolution-01 교정 산물: 외부메일 `ConfirmationRuleRecord`) | 경계·권한·확인 규칙 | `boundary` | [schema](../../schemas/user.boundary_authority.schema.json) |
| 13 | `user.evaluation_cases` | ✅ 6건 (→ 별도 파일 `evaluation-cases.yaml`; 전부 pass) | 충실도 테스트 케이스 | `evalcase` | [schema](../../schemas/user.evaluation_cases.schema.json) |
| 14 | `user.drift_history` | ✅ 2건 (→ 별도 파일 `drift-history.yaml`; 교정 `DriftRecord` ×2) | 변경·대체 이력 | `drift` | [schema](../../schemas/user.drift_history.schema.json) |
| 7–9, 12 | `red_flags`, `workflow_playbooks`, `domain_overlays`, `memory_project_graph` | ⬜ 미시드 | (아직 증거 없음 — 우겨넣지 않음, G1) | — | [schemas](../../schemas) |

> 4개 팩이 아직 비어 있는 것은 **버그가 아니라 상태**입니다. 증거가 없는 팩을 가짜로 채우지 않는
> 것이 이 프로젝트의 G1 원칙입니다 — revolution-02 는 `coverage`를 0.8 로 만들려 얇은 팩을
> 우겨넣는 것을 **의도적으로 거부**했습니다. 현재 위치(**L2 Working** — 데이터-엔진을 두 바퀴
> 돌렸고, revolution-02 에서 `decision_fidelity`는 1.0 에 닿았으나 성숙도는 L2 *그대로*)와
> *그 다음 한 수*는 아래 [수렴 리포트](#4-convergence-reportmd--측정된-수렴)와
> [`revolution-01/README.md`](./revolution-01/README.md) ·
> [`revolution-02/README.md`](./revolution-02/README.md)가 숫자로 보여줍니다.

### 2) [`evaluation-cases.yaml`](./evaluation-cases.yaml) — 충실도 테스트 케이스 (`user.evaluation_cases`)

6개의 `EvaluationCaseRecord`(입력 과제·기대 행동·불가 행동·루브릭). 게이트별 회귀를 잡습니다:
naming 준수, 증거 추적성(G1), 경계 확인(G5·`boundary_compliance`), 산출물 형식(`artifact_fit`),
스코프 규율(G2), 드리프트 처리. [수렴 모델](../../spec/06-convergence-model.md)의
`decision_fidelity` 입력입니다.

### 3) [`runtime-adapter.md`](./runtime-adapter.md) — 컴파일된 런타임 (the Personal Agent)

확인된 슬라이스만 골라([에이전트 컴파일러](../../skills/10-agent-compiler.md), S10)
`AssistantProfile`로 묶은 결과 — 즉 Logotekton의 **Personal Agent**입니다. 어떤 팩의 어떤
레코드가 활성화됐는지, 무엇이 `pending`이라 **컴파일에서 제외**됐는지(G3), 외부 통신·비가역
행동 앞에서 어떤 `ask_confirm` 경계가 걸리는지(G5)를 보여줍니다. 팩 클래스로는 어댑터 팩
(`personal.logotekton.runtime_adapter`)에 해당하며, 원본 인스턴스 팩과 섞이지 않습니다.

### 4) [`convergence-report.md`](./convergence-report.md) — 측정된 수렴

위 인스턴스 집합과 `evaluation-cases.yaml`·`drift-history.yaml`을 입력으로,
[수렴 모델](../../spec/06-convergence-model.md)의 6개 지표(`coverage`, `confirmation_ratio`,
`decision_fidelity`, `correction_cost`, `drift_stability`, `traceability`)와 현재 성숙도 단계
(L0–L4)를 계산한 결과입니다. 이 문서는 **T0 베이스라인**(L0)을 보존하며, 그 §5가 지목한 다음
한 수를 실행한 **T1 결과(L2 Working)**는 [`revolution-01/README.md`](./revolution-01/README.md)에
있습니다. "에이전트가 점점 나처럼 된다"가 느낌이 아니라 **숫자**라는 점을 실제 데이터로
보여줍니다. 같은 산출은 [`../../tools/`](../../tools)의 검증·수렴 스크립트나
OpenCrab의 `opencrab_pack_qa`로 재현할 수 있습니다.

### 5) [`revolution-01/`](./revolution-01/) — 데이터-엔진을 한 바퀴 돌린 기록

merge actuator([`../../tools/pab_merge.py`](../../tools/pab_merge.py)) + eval.004 교정 + DriftRecord로
바퀴를 실제로 한 번 돌려 **L0 → L2**로 오른 T0→T1 측정과 재현 명령. 카파시 리뷰가 지적한
"바퀴가 한 번도 안 돌았다"에 대한 직접 응답입니다.

### 6) [`revolution-02/`](./revolution-02/) — 한 번 더 돌리며 안전성을 시험한 기록

바퀴를 두 번째로 돌린 T1→T2 측정. 네 판정을 모두 밟고(`merge`/`insert`/`insert`/**`conflict→surface`**),
*확인된* 후보가 actuator 에 의해 차단되어 사람 검토로 surface 되는 **안전 속성**을 증명합니다.
정직한 헤드라인: `decision_fidelity` 0.92→**1.00**, `coverage` 0.57→0.71 인데도 성숙도는 **L2 그대로** —
리포트가 남은 L3 빗장 둘(`coverage≥0.8`, `correction_cost`=NA)을 정확히 가리킵니다. 한 바퀴가 가짜
도약 대신 *다음 병목*을 숫자 하나로 좁혀 보여주는 사례. (후속 §6: `result.edit_fraction` 계측으로
`correction_cost` NA→0.08 → 남은 L3 빗장이 `coverage`<0.8 **하나**로 좁혀짐.)

## 읽는 순서 (추천)

1. **[`instance-records.yaml`](./instance-records.yaml)** — 시드된 9개 팩의 확인된 레코드.
   `user.identity_roles`의 창립자 귀속 레코드가 다른 모든 팩의 기준점입니다. 가장 흥미로운
   암묵지는 `user.tacit_heuristics`(교정·diff에서 나온 "이건 이렇게" 규칙; 3개 세션에서 재유도
   → rev-01·rev-02 **2회 병합**으로 `repetition_count`=3)입니다.
2. **[`evaluation-cases.yaml`](./evaluation-cases.yaml)** — 무엇을 "제대로"로 보는가. 기대/불가
   행동으로 충실도와 경계 준수를 못박습니다.
3. **[`runtime-adapter.md`](./runtime-adapter.md)** — 위 레코드들이 하나의 통제된 프로필로
   합쳐진 모습.
4. **[`convergence-report.md`](./convergence-report.md)** — T0 베이스라인(L0), 그리고 그것이
   예측한 다음 한 수.
5. **[`revolution-01/README.md`](./revolution-01/README.md)** — 그 한 수를 실행해 바퀴를 돌린
   T1 결과(L0→L2), 재현 명령 포함.
6. **[`revolution-02/README.md`](./revolution-02/README.md)** — 바퀴를 한 번 더 돌린 T1→T2.
   네 판정 전부 + 충돌 surface(안전), 그리고 *성숙도는 L2 그대로*인 정직한 한 칸.

> 이 예제는 한 시점의 **스냅샷**입니다. 사람은 변하므로 수렴은 한 번 도달하고 끝나는 점이
> 아니라 드리프트를 흡수하며 머무는 상태이고, 그래서 `user.drift_history`가 14개 팩 중 하나로
> 설계돼 있습니다([수렴 모델](../../spec/06-convergence-model.md) §3).

## 인접 폴더

- [`../../templates/`](../../templates) — 당신이 직접 시작할 **빈 채우기 양식** +
  [QUICKSTART](../../templates/QUICKSTART.md). 이 예제는 그 양식을 실제로 채운 모습입니다.
- [`../../schemas/`](../../schemas) — 여기 레코드가 검증되는 `user.*` JSON Schema +
  [통합 베이스 레코드](../../schemas/record.base.schema.json).
- [`../../skills/`](../../skills) — 증거를 후보로 바꾸고 확인·라우팅·컴파일하는 *방법*(이
  예제를 만든 절차).
- [`../../spec/`](../../spec) — 정규 사양. 어휘는 [01 커널 스키마](../../spec/01-kernel-schema.md),
  파이프라인은 [02](../../spec/02-builder-pipeline.md), 팩 정의는
  [03 팩 카탈로그](../../spec/03-pack-catalog.md).

> 이름 규칙: 이 문서는 정식 팩 이름만 씁니다. 산출물은 **Personal Agent**, 플랫폼은
> **OpenCrab**으로 부릅니다. 구 코드명(`pa.t03`, `t06`, `x12`, `.ba` 등)은 더 이상 쓰지 않으며,
> 이전표는 [`../../spec/08-naming-and-ids.md`](../../spec/08-naming-and-ids.md) §5에만 있습니다.
