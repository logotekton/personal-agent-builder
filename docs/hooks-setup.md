# 훅 배선 설정 (Hooks Setup) — Claude Code & Codex CLI

> **EN:** This repo ships ready-to-commit hook configs that wire the [trigger model](../spec/09-triggers.md)
> into two hosts so auto-capture can run live: `.claude/settings.json` (Claude Code) and
> `.codex/config.toml` (Codex CLI). Both call one cross-platform entrypoint,
> [`tools/pab.py`](../tools/pab.py) (Python — needs only `python` on PATH, **not `bash`**, so it
> works on native Windows), which is a **STUB** today (logs intent, exits 0, no OpenCrab staging
> yet). The full per-host adapter map is [skills/14-host-binding.md](../skills/14-host-binding.md).
> Verified on **codex-cli 0.141.0** (TOML parses, 5 hooks load; runtime `/hooks` firing must be
> confirmed interactively).

훅은 빌더의 **트리거**([09](../spec/09-triggers.md))를 실제 호스트에 연결해 *자동 포착*을
가동하는 배선입니다. 이 레포는 Claude Code·Codex CLI 두 호스트용 설정을 **커밋된 채로** 제공합니다.

## 어디에 무엇이 쓰이나 (경로 — 특히 Codex 주의)

| 호스트 | 이 레포의 파일 | 호스트가 읽는 위치(레포 단위) | 사용자 단위(머신 전역) |
|--------|----------------|-------------------------------|------------------------|
| **Claude Code** | [`.claude/settings.json`](../.claude/settings.json) | `<repo>/.claude/settings.json` (팀 공유, 커밋) · `.claude/settings.local.json`(나만, gitignore) | `~/.claude/settings.json` |
| **Codex CLI** | [`.codex/config.toml`](../.codex/config.toml) | `<repo>/.codex/config.toml` **또는** `<repo>/.codex/hooks.json` | `~/.codex/config.toml` · `~/.codex/hooks.json` |

- **레포에 커밋 = 이식성.** 그 레포를 여는 모든 세션(데스크탑이든 웹이든)에 훅이 따라옵니다.
- ⚠️ **Codex 헷갈림 포인트:** Codex는 `[[hooks.*]]` TOML 테이블(이 레포의 `config.toml` 방식)
  **또는** 동일 구조의 `hooks.json` 둘 다 받습니다. 위치도 *유저(`~/.codex/`)* 와 *레포(`<repo>/.codex/`)*
  두 층이 있습니다. 레포 커밋용으로는 **`<repo>/.codex/config.toml`** 하나면 충분합니다(이 레포가
  쓰는 방식). `hooks.json`을 따로 둘 필요 없습니다.
- ⚠️ **Claude *Desktop 앱* 과 혼동 금지:** 채팅 클라이언트(Claude Desktop)는
  `claude_desktop_config.json`으로 MCP만 붙이고 훅 시스템이 없습니다. 여기서 말하는 건 **Claude
  Code**(CLI/IDE/웹)입니다.

## 배선된 5개 훅 (양쪽 1:1)

| 트리거(09) | Claude 이벤트 | Codex 이벤트 | `pab` 서브커맨드 | 하는 일 |
|------------|----------------|--------------|------------------|---------|
| session_start | `SessionStart` | `SessionStart` | `compile-adapter` | 확인 슬라이스 → 런타임 어댑터 |
| turn/correction | `UserPromptSubmit` | `UserPromptSubmit` | `capture --from prompt` | 발화 증거 적재·교정 감지(스테이징) |
| tool_result | `PostToolUse` | `PostToolUse` | `capture --from tool` | 도구 결과 증거 적재(스테이징) |
| pre_external_action | `PreToolUse` | `PreToolUse` | `boundary-check` | 외부·비가역 전 경계 검사 |
| session_end | `Stop` | `Stop` | `mine-and-review` | 마이닝 → **한국어 리뷰보드**(승격은 여기만) |

Codex의 `PreToolUse` `matcher`는 도구명 정규식인데, Codex 도구명은 Claude와 달라서 이 레포는
넓게(`""`=전체) 두었습니다 — `/hooks`로 실제 도구명을 확인한 뒤 좁히세요. (Claude 쪽은
`Bash|Write|Edit|MultiEdit|mcp__.*`로 지정.)

## 명령 형식·플랫폼 (⚠️ Windows 주의)

두 설정 모두 훅 명령이 **`python tools/pab.py <sub>`** 입니다. 이전엔 `bash "$(git rev-parse
--show-toplevel)/tools/pab"` 형태였는데, **native Windows에서는 `bash`/`$(...)`가 PATH/셸에
없어 실패**합니다(Codex CLI 0.141.0에서 확인됨). 그래서 `bash`·명령치환을 제거하고 **`python`만
있으면 도는** 크로스플랫폼 진입점으로 바꿨습니다.

| 플랫폼 | 명령 | 전제 |
|--------|------|------|
| **Windows** (네이티브 Codex/Claude Code) | `python tools/pab.py <sub>` (현재 설정) | `python`이 PATH에 있음(Codex가 이미 사용). Git Bash/WSL 불필요. |
| **macOS / Linux** | 동일 `python tools/pab.py <sub>` | `python`이 Python 3이어야 함. Python 3만 있고 `python`이 없으면 명령을 `python3 tools/pab.py …`로 바꾸거나 `tools/pab`(bash 래퍼) 사용 |

- 명령은 **상대경로**(`tools/pab.py`)라 훅 실행 시 **cwd=레포 루트**를 전제합니다(두 호스트의 기본
  동작). cwd가 다르면 절대경로로 바꾸세요.
- `tools/pab`(bash)는 Unix 편의 래퍼로 남겨 두었고, 내부적으로 `python3 tools/pab.py`를 호출합니다.

## ⚠️ 지금은 STUB 입니다 (정직하게)

[`tools/pab.py`](../tools/pab.py)는 **자리표시 스텁**입니다 — 무엇을 *할지* 로그로 남기고 `exit 0`만
합니다. **아직 OpenCrab에 아무것도 스테이징하지 않습니다.** 그래서 지금 훅을 켜도 동작은
안전무해하지만 라이브 포착은 아닙니다. 로그는 `${PAB_LOG:-${TMPDIR:-/tmp}/pab-hooks.log}`에 쌓입니다.

**라이브로 만들려면** `pab.py`의 각 분기(`compile-adapter`/`capture`/`boundary-check`/
`mine-and-review`)를 실제 호출로 교체:
- `capture` → `opencrab ingest_text(pack_visibility="draft")`로 후보 **스테이징**(pending, G3).
- `mine-and-review` → 트랜스크립트 마이닝 → 리뷰보드 → 승인분만 인스턴스 팩으로 라우팅.
  여기서 [dedup judge](../spec/10-dedup-and-merge.md)가 novel/duplicate/refinement/conflict를
  분류해 confirm/**merge**/**supersede**로 보냅니다(중복 없이 누적).
- `boundary-check` → 경계 규칙 매칭 시 ask_confirm/deny.

불변식: 포착은 스테이징만(G3), 승격은 사람 확인 후, 민감 항목은 경계 먼저(G5).

## 활성화 / 신뢰

- **Claude Code:** 프로젝트 `settings.json`의 훅은 보안상 **사용자 승인** 후 실행됩니다. 설정은
  `update-config` 스킬 또는 직접 편집으로 관리합니다.
- **Codex CLI:** 비관리 명령 훅은 **해시 기준 검토·신뢰**가 필요합니다 — `/hooks`로 점검·신뢰·
  비활성화. 훅이 바뀌면 다시 검토 대상이 됩니다. (`notify`는 `agent-turn-complete` 알림 채널로 별도.)

## 관련 문서
- 호스트별 어댑터 전체(매핑·Agents SDK·순수 API): [skills/14-host-binding.md](../skills/14-host-binding.md)
- 트리거 모델(2계층·스테이징/승격): [spec/09-triggers.md](../spec/09-triggers.md)
- 중복 억제(리뷰보드의 merge/supersede): [spec/10-dedup-and-merge.md](../spec/10-dedup-and-merge.md)
- 사용자 절차 전체: [docs/build-your-personal-agent.md](./build-your-personal-agent.md)

> 출처: Codex 훅 이벤트·경로·신뢰 모델은 OpenAI Codex 문서(developers.openai.com/codex/hooks)와
> 설정 참조에 근거. Claude Code 훅 스키마는 Claude Code settings.json 훅 사양에 근거.
