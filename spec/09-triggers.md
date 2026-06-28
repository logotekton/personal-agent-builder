# 09 · 트리거 (Triggers — when the builder fires)

> **EN:** A trigger is a skill's **activation condition** — when it fires and what it
> produces — bound to a host hook (Claude Code hooks / OpenCrab crab_orchestration entry
> conditions / cron). The model is two-layer: **ambient event capture** (always-on, stages
> candidates as you work) + a **single session-boundary confirmation** (the one human
> checkpoint). The cardinal rule: a trigger fires **detection/staging only** — promotion to
> a runtime-active record stays gated (G3/G5) unless a narrow `auto_confirm_policy` allows it.
> Machine schema: [`../schemas/trigger.schema.json`](../schemas/trigger.schema.json).

트리거는 빌더가 *언제* 켜지는가를 정의합니다. 핵심은 한 줄로 요약됩니다:

> **포착(detection)은 앰비언트로 자동, 승격(promotion)은 한 번의 명시적 확인.**
> 작업 중 마찰 0, 사람 체크포인트는 세션 끝에 딱 1회.

암묵지는 *말로 꺼내지 않는 것*이라, "이제 캡처하자"는 명령형 트리거는 본질을 놓칩니다. 그래서
포착은 **행동 신호에서 자동**으로 일어나야 하고, 동시에 휴먼인더루프(G3)·프라이버시(G5)를
지키려면 **승격은 자동이 아니어야** 합니다. 이 둘을 트리거가 분리합니다.

## 1. 2계층 모델

```
┌─ 계층 A · 앰비언트 포착 (always-on, 무마찰) ──────────────────────────┐
│  매 턴 / 도구결과 → EvidenceItem 적재          (evidence_capture)      │
│  사용자 교정·재작성 → 후보 스테이징  ★flagship  (diff_mining)          │
│  반복 요청·명시 선호 → 후보 스테이징           (session_mining/extract) │
│  ↳ 전부 pending/draft 로만 쌓임 (G1 증거결속, G3 비활성)               │
└───────────────────────────────────────────────────────────────────────┘
                                  │  (세션 경계)
                                  ▼
┌─ 계층 B · 단일 확인 체크포인트 (deliberate) ──────────────────────────┐
│  세션 끝 / 큐 ≥ K / 명령 → 한국어 리뷰보드     (confirmation_gate)     │
│  confirm·edit·reject·narrow → 승인된 것만 라우팅 (pack_router)         │
│  ↳ 여기서만 pending → confirmed (런타임 활성)                          │
└───────────────────────────────────────────────────────────────────────┘
```

- **계층 A는 공격적으로 깔아도 안전합니다** — 무엇을 하든 `requires_confirmation: false`이지만
  *스테이징만* 하기 때문입니다. 라이브 규칙이 되지 않습니다.
- **계층 B가 유일한 사람 개입점**입니다. 작업 중엔 아무것도 묻지 않고, 끝에 한 번 빠르게 승인.

## 2. 스킬별 트리거 (정식 표)

| 스킬 | signal | cadence | host_hook | produces | 확인? | 기본 |
|------|--------|---------|-----------|----------|:---:|------|
| evidence_capture | turn / tool_result | continuous | UserPromptSubmit · PostToolUse | evidence_staged | ✗ | enabled |
| **diff_mining** ★ | user_correction | event | UserPromptSubmit · PostToolUse | candidate_staged | ✗ | enabled |
| session_mining | session_end | session_boundary | Stop · Cron | candidate_staged | ✗ | enabled |
| candidate_extraction | review_queue_threshold | threshold | Stop · chained | candidate_staged | ✗ | enabled |
| scope_context | candidate_created | event | chained | scoped | ✗ | enabled |
| elicitation_questioning | coverage_gap / command | event · command | orchestrator · command | candidate_staged | ✓ (묻는다) | suggested |
| **confirmation_gate** | session_end / queue≥K / command | session_boundary | Stop · command | review_requested | ✓ **(게이트)** | enabled |
| pack_router | candidate_confirmed | event | chained | routed | ✗ (게이트 후) | enabled |
| privacy_boundary | sensitivity_flag / pre_external_action | event | PreToolUse | boundary_applied | ✓ (ask_confirm) | enabled |
| agent_compiler | session_start | session_boundary | SessionStart | compiled | ✗ | enabled |
| evaluation_drift | pack_updated / schedule | schedule | Cron · chained | evaluated · drift_recorded | ✗ | suggested |
| crab_orchestration | (메타: 위 전부를 라우팅) | — | orchestrator | — | — | enabled |

`kernel_schema`는 스키마 척추라 트리거가 없습니다. 각 스킬 문서의 **## 트리거** 절에 동일한
블록이 [trigger.schema.json](../schemas/trigger.schema.json) 형식으로 들어 있습니다.

## 3. 호스트 매핑 (트리거 = 훅 바인딩)

트리거는 추상 개념이 아니라 **실제 호스트 훅에 그대로 사상**됩니다.

### Claude Code 훅 (in-session, 가장 자연스러움)
| 훅 이벤트 | 묶이는 트리거 | 하는 일 |
|-----------|---------------|---------|
| `SessionStart` | agent_compiler | 확인된 슬라이스로 런타임 어댑터 컴파일·로드 |
| `UserPromptSubmit` | evidence_capture, diff_mining | 사용자 발화에서 증거·교정 신호 감지 → 스테이징 |
| `PostToolUse` | evidence_capture | 도구 결과를 EvidenceItem으로 적재 |
| `PreToolUse` | privacy_boundary | 외부·비가역 도구 호출 직전 경계 검사(ask_confirm/block) |
| `Stop` (세션 끝) | session_mining, candidate_extraction, confirmation_gate | 트랜스크립트 마이닝 → 후보 → **한국어 리뷰보드** 제시 |

> 이 환경은 이미 `SessionStart`·`UserPromptSubmit`·`Stop` 훅을 사용합니다 — 메커니즘이
> 검증된 자리입니다. 훅 설정은 `settings.json`에서 합니다([update-config] 참고).

### OpenCrab (crab_orchestration 진입 조건)
crab_orchestration의 9개 워크플로 상태의 *진입 조건*이 곧 트리거입니다. 핸드오프 규칙의 입력
쪽을 트리거 라우팅표로 둡니다 → [12 crab_orchestration](../skills/12-crab-orchestration.md).
스테이징 저장소는 `opencrab_ingest_text(pack_visibility="draft")`입니다.

### Cron (배치/백그라운드)
`durable` cron으로 "새 트랜스크립트를 주기적으로 마이닝"을 돌릴 수 있습니다(예: 매일 밤).
주의: cron은 세션 idle 시에만 발화하고 7일 후 만료되며, 헤드리스 실행에서는 인증된 MCP가
없을 수 있습니다(OpenCrab은 mcp_key라 키가 있으면 동작).

## 4. 스테이징 vs 승격 (절대 경계)

| | 스테이징 (계층 A) | 승격 (계층 B) |
|--|------------------|---------------|
| 누가 | 트리거 자동 | 확인 게이트 (사람) |
| 상태 | `pending` / `draft` | `confirmed` / `narrowed` |
| 런타임 | **비활성** (컴파일 제외, G3) | 활성 |
| 프라이버시 | 민감 항목 플래그만 | 민감 항목은 경계 규칙 먼저(G5) |

이 경계가 "다 자동인데 안 무섭다"의 핵심입니다. 트리거를 아무리 공격적으로 깔아도 라이브
규칙은 사람을 거칩니다.

## 5. auto-confirm 정책 (좁은 예외)

매번 묻는 게 번거로운 *명백한* 케이스를 위해, 확인 게이트를 좁게 우회하는 정책을 정의할 수
있습니다. **모든 조건이 참일 때만** 자동 확정:

```yaml
auto_confirm_policy:
  min_confidence: 0.9
  allowed_sensitivity: [public, internal]        # restricted 절대 불가, sensitive는 경계규칙 필요
  require_any: [explicit_user_statement, repetition_ge_3, correction_backed]
  never_auto_confirm_types:                       # 고위험 타입은 항상 사람 검토
    - BoundaryRuleCandidate
    - DecisionPolicyCandidate
```

정책이 없으면(기본) **항상 사람 검토**입니다. 정책은 신뢰 수준을 올리는 *선택적 노브*이지,
프라이버시 모델을 약화시키는 우회로가 아닙니다 — `never_auto_confirm_types`와
`allowed_sensitivity`가 그 선을 지킵니다.

## 6. 게이트 보존 (왜 안전한가)

- **G1** 모든 스테이징 후보는 `evidence_refs`에 묶임 — 트리거는 증거 없는 항목을 만들지 않음.
- **G3** 스테이징은 `pending`/`draft`. 컴파일러는 `confirmed`만 활성화 → 미확인 항목 런타임 진입 0.
- **G5** `sensitivity_flag` 트리거(privacy_boundary)가 민감 항목을 *승격 전에* 잡아 경계 규칙을 요구.
- 따라서 **계층 A 트리거는 전부 `enabled`로 두어도** 안전합니다. 위험은 승격에만 있고, 승격은
  계층 B(+선택적 좁은 정책)가 통제합니다.

## 인접 문서
- 머신 스키마: [`../schemas/trigger.schema.json`](../schemas/trigger.schema.json)
- 오케스트레이션(트리거 라우팅표): [12 crab_orchestration](../skills/12-crab-orchestration.md)
- 라이프사이클·게이트: [01 커널 스키마](./01-kernel-schema.md)
- 프라이버시/권한(경계 트리거): [04 프라이버시·경계](./04-privacy-boundary.md)
- 사용자 개입점·전체 절차: [다른 유저용 설명서](../docs/build-your-personal-agent.md)
