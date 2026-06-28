# 00 · 개요 (System Overview)

> **EN:** Personal Agent Builder converts a person's persona and tacit knowledge into
> evidence-bound ontology packs and compiles them into a controlled assistant — the
> Personal Agent. Four pack classes (skill / template / instance / adapter), a 12-step
> evidence-bound pipeline, 14 user ontology packs, a privacy/authority model, an
> evaluation+drift loop, and a measurable convergence model. Read order below.

## 핵심 명제 — de-averaging (왜 만드는가)

> 목표는 *일반적으로 똑똑한* 에이전트가 아니라 **당신으로 수렴하는** 에이전트입니다. 그 핵심은
> **de-averaging**입니다: 에이전트는 **당신의 증거가 있는 곳에서만 당신처럼** 행동하고, 증거가 없는
> 곳에서는 일반·평균값으로 둘러대지 않고 **기권하거나 묻습니다.** 빈 영역을 인구 평균으로 채우는
> 순간, 그건 *당신*이 아니라 *이름만 당신인 일반 모델*이 됩니다.

그래서 이 시스템은 (a) 모든 활성 규칙을 **증거에 결속**하고(G1·`traceability`=1.0), (b) 성숙도를
폭만이 아니라 **깊이**로 재며(한 영역을 먼저 깊게 — overfit-tiny-set-first), (c) 데이터가 없는
영역을 **off-frontier(draft-only)** 로 표시해 *모르는 곳을 아는 것*을 측정합니다. 측정·강제는
[06 수렴 모델 §8](./06-convergence-model.md#8-깊이de-averaging--모르는-곳을-아는-것이-수렴이다),
부정 증거(무엇이 *당신이 아닌가*)는 [`user.red_flags`](./03-pack-catalog.md)가 담습니다.

## 무엇을 만드는가

세 가지를 분리해서 다룹니다 — 섞으면 신뢰가 무너지기 때문입니다(거버넌스 핵심).

1. **방법(스킬)** — 암묵지를 어떻게 포착·추출·확인·라우팅·컴파일하는가. → 13개 `skill.pab.*`
2. **형태(템플릿/스키마)** — 각 팩이 어떤 필드와 검증 규칙을 갖는가. → 14개 `user.*` 스키마
3. **데이터(인스턴스)** — 특정 개인의 확인된 레코드. → `personal.<subject>.*`
4. **런타임(어댑터)** — 확인된 슬라이스를 모아 작업별로 컴파일한 실행 프로필. → `*.runtime_adapter`

## 읽는 순서

| 문서 | 내용 |
|------|------|
| [01 커널 스키마](./01-kernel-schema.md) | 노드/엣지 타입, 라이프사이클, 6개 게이트, 베이스 레코드, 후보↔라우팅 |
| [02 빌더 파이프라인](./02-builder-pipeline.md) | 12단계 + 13개 스킬이 어떻게 연결되는가 |
| [03 팩 카탈로그](./03-pack-catalog.md) | 14개 user 온톨로지 팩의 목적·레코드 타입 |
| [04 프라이버시·경계](./04-privacy-boundary.md) | 경계 범주, 권한 레벨, 기본 안전 정책 |
| [05 평가·드리프트](./05-evaluation-drift.md) | 8개 지표, 평가 케이스, 드리프트 루프 |
| [06 수렴 모델](./06-convergence-model.md) | 6개 수렴 지표 + 5단계 성숙도 (참여 훅) |
| [07 9-space 크로스워크](./07-opencrab-9space-crosswalk.md) | OpenCrab 정식 문법과의 정합 |
| [08 네이밍·ID](./08-naming-and-ids.md) | 정식 이름, system_pack_id vs display_name |
| [09 트리거](./09-triggers.md) | 스킬 발화 조건, 훅 매핑, 스테이징/승격 경계, auto-confirm 정책 |
| [10 중복 억제·병합](./10-dedup-and-merge.md) | upsert·dedup judge·merge/supersede, redundancy/merge_rate 지표 |
| [12 확인 정책](./12-confirmation-policy.md) | 승격에 사람 확인이 언제 필요한가 — regret·네 결정 축·4계층 임계(섀도 캘리브레이션·성숙도 게이트). 07/09 심화 |

## 한눈에 보는 파이프라인

```
증거포착 → (세션마이닝 | 질문 | diff마이닝) → 후보추출 → 스코프지정
        → 확인게이트 → 팩라우팅 → 프라이버시경계 → 컴파일 → 평가/드리프트 ↺
```

각 단계는 입력/출력 계약과 담당 Crab 역할을 가집니다([02](./02-builder-pipeline.md),
[12 오케스트레이션](../skills/12-crab-orchestration.md)).

## 신뢰의 근거 (6개 게이트)

G1 증거 없는 주장 금지 · G2 스코프 없는 규칙 금지 · G3 미확인 후보의 런타임 활성화 금지 ·
G4 행동 언어만 · G5 승격 전 프라이버시 · G6 템플릿/인스턴스 분리. → [01](./01-kernel-schema.md#2-품질-게이트-quality-gates)

## OpenCrab과의 관계

OpenCrab은 **플랫폼/인프라**(온톨로지 저장·검색·QA·crab_agent 빌드)이고, **Personal Agent**는
이 위에서 만들어지는 **산출물(공식 모델명)**입니다. PA 스키마는 OpenCrab의 9-space 문법으로
사상됩니다([07](./07-opencrab-9space-crosswalk.md)).
