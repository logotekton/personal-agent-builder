# spec/ — 사양 색인 (Specification Index)

> **EN:** This is the index for the Personal Agent Builder specification (v0.3). The twelve
> documents below (`00`–`10` and `12`) are the normative spec: the kernel schema, the builder
> pipeline, the pack catalog, the privacy/authority model, the evaluation+drift loop, the
> convergence model, the OpenCrab 9-space crosswalk, the naming/ID policy, the trigger
> (activation) model, dedup & merge, and the confirmation policy (`12`, which deepens the
> human-review decision rule of `07`/`09`). New readers
> should start at [`00-overview.md`](./00-overview.md). The kernel schema
> ([`01`](./01-kernel-schema.md)) is the single source of vocabulary every other file uses.

이 폴더는 Personal Agent Builder의 **정규 사양**입니다. 아래 12개 문서가 시스템의 어휘·계약·
정책을 고정합니다. 다른 폴더(`../schemas`, `../skills`, `../templates`)는 모두 이 사양을
기준으로 삼습니다. 큰 그림과 읽는 순서는 [`00-overview.md`](./00-overview.md)에 있습니다.
(번호 `11`은 결번 — 구 `spec/11`이 `skills/14-host-binding.md`로 이전되며 비었고, 새 확인
정책은 `07`/`09`의 심화라 `12`로 이어 붙였습니다.)

## 문서 목록 (00 → 10, 12)

| 문서 | 한 줄 설명 | EN one-liner |
|------|-----------|--------------|
| [`00-overview.md`](./00-overview.md) | 시스템 개요 — 4개 팩 클래스, 파이프라인, 읽는 순서. 여기서 시작. | System overview, four pack classes, and the read order — start here. |
| [`01-kernel-schema.md`](./01-kernel-schema.md) | 커널 스키마 — 노드/엣지 타입, 라이프사이클, 6개 게이트(G1–G6), 통합 베이스 레코드, 후보↔팩 라우팅(1:1, 전수). 모든 어휘의 출처. | The kernel schema: node/edge types, lifecycle, six gates, the base record, and the 1:1 candidate↔pack routing — the source of all vocabulary. |
| [`02-builder-pipeline.md`](./02-builder-pipeline.md) | 빌더 파이프라인 — 증거에서 컴파일까지 12단계와 13개 빌더 스킬이 어떻게 연결되는가. | The 12-step evidence-bound pipeline and how the 13 builder skills wire into it. |
| [`03-pack-catalog.md`](./03-pack-catalog.md) | 팩 카탈로그 — 14개 `user.*` 온톨로지 팩의 목적·레코드 타입·라우팅 후보·스키마 링크. | The catalog of all 14 user ontology packs: purpose, record types, routing candidate, and schema link. |
| [`04-privacy-boundary.md`](./04-privacy-boundary.md) | 프라이버시·경계 — 6개 경계 범주, 8단 권한 사다리, 기본 안전 정책(외부 노출·비가역 행동 전 확인). | The privacy/authority model: six boundary categories, the eight-rung authority ladder, and the default safe policy. |
| [`05-evaluation-drift.md`](./05-evaluation-drift.md) | 평가·드리프트 — 8개 충실도 지표, 재현 가능한 평가 케이스, 실패→후보/경계/드리프트 루프. | Eight evaluation metrics, reproducible evaluation cases, and the failure→drift loop. |
| [`06-convergence-model.md`](./06-convergence-model.md) | 수렴 모델 — 6개 수렴 지표와 5단계 성숙도(L0–L4). 측정 가능한 참여 훅. | The six convergence indices and five maturity tiers (L0–L4) — the measurable participation hook. |
| [`07-opencrab-9space-crosswalk.md`](./07-opencrab-9space-crosswalk.md) | 9-space 크로스워크 — PA 노드를 OpenCrab MetaOntology OS의 9공간 정식 문법으로 사상. | Maps every PA node into OpenCrab's canonical nine-space grammar. |
| [`08-naming-and-ids.md`](./08-naming-and-ids.md) | 네이밍·ID 정책 — Personal Agent vs OpenCrab, `system_pack_id` vs `display_name`, 인스턴스 ID 형식, 구 코드명→정식 이름 이전표. | The naming/ID policy: product vs platform, pack ids vs display names, instance id format, and the codename migration table. |
| [`09-triggers.md`](./09-triggers.md) | 트리거 — 스킬 발화 조건(2계층: 앰비언트 포착 + 단일 확인), 호스트 훅 매핑(SessionStart/UserPromptSubmit/PostToolUse/Stop/Cron), 스테이징/승격 경계, auto-confirm 정책. | The trigger (activation) model: ambient capture + single confirmation, host-hook mapping, the staging↔promotion boundary, and the auto-confirm policy. |
| [`10-dedup-and-merge.md`](./10-dedup-and-merge.md) | 중복 억제·병합 — 레코드는 append가 아니라 upsert; 확인 게이트의 dedup judge(novel/duplicate/refinement/conflict → confirm/merge/supersede); `redundancy_ratio`·`pack_cardinality`·`merge_rate` 지표. | Dedup & merge: records are upserted not appended; a dedup judge at the gate; redundancy/cardinality/merge-rate signals. |
| [`12-confirmation-policy.md`](./12-confirmation-policy.md) | 확인 정책 — 승격에 사람 확인이 *언제* 필요한가의 결정 규칙. regret=impact×(1−confidence), 네 결정 축(임팩트 티어·신뢰도·민감도·dedup 판정), 4계층 임계 설정(보수 기본→사용자 다이얼→`target_error_rate` 섀도 캘리브레이션→성숙도 게이트). `07`/`09` 심화. | Confirmation policy: when promotion needs a human. Regret-minimizing default-deny with four decision axes and four-layer threshold calibration (Karpathy shadow mode / autonomy slider). Deepens `07`/`09`. |

## 인접 폴더

- [`../schemas/`](../schemas) — 14개 팩 + 통합 베이스 레코드의 JSON Schema(기계 검증용).
  베이스: [`../schemas/record.base.schema.json`](../schemas/record.base.schema.json).
- [`../skills/`](../skills) — 13개 빌더 스킬 문서(*방법*). 파이프라인 매핑은 [`02`](./02-builder-pipeline.md).
- [`../templates/`](../templates) — 새 사용자용 빈 채우기 템플릿 + [QUICKSTART](../templates/QUICKSTART.md).
- [`../tools/`](../tools) — 스키마 검증·수렴 지표 계산 스크립트.

> 규칙: 이 사양은 [Canonical Design Contract(v0.3)]를 따릅니다. 정식 이름(14개 `user.*` 팩,
> 14개 후보 타입)만 사용하며, 구 코드명(`pa.t03`, `t06`, `x12`, `.ba` 등)은 [`08`](./08-naming-and-ids.md)의
> 이전표에서만 언급됩니다.
