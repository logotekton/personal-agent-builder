# 거버넌스 (Governance)

> **EN:** How this project is governed. It fixes the **four pack classes** and the
> hard **"never mix"** rule (the `schema_governance` invariant), how versions move
> (spec `vX.Y`; packs **semver**), and the decision process for changing the
> **canonical contract** — the single schema all files derive from. The canonical
> contract is the source of truth; every change to it is reviewed, versioned, and
> recorded in [`CHANGELOG.md`](./CHANGELOG.md). Founder: **Logotekton**.

이 문서는 *방법론과 스키마*가 어떻게 합의되고 바뀌는지를 정합니다. 개인 인스턴스
데이터(`personal.<subject>.*`)의 소유·권한은 여기서 다루지 않습니다 — 그것은
[04 프라이버시·경계](./spec/04-privacy-boundary.md)와
[08 네이밍·ID](./spec/08-naming-and-ids.md)가 결정합니다. 여기서 다루는 것은 **공용
자산**(스킬·템플릿 스키마·정식 어휘·수렴 모델)의 거버넌스입니다.

---

## 1. 단일 진리 원천 (The canonical contract)

이 프로젝트에는 **하나의 진리 원천**이 있습니다: **정식 설계 계약(canonical contract)**.
이는 두 개의 짝으로 구현됩니다.

| 산출물 | 역할 | 기계 검증 |
|--------|------|-----------|
| [`spec/01-kernel-schema.md`](./spec/01-kernel-schema.md) | 사람이 읽는 정식 어휘·라이프사이클·게이트·라우팅 | — |
| [`schemas/record.base.schema.json`](./schemas/record.base.schema.json) | 모든 인스턴스 레코드가 `allOf`로 확장하는 통합 베이스 레코드 | draft 2020-12 |

다른 모든 파일(README, 나머지 spec, 14개 팩 스키마, 13개 스킬, 템플릿, 예제)은 이 계약의
**파생물**입니다. 파생물과 계약이 충돌하면 **계약이 이깁니다**, 그리고 그 충돌은 버그로
간주되어 수정됩니다.

**핵심 규칙:** 새 어휘를 발명하지 않습니다. 노드/엣지/팩 이름·후보 타입·`review_status`·
`sensitivity` 값은 모두 커널 스키마에서 가져옵니다. 구 코드명(`pa.t03`, `t06`, `x12`, `.ba`
등)은 오직 "구 코드명" 컬럼/주석에서만 등장합니다 → [08 §3](./spec/08-naming-and-ids.md).

---

## 2. 네 개의 팩 클래스 — "절대 섞지 않는다" (`schema_governance`)

시스템은 네 종류의 팩으로 구성되며, **이들은 절대 한 팩 안에서 섞이지 않습니다.** 이것이
`schema_governance` 거버넌스 팩이 강제하는 핵심 불변식입니다.

| 클래스 | 접두사 | 담는 것 | 개수 | 예 |
|--------|--------|---------|------|----|
| **skill pack** | `skill.pab.*` | *방법* — 어떻게 빌드하는가(프로세스 규칙) | 13 | `skill.pab.candidate_extraction` |
| **template pack** | `user.*` (스키마) | *형태* — 레코드의 모양(스키마 규칙) | 14 | `user.decision_policy` |
| **instance pack** | `personal.<subject>.*` | *데이터* — 승인된 실제 레코드 | 주체당 14 | `personal.logotekton.decision_policy` |
| **adapter pack** | `*.runtime_adapter` | *런타임* — 컴파일된 실행 규칙 | N | `logotekton.runtime_adapter` |

여기에 더해 **거버넌스 팩**이 메타 규칙을 담습니다: `naming`, `schema_governance`,
`convergence_model`, `9space_crosswalk`, `qa`.

### 왜 섞지 않는가

- **방법 ≠ 데이터:** 스킬(HOW)이 인스턴스 레코드(DATA)를 담으면, 방법을 업데이트할 때
  남의 사적 데이터를 건드리게 됩니다. 게이트 **G6**(템플릿/인스턴스 분리)의 일반화입니다.
- **형태 ≠ 데이터:** 템플릿(SHAPE)은 라이브 레코드를 담지 않습니다. 빈 스키마는 공용이고,
  채워진 인스턴스는 비공개입니다.
- **데이터 ≠ 런타임:** 어댑터(RUNTIME)는 *확인된* 슬라이스에서만 컴파일됩니다. 펜딩 후보가
  런타임으로 새어 들어가지 않습니다(게이트 **G3**).

이 규칙을 어기는 PR은 클래스 위반으로 **반려**됩니다. 검증은
[`tools/validate_packs.py`](./tools/validate_packs.py)가 접두사·스키마 차원에서 강제합니다.

---

## 3. 버전 관리 (Versioning)

두 가지 버전 축이 **독립적으로** 움직입니다.

### 3.1 사양 버전 — `spec vX.Y`

전체 사양은 하나의 `vX.Y` 번호를 공유합니다(현재 **v0.3**). 이는 *정식 계약의 릴리스*를
가리킵니다.

- **MINOR (`X.y`):** 하위 호환되는 어휘 확장(새 선택 필드, 새 평가 지표, 명료화).
- **MAJOR (`x.0`):** 하위 비호환 변경 — 노드/엣지/팩 이름 삭제·rename, 필수 필드 추가,
  enum 값 제거, 라우팅 1:1 전수 매핑의 변경.
- `1.0` 이전(`0.y`)에는 MINOR 안에서도 깨는 변경이 있을 수 있으나, 반드시 마이그레이션
  노트를 [`CHANGELOG.md`](./CHANGELOG.md)에 남깁니다.

> 예: v0.1/v0.2의 `score`/`claim` 표류를 통합 베이스 레코드로 정합화한 것이 **v0.3**입니다.

### 3.2 팩 버전 — semver (`MAJOR.MINOR.PATCH`)

개별 팩(skill / template / instance / adapter)은 각자 **[semver](https://semver.org)**로
버전을 답니다. 같은 spec `vX.Y` 안에서도 팩은 독립적으로 진화합니다.

| 변경 | 범프 | 예 |
|------|------|----|
| **PATCH** `x.y.Z` | 동작·스키마 불변, 문서/오타/예시 수정 | 스킬 문장 다듬기 |
| **MINOR** `x.Y.0` | 하위 호환 추가 — 선택 필드·새 `record_type` 값 추가, 게이트 완화 없음 | 팩에 선택 `linked_domains` 노출 |
| **MAJOR** `X.0.0` | 하위 비호환 — 필수 필드 추가, enum 값 제거, `record_type` rename | 필드 rename |

규칙:

1. **팩 rename은 MAJOR이며 드리프트입니다.** 새 ID를 부여하고, 옛 ID를
   `user.drift_history`에 `supersedes`로 기록합니다 → [08 §5](./spec/08-naming-and-ids.md).
2. 인스턴스 데이터는 자신이 **검증된 기준이 된 베이스 스키마/팩 버전**을 참조로 들고
   있어야 합니다(재현 검증을 위해).
3. 팩 MAJOR가 spec MAJOR를 강제하지는 않습니다. 그러나 spec MAJOR는 영향받는 모든 팩의
   적어도 MINOR 범프를 유발합니다.

---

## 4. 계약을 바꾸는 결정 과정 (Decision process)

정식 계약(§1)을 건드리는 변경은 가벼운 **RFC 흐름**을 거칩니다. 라이프사이클의 정신을
거버넌스에 그대로 적용합니다 — *증거에 묶고, 스코프를 지정하고, 검토하고, 기록한다.*

```
proposal(이슈) → discussion → draft PR → review → decision → merge → CHANGELOG 기록
     │ 동기·증거    │ 합의 형성   │ 계약+파생   │ 메인테이너  │ 합의/    │ spec/  │ 모든
     │ (왜 바뀌어야) │            │ 동시 수정   │ 검토        │ 거부/연기 │ pack    │ 계약 변경
     │              │            │ (정합 유지) │ (G6/G3 등)  │          │ 버전 범프│ 1줄 이상
```

규칙:

- **계약과 파생물은 같은 PR에서 함께 바뀝니다.** 커널 스키마를 바꾸면서 베이스 스키마·
  영향받는 팩 스키마·관련 spec/스킬을 같은 PR에서 갱신해 정합 상태를 유지합니다.
- **모든 계약 변경은 [`CHANGELOG.md`](./CHANGELOG.md)에 기록됩니다.** 무엇이·왜·마이그레이션
  방법을 적습니다. 기록 없는 계약 변경은 머지되지 않습니다.
- **증거 게이트는 거버넌스에도 적용됩니다.** 새 게이트 완화·새 필수 필드 같은 변경은
  그것이 깨는/지키는 실제 예제로 뒷받침되어야 합니다(추측 금지, G1의 정신).
- **양방향 문(two-way door) 우선.** 되돌리기 쉬운 변경(MINOR/PATCH)은 빠르게, 되돌리기
  어려운 변경(MAJOR rename·필드 삭제)은 보수적으로.
- **막다른 경우 founder가 타이브레이커.** 합의가 막히면 메인테이너 합의를, 그조차 막히면
  founder(§6)가 최종 결정하되, 결정 근거를 PR에 남깁니다.

변경 분류와 필요한 합의 수준:

| 변경 종류 | 필요 절차 | 버전 영향 |
|-----------|-----------|-----------|
| 오타·문서·예시 | 1 리뷰 승인 | PATCH |
| 선택 필드·새 enum 값 추가 | 1 리뷰 + CHANGELOG | spec MINOR / 팩 MINOR |
| 필수 필드·라우팅·게이트 변경 | RFC 이슈 + ≥2 메인테이너 + CHANGELOG | spec MAJOR(0.y는 MINOR+노트) |
| 팩 rename·삭제 | RFC + 드리프트 레코드 + ≥2 메인테이너 | 팩 MAJOR + spec MINOR↑ |
| 새 팩 클래스/거버넌스 규칙 | RFC + founder 승인 | spec MAJOR |

---

## 5. 역할 (Roles)

| 역할 | 책임 | 권한 |
|------|------|------|
| **Founder** | 비전·정식 어휘의 수호, 최종 타이브레이커 | §6 |
| **Maintainer** | PR 리뷰·머지, 릴리스 컷, 게이트/클래스 위반 반려 | 머지·릴리스 |
| **Pack Architect** | 특정 팩 클래스/팩의 스키마 정합성 소유 | 해당 팩 리뷰 |
| **Contributor** | 이슈·RFC·PR 제출 | 제안 |
| **User (subject)** | 자기 `personal.<subject>.*` 인스턴스의 단독 소유자 | 자기 데이터 전권 |

- 역할은 **귀속이지 소유가 아닙니다.** founder/maintainer라는 사실이 다른 사용자의 인스턴스
  데이터에 대한 권한을 주지 않습니다 → [08 §6](./spec/08-naming-and-ids.md),
  [04 경계·권한](./spec/04-privacy-boundary.md).
- 운영(런타임) 역할(Orchestrator, Evidence, Confirmation 등)은 거버넌스 역할과 별개이며
  [12 crab-orchestration](./skills/12-crab-orchestration.md)에서 정의됩니다.

기여 방법·행동 강령·PR 체크리스트 → [`CONTRIBUTING.md`](./CONTRIBUTING.md).

---

## 6. 창립자 귀속 (Founder attribution)

이 프로젝트는 한 사람(**Logotekton**)의 개인 에이전트를 만들려다 시작되었고, 그 사실은
보존됩니다.

- founder는 정식 어휘의 수호자이자 막힌 합의의 **최종 타이브레이커**입니다(§4). 일상적
  결정은 메인테이너 합의로 이루어집니다.
- 창립자 귀속은 `user.identity_roles` 팩의 **`AttributionRecord`** 타입으로,
  `attributed_to`에 대상을 명시해 기록합니다. 표준 문구:
  *"Logotekton founded the Personal Agent project."*
  → [`schemas/user.identity_roles.schema.json`](./schemas/user.identity_roles.schema.json).
- **귀속은 증거 게이트의 예외가 아닙니다.** 다른 레코드와 동일하게 ≥1 `evidence_refs`(G1)와
  비어 있지 않은 `scope`(G2)를 가져야 합니다. 귀속은 *주장*이지 무조건적 사실 선언이
  아닙니다.
- **귀속은 보존되되 소유·권한과 분리됩니다.** founder라는 사실이 다른 사용자
  데이터(`personal.<other>.*`)에 대한 권한을 부여하지 않습니다.

---

## 7. 라이선스·소유 (License & ownership)

- 코드·스키마: **MIT** / 문서·사양: **CC BY-SA 4.0** → [`LICENSE`](./LICENSE).
- **당신의 개인 인스턴스 데이터는 당신의 것**이며 이 라이선스의 적용을 받지 않습니다.
  거버넌스는 공용 자산만 다룹니다.

---

## 8. 빠른 점검 체크리스트 (PR 머지 전)

- [ ] 변경이 정식 계약(§1)을 건드리면, 베이스 스키마·영향 팩·관련 spec/스킬을 **같은 PR**에서 정합화했는가
- [ ] 네 팩 클래스를 섞지 않았는가 (`skill.pab.*` / `user.*` / `personal.<subject>.*` / `*.runtime_adapter`) — §2
- [ ] 새 어휘를 발명하지 않고 커널 스키마의 정식 이름만 썼는가 (구 코드명 누출 없음)
- [ ] 버전을 올바르게 범프했는가 (spec `vX.Y` / 팩 semver) — §3
- [ ] 모든 계약 변경을 [`CHANGELOG.md`](./CHANGELOG.md)에 무엇·왜·마이그레이션으로 기록했는가 — §4
- [ ] 팩 rename이면 드리프트 레코드(`supersedes`)를 남겼는가 — §3.1
- [ ] 변경 종류에 맞는 합의 수준을 충족했는가 (§4 표)

---

연관 문서: [README](./README.md) · [01 커널 스키마](./spec/01-kernel-schema.md) ·
[03 팩 카탈로그](./spec/03-pack-catalog.md) · [08 네이밍·ID](./spec/08-naming-and-ids.md) ·
[CONTRIBUTING](./CONTRIBUTING.md) · [CHANGELOG](./CHANGELOG.md).
