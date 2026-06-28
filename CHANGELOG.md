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

### Karpathy review 후속 — 자기기만 방지 (실행 게이트 강화)
- **#3 채점 무결성 게이트 — "보상이 검증이 아니라 기록"의 부분 해소.** `decision_fidelity`가 읽는
  `result.status`가 *사람이 친 자유 문자열*이라 아무도 루브릭과 대조하지 않던 문제에 대해,
  [`validate_packs.py`](./tools/validate_packs.py)가 평가 케이스의 **기록 내부 정합성**을 강제하도록
  했습니다: 가중치 합=1 · `status=pass`면 `score≥pass_threshold` · `unacceptable_fired`면 status=`fail`
  (하드페일) · `judge=llm_judge`면 `judge_config`(model·temperature) 필수. 스키마에 `judge_config`·
  `result.unacceptable_fired` 추가. logotekton 예제는 모두 정합이라 **42 PASS 불변**. 테스트 +6(46개).
  *정직한 한계:* 프로필을 실제 실행해 status를 도출하는 **라이브 채점기**는 컴파일된 런타임(현 스텁)이
  필요해 별개이며, 이 게이트는 그 전제인 "기록이 자기 루브릭과 모순되지 않음"만 보장합니다.
  → [`spec/05`](./spec/05-evaluation-drift.md), [`schemas/user.evaluation_cases.schema.json`](./schemas/user.evaluation_cases.schema.json).
- **#4 자율성 자기인증 차단 — `human_confirmation_ratio`.** spec/12 §4.4가 정의만 해 둔 *사람 게이트 흐름만
  세는* 비율을 [`convergence_report.py`](./tools/convergence_report.py)에 구현하고, **성숙도 L2 게이트가
  `confirmation_ratio` 대신 이 값을 쓰도록** 바꿨습니다(베이스 레코드 `auto_confirmed` 플래그 → 자동확정
  승격은 분자·분모에서 제외). auto-confirm을 켜도 시스템이 *제 성숙도를 자기인증*(목줄이 스스로 풀림)하지
  못합니다. auto-confirm 0건인 logotekton 예제는 값·티어 불변(L2). 회귀 테스트가 "confirmation_ratio 0.75는
  통과하나 human_confirmation_ratio 0.30은 L2를 막음"을 잠금. → [`spec/06`](./spec/06-convergence-model.md)·
  [`spec/12 §4.4`](./spec/12-confirmation-policy.md), [`schemas/record.base.schema.json`](./schemas/record.base.schema.json).

### Added
- **`result.edit_fraction`(0..1) — `correction_cost` 계측.** `user.evaluation_cases`의 `result`에
  작업별 사용자 편집 비율 필드를 형식화해, `correction_cost` 지표가 NA에서 *측정값*으로 전환됩니다
  (미측정 NA는 L3/L4 게이트를 통과하지 못함). → [`spec/05-evaluation-drift.md`](./spec/05-evaluation-drift.md),
  [`schemas/user.evaluation_cases.schema.json`](./schemas/user.evaluation_cases.schema.json).
- **dedup/merge actuator + 데이터-엔진 플라이휠.** 결정론적 dedup judge + upsert/supersede/surface
  액추에이터([`tools/pab_merge.py`](./tools/pab_merge.py))와, 실제 레코드 위에서 바퀴를 두 번 돌린
  worked example([`examples/logotekton/revolution-01`](./examples/logotekton/revolution-01/) ·
  [`revolution-02`](./examples/logotekton/revolution-02/), `.pre` 재현 픽스처 포함).
- **`spec/01` §9 프라이버시·권한 모델 요약** — 다른 문서들이 가리키던 "커널 §9"에 실재하는 섹션을
  부여(정식 정의는 spec/04). §7 베이스 레코드에 병합 필드 `canonical_key`·`repetition_count`·
  `merge_history`(선택) 명시.
- **회귀 테스트 스위트** [`tests/`](./tests/README.md) — 도구가 산출하는 *모든 숫자*(canonical_key·
  네 판정·6 수렴 지표·`merge_rate`·게이트·예제 42 PASS)를 잠그는 stdlib 36 테스트. **CI**
  ([`.github/workflows/ci.yml`](./.github/workflows/ci.yml))가 push·PR마다 게이트+테스트 실행.
- **문서 링크 무결성 게이트** [`tools/check_anchors.py`](./tools/check_anchors.py) — 저장소 전체
  교차문서 Markdown 링크·`#앵커`가 실재 헤딩(GitHub 슬러그)으로 해소되는지 검사하는 stdlib 도구.
  CI 게이트로 편입(broken≠0이면 빌드 실패)되어, 헤딩 rename이 참조를 조용히 끊는 것을 막습니다.
  (이 도구가 skills/08의 깨진 자기 앵커 3건을 발견 — 아래 Fixed.)
- **문서 명령 무결성 게이트** [`tools/check_commands.py`](./tools/check_commands.py) — 문서에 적힌
  이 저장소 도구의 안전·읽기전용 명령(validate/convergence/dedup/check_anchors)을 실제로 실행해
  하나라도 실패하면 빌드를 깨는 stdlib 도구. "**모든 figure는 명령으로 재현된다**"는 명제를 *실행 가능한
  게이트*로 만들어, CLI 시그니처가 바뀌어 문서의 명령이 조용히 깨지는 것을 막습니다(아래 it.13 회귀
  클래스). 플레이스홀더·부수효과(`--apply`/`--out`)·테스트 스위트·버전 의존 `python -c` 점검(예:
  3.11+ `tomllib`)은 범위 밖으로 건너뜁니다. 테스트는 38개로 늘어 두 가드(앵커·명령)와 디렉터리-형
  CLI까지 잠급니다.

### Reconciled (정합화)
- **14개 빌더 스킬을 병합 층(spec/10)과 정합화.** 확인 게이트의 검토 액션은 *여섯 기본 + dedup judge의
  merge/supersede*이고, `conflict`는 사람에게 노출(자동 적용 금지, G3/G5 2차 게이트)임을 skills
  `02·04·05·06·07·08·09·10·11·12·13`에 일관 반영. skill 09는 빌드타임(dedup conflict→surface)과
  런타임(더 엄격한 규칙 합성)을 분리. skill 01은 교차세션 재유도가 *중복이 아니라 병합 연료*임을 명확화.
- **빌더 파이프라인 문서(spec/02)를 병합 층과 정합화.** S07 확인 게이트 기술에 dedup judge의 추천 액션
  (`duplicate→merge`·`refinement→supersede`)과 `conflict→surface`(자동 적용 금지, 2차 관문)를 명시하고,
  다이어그램 각주·"관련 문서"에 [spec/10] 링크를 추가. `review_status` enum은 그대로 둠(merge/supersede는
  *상태*가 아니라 *게이트 액션* — 어드버서리얼 검증으로 확인). → [`spec/02-builder-pipeline.md`](./spec/02-builder-pipeline.md).

### Fixed
- **systemic "커널 §9" dangling 참조.** spec/01엔 §8까지뿐이었는데 schema·spec/03·skills가 권한
  모델을 "kernel §9"로 가리켰음 → spec/01 §9 추가로 일괄 해소.
- skills 곳곳의 잘못된 교차참조(예: 후보 필드의 "커널 §8"→`candidate.schema.json`, 컴파일러 갭
  로그의 metric `correction_cost`→`coverage`, `§3 [B]`→`§3 [3]`)와 깨진 라벨 정정.
- **깨진 자기 앵커 링크 정정(skills/08).** `§3 라우팅 표`를 가리키는 세 개의 자기 링크가
  `#3-라우팅-표-1-1-전수`로 잘못 작성되어 실제 헤딩 슬러그(`#3-라우팅-표-11-전수`, `(1:1, 전수)`의
  `1:1`이 `11`로 정규화)와 어긋났음 → 다른 모든 링크가 쓰는 `11` 규약으로 통일. 저장소 전체 앵커
  링크를 GitHub 슬러그 알고리즘으로 일괄 점검(현재 167개, broken=0; CI가 매번 재확인).
- **실행되지 않던 문서 명령·낡은 라이브 출력 정정("모든 figure는 명령으로 재현"의 위반).**
  `convergence_report.py`는 *디렉터리 하나*를 받는데 문서 세 곳이 깨진 형태였음 — `tools/README.md`
  §2의 두-파일 형태, `CONTRIBUTING.md`의 인자 없는 형태, `templates/QUICKSTART.md`의 존재하지 않는
  `--subject` 플래그(모두 exit 2). 디렉터리 형태로 통일. 더불어 `tools/README.md` §2의 "기대 출력"이
  플라이휠 이전(T0: L1·coverage 0.43·df 0.75·correction_cost 0.21)을 *라이브*인 양 제시 → 실제 라이브
  **T2(L2·0.71·1.00·0.08·drift 0.89)** 로 교정하고 T0 베이스라인은 `convergence-report.md`,
  델타는 revolution-01/02가 보존함을 명시. 회귀 테스트로 디렉터리-형 CLI를 잠금(36 tests).

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
