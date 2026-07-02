# 17 · 부트스트랩 (Bootstrap — repo → OpenCrab provisioning)

> **EN:** Operating instructions for `skill.pab.bootstrap` — the **provisioning adapter**
> (like `14-host-binding`, an adapter, *not* a pipeline step) that takes a fresh clone of
> this repo and stands up the full **3-project operating topology** on OpenCrab: (1) create
> the three projects, (2) ingest the repo's method/shape sources as builder packs (~44),
> (3) prepare the 14 empty `personal.<subject>.*` shells in the personal-agent project —
> and then asks the owner two decisions the agent must never make for them: **(0) the
> subject handle** that names every `personal.<subject>.*` pack, and **(4) the activation
> mode** (command-trigger / ambient hooks / manual). Every stage is **idempotent**: anything that
> already exists is skipped, never duplicated. The deterministic ingest plan comes from
> [`tools/bootstrap_plan.py`](../tools/bootstrap_plan.py); execution uses the OpenCrab MCP
> tools an agent already has. A bootstrap run ends with the skill-16 style report.

부트스트랩은 "처음 이 레포를 접한 사용자"가 문서 더미에서 **운영 가능한 3층 토폴로지**
([spec/07](../spec/07-opencrab-9space-crosswalk.md#프로젝트-토폴로지--빌더-장치-증거-아카이브-개인-에이전트-3-project))까지
가는 절차입니다. [14 호스트 배선](./14-host-binding.md)처럼 **어댑터**이며 파이프라인 단계가
아닙니다 — 파이프라인(01–12)이 *돌 수 있는 무대*를 만드는 일입니다.

- **전제:** OpenCrab MCP 도구(`opencrab_project_manage` / `opencrab_ingest_text` /
  `opencrab_search_packs`)에 접근 가능한 에이전트. 없으면 이 문서의 각 단계를 OpenCrab
  웹 UI로 수동 수행해도 됩니다(계약은 동일).
- **멱등성(불변 규칙):** 모든 단계는 *생성 전에 존재를 확인*합니다. 같은 이름의
  프로젝트/팩이 있으면 **건너뛰고 보고**합니다. 부트스트랩을 두 번 돌려도 결과는 한 번과
  같아야 합니다.
- **하지 않는 일:** 개인 데이터를 만들지 않습니다. 어떤 레코드도 confirmed 로 만들지
  않습니다(G3). 빌더 프로젝트에 개인 인스턴스를 넣지 않습니다(G6).

> 한 줄 계약: **fresh clone → 주체 핸들 선택 + 3 프로젝트 + 빌더 팩 + 빈 14 뼈대 + 발화 모드 선택.**
> 개인 *기억*은 하나도 생기지 않는다 — 기억은 이후 파이프라인과 게이트가 채운다.

---

## Stage 0 · 주체 핸들(subject) 선택 — 소유자 입력, 필수

`personal.<subject>.*` 의 `<subject>` 는 소유자의 닉네임(핸들)입니다. **에이전트가 지어내지
않고 반드시 소유자에게 묻습니다.**

- **문법:** 모든 레코드 id 가 `<subject>.<recordkind>.NNN`
  ([record.base](../schemas/record.base.schema.json) · [spec/08](../spec/08-naming-and-ids.md))이므로
  핸들은 `^[a-z0-9_]+$` 만 허용합니다 (소문자·숫자·언더스코어).
- **정규화 제안:** 소유자가 `Logo Tekton` 처럼 답하면 그대로 쓰지 말고 `logo_tekton` 을
  제안하고 **확인을 받습니다** — 조용한 변형 금지.
- **미응답 시:** 기본값이 없습니다. Stage 1–2(주체 무관 장치)는 진행하되 **Stage 3 은
  차단**하고 최종 보고에 `WAITING_FOR_SUBJECT` 로 남깁니다.
- `python tools/bootstrap_plan.py . --subject <핸들>` 이 같은 문법을 기계 검증합니다
  (위반 시 exit 2 + 정규화 제안).

## Stage 1 · 프로젝트 3개 생성

| 프로젝트 이름 (기본값) | 역할 | metadata.role |
|------------------------|------|----------------|
| `personal agent builder skills` | 빌더 장치 — 방법(skill.pab.*)+형태(템플릿)+스펙 | `builder_apparatus` |
| `personal agent evidence` | 증거 아카이브 — 세션 증거·pending 후보 보드 (비계) | `personal_agent_evidence_archive` |
| `personal agent` | 개인 에이전트 — 승인된 14팩 + 런타임 어댑터 | `personal_agent_canonical` |

절차: `opencrab_project_manage(action=list)` 로 세 이름을 조회 → 없는 것만
`action=create` (description 에 역할 한 줄, metadata 에 위 role). 이름은 소유자가 바꿔도
되지만 **세 층의 분리 자체는 계약**입니다([spec/07 불변식](../spec/07-opencrab-9space-crosswalk.md)).

## Stage 2 · 빌더 팩 ingest (~44팩)

레포의 방법·형태 원료를 빌더 프로젝트의 팩으로 올립니다. **무엇을 어떤 이름으로 올릴지는
결정론적 계획 도구가 산출**합니다 — 손으로 세지 않습니다:

```bash
python tools/bootstrap_plan.py .
```

계획의 매핑 규칙(도구와 이 표는 항상 일치해야 함):

| 원료 (repo) | 팩 이름 규칙 | 개수 |
|--------------|--------------|------|
| `skills/NN-<name>.md` | `skill.pab.<name_snake>.v0.1` | 17 |
| `spec/NN-<name>.md` | `pa.<name_snake>.v0.1` | 12 |
| `templates/user.<pack>.template.yaml` + 짝 스키마 `schemas/user.<pack>.schema.json` | `personal.<pack>.template.v0.1` | 14 |
| 공용 스키마 3종 (`record.base` · `candidate` · `trigger`) | `pa.shared_schemas.v0.1` (한 팩) | 1 |
| **합계** | | **44** |

절차: 각 항목을 `opencrab_ingest_text`(title=팩 이름, content=파일 원문, visibility=private)
로 올리고 빌더 프로젝트에 `add_packs`. **이미 같은 title 의 팩이 있으면 건너뜁니다**
(`opencrab_search_packs` 로 선조회). 문서가 갱신됐을 때는 새 팩이 아니라 기존 팩에
`opencrab_pack_update` — 팩 증식(sprawl)은 [spec/10](../spec/10-dedup-and-merge.md)이 금지하는
안티패턴입니다.

## Stage 3 · `personal.<subject>.*` 빈 뼈대 14개

개인 에이전트 프로젝트에 14개 정식 팩의 **빈 컨테이너**를 만듭니다 — 내용은
"이 팩은 확인 게이트를 통과한 레코드의 upsert 를 기다리는 빈 뼈대" 선언과 해당 템플릿/스키마
링크뿐입니다.

- **왜 비어 있어야 하나:** 3층 규칙 — *pending 은 evidence 층으로, confirmed 만 이 층으로*.
  뼈대에 임시 레코드를 채우는 순간 G3(미확인 런타임 진입 금지)가 뚫립니다.
- 이름: `personal.<subject>.<pack>.v0.1` — `<subject>` 는 **Stage 0 에서 소유자가 확정한 핸들**
  (예: `personal.logotekton.persona_core.v0.1`). 핸들 없이는 이 단계를 실행하지 않습니다.
- 멱등성: 동일.

## Stage 4 · 발화 모드 선택 (필수 — 에이전트가 정하지 않는다)

프로비저닝이 끝나면 **반드시 소유자에게 묻습니다.** 세 모드는
[spec/09](../spec/09-triggers.md)의 `default_state` 어휘로 정확히 표현됩니다:

| 모드 | 뜻 | 트리거 default_state 프로파일 | 지금 동작? |
|------|-----|-------------------------------|------------|
| **A. 명령형 (권장 기본)** | "이 세션 기반으로 팩 만들어줘" 같은 명시 요청에만 빌더가 돈다 | command 트리거(15 등) `enabled`, 앰비언트(계층 A) `suggested` | ✅ 오늘 동작 |
| **B. 훅 자동 (ambient)** | 훅이 세션을 상시 포착·스테이징, 세션 끝에 리뷰보드 1회 | 계층 A 전부 `enabled` ([hooks-setup](../docs/hooks-setup.md)) | ⚠️ `tools/pab` 실배선 후 옵트인 (현재 STUB) |
| **C. 수동** | 사용자가 스킬 문서를 직접 따라 실행 | 전부 `off` | ✅ 오늘 동작 |

- 답이 없으면 **A**가 기본입니다(스테이징-only + 명시 명령이라 가장 안전).
- 선택 결과는 **증거 아카이브 프로젝트**에 부트스트랩 보고의 일부로 기록합니다
  (주인별 운영 상태이지 장치가 아니므로 빌더 프로젝트가 아님).

## 최종 보고 (Required final report)

모든 부트스트랩 런은 이 블록으로 끝납니다([16 ingest 판정 게이트](./16-ingest-decision-gate.md)의
런-레벨 계약을 따름):

```text
Bootstrap report
Projects: created N / skipped M (existing)
Builder packs: created N / skipped M   (plan total: 44)
Personal shells: created N / skipped M (target: 14)
Subject: <handle> — chosen by owner | WAITING_FOR_SUBJECT
Activation mode: A(command) | B(ambient) | C(manual)  — chosen by owner
Personal records created: 0            (MUST be 0 — bootstrap makes no memory)
Ingest judgement: YES (apparatus only) | NO (aborted)
Next action: run skill 15 on a real session | wire hooks (docs/hooks-setup.md) | none
```

## 검증 (Verification)

- `python tools/bootstrap_plan.py .` 의 합계와 실제 생성/건너뜀 수의 합이 일치해야 합니다.
- `opencrab_project_manage(action=list)` 에 세 프로젝트, 빌더에 44팩, 개인 에이전트에 14뼈대.
- 개인 에이전트 프로젝트의 어떤 팩에도 레코드가 없어야 합니다(뼈대 선언문뿐).

## 인접 문서

- 3층 토폴로지·불변식: [spec/07](../spec/07-opencrab-9space-crosswalk.md#프로젝트-토폴로지--빌더-장치-증거-아카이브-개인-에이전트-3-project)
- 발화 모드의 어휘(`default_state`)·훅 매핑: [spec/09](../spec/09-triggers.md) · [14 호스트 배선](./14-host-binding.md)
- 부트스트랩 뒤 첫 실사용: [15 암묵지 채굴](./15-tacit-knowledge-mining.md) → [16 ingest 판정](./16-ingest-decision-gate.md)
- 새 사용자 안내: [templates/QUICKSTART.md](../templates/QUICKSTART.md)

> 트리거 없음 — 부트스트랩은 어댑터라 발화 조건이 아니라 *설치 시점*에 명시 요청으로 한 번
> 실행됩니다(재실행은 멱등). [check_triggers](../tools/check_triggers.py) 대상 아님.
