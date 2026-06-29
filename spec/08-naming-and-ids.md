# 08 · 네이밍 · ID 정책 (Naming & IDs)

> **EN:** This is the naming and identifier policy for the whole repo. The product's
> user-facing model name is **Personal Agent**; the underlying platform/infra is
> **OpenCrab**. Every pack carries a short `system_pack_id` (for tooling/paths) and a
> canonical `display_name` (user-facing). Instance records use the id format
> `<subject>.<recordkind>.NNN`. This doc also fixes the four pack-class prefixes and gives
> the complete codename→canonical migration table so no old codename (`pa.t03`, `t06`,
> `x12`, `.ba`…) leaks into v0.3. See [01-kernel-schema](./01-kernel-schema.md) for the
> vocabulary this policy names, and [`schemas/record.base.schema.json`](../schemas/record.base.schema.json)
> for the machine-checked id pattern.

이름은 거버넌스입니다. 어휘가 흔들리면 검색·라우팅·검증이 모두 깨집니다. 이 문서는 **무엇을
어떻게 부르고, 어떤 ID 형식을 쓰는가**를 한 곳에 고정합니다. 다른 모든 문서·스키마·팩은
여기서 정한 이름만 씁니다.

## 1. 제품명 vs 플랫폼명

| 무엇 | 정식 이름 | 어디에 쓰나 |
|------|-----------|-------------|
| **산출물(공식 모델명)** | **Personal Agent** | 사용자 대면 문서, README, 에이전트 프로필 이름 |
| **빌더 방법론/저장소** | Personal Agent Builder | 이 저장소·사양의 이름 |
| **플랫폼/인프라** | **OpenCrab** | 온톨로지 저장·검색·QA·`opencrab_crab_agent` 빌드 |

핵심 구분: **Personal Agent는 OpenCrab 위에서 만들어지는 산출물**입니다. "OpenCrab으로
빌드한 Personal Agent"가 맞고, "OpenCrab 에이전트"라고 산출물을 부르지 않습니다. 자세한
관계 → [00-overview](./00-overview.md#opencrab과의-관계).

## 2. `system_pack_id` vs `display_name`

모든 팩(스킬·템플릿·인스턴스·어댑터)은 **두 개의 이름**을 가집니다.

| 필드 | 성격 | 규칙 |
|------|------|------|
| `system_pack_id` | 기계용 — 경로·파일명·라우팅 키 | 짧고 안정적, `[a-z0-9_.]`만, 한 번 정하면 불변(rename은 드리프트 기록) |
| `display_name` | 사람용 — **정식 표준 이름** | [01 §5](./01-kernel-schema.md#5-14개-user-온톨로지-팩-정식-이름)·[03 팩 카탈로그](./03-pack-catalog.md)의 정식 이름과 1:1 일치 |

- `system_pack_id`는 도구 편의를 위해 **짧을 수 있습니다** (예: 스키마 파일명
  `user.tool_stack.schema.json`). 하지만 사람에게 보여줄 때의 **정식(canonical) 이름**은
  언제나 `display_name`입니다.
- 충돌 시 우선순위: **`display_name`(정식) > `system_pack_id`(편의)**. 둘이 어긋나면
  `display_name` 쪽을 진실로 보고 `system_pack_id`를 맞춥니다.
- 베이스 레코드의 표시 별칭(`statement`의 display alias 등)과 마찬가지로,
  `system_pack_id`는 *별칭이지 진실의 원천이 아닙니다*.

## 3. 인스턴스 레코드 ID 형식

확인된 인스턴스 레코드의 ID는 **세 토막**입니다:

```
<subject>.<recordkind>.NNN
└─ 주인   └─ 레코드 종류   └─ 3자리+ 일련번호
```

| 토막 | 의미 | 예 |
|------|------|----|
| `<subject>` | 에이전트의 주인(`UserSubject`) 식별자 | `logotekton` |
| `<recordkind>` | 레코드 종류의 짧은 키 | `role`, `style`, `heuristic`, `boundary` |
| `NNN` | 주인+종류 안에서의 일련번호 (≥3자리, zero-pad) | `001`, `042` |

예: `logotekton.role.001`, `logotekton.heuristic.042`, `logotekton.boundary.007`.

이 형식은 기계 검증됩니다 → [`schemas/record.base.schema.json`](../schemas/record.base.schema.json)
의 `id.pattern` (`^[a-z0-9_]+\.[a-z0-9_]+\.[0-9]{3,}$`). 후보(candidate) 단계의 임시
식별자 `candidate_id`는 이 형식을 따르지 않아도 되며, **확인(confirm) 후 팩에 라우팅될 때
정식 인스턴스 ID를 부여**받습니다([02 파이프라인](./02-builder-pipeline.md)의 확인 게이트·팩
라우팅 단계).

`<recordkind>` 권장 키(팩별):

| 팩 | recordkind 키 | | 팩 | recordkind 키 |
|----|---------------|-|----|---------------|
| `user.identity_roles` | `role` | | `user.workflow_playbooks` | `workflow` |
| `user.persona_core` | `trait` | | `user.domain_overlays` | `domain` |
| `user.communication_style` | `style` | | `user.tool_stack` | `tool` |
| `user.artifact_policy` | `artifact` | | `user.boundary_authority` | `boundary` |
| `user.decision_policy` | `decision` | | `user.memory_project_graph` | `project` |
| `user.tacit_heuristics` | `heuristic` | | `user.evaluation_cases` | `evalcase` |
| `user.red_flags` | `redflag` | | `user.drift_history` | `drift` |

## 4. 팩 클래스 접두사 (4개 클래스 — 절대 섞지 않음)

네 가지 팩 클래스는 **접두사로 구분**됩니다. 거버넌스 규칙(스킬·템플릿·인스턴스·어댑터를
섞지 않음, 게이트 G6)이 이름 단계에서부터 강제됩니다.

| 클래스 | 접두사 패턴 | 담는 것 | 예 |
|--------|-------------|---------|----|
| **스킬 팩** | `skill.pab.*` | 절차 규칙(HOW) — 13개 | `skill.pab.evidence_capture`, `skill.pab.kernel_schema` |
| **템플릿 팩** | `user.*.template` / `user.*` 스키마 | 형태 규칙(SHAPE) — 14개 | `user.communication_style`, `user.tool_stack.template` |
| **인스턴스 팩** | `personal.<subject>.*` | 확인된 레코드(DATA) — 주인당 14개 | `personal.logotekton.identity_roles` |
| **어댑터 팩** | `*.runtime_adapter` | 실행 규칙(RUNTIME) | `personal.logotekton.runtime_adapter` |

여기에 거버넌스 팩이 더해집니다: `naming`(이 문서), `schema_governance`,
`convergence_model`, `9space_crosswalk`, `qa`.

접두사 읽는 법:
- `skill.pab.` — `pab` = Personal Agent Builder. 이 접두사를 보면 **방법(절차)** 입니다.
- `user.` — 비어 있는 **형태/스키마**입니다. 라이브 레코드를 담지 않습니다(G6).
  `user.<pack>.template`은 사용자가 채워 넣을 빈 양식, `user.<pack>.schema.json`은 그 기계
  검증 스키마([`schemas/`](../schemas))입니다.
- `personal.<subject>.` — **특정 개인의 데이터**입니다. 주인 이름이 접두사에 박혀 있어
  소유와 프라이버시 경계가 이름에서 드러납니다.
- `*.runtime_adapter` — 확인된 슬라이스를 컴파일한 **런타임**입니다. 원본 팩이 아니라
  `compiled_into` 산출물입니다([02 §컴파일](./02-builder-pipeline.md)).

> 같은 `<pack>` 이름이 클래스마다 반복됩니다. 예: `user.tool_stack`(형태) ↔
> `personal.logotekton.tool_stack`(데이터)는 **같은 팩의 다른 클래스**입니다. 접두사만이
> 클래스를 결정합니다.

> **OpenCrab 배치.** 이 4개 클래스는 OpenCrab에서 *두 프로젝트*로 나뉩니다 — 방법+형태(`skill.pab.*`
> + `user.*`)는 재사용 가능한 **빌더** 프로젝트에, 데이터+런타임(`personal.<subject>.*` +
> `*.runtime_adapter`)은 주인당 하나인 **개인 에이전트** 프로젝트에. 빌더로 *만들고* 개인 에이전트로
> *인제스트*합니다([07 프로젝트 토폴로지](./07-opencrab-9space-crosswalk.md#프로젝트-토폴로지--빌더-공장과-산출-인제스트-2-project)).

## 5. 코드명 → 정식 이름 마이그레이션 표

v0.1/v0.2의 **구 코드명**은 모두 폐기됩니다. 아래 표가 유일한 이행 매핑입니다. 새 문서·코드는
정식 이름만 쓰고, 구 코드명은 *"구 코드명"* 주석으로만 언급합니다(검색 호환을 위해).

| # | 정식 이름 (display_name) | 구 코드명 | 의미 |
|---|--------------------------|-----------|------|
| 1 | `user.identity_roles` | `pa.roles` | 역할·정체성·맥락 |
| 2 | `user.persona_core` | `pa.core` | 안정 선호/가치/우선순위 |
| 3 | `user.communication_style` | `pa.t03` | 응답 형식/언어/구조 |
| 4 | `user.artifact_policy` | `pa.t04` | 선호 출력물 형태 |
| 5 | `user.decision_policy` | `pa.t05` | 우선순위/승인/거부 규칙 |
| 6 | `user.tacit_heuristics` | `t06` | 암묵 판단 규칙 |
| 7 | `user.red_flags` | `t07` | 위험 신호 |
| 8 | `user.workflow_playbooks` | `t08` | 반복 작업 시퀀스 |
| 9 | `user.domain_overlays` | `t09` | 도메인 특화 지식 |
| 10 | `user.tool_stack` | `t10` | 도구/사용 패턴 |
| 11 | `user.boundary_authority` | `t11`, `.ba` | 프라이버시/권한 규칙 |
| 12 | `user.memory_project_graph` | `x12` | 프로젝트·목표·메모리 |
| 13 | `user.evaluation_cases` | `x13` | 충실도 테스트 케이스 |
| 14 | `user.drift_history` | `x14` | 변경·버전 이력 |

후보 타입도 일부 개명되었습니다(라우터 정합용):

| 정식 candidate_type | 구 이름 |
|---------------------|---------|
| `DomainOverlayCandidate` | 구 `DomainSpecificCandidate` |
| `ProjectMemoryCandidate` | 구 `ProjectGoalCandidate` |
| `IdentityRoleCandidate` | (신규 — 누락이었음) |

전체 14:14 후보↔팩 매핑 → [01 §6](./01-kernel-schema.md#6-후보-타입--라우팅-11-전수).

**마이그레이션 규칙**
1. 구 코드명을 만나면 위 표로 *기계적으로* 치환합니다. 새 이름을 추측하지 않습니다.
2. 팩을 rename할 때는 새 ID를 부여하고, 옛 ID는 `user.drift_history`에 `supersedes`로
   기록합니다(이름 변경도 드리프트입니다).
3. 구 코드명은 문서 본문에 단독으로 등장하지 않습니다 — 오직 "구 코드명" 컬럼/주석에서만.

## 6. 창립자 귀속(Founder attribution) 규칙

이 프로젝트는 한 사람(**Logotekton**)의 개인 에이전트를 만들려다 시작되었고, 그 사실은
정체성·귀속 레코드에 보존됩니다.

규칙:
- 창립자 귀속이 필요한 정체성 주장은 `user.identity_roles` 팩의 **`AttributionRecord`**
  타입으로 기록하고, `attributed_to` 필드에 귀속 대상을 명시합니다
  (→ [`schemas/user.identity_roles.schema.json`](../schemas/user.identity_roles.schema.json)).
  표준 문구: *"Logotekton founded the Personal Agent project."*
- 창립자 귀속은 **증거 게이트의 예외가 아닙니다.** 다른 모든 레코드와 동일하게 ≥1개의
  `evidence_refs`(G1)와 비어 있지 않은 `scope`(G2)를 가져야 합니다. 귀속은 *주장*이지
  무조건적 사실 선언이 아닙니다.
- 귀속은 **보존되되 소유와 분리**됩니다. 창립자라는 사실이 다른 사용자의 인스턴스
  데이터(`personal.<other>.*`)에 대한 권한을 주지 않습니다. 권한·소유는 접두사
  `personal.<subject>.`와 [04 프라이버시·경계](./04-privacy-boundary.md)의 경계/권한
  모델이 결정합니다.
- 개인 정체성·시민 정체성에 닿는 귀속 레코드는 흔히 `sensitivity ≥ internal`이며 승격 전
  `BoundaryRule`을 받습니다(G5).

## 7. 빠른 점검 체크리스트

- [ ] 사용자 대면 텍스트에서 산출물을 **Personal Agent**로, 플랫폼을 **OpenCrab**으로 불렀는가
- [ ] 팩 이름이 [01 §5](./01-kernel-schema.md#5-14개-user-온톨로지-팩-정식-이름)의
      정식 `display_name`과 1:1 일치하는가 (구 코드명 누출 없음)
- [ ] 인스턴스 ID가 `<subject>.<recordkind>.NNN`(≥3자리)이고 베이스 스키마 패턴을 통과하는가
- [ ] 접두사가 팩 클래스를 정확히 반영하는가 (`skill.pab.*` / `user.*` / `personal.<subject>.*` / `*.runtime_adapter`)
- [ ] 창립자 귀속이 `AttributionRecord` + `evidence_refs`로 기록되었고, 권한을 부여하지 않는가

연관 문서: [00 개요](./00-overview.md) · [01 커널 스키마](./01-kernel-schema.md) ·
[03 팩 카탈로그](./03-pack-catalog.md) · [04 프라이버시·경계](./04-privacy-boundary.md) ·
[07 9-space 크로스워크](./07-opencrab-9space-crosswalk.md).
