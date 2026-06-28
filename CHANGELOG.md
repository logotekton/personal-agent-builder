# Changelog

> **EN:** All notable changes to the Personal Agent Builder specification are recorded
> here. The format follows [Keep a Changelog](https://keepachangelog.com/) and the project
> adheres to semantic-ish spec versioning (`v0.MAJOR.MINOR`). **v0.3 is the first public
> release**: it reconciles every inconsistency found across the earlier private `v0.1`
> (13 skill packs) and `v0.2` (template-schema reinforcement) drafts into one canonical
> contract. The single source of truth is [`spec/01-kernel-schema.md`](./spec/01-kernel-schema.md);
> per-pack definitions live in [`spec/03-pack-catalog.md`](./spec/03-pack-catalog.md).

이 문서는 Personal Agent Builder **사양(spec)**의 주요 변경을 기록합니다. 형식은
[Keep a Changelog](https://keepachangelog.com/) 규칙을 따르며, 버전은 `v0.MAJOR.MINOR`
체계를 씁니다. 변경 항목은 `Added`(추가) · `Changed`(변경) · `Reconciled`(정합화) ·
`Deprecated`(폐기) · `Removed`(제거) · `Fixed`(수정)로 분류합니다.

용어의 정식 정의는 [커널 스키마](./spec/01-kernel-schema.md)와
[팩 카탈로그](./spec/03-pack-catalog.md)를 기준으로 삼습니다. 이 변경 기록은 그 정의를
요약·추적할 뿐, 새 어휘를 만들지 않습니다.

---

## [Unreleased]

### Added (예정)
- 더 많은 평가 케이스(EvaluationCase) 시드 및 다중 사용자 예제.
- 자동 채굴 도구(session_mining / diff_mining)의 참조 구현.
- 수렴 지표 대시보드(longitudinal convergence tracking).

> 변경 제안은 [`CONTRIBUTING.md`](./CONTRIBUTING.md) · 거버넌스는
> [`GOVERNANCE.md`](./GOVERNANCE.md)를 참고하세요.

---

## [0.3.0] — 2026-06-28

**첫 공개 릴리스.** `v0.1`/`v0.2`에서 누적된 불일치를 하나의 정식 계약(canonical contract)으로
정합화했습니다. 이번 릴리스의 핵심은 *새 기능*보다 **정합화(reconciliation)**입니다 — 흩어져
있던 어휘·필드·라우팅을 단일 기준으로 묶었습니다.

### Reconciled (정합화 — v0.1/v0.2 불일치 해소)

- **후보 타입 11 → 14, 라우팅 1:1 전수화.** `v0.1`은 후보 타입 11개 vs 라우팅 13개로
  불일치했습니다. v0.3은 **14개 후보 타입을 14개 `user.*` 팩에 1:1 전수(total) 매핑**하여
  라우터를 완전하게 만들었습니다. 신규 `IdentityRoleCandidate → user.identity_roles`(누락이었음),
  개명 `DomainSpecificCandidate → DomainOverlayCandidate`,
  `ProjectGoalCandidate → ProjectMemoryCandidate`.
  → [`spec/01-kernel-schema.md`](./spec/01-kernel-schema.md) §6.
- **통합 베이스 레코드: 필드 표류 해소.** `v0.1`은 `score`, `v0.2`는 `confidence`를 썼고,
  주장 본문은 팩마다 `claim`/`rule_statement`/`instruction`/`output_rule`로 갈렸습니다.
  v0.3은 **`score` → `confidence`(0..1)**, 그리고 위 본문 필드를 모두 **`statement`**
  하나로 통일했습니다(팩 문서는 표시용 별칭만 둘 수 있음). 모든 인스턴스 레코드는 단일
  베이스를 `allOf`로 확장합니다.
  → [`schemas/record.base.schema.json`](./schemas/record.base.schema.json),
  [`spec/01-kernel-schema.md`](./spec/01-kernel-schema.md) §7.
- **정식 팩 이름이 코드명을 대체.** 구 코드명(`pa.t03`, `t06`, `x12`, `.ba`, `pa.roles`,
  `pa.core` 등)을 **폐기**하고 14개 정식 이름(`user.identity_roles` …
  `user.drift_history`)으로 통일했습니다. 구 코드명은 추적용으로만 표에 병기됩니다.
  → [`spec/01-kernel-schema.md`](./spec/01-kernel-schema.md) §5,
  [`spec/03-pack-catalog.md`](./spec/03-pack-catalog.md).
- **컴파일러 입력에 `identity_roles` 추가.** 에이전트 컴파일러(skill 10)가 읽는 확정 슬라이스
  목록에 `user.identity_roles`를 포함시켜, 정체성·역할 맥락이 런타임 프로필 생성에 반영되도록
  했습니다(이전엔 누락).
  → [`skills/10-agent-compiler.md`](./skills/10-agent-compiler.md).
- **`review_status` / `sensitivity` enum 고정.** 검토 상태는
  `{pending, confirmed, rejected, narrowed, sensitive, deferred}`, 민감도는
  `{public, internal, sensitive, restricted}`로 고정. 게이트 G3(확정/축소/편집만 런타임
  활성)과 G5(민감 항목은 경계 규칙 선행)를 스키마로 강제합니다.

### Added (신규)

- **수렴 모델(convergence model).** "더 나아졌다"를 느낌이 아니라 6개 지표
  (coverage, confirmation_ratio, decision_fidelity, correction_cost, drift_stability,
  traceability)와 5단계 성숙도(L0 Seed → L4 Convergent)로 측정합니다. 참여 후크이자
  품질의 객관적 기준입니다.
  → [`spec/06-convergence-model.md`](./spec/06-convergence-model.md).
- **OpenCrab 9-space 크로스워크.** 노드 타입을 MetaOntology OS의 9개 공간
  (subject, resource, evidence, concept, claim, community, outcome, lever, policy)에
  매핑하는 `maps_to` 엣지와 정합 표를 추가했습니다.
  → [`spec/07-opencrab-9space-crosswalk.md`](./spec/07-opencrab-9space-crosswalk.md).
- **6개 품질 게이트(G1–G6) 명문화.** 증거 없는 주장 금지(G1), 스코프 없는 휴리스틱 금지(G2),
  대기 후보의 런타임 활성 금지(G3), 행동 기반 언어만(G4), 승격 전 프라이버시(G5),
  템플릿/인스턴스 분리(G6). 코드로도 강제 →
  [`tools/validate_packs.py`](./tools/validate_packs.py).
- **4개 팩 클래스 거버넌스 규칙.** skill(방법) · template(스키마) · instance(데이터) ·
  adapter(런타임)는 절대 섞지 않습니다.
  → [`spec/00-overview.md`](./spec/00-overview.md),
  [`spec/08-naming-and-ids.md`](./spec/08-naming-and-ids.md).
- **14개 `user.*` 팩 JSON Schema 전부.** 통합 베이스를 확장하는 14개 인스턴스 스키마와
  후보 스키마, 평가 케이스 스키마를 추가했습니다(draft 2020-12).
  → [`schemas/`](./schemas).

### Changed (변경)

- **명제 표현 강화.** 핵심 명제를 "포착하면 쌓여 **수렴**한다"로 통일하고, 라이프사이클을
  단일 spine(`raw_signal → … → runtime_activated`)으로 표준화했습니다.
- **언어 정책 명문화.** Korean 우선, 각 상위 문서는 짧은 영어 요약 블록(`> **EN:**`)으로
  시작합니다. 스키마·JSON 키·코드 식별자는 영어를 유지합니다.

### Deprecated (폐기)

- 필드: `score`(→ `confidence`), bare `claim` / `rule_statement` / `instruction` /
  `output_rule`(→ 모두 `statement`로 통일; 팩은 표시용 별칭만 허용).
- 코드명: `pa.t03`, `t06`, `t07`, `t08`, `t09`, `t10`, `t11`, `.ba`, `x12`, `x13`,
  `x14`, `pa.roles`, `pa.core`(→ 14개 `user.*` 정식 이름). 추적용 병기 외 사용 금지.
- 후보 타입명: `DomainSpecificCandidate`(→ `DomainOverlayCandidate`),
  `ProjectGoalCandidate`(→ `ProjectMemoryCandidate`).

---

## [0.2.0] — *historical (비공개 초안)*

> 템플릿 스키마 강화 단계. 공개되지 않은 내부 초안입니다.

- **Changed** — 14개 `user.*.template` 스키마의 형태(SHAPE)를 보강하고 필드 제약을
  강화했습니다(템플릿 팩 클래스의 기반 정립).
- **Changed** — 주장 본문 필드를 `confidence` 기반으로 전환하기 시작했으나,
  `v0.1`의 `score`와 혼재하여 **필드 표류**가 남았습니다(→ v0.3에서 정합화).
- **Known issue** — 후보 타입(11)과 라우팅 대상 팩(13) 수의 불일치가 미해결로 남음.

## [0.1.0] — *historical (비공개 초안)*

> 최초 초안. **13개 skill 팩**(빌더 파이프라인)을 정의한 방법론 중심 버전입니다.

- **Added** — 13개 빌더 스킬(`skill.pab.*`): evidence_capture … kernel_schema.
  암묵지를 팩으로 바꾸는 *방법*을 정의했습니다.
- **Added** — 증거 기반 라이프사이클과 노드/엣지 그래프 모델 초안.
- **Known issue** — 레코드 점수 필드로 `score`를 사용했고, 코드명(`pa.t03`, `t06`,
  `x12`, `.ba` 등)이 정식 이름 없이 혼용됨(→ v0.3에서 정합화).

---

[Unreleased]: https://github.com/logotekton/personal-agent-builder/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/logotekton/personal-agent-builder/releases/tag/v0.3.0
