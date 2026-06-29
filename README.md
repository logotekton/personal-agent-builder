# Personal Agent Builder

> **EN summary** — A method and an open schema for turning *what you tacitly know* and
> *how you consistently act* into evidence-bound ontology packs, captured from real sessions
> with an AI agent. As the packs accumulate, they **converge** into a *Personal Agent*: a
> controlled, **delegable working-self** that decides, writes, and acts the way **you** would
> approve *in the domains where it has your evidence* — and **abstains** (rather than faking
> you with population averages) everywhere else — and can prove why, from evidence. It is built
> from *observed behavior*, not guessed psychology: a verbal self-description is carried as a
> low-trust, draft-only signal, never mistaken for behavioral evidence, and "the agent is
> becoming you" is treated as a reviewed application claim, not an inherited fact. This is a
> working-self, **not a whole-person digital twin**. This repo is the open specification:
> the builder skills, the 14 user ontology packs, the privacy model, the evaluation loop, and a
> measurable convergence model. Built on the [OpenCrab](https://opencrab.ai) ontology platform.
> Contributions welcome — see [CONTRIBUTING](./CONTRIBUTING.md).

---

## 왜 이 프로젝트인가

당신은 이미 매일 AI 에이전트와 일합니다. 무언가를 부탁하고, 결과를 고치고, "이건 이렇게
해줘"라고 말하고, 어떤 출력은 받아들이고 어떤 출력은 버립니다. 그 한 번의 교정, 한 번의
"아니 그거 말고", 한 번의 포맷 선호 — 거기에는 **당신만의 암묵지**가 들어 있습니다. 그런데
세션이 끝나면 그 지식은 흩어져 사라집니다. 다음 세션의 에이전트는 당신을 다시 모릅니다.

**Personal Agent Builder는 그 흩어지는 암묵지를 붙잡습니다.**

핵심 명제는 단순합니다:

> 개인의 페르소나와 암묵지를, AI 에이전트와의 실제 세션에서 **증거 기반 온톨로지 팩**으로
> 포착하면, 그것이 쌓여 **개인 에이전트(Personal Agent)**로 **수렴**한다.

추측으로 만든 "AI 페르소나"가 아닙니다. 매 항목이 **실제 증거**(세션, 교정, 파일, 결정
기록)에 묶이고, **당신의 승인**을 거친 뒤에야 에이전트의 규칙이 됩니다. 그래서 이 에이전트는
"왜 그렇게 했어?"라는 질문에 항상 답할 수 있습니다 — 근거를 가리키며.

## 한 장 그림

```
  실제 AI 세션 ─┐
   교정/diff  ─┤   (1) 증거 포착        EvidenceItem
   인터뷰     ─┘        │
                        ▼
            (2) 채굴/추출            CandidateAssertion  ── 모든 후보는 증거에 묶임
                        │
                        ▼
            (3) 스코프 지정          "언제/어디서 참인가"
                        │
                        ▼
        ┌── (4) 확인 게이트 ──┐      ← 당신이 confirm / edit / reject / narrow
        │   (사람이 검토)     │
        └─────────┬──────────┘
                  ▼ (confirmed만 통과)
            (5) 팩 라우팅            14개 user.* 온톨로지 팩 중 하나로
                  │
                  ▼
            (6) 컴파일               필요한 슬라이스만 → 런타임 어댑터
                  │
                  ▼
          ┌───────────────────┐
          │  Personal Agent   │  ── 당신처럼 판단/작성/행동 (확인 경계 안에서)
          └─────────┬─────────┘
                    ▼
            (7) 평가 & 드리프트      충실도↑, 교정비용↓, 수렴 측정
                    │
                    └──────► 다시 증거로 (루프)
```

14개의 팩이 채워질수록 그림 가운데의 에이전트는 점점 더 **당신**이 됩니다. 그 "점점 더"를
우리는 추측이 아니라 [**수렴 지표**](./spec/06-convergence-model.md)로 측정합니다.

단, 에이전트는 *당신의 증거가 있는 곳에서만* 당신처럼 행동하고, 없는 곳에서는 평균값으로
둘러대지 않고 **기권하거나 묻습니다**(de-averaging). 그래서 이것은 *위임 가능한 '일하는 자아'*이지
전인격 복제가 아닙니다 — 증거가 주로 AI 작업 세션에서 오므로 관계·정서·미적 자아는 채널의
구조적 한계로 [off-ontology](./spec/00-overview.md)이며, 거기서 에이전트는 권위 있게 행동하지
않습니다([스코프·입장](./spec/00-overview.md)).

## 이 저장소에 있는 것

| 폴더 | 내용 |
|------|------|
| [`docs/`](./docs) | **다른 사람을 위한 설명서** — 개념·목적·전체 절차·사용자 개입 시점으로 자기 개인 에이전트를 만드는 법 ([build-your-personal-agent](./docs/build-your-personal-agent.md)) + 훅 배선 설정([hooks-setup](./docs/hooks-setup.md)) |
| [`.claude/`](./.claude), [`.codex/`](./.codex) | 커밋된 **훅 설정** — Claude Code(`settings.json`)·Codex CLI(`config.toml`)에서 자동 포착을 가동하는 배선 + 공유 스텁 [`tools/pab`](./tools/pab) (현재 STUB) |
| [`spec/`](./spec) | 시스템 전체 사양 — 커널 스키마, 빌더 파이프라인, 팩 카탈로그, 프라이버시, 평가, **수렴 모델**, 9-space 크로스워크, 네이밍, **트리거**, 중복 억제·병합, **확인 정책** |
| [`schemas/`](./schemas) | 14개 user 온톨로지 팩의 JSON Schema + 통합 베이스 레코드 + 후보/평가/**트리거** 스키마 (기계 검증용) |
| [`skills/`](./skills) | 13개 빌더 스킬 문서 — 암묵지를 팩으로 바꾸는 *방법* (각 스킬의 발화 **트리거** 포함) + 트리거를 실제 호스트(Claude/Codex/Agents SDK/API)에 배선하는 **호스트 배선 어댑터** |
| [`examples/logotekton/`](./examples/logotekton) | 처음부터 끝까지 동작하는 실제 인스턴스 예제 |
| [`templates/`](./templates) | 새 사용자가 자기 에이전트를 시작할 수 있는 **빈 채우기 템플릿** + [QUICKSTART](./templates/QUICKSTART.md) |
| [`tools/`](./tools) | 결정론적 스크립트 — 스키마 검증(`validate_packs`), 수렴 지표(`convergence_report`), 중복 신호(`dedup_check`), dedup/병합 actuator(`pab_merge`), 컨텍스트 선택 참조 술어(`context_select`), 문서 링크·커맨드 무결성 가드(`check_anchors`·`check_commands`). 모두 테스트로 잠김 |

## 핵심 설계 원칙 (왜 믿을 수 있는가)

1. **증거 우선 (Evidence-first)** — 증거 없는 주장은 없습니다. 모든 레코드는 ≥1개의
   `evidence_refs`를 가집니다. (게이트 G1)
2. **사람이 승인 (Human-in-the-loop)** — 추출된 후보는 *당신이 확인하기 전엔* 절대 런타임
   규칙이 되지 않습니다. (게이트 G3)
3. **스코프 강제 (Always scoped)** — "항상 참인 규칙"은 없습니다. 모든 규칙은 *언제/어디서*
   참인지 명시합니다. (게이트 G2)
4. **프라이버시 경계 (Privacy by boundary)** — 민감 항목은 경계 규칙을 먼저 받고, 외부
   노출·비가역 행동은 항상 확인을 요구합니다.
5. **마이크로 팩 분리 (Micro-pack split)** — 14개로 쪼개 검색 정밀도와 거버넌스를 확보합니다.
   스킬(방법)·템플릿(스키마)·인스턴스(데이터)·어댑터(런타임)는 절대 섞지 않습니다.
6. **측정 가능한 수렴 (Measurable convergence)** — "더 나아졌다"를 느낌이 아니라 6개 지표와
   5단계 성숙도(L0~L4)로 측정합니다. 성숙도의 *깊이*는 **관찰된 행동**으로만 셉니다 — 폭만
   넓힌다고 오르지 않습니다([수렴 모델](./spec/06-convergence-model.md)).
7. **행동 증거만 · 클레임 계층 분리 (Behavioral, claim-layered)** — 에이전트는 *관찰된 행동*에서
   만들어집니다(게이트 G4). 말로 한 자기서술("나는 ~한 사람이다")은 `reliability: self_reported`
   저신뢰 채널로 *운반만* 되고 — 자동 승격 금지·draft 전용·여섯 수렴 지표 전부에서 제외 — 행동
   증거로 둔갑하지 않습니다. "에이전트가 당신이 된다"는 것은 증거가 아니라 *사람 검토를 요하는
   적용 주장*입니다([01 §7.1](./spec/01-kernel-schema.md)).
8. **de-averaging — 위임 가능한 '일하는 자아' (a working-self, not a twin)** — 에이전트는 당신의
   증거가 있는 곳에서만 당신처럼 행동하고, 없는 곳에서는 평균값으로 둘러대지 않고 **기권**합니다.
   그래서 산출물은 *전인격 트윈*이 아니라 일·판단 영역의 **일하는 자아**입니다([스코프·입장](./spec/00-overview.md)).

## 누구를 위한 것인가 / 어떻게 참여하나

- **자기 에이전트를 만들고 싶은 사람** → [`templates/QUICKSTART.md`](./templates/QUICKSTART.md)
  로 첫 세션에서 시작하세요. 당신의 데이터는 기본 비공개입니다.
- **스키마/방법론에 기여하고 싶은 사람** → 14개 팩 스키마, 13개 스킬, 수렴 지표는 모두
  열려 있습니다. [`CONTRIBUTING.md`](./CONTRIBUTING.md) · [`GOVERNANCE.md`](./GOVERNANCE.md).
- **연구자·도구 제작자** → 9-space 크로스워크로 OpenCrab MetaOntology OS와 정합합니다.
  검증 스크립트로 누구나 팩 품질을 재현 검사할 수 있습니다.

이 프로젝트는 한 사람(Logotekton)의 개인 에이전트를 만들려다 시작됐지만, 만들고 보니
**그 방법 자체가 누구에게나 적용되는 공용 자산**이었습니다. 그래서 공개합니다.

## 상태

- 사양 버전: **v0.3** (v0.1/v0.2의 불일치를 정합화한 첫 공개 릴리스; Unreleased 에서 지속 강화).
- 성숙도: 빌더 스킬 + 14 팩 스키마 + 수렴 모델(**깊이 게이트**) + **reliability 클레임-계층** +
  9-space 크로스워크 정의 완료. 결정론적 검증·수렴·병합·컨텍스트-선택 도구는 테스트(72개)·CI 로
  잠겨 있고, 모든 예제 숫자는 도구로 재현됩니다.
- **정직한 한계**: 라이브 자동 포착/컴파일러([`tools/pab`](./tools/pab))는 아직 STUB 입니다 — 검증된 것은
  스키마·지표·선택 수학(참조 술어)이고, 호스트 런타임 배선이 남은 *몸-작업*입니다.
- 다음: 라이브 컴파일러 배선, 더 많은 평가 케이스, 다중 사용자 예제, 자동 채굴 도구.
  [`CHANGELOG.md`](./CHANGELOG.md) 참고.

## 라이선스

코드/스키마: [MIT](./LICENSE). 문서/사양: CC BY-SA 4.0. 자세한 내용은 LICENSE 참고.
당신의 개인 인스턴스 데이터는 당신의 것이며, 이 라이선스의 적용을 받지 않습니다.
