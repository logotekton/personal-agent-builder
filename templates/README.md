# templates/ — 빈 채우기 템플릿 색인 (Fill-in Templates Index)

> **EN:** This folder holds 14 blank fill-in YAML templates — one per `user.*` ontology
> pack — that a **new** person copies to start their own evidence-bound **self-map** (the
> material a Personal Agent later compiles from; the map comes first). Each template is
> the unified base record (the same fields every instance record must have) with **empty
> values**, **Korean inline comments** explaining every field, and **one commented-out
> example** showing a filled record. Templates are the *shape* you fill in by hand or with a
> builder skill; the machine-checkable contract is the JSON Schema in
> [`../schemas/`](../schemas). First time here? Start with
> [`QUICKSTART.md`](./QUICKSTART.md). Templates never hold live records (Gate G6).

이 폴더는 **새 사용자가 자기 증거 기반 자기지도(self-map)를 시작하기 위해 복사하는** 14개의 빈 YAML
템플릿입니다 — 14개 `user.*` 온톨로지 팩마다 하나씩(그 지도가 나중에 Personal Agent로 컴파일됨, 지도가 먼저). 각 템플릿은 통합 베이스
레코드([`../spec/01-kernel-schema.md`](../spec/01-kernel-schema.md) §7)의 필드를 **빈 값**으로
나열하고, 각 필드 옆에 **무엇을 어떻게 채우는지**를 한국어 주석으로 달고, **주석 처리된 예제
레코드 1개**로 "완성된 모습"을 보여줍니다. 추측으로 채우는 게 아니라, 실제 세션·교정·결정에서
나온 증거에 묶어 채웁니다 — 빈 칸을 다 채우면 그게 곧 인스턴스 레코드입니다.

## 왜 별도 폴더인가 (스킬·스키마와의 차이)

[Canonical Design Contract](../spec/01-kernel-schema.md)는 네 개의 팩 계층을 **절대 섞지
말라**고 규정합니다(거버넌스 규칙). 이 폴더는 그중 **템플릿 계층(형태, SHAPE)**입니다:

| 계층 | 무엇 | 어디 |
|------|------|------|
| 스킬(HOW, 방법) | 증거를 후보로 바꾸는 운영 절차 | [`../skills/`](../skills) |
| **템플릿(SHAPE, 형태)** | **사람이 손으로 채우는 빈 양식** | **여기 (`templates/`)** |
| 인스턴스(DATA, 데이터) | 확인된 실제 레코드 | 당신의 비공개 인스턴스 / [`../examples/logotekton/`](../examples/logotekton) |
| 스키마(검증) | 기계 검증용 JSON Schema | [`../schemas/`](../schemas) |

핵심: **템플릿은 라이브 레코드를 담지 않습니다(게이트 G6).** 템플릿의 값은 항상 비어 있고,
예제는 항상 주석 처리되어 있습니다. 채워진 진짜 레코드는 이 폴더가 아니라 당신의 인스턴스
팩(`personal.<subject>.*`)으로 갑니다. 그래서 `validate_packs.py`로 이 폴더를 검사하면 템플릿은
"데이터 없음"으로, 인스턴스는 "스키마 통과"로 분리되어야 정상입니다.

## 14개 템플릿 파일 (팩 순서)

각 파일은 동일 번호의 `user.*` 팩 스키마와 1:1로 대응합니다. `id`의 레코드 종류 토큰
(`role`, `trait`, …)은 인스턴스 id 형식 `<subject>.<recordkind>.NNN`
([`../spec/08-naming-and-ids.md`](../spec/08-naming-and-ids.md))과 맞춥니다.

| # | 템플릿 | 채우는 팩 | 베이스 외 핵심 필드(예) | id 종류 토큰 | 스키마 |
|---|--------|-----------|--------------------------|--------------|--------|
| 1 | [`user.identity_roles.template.yaml`](./user.identity_roles.template.yaml) | `user.identity_roles` | `role_name`, `role_kind`, `active_status` | `role` | [schema](../schemas/user.identity_roles.schema.json) |
| 2 | [`user.persona_core.template.yaml`](./user.persona_core.template.yaml) | `user.persona_core` | `direction`, `trait_dimension`, `stability` | `trait` | [schema](../schemas/user.persona_core.schema.json) |
| 3 | [`user.communication_style.template.yaml`](./user.communication_style.template.yaml) | `user.communication_style` | `format_target`, `tone_register`, `enforcement` | `style` | [schema](../schemas/user.communication_style.schema.json) |
| 4 | [`user.artifact_policy.template.yaml`](./user.artifact_policy.template.yaml) | `user.artifact_policy` | 선호 산출물 형태/포맷 규칙 | `artifact` | [schema](../schemas/user.artifact_policy.schema.json) |
| 5 | [`user.decision_policy.template.yaml`](./user.decision_policy.template.yaml) | `user.decision_policy` | 우선순위·트레이드오프·승인/거부 | `decision` | [schema](../schemas/user.decision_policy.schema.json) |
| 6 | [`user.tacit_heuristics.template.yaml`](./user.tacit_heuristics.template.yaml) | `user.tacit_heuristics` | 암묵 판단 규칙·반례 | `heuristic` | [schema](../schemas/user.tacit_heuristics.schema.json) |
| 7 | [`user.red_flags.template.yaml`](./user.red_flags.template.yaml) | `user.red_flags` | 위험 신호·트리거·대응 | `redflag` | [schema](../schemas/user.red_flags.schema.json) |
| 8 | [`user.workflow_playbooks.template.yaml`](./user.workflow_playbooks.template.yaml) | `user.workflow_playbooks` | 반복 단계 시퀀스·산출물 | `workflow` | [schema](../schemas/user.workflow_playbooks.schema.json) |
| 9 | [`user.domain_overlays.template.yaml`](./user.domain_overlays.template.yaml) | `user.domain_overlays` | 도메인·주의 패턴·용어 | `domain` | [schema](../schemas/user.domain_overlays.schema.json) |
| 10 | [`user.tool_stack.template.yaml`](./user.tool_stack.template.yaml) | `user.tool_stack` | 도구 선택·사용 패턴 | `tool` | [schema](../schemas/user.tool_stack.schema.json) |
| 11 | [`user.boundary_authority.template.yaml`](./user.boundary_authority.template.yaml) | `user.boundary_authority` | 경계 범주·권한 레벨·확인 규칙 | `boundary` | [schema](../schemas/user.boundary_authority.schema.json) |
| 12 | [`user.memory_project_graph.template.yaml`](./user.memory_project_graph.template.yaml) | `user.memory_project_graph` | 프로젝트·목표·메모리 링크 | `project` | [schema](../schemas/user.memory_project_graph.schema.json) |
| 13 | [`user.evaluation_cases.template.yaml`](./user.evaluation_cases.template.yaml) | `user.evaluation_cases` | 입력 과제·기대/불가 행동·루브릭 | `evalcase` | [schema](../schemas/user.evaluation_cases.schema.json) |
| 14 | [`user.drift_history.template.yaml`](./user.drift_history.template.yaml) | `user.drift_history` | 대체·감쇠·갱신 이력 | `drift` | [schema](../schemas/user.drift_history.schema.json) |

> 한 번에 전부 보고 싶다면: 위 14개 파일은 모두 한 묶음
> [`_ALL_TEMPLATES.yaml`](./_ALL_TEMPLATES.yaml)에도 `--- # user.<name>` 구획으로 들어
> 있습니다(복사-시작 번들). 개별 파일은 그 번들을 팩별로 분리한 것입니다.

> 이름 규칙: 14개 정식 팩 이름만 씁니다. 구 코드명(`pa.t03`, `t06`, `x12`, `.ba` 등)은 더
> 이상 쓰지 않으며, 이전표는 [`../spec/08-naming-and-ids.md`](../spec/08-naming-and-ids.md)에만
> 있습니다.

## 모든 템플릿에 공통인 베이스 필드

14개 템플릿은 모두 통합 베이스 레코드를 확장하므로, 어느 파일을 열어도 아래 **필수 필드**가
먼저 나오고 그다음 팩 고유 필드가 옵니다(기계 검증:
[`../schemas/record.base.schema.json`](../schemas/record.base.schema.json)).

| 필드 | 채우는 법 | 게이트 |
|------|-----------|--------|
| `id` | `<subject>.<recordkind>.NNN` (예: `jane.role.001`). subject는 당신의 핸들. | — |
| `record_type` | 해당 팩의 `record_type` enum 중 하나 (각 템플릿 주석에 목록). | — |
| `label` | 한 줄 사람용 이름. | — |
| `statement` | 행동 언어로 쓴 스코프된 규칙/주장. 추측 심리가 아니라 **관찰된 행동**. | G4 |
| `evidence_refs` | ≥1개 `EvidenceItem` 참조. 증거 없으면 채우지 마세요. | G1 |
| `confidence` | 0.0–1.0. **0.7 미만이면 `counterexamples` 필수.** | — |
| `scope` | *언제/어디서* 참인가. 비워둘 수 없음("항상 참"은 금지). | G2 |
| `review_status` | `pending`로 시작 → 검토 후 `confirmed`/`narrowed`/… | G3 |
| `sensitivity` | `public`/`internal`/`sensitive`/`restricted`. sensitive·restricted는 경계 규칙 먼저. | G5 |
| `created_at`, `updated_at` | ISO-8601 date-time. | — |

선택 필드(`aliases`, `priority_weight`, `counterexamples`, `exception_rules`,
`related_records`, `supersedes`, `linked_projects`, `linked_domains`, `examples`,
`anti_examples`)는 필요할 때만 채우되, 위 검증 규칙(특히 G1·G2·G4·G5)은 항상 지킵니다.

## 빠른 사용법 (3단계)

자세한 단계별 가이드는 [`QUICKSTART.md`](./QUICKSTART.md)에 있습니다. 요약:

1. **복사** — 시작하려는 팩의 `*.template.yaml`을 당신의 인스턴스 폴더로 복사하고
   `template`을 당신 핸들로 바꿉니다 (예: `personal.jane/identity_roles.yaml`).
2. **채움** — 주석을 따라 베이스 필드부터 채웁니다. 각 항목은 실제 증거에 묶고(G1), 스코프를
   주고(G2), 행동 언어로 씁니다(G4). 자신 없으면 `review_status: pending`으로 두세요.
3. **검증** — [`../tools/`](../tools)의 검증 스크립트로 스키마·게이트를 확인합니다. 확인된
   항목만 런타임으로 컴파일됩니다(G3).

처음 시작하기 좋은 순서: `identity_roles` → `persona_core` → `communication_style`. 이 세 팩만
채워도 [수렴 모델](../spec/06-convergence-model.md)의 **L1(Sketch)**로 가는 첫발입니다.

## 인접 폴더

- [`QUICKSTART.md`](./QUICKSTART.md) — 첫 세션부터 템플릿을 채워 첫 인스턴스 팩을 만드는 안내.
- [`../schemas/`](../schemas) — 이 템플릿들이 검증되는 14개 `user.*` JSON Schema +
  [통합 베이스 레코드](../schemas/record.base.schema.json).
- [`../spec/03-pack-catalog.md`](../spec/03-pack-catalog.md) — 각 팩의 목적·레코드 타입·예제.
- [`../skills/`](../skills) — 증거에서 후보를 추출·확인·라우팅하는 *방법*(이 빈 양식을 채우는 절차).
- [`../examples/logotekton/`](../examples/logotekton) — 끝까지 채워진 실제 인스턴스 예제.
