# ECWM 세션 — 전이성 테스트 적용 (worked example: mine the decider, not the topic)

> **EN:** A real first-session extraction normalized by the **transferability test**
> ([skills/02 §1.1](../../../skills/02-session-mining.md#11-전이성-테스트--주체를-캐고-주제를-캐지-마라-mine-the-decider-not-the-topic)).
> The raw extraction (OpenCrab pack `personal.logotekton.ecwm_session.v0.1`) mixed *project facts*
> ("ECWM is a next-gen architecture", "ECWM connects to OpenCrab") with *tacit knowledge* (how the
> user decides, reasons, prefers). This example shows the filter applied: project facts relegated
> to `memory_project_graph`, project-flavored patterns re-scoped to their transferable core, and
> the result normalized to the canonical [`candidate.schema.json`](../../../schemas/candidate.schema.json)
> contract. Output: [`candidates.yaml`](./candidates.yaml).

이 폴더는 **실제 ECWM 구상 세션** 추출을 [전이성 테스트](../../../skills/02-session-mining.md#11-전이성-테스트--주체를-캐고-주제를-캐지-마라-mine-the-decider-not-the-topic)로
거른 worked example입니다. 원본은 빌더 스킬로 추출돼 OpenCrab "personal agent" 프로젝트에 들어간
`personal.logotekton.ecwm_session.v0.1` 팩(후보 11개). 문제는 *프로젝트 사실*과 *암묵지*가 섞여
있었다는 것 — 개인 에이전트는 *당신이 무엇을 만드는가*가 아니라 *당신이 어떻게 생각하는가*입니다.

## 테스트 — "프로젝트를 바꿔도 참인가?"

| 원본 후보 | 판정 | 조치 |
|-----------|------|------|
| DOMAIN-001 "ECWM은 ~한 차세대 아키텍처" | ❌ 프로젝트 사실 | `domain_overlays` → **`memory_project_graph` 강등** (`project_cand.001`) |
| MEMORY-001 "ECWM은 OpenCrab과 연결" | ❌ 프로젝트 사실 | `memory_project_graph` 유지 (`project_cand.002`) |
| DECISION-001 "온톨로지/증거/런타임 명시 분리 선호" | ◐ 암묵지(재스코프) | ECWM 8계층 제거 → "관심사 명시적 계층분리 선호" (`decision_cand.001`) |
| ARTIFACT-001 "복잡 개념 → 배경·근거·단계 담은 MD 플랜" | ✅ 암묵지 | `artifact_policy` (`artifact_cand.001`) |
| TACIT-001 "고차원이면 다중 투영" | ◐ 암묵지(재스코프) | 'One-Model-Many-Projections' 브랜딩 제거 (`heuristic_cand.001`) |
| REDFLAG-002 "AI 추출 주장을 확정사실로 안 본다" | ✅ 암묵지 | `red_flags` (`redflag_cand.001`) |
| WORKFLOW-001 "개념정의→…→산출물" | ✅ 암묵지 | `workflow_playbooks` (`workflow_cand.001`) |
| TOOL-001 "OpenCrab을 능동 빌드도구로" | ✅ 암묵지 | `tool_stack` (`tool_cand.001`) |
| DECISION-002 "MCP-first" | — | 사용자 거절 (제외) |
| REDFLAG-001 "ECWM을 단순 그래프로 붕괴 금지" | ◐ 프로젝트 종속 | 일반 원칙 재스코프 또는 강등 (보류) |
| EVAL-001 "좋은 답은 개념층 구분" | ✅ 암묵지(보류) | 원본 evidence_refs 확정 후 `evaluation_cases` |

**결과:** 11개 중 **2개 순수 프로젝트 사실**(강등) · **2개 재스코프** · **6개 전이 가능 암묵지 유지** ·
**1개 거절** · **2개 보류**(원본 재확인 필요). 정규화 산출 = [`candidates.yaml`](./candidates.yaml)의 후보 8개.

## 정규화로 바뀐 것

1. **프로젝트 사실 강등** — 페르소나/도메인 팩 → `memory_project_graph`(런타임이 "현재 프로젝트 맥락"으로만 씀).
2. **재스코프** — 프로젝트 고유 디테일을 벗기고 *패턴*만; `scope`는 프로젝트명이 아닌 *패턴 조건*.
3. **sensitivity** — `work_pattern`/`work_preference`/`low` → 정식 enum `{public, internal, sensitive, restricted}`.
4. **어휘 정규화** — `review_status: candidate_pending_review` → `validation_status: pending`; id `CAND-ECWM-…` → `<subject>.<recordkind>.NNN`.
5. **증거 보존** — `evidence_refs`(EV-ECWM-NN)는 원본 세션 앵커 그대로(G1, 증거 신설 없음).

## 단계·재현

- 이건 **확인 전(pending) 후보**입니다. 다음은 S07 확인 게이트 → S08 라우팅 → 14개 정식 팩의 *베이스
  레코드*(그때 `validate_packs.py` 검증 대상). 현재는 후보 단계(G3: 확인 전 런타임 비활성).
- 후보 8개는 [`candidate.schema.json`](../../../schemas/candidate.schema.json)의 필수필드·enum·
  **candidate_type↔proposed_target_pack 1:1 라우터**·G1(evidence_refs≥1)을 모두 만족합니다(구조 검증 완료).

## 인접 문서
- 전이성 테스트(제1 추출 필터): [`skills/02-session-mining.md §1.1`](../../../skills/02-session-mining.md)
- 후보 계약·1:1 라우팅: [`schemas/candidate.schema.json`](../../../schemas/candidate.schema.json) · [`skills/05-candidate-extraction.md`](../../../skills/05-candidate-extraction.md)
- 프로젝트 사실의 귀착지: [`spec/03 §12 memory_project_graph`](../../../spec/03-pack-catalog.md#12-usermemory_project_graph)
- de-averaging 입구: [`spec/00-overview.md`](../../../spec/00-overview.md)
