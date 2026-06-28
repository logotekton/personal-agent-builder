# 14 · 호스트 배선 어댑터 (Host Binding — make auto-capture live)

> **배포 어댑터 — 파이프라인 단계가 아닙니다.** 1–13은 *방법*(파이프라인), 이 문서는 그 방법의
> **트리거([09](../spec/09-triggers.md))를 실제 호스트에 배선해 자동 포착을 실가동**하는 법입니다.

> **EN:** Triggers are abstract (signal → produces → requires_confirmation). A *host adapter*
> binds each trigger to a concrete host mechanism so capture actually runs. Claude Code →
> `settings.json` hooks. **Codex CLI → a Claude-style hooks system with the same events**
> (`config.toml`/`hooks.json`). OpenAI Agents SDK → `RunHooks`/`AgentHooks` + guardrails +
> sessions. Plain API / ChatGPT → your own orchestration middleware. The portable substrate
> across all of them is **MCP** (OpenCrab is an MCP server callable from any of these hosts),
> so the capture/stage/promote *actions* are identical — only the *triggering* differs.

## 1. 원리 — 트리거는 추상, 배선은 호스트별

[09 트리거](../spec/09-triggers.md)는 *언제 무엇이 일어나는가*를 호스트 독립적으로 정의합니다.
이 어댑터는 그 추상 트리거의 `host_hook`을 **실제 메커니즘**에 연결합니다. 두 가지가 호스트가
바뀌어도 그대로입니다:

- **행동(capture/stage/promote)** → 전부 MCP로 수행(OpenCrab `ingest_text`/`pack_update`).
  Claude·Codex·Agents SDK 모두 MCP를 지원하므로 *행동 코드는 한 벌*이면 됩니다.
- **불변식(G3/G5)** → 스테이징은 `pending`/`draft`, 승격은 게이트. 호스트와 무관하게 동일.

바뀌는 건 오직 **"무엇이 트리거를 발화시키는가"** — 그게 아래 호스트별 표입니다.

## 2. 호스트별 매핑 (한 장 표)

| 추상 트리거 (09) | Claude Code 훅 | **Codex CLI 훅** | OpenAI Agents SDK | 순수 API / ChatGPT |
|------------------|----------------|------------------|--------------------|--------------------|
| `session_start` → 컴파일 | `SessionStart` | `SessionStart` | `on_agent_start` | 세션 init 코드 |
| `turn`/`user_correction` → 포착 | `UserPromptSubmit` | `UserPromptSubmit` | 입력 처리 / `RunHooks` | 요청 전 미들웨어 |
| `tool_result` → 포착 | `PostToolUse` | `PostToolUse` | `on_tool_end` | 도구 실행 후 래퍼 |
| `pre_external_action` → 경계 | `PreToolUse` | `PreToolUse` · `PermissionRequest` | 입력 guardrail / 도구 게이트 | 도구 호출 인터셉터 |
| `session_end` → 마이닝+리뷰 | `Stop` | `Stop` | `on_agent_end` | 대화 종료 핸들러 |
| `schedule` → 배치 | 외부 cron | 외부 cron | 외부 스케줄러 | cron / 큐 워커 |

> **핵심 결론:** Codex CLI는 Claude와 **거의 1:1**입니다(같은 이벤트 이름). Claude→Codex 이식은
> 사실상 *설정 파일만 바꾸는 일*입니다. 프로그램형 에이전트(자체 빌드)는 Agents SDK 콜백,
> 호스트 훅이 없는 순수 API/ChatGPT는 *당신의 래퍼 레이어*에 같은 트리거 논리를 넣습니다.

## 3. Claude Code — 실가동 배선 (primary, 이 환경에서 검증됨)

`settings.json`의 `hooks`에 트리거를 배선합니다(이 환경은 이미 SessionStart/UserPromptSubmit/
Stop 훅을 사용 → 메커니즘 검증됨). 훅은 셸 명령을 실행하므로, 명령이 작은 스크립트를 호출해
OpenCrab MCP로 스테이징합니다.

```jsonc
// .claude/settings.json (발췌, 대표값)
{
  "hooks": {
    "SessionStart":     [{ "hooks": [{ "type": "command", "command": "pab compile-adapter" }] }],
    "UserPromptSubmit": [{ "hooks": [{ "type": "command", "command": "pab capture --from prompt" }] }],
    "PostToolUse":      [{ "hooks": [{ "type": "command", "command": "pab capture --from tool" }] }],
    "PreToolUse":       [{ "matcher": "Bash|Write|Edit|mcp__.*",
                          "hooks": [{ "type": "command", "command": "pab boundary-check" }] }],
    "Stop":             [{ "hooks": [{ "type": "command", "command": "pab mine-and-review" }] }]
  }
}
```

- `pab capture` = 발화/도구 결과를 EvidenceItem으로 적재 + 교정 감지 → **draft 후보 스테이징**
  (OpenCrab `ingest_text(pack_visibility:"draft")`). `requires_confirmation:false`, 스테이징만.
- `pab boundary-check` = 외부·비가역 도구 호출 직전 경계 검사 → 필요시 ask_confirm/block(G5).
- `pab mine-and-review` = 세션 끝에 트랜스크립트 마이닝 → **한국어 리뷰보드** 제시(승격은 여기만).
- 설정/문제 해결은 `update-config` 스킬, 검증은 `pab validate`로.

> 훅은 셸을 실행할 뿐이므로, MCP 호출은 `pab` 같은 얇은 스크립트(또는 로컬 큐)가 담당합니다.
> 행동은 전부 MCP라 호스트가 바뀌어도 이 스크립트는 재사용됩니다.

## 4. Codex CLI — 같은 이벤트, 다른 설정 파일

Codex CLI는 Claude식 훅 시스템을 제공합니다. 라이프사이클 이벤트가 거의 동일합니다:
`SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PermissionRequest`, `PostToolUse`,
`PreCompact`/`PostCompact`, `SubagentStart`, `SubagentStop`, `Stop`.

- **설정 위치:** `~/.codex/hooks.json` 또는 `~/.codex/config.toml`의 인라인 `[hooks]`,
  레포 단위 `<repo>/.codex/hooks.json`·`config.toml`. (Claude의 `settings.json` 대체)
- **신뢰 모델:** 비관리 명령 훅은 *해시 기준 검토·신뢰*가 필요하고, 바뀌면 다시 검토 대상.
  `/hooks`로 점검·신뢰·비활성화.
- **`notify`:** 외부 프로그램을 `agent-turn-complete` 같은 이벤트에 거는 알림 채널(보조).
- **승인/샌드박스 모드:** 도구 실행 게이트(= `PreToolUse` 경계의 또 다른 표면).

```toml
# ~/.codex/config.toml (발췌, 대표값)
[hooks]
SessionStart = [{ command = "pab compile-adapter" }]
PostToolUse  = [{ command = "pab capture --from tool" }]
Stop         = [{ command = "pab mine-and-review" }]
```

→ Claude 배선(§3)의 `pab ...` 스크립트를 **그대로 재사용**하고 설정 파일만 바꾸면 됩니다.

## 5. OpenAI Agents SDK — 프로그램형 에이전트(자체 빌드)

호스트 훅 대신 **라이프사이클 콜백**으로 배선합니다.

- `RunHooks`(전역 관찰자) / `AgentHooks`(특정 에이전트) — `on_agent_start`(컴파일),
  `on_tool_start`/`on_tool_end`(포착), `on_agent_end`(마이닝+리뷰), `on_handoff`.
- **Guardrails**(input/output) = 경계·프라이버시 레이어(09/04와 대응).
- **Sessions** = 메모리(인스턴스 어댑터 로드 자리).

```python
from agents import RunHooks
class PABHooks(RunHooks):
    async def on_agent_start(self, ctx, agent):           # session_start
        await mcp.compile_adapter(subject=ctx.subject)
    async def on_tool_end(self, ctx, agent, tool, result):# tool_result 포착
        await mcp.stage_evidence(result)                  # draft, 스테이징만
    async def on_agent_end(self, ctx, agent, output):     # session_end
        await mcp.mine_and_request_review(ctx.transcript) # 승격은 리뷰 후
# guardrails = boundary(09 PreToolUse 대응) · sessions = 인스턴스 메모리
```

## 6. 순수 API / ChatGPT — 래퍼 레이어 (훅 없음)

호스트 훅이 없으면, **당신의 오케스트레이션 미들웨어**에 같은 트리거 논리를 넣습니다:

- 세션 init → 어댑터 컴파일을 시스템 프롬프트에 주입(`session_start`).
- 각 모델 호출 전후 미들웨어 → 증거 적재·교정 감지(`turn`/`tool_result`).
- 도구 호출 인터셉터 → 경계 검사(`pre_external_action`).
- 대화 종료 핸들러 → 마이닝 + 리뷰보드(`session_end`).
- 외부 스케줄러(cron/큐) → 배치 마이닝(`schedule`).
- 또는 빌더 동작을 **MCP 툴로 노출**해 모델이 직접 호출하게 함(가장 이식성 높음).

ChatGPT 소비자 제품은 *memory*(인스턴스 팩의 가장 가까운 유사물)는 있으나 라이프사이클 훅이
없으므로, 위 래퍼/앱 레이어 또는 MCP 경로를 씁니다.

## 7. 불변식 (호스트 무관)

- 스테이징은 항상 `pending`/`draft`, 컴파일러는 `confirmed`만 활성화(G3). 호스트와 무관.
- 민감 항목은 승격 전 경계 규칙(G5). 외부·비가역 행동 전 ask_confirm.
- 행동(capture/stage/promote)은 MCP(OpenCrab)로 — *한 벌의 행동 코드, 여러 호스트의 트리거*.

## 인접 문서
- 추상 트리거 모델: [../spec/09-triggers.md](../spec/09-triggers.md)
- 오케스트레이션(트리거 라우팅): [12 crab_orchestration](./12-crab-orchestration.md)
- 프라이버시/경계(boundary·guardrail 대응): [../spec/04-privacy-boundary.md](../spec/04-privacy-boundary.md)
- 머신 스키마: [../schemas/trigger.schema.json](../schemas/trigger.schema.json)
- 사용자 절차·개입 시점: [../docs/build-your-personal-agent.md](../docs/build-your-personal-agent.md)
