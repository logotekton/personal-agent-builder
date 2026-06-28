# 기여 가이드 (Contributing)

> **EN:** Three ways to take part. **(a) Build your own agent** — start at
> [`templates/QUICKSTART.md`](./templates/QUICKSTART.md); your instance data stays private
> and is never sent upstream in a PR. **(b) Improve the method** — schemas, the 13 skills,
> and convergence metrics are open; PRs must respect the six quality gates (G1–G6), use the
> canonical vocabulary, and pass [`tools/validate_packs.py`](./tools/validate_packs.py).
> **(c) Research & tooling** — the [9-space crosswalk](./spec/07-opencrab-9space-crosswalk.md)
> makes PA packs first-class on OpenCrab, and every quality claim is meant to be reproducibly
> re-checked. The core rule for all three: **never weaken a quality gate without discussion,
> keep template/instance separation, and add nothing that isn't evidence-bound.**

이 프로젝트는 *방법론*(스키마·스킬·지표)을 공개하고, *당신의 인스턴스 데이터*는 비공개로
둡니다. 그 두 가지를 섞지 않는 것이 모든 기여의 출발점입니다. 어휘는 전부
[커널 스키마](./spec/01-kernel-schema.md)와 [네이밍 정책](./spec/08-naming-and-ids.md)을
따릅니다 — 새 이름을 만들지 마세요. 거버넌스 의사결정 절차는 [GOVERNANCE.md](./GOVERNANCE.md)를
참고하세요.

---

## 1. 세 종류의 참여자

같은 저장소지만, 당신이 누구냐에 따라 *건드리는 곳*과 *지켜야 할 것*이 다릅니다.

| | 당신은 | 어디서 시작 | 무엇을 만지나 | 핵심 약속 |
|---|--------|------------|--------------|-----------|
| **(a)** | 내 에이전트를 만들고 싶은 사람 | [`templates/QUICKSTART.md`](./templates/QUICKSTART.md) | 당신만의 `personal.<당신>.*` 인스턴스 | **당신 데이터는 당신 것, PR에 올리지 않음** |
| **(b)** | 스키마·스킬·지표를 개선하고 싶은 사람 | 이 문서 §3 | [`schemas/`](./schemas) · [`skills/`](./skills) · [`tools/`](./tools) · [`spec/`](./spec) | **게이트를 약화시키지 않음, 정식 이름만 사용** |
| **(c)** | 연구자·도구 제작자 | [`spec/07-opencrab-9space-crosswalk.md`](./spec/07-opencrab-9space-crosswalk.md) | 크로스워크·지표·재현 QA | **재현 가능한 측정, 증거 추적성 보존** |

세 갈래 모두를 관통하는 단 하나의 규칙이 있습니다:

> **품질 게이트(G1–G6)를 토론 없이 약화시키지 않는다 · 템플릿/인스턴스를 섞지 않는다 ·
> 증거에 묶이지 않은 것은 더하지 않는다.**

---

## 2. (a) 자기 에이전트를 만드는 사람 — 기여라기보다 *사용*

가장 흔하고, 가장 환영하는 경우입니다. 사실 이건 "기여"가 아니라 **사용**입니다.

- [`templates/QUICKSTART.md`](./templates/QUICKSTART.md)로 첫 세션(30~60분)에서 시작하세요.
- **당신의 인스턴스 레코드(`personal.<당신>.*`)는 당신 것입니다.** MIT/CC 라이선스의 적용을
  받지 않고([README 라이선스](./README.md#라이선스)), **PR로 올라가지 않습니다.**
  `.gitignore`가 개인 인스턴스 경로를 무시하도록 되어 있습니다 — 실수로라도 커밋하지 마세요.
- 당신이 *방법론*에 무언가 발견했다면(이 템플릿이 헷갈렸다, 이 게이트가 막혔다, 이 스키마
  필드가 부족하다) — 그때 (b)로 넘어와 **이슈/PR**을 열어 주세요. 그게 진짜 기여입니다.

> 한 줄: **데이터는 비공개, 깨달음은 공개.** 당신의 레코드가 아니라 *그 레코드를 만들며 얻은
> 방법론 개선*을 공유하세요.

---

## 3. (b) 스키마·스킬·지표를 개선하는 사람

여기가 PR이 실제로 일어나는 곳입니다. 무엇을 만지든 아래 4대 불변식을 깨지 마세요.

### 3.1 절대 불변식 (Hard invariants)

1. **품질 게이트를 약화시키지 말 것.** G1–G6([커널 §2](./spec/01-kernel-schema.md#2-품질-게이트-quality-gates))는
   시스템 신뢰의 근거입니다. 게이트를 완화·우회·삭제하는 PR은 **먼저 이슈로 토론**해야 하며,
   [GOVERNANCE.md](./GOVERNANCE.md)의 변경 절차를 거칩니다. 코드 한 줄로 슬쩍 끄지 마세요.
2. **정식 어휘만 쓸 것.** 14개 팩 이름(`user.identity_roles` … `user.drift_history`),
   14개 후보 타입(`IdentityRoleCandidate` … `DriftRecordCandidate`), 노드·엣지 이름은 모두
   [커널 스키마](./spec/01-kernel-schema.md)·[네이밍 정책](./spec/08-naming-and-ids.md)에
   고정돼 있습니다. **구 코드명(`pa.t03`, `t06`, `x12`, `.ba` 등)을 새로 도입하지 마세요** —
   마이그레이션 표를 인용할 때 "구 코드명"으로 표기하는 경우만 허용됩니다.
3. **템플릿/인스턴스를 분리할 것(G6).** 템플릿·스키마·스킬·어댑터는 라이브 레코드를 담지
   않습니다. 예시는 합성/공개 데이터(`examples/logotekton/`류)만 사용하고, 실제 개인 데이터를
   넣지 마세요.
4. **증거에 묶인 것만 더할 것(G1).** 새 스키마 필드든 새 스킬 규칙이든, "왜 이게 필요한가"를
   **세션·교정·사양 근거**로 댈 수 있어야 합니다. 추측으로 만든 필드는 받지 않습니다.

### 3.2 자료별 규칙

**JSON Schema (`schemas/`)** — draft 2020-12. 모든 인스턴스 팩 스키마는
[`record.base.schema.json`](./schemas/record.base.schema.json)을 `allOf` + `$ref`로 확장하고,
팩 고유의 `record_type` enum과 추가 필드만 더합니다. `$id`·`title`·`description`을 채우고,
`description`에는 근거 사양([`spec/03-pack-catalog.md`](./spec/03-pack-catalog.md))을 인용하세요.

- 베이스의 필수 필드를 약화시키지 마세요(`evidence_refs` minItems는 1 이상 유지 — G1).
- 폐기 필드를 되살리지 마세요: `score`(→`confidence`), bare `claim`/`rule_statement`/
  `instruction`/`output_rule`(→`statement`). 표시용 별칭이 필요하면 `description`에 적습니다.
- `id` 패턴(`<subject>.<recordkind>.NNN`)을 바꾸려면 [네이밍 정책](./spec/08-naming-and-ids.md)
  먼저 갱신하고, 드리프트 기록 절차를 따르세요.

**스킬 문서 (`skills/`)** — 13개 빌더 스킬은 고정 순서·고정 id입니다([스킬 README](./skills/README.md)).
스킬을 추가·재배열하려면 거버넌스 토론이 필요합니다. 산문은 한국어 우선 + `> **EN:**` 요약으로
시작하고, 입력→출력 계약과 어느 게이트를 강제하는지를 명시하세요.

**사양 문서 (`spec/`)** — 사양을 바꾸면 그것이 **단일 진실원**이 되므로, 영향받는 스키마·스킬·
템플릿을 같은 PR에서 함께 정합화하세요. 끊어진 정합은 머지하지 않습니다.

**지표·도구 (`tools/`)** — 수렴 지표([수렴 모델](./spec/06-convergence-model.md))나
평가 지표([평가·드리프트](./spec/05-evaluation-drift.md))를 바꾸면, 정의·방향(↑/↓)·성숙도
임계값을 사양과 동시에 갱신하고, `traceability`는 **항상 1.0**이라는 불변식을 깨지 마세요.

### 3.3 제출 전 반드시 실행

```bash
python tools/validate_packs.py examples/logotekton      # 스키마·게이트·정식 이름 검증 (필수, 통과해야 머지)
python tools/convergence_report.py examples/logotekton  # 예제 인스턴스에 영향 줬다면 지표 재계산
#   (도구를 바꿨다면) python -m unittest discover -s tests   # 모든 숫자를 잠근 회귀 스위트
```

`tools/validate_packs.py`는 게이트(G1·G2·G3·G6)와 정식 이름, 베이스 레코드 적합성을
기계적으로 검사합니다. **빨간불인 PR은 머지하지 않습니다.** OpenCrab을 쓴다면 동일 검사를
`opencrab_pack_qa`로 재현할 수 있습니다.

---

## 4. (c) 연구자 · 도구 제작자

PA 스키마를 외부 도구·연구에 연결하려는 분을 위한 갈래입니다.

- **9-space 크로스워크**: 모든 PA 노드는 OpenCrab MetaOntology OS의 9개 공간
  (`subject·resource·evidence·concept·claim·community·outcome·lever·policy`)으로
  사상됩니다([07 크로스워크](./spec/07-opencrab-9space-crosswalk.md)). 새 노드를 제안하면
  반드시 9-space 매핑(`maps_to`)을 함께 제시하세요 — 매핑 없는 노드는 플랫폼에서 고아가 됩니다.
- **재현 가능한 QA**: 품질 주장은 누구나 다시 검사할 수 있어야 합니다. 새 지표·새 채굴법을
  제안할 때는 (1) 정의, (2) 입력(어느 팩·필드에서 오는가), (3) 재현 명령
  (`tools/…` 또는 `opencrab_pack_qa`/`opencrab_project_run`), (4) 예제 결과를 함께 내세요.
- **증거 추적성 보존**: 어떤 변환·집계도 `supported_by`(claim→evidence) 사슬을 끊어선
  안 됩니다. 추적성이 끊기면 게이트 G1과 수렴 지표 `traceability=1.0`이 동시에 무너집니다.

연구 결과로 사양 변경이 필요하면 (b)의 절차로 합류하세요.

---

## 5. PR 체크리스트

PR 본문에 아래를 붙여 자기점검하세요. 하나라도 "아니오"면 *왜 괜찮은지* 본문에 설명하세요.

```
[ ] 어떤 품질 게이트(G1–G6)도 약화/우회/삭제하지 않았다 (했다면 연결된 이슈가 있다)
[ ] 정식 어휘만 사용했다 — 14개 팩 이름 · 14개 후보 타입 · 노드/엣지 이름
[ ] 구 코드명(pa.t03/t06/x12/.ba…)을 새로 도입하지 않았다 (마이그레이션 표 인용 제외)
[ ] 템플릿/인스턴스를 분리했다 (G6) — 예시는 합성/공개 데이터만, 실제 개인 데이터 없음
[ ] 더한 항목은 증거/사양 근거가 있다 (G1) — 추측 필드 아님
[ ] JSON Schema라면: draft 2020-12 · record.base를 allOf+$ref로 확장 · $id/title/description 채움
[ ] 폐기 필드(score, bare claim/rule_statement/instruction/output_rule)를 되살리지 않았다
[ ] `python tools/validate_packs.py` 통과 (출력 첨부)
[ ] 사양을 바꿨다면 영향받는 스키마·스킬·템플릿을 같은 PR에서 정합화했다
[ ] 문서는 한국어 우선 + 짧은 `> **EN:**` 요약으로 시작한다
[ ] 상호 링크는 형제 파일에 대한 상대 경로(예: ./spec/01-kernel-schema.md)를 쓴다
```

---

## 6. 문서 작성 규칙 (요약)

- **언어**: 한국어 우선. 모든 최상위 문서는 2~4문장의 `> **EN:**` 영어 요약으로 시작합니다.
  스키마 키·코드 식별자는 영어([저장소 언어 정책](./spec/08-naming-and-ids.md)).
- **상호 링크**: 형제 파일에 대한 **상대 마크다운 경로**(예: `./skills/05-candidate-extraction.md`)를
  쓰고, 절대 URL을 쓰지 마세요.
- **밀도**: 채움말이 아니라 구체적으로. 기존 사양 문서([`spec/`](./spec))의 밀도를 기준으로 삼으세요.

---

## 7. 행동 규범 · 라이선스

- 기여는 [README 라이선스](./README.md#라이선스)를 따릅니다 — 코드/스키마는 MIT, 문서/사양은
  CC BY-SA 4.0. **당신의 개인 인스턴스 데이터는 이 라이선스의 적용을 받지 않으며, 당신 것입니다.**
- 의사결정·역할·게이트 변경 절차 등 거버넌스는 [GOVERNANCE.md](./GOVERNANCE.md)를 참고하세요.
- 막히면 이슈를 여세요. 좋은 이슈 하나가 좋은 PR의 절반입니다.
