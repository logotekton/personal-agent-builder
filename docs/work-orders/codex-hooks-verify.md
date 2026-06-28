# 업무지시서 — Codex CLI / Claude Code 훅 배선 검증·수정 (PAB auto-capture)

> **EN:** Verify and, where needed, fix this repo's hook wiring for **Codex CLI** and **Claude Code**
> so the 5 auto-capture triggers fire into `tools/pab`. Codex is authoritative about its own
> installed version — VERIFY against the real environment (`codex --version`, `/hooks`) and
> self-correct; do NOT blindly trust the assumptions in this document.
> **EN:** **If `codex` is not installed / `/hooks` is unreachable, do STATIC verification only,
> change nothing runtime-dependent, and escalate (§8).** Keep both hosts 1:1, keep `tools/pab`
> a STUB (exit 0, never blocks), and do NOT touch `spec/*`, `schemas/*`, skill semantics, the 14
> pack names, or the 6 gates.

이 문서를 Codex 에이전트에게 그대로 주고 실행시키면 됩니다. **추측 금지 — 실측 안 되면 멈추고 보고.**

---

## 1. 목적·배경

이 레포는 [트리거 모델](../../spec/09-triggers.md)을 두 호스트(Claude Code · Codex CLI)에 연결해
*자동 포착*을 가동하는 훅 설정을 커밋해 두었습니다. 목표는 Codex CLI 훅 배선이 **실제 설치된
버전에서 실제로 발화**하도록 포맷·경로·이벤트명·도구명 matcher를 검증/수정하고, Claude Code 쪽과
**1:1 동등성**(같은 5개 트리거 → 같은 `pab` 서브커맨드)을 유지하는 것입니다. `tools/pab`는
**스텁 상태를 유지**합니다(로그만, `exit 0`, 라이브화 금지). 이 문서의 스키마는 *가정*이며,
**Codex의 `/hooks`·`codex --version` 출력이 최종 권위**입니다.

---

## 2. 범위 (Scope)

**IN (수정 가능):**
- `.codex/config.toml` (필요 시 `.codex/hooks.json`으로 **이전** — 둘 중 하나만, 병행 금지; T1 참조)
- `.claude/settings.json` (경로·matcher·`$CLAUDE_PROJECT_DIR` **재점검만**, 불필요한 변경 금지)
- 훅이 `tools/pab`를 **부르는 방식**(경로/쿼팅) — 단 *호출 측*(`.codex/*`·`.claude/settings.json`)에서만
- `docs/hooks-setup.md` (변경 사항 반영)

**OUT (절대 변경 금지):**
- `spec/*`, `schemas/*`, `skills/*` — **읽기 전용.** 어떤 파일도 생성/이동/개명/편집 금지.
- 스킬 의미론, 정전(canonical) **14개 팩 이름**, **6개 게이트**.
- `tools/pab` **파일 내용 일체** — shebang, `set -u`, `$PAB_LOG` 기본값, `case` 분기, 로그 형식 포함.
  허용은 **파일 권한(exec 비트)뿐.** *유일한 내용 예외*: pab 헤더 주석의 stdin 설명이 부정확하면
  (`turn_id`는 turn-scoped 이벤트에만, `model`은 매 이벤트 보장 아님) **주석 한 줄만** 정정 가능 —
  로직은 한 글자도 바꾸지 말 것.
- `tools/pab`를 "라이브"로 만드는 것(OpenCrab 스테이징 연결) — **스텁 유지.**
- `notify` 채널, MCP 서버 설정.

---

## 3. 사전 확인 (Pre-flight) — 작업 전 순서대로 실행, 분기 준수

### 0) Codex 가용성 분기 (★ 가장 먼저, 필수)
```bash
command -v codex >/dev/null 2>&1 && codex --version || echo "CODEX_ABSENT"
```
- **`CODEX_ABSENT`(미설치) 또는 인터랙티브 `/hooks` 접근 불가**면 → **정적 검증 전용 모드**로 전환:
  (a) `§5`의 정적 검사(TOML/JSON 파싱, `bash -n`, 링크 해석)만 수행,
  (b) 실제 발화·trust·도구명에 의존하는 **모든 변경 보류**(특히 T1 이전, T3 matcher 좁히기, T5 trust),
  (c) 발화/도구명/trust 관련 모든 주장에 **`UNVERIFIED`** 표시,
  (d) `§8` 에스컬레이션으로 보고 후 종료. **`/hooks` 출력을 지어내지 말 것.**

### 1) 브랜치·작업트리 안전
```bash
git rev-parse --abbrev-ref HEAD
git status --porcelain
```
- 기본 브랜치(`main`/`master`)면 **커밋 전 새 브랜치를 만든다.**
- 시작 트리가 더럽다면(이 작업과 무관한 변경 존재) **멈추고 §8 보고** — 무관한 변경을 같은 커밋에 넣지 말 것.

### 2) 대상 파일·권한 확인
```bash
cat .codex/config.toml
cat .claude/settings.json
cat tools/pab
cat docs/hooks-setup.md
ls -la tools/pab && (test -x tools/pab && echo "OK: executable" || echo "FAIL: not executable")
```

### 3) (Codex 있을 때만) 실제 스키마 확인
- Codex 세션 안에서 **`/hooks`** 실행 → 다음을 **로그로 기록**: 이벤트명 목록 · 필드명(`timeout` vs
  `timeoutSec`) · **실제 도구명** · 각 훅의 **trust 상태**. 이 실측값이 아래 가정과 다르면 **실측값을 따른다.**

---

## 4. 작업 항목 (Tasks) — 각 항목 ACCEPTANCE 명시

### T1 — Codex 훅 FORMAT·PATH 검증/수정
가정(검증 대상):
- 현재 파일은 `<repo>/.codex/config.toml`에 인라인 `[[hooks.EVENT]]` + 중첩 `[[hooks.EVENT.hooks]]`
  구조 — **현행 스키마의 유효 형태.** 필드: `type="command"`, `command`, `matcher`, `timeout`(정수·초),
  `statusMessage`.
- 이벤트명(verbatim): `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PermissionRequest`,
  `PostToolUse`, `PreCompact`, `PostCompact`, `SubagentStart`, `SubagentStop`, `Stop`.
  배선된 5개: `SessionStart`/`UserPromptSubmit`/`PostToolUse`/`PreToolUse`/`Stop`.
- 레거시 `[[hooks]]` + `event="..."`는 **무효**(config 로드가 깨짐). 현재 파일은 안 씀 — **유지.**

검증할 리스크(실제 발화로만 판정):
- 일부 버전에서 **repo-level 인라인 훅이 `SessionStart`/`Stop`을 발화하지 않은 보고**가 있음
  (openai/codex 이슈 트래커 참조; 인라인 테이블에도 영향인지는 **미확정**). → §5 스모크로 **실제 발화 확인.**
- 깨진 훅 블록은 **config 전체 로드를 brick**할 수 있음 → 편집 후 반드시 §5a 재실행.
- `timeout` vs `timeoutSec`: 캐논은 `timeout`(현재 사용). 설치 버전에서 맞는지 `/hooks` 또는 짧은
  `sleep` 테스트로 확인(틀린 키는 에러가 아니라 *무시*됨).

수정 지침:
- 인라인 `config.toml` 훅이 **실제로 발화하면** → 현 형태 유지.
- **발화하지 않음을 실측으로 관측한 경우에만** → 동일 스키마의 `<repo>/.codex/hooks.json`으로 **이전**
  (아래 매핑). **"발화 확인 불가"를 "발화 안 함"으로 간주하지 말 것** — 불확정이면 이전하지 말고 유지.
  이전 시 `config.toml`의 `[[hooks.*]]`는 제거(한 레이어에 한 표현만).

```jsonc
// .codex/hooks.json — config.toml가 발화하지 않을 때만 사용. matcher는 T3 결과.
{
  "hooks": {
    "SessionStart":     [ { "hooks": [ { "type": "command", "command": "bash \"$(git rev-parse --show-toplevel)/tools/pab\" compile-adapter",     "timeout": 30, "statusMessage": "PAB: compile runtime adapter" } ] } ],
    "UserPromptSubmit": [ { "hooks": [ { "type": "command", "command": "bash \"$(git rev-parse --show-toplevel)/tools/pab\" capture --from prompt", "timeout": 20, "statusMessage": "PAB: capture prompt evidence" } ] } ],
    "PostToolUse":      [ { "hooks": [ { "type": "command", "command": "bash \"$(git rev-parse --show-toplevel)/tools/pab\" capture --from tool",   "timeout": 20, "statusMessage": "PAB: capture tool evidence" } ] } ],
    "PreToolUse":       [ { "matcher": "<T3에서 실측 도구명으로 좁힘 — 미확정이면 \"\">", "hooks": [ { "type": "command", "command": "bash \"$(git rev-parse --show-toplevel)/tools/pab\" boundary-check", "timeout": 20, "statusMessage": "PAB: boundary check" } ] } ],
    "Stop":             [ { "hooks": [ { "type": "command", "command": "bash \"$(git rev-parse --show-toplevel)/tools/pab\" mine-and-review",      "timeout": 60, "statusMessage": "PAB: mine + review board" } ] } ]
  }
}
```
**ACCEPTANCE T1:** `/hooks`로 이벤트명·필드명이 일치함을 로그로 확인 · 표현은 한 레이어에 **하나만**
(collision warning 없음) · 레거시 `event=` 없음 · §5 스모크에서 5개 이벤트 **실제 발화**(특히
`SessionStart`/`Stop`). *Codex 미설치면* 이 항목 전체 **보류 + UNVERIFIED 보고**.

### T2 — `pab` 호출이 실제로 실행되는지 검증
```bash
bash "$(git rev-parse --show-toplevel)/tools/pab" compile-adapter < /dev/null; echo "exit=$?"
git rev-parse --show-toplevel
```
- `exit=0` 필수. 비-0이면 경로/쿼팅/exec 비트 문제 — `ls -la tools/pab`, 필요 시 `chmod +x tools/pab`.
- `command`를 **배열 형태 `["bash", ...]`로 바꾸지 말 것** — `$(git rev-parse ...)`는 셸 파싱될 때만
  확장됨(배열이면 확장 안 돼 깨짐). Windows 네이티브 Codex는 bare `bash`가 실패할 수 있음
  (이 레포는 Unix/macOS/CI 대상 — 현 형태 유지, docs에 1줄 주석).

**ACCEPTANCE T2:** 위 실행 `exit=0` · 로그에 `pab compile-adapter` 라인 추가 · pab는 executable.

### T3 — `PreToolUse` matcher: **기본은 `""` 유지**, 실측 시에만 좁힘
- **기본값 = 현 상태(`""`, 전체 매칭) 유지.** 좁히기는 `/hooks` 또는 실제 도구 호출 stdin의
  `tool_name`으로 **실측 도구명을 확보한 경우에만** 수행.
- `matcher`는 `Pre/PostToolUse`에서 **도구명** 정규식, `SessionStart`에서 `source`
  (`startup`|`resume`|`clear`) 정규식. `""`/`"*"`/생략 = 전체.
- 예시 정규식 `^(<실측이름1>|<실측이름2>)$`는 **형식 예시일 뿐 채워 넣을 템플릿이 아님.** 이 문서에
  검증된 Codex 도구명은 **없음** — `Bash`/`Shell` 등 추측 이름 사용 금지.
- 실측 못 하면 **matcher를 절대 바꾸지 말고** 사유를 보고서에 적고 §8 보고.

**ACCEPTANCE T3:** matcher가 `/hooks` 실측 도구명 정규식으로 설정되고 그 목록이 설정 주석 + docs에
기록됨. *실측 불가면* `""` 유지 + 사유 보고(좁히기 보류).

### T4 — Claude ↔ Codex 1:1 동등성 + `.claude/settings.json` 재점검
| 트리거 | Claude 이벤트 | Codex 이벤트 | `pab` 서브커맨드 |
|---|---|---|---|
| session_start | `SessionStart` | `SessionStart` | `compile-adapter` |
| turn/correction | `UserPromptSubmit` | `UserPromptSubmit` | `capture --from prompt` |
| tool_result | `PostToolUse` | `PostToolUse` | `capture --from tool` |
| pre_external_action | `PreToolUse` | `PreToolUse` | `boundary-check` |
| session_end | `Stop` | `Stop` | `mine-and-review` |

- `.claude/settings.json`은 **유효 — 깨지 않게 검증만.** `"\"$CLAUDE_PROJECT_DIR/tools/pab\" <sub>"`는
  문서화된 셸-폼 변형과 일치(공식 예제의 정확한 형태는 아니지만 허용 변형). `$CLAUDE_PROJECT_DIR`는
  런타임이 export하는 변수 — 정상.
- `PreToolUse` matcher `Bash|Write|Edit|MultiEdit|mcp__.*`: `MultiEdit` 미존재 시 단지 inert(에러 아님).
  **확인 불가면 기본값 = 현 상태 유지(제거하지 않음)** — 불필요한 churn 금지.

**ACCEPTANCE T4:** 위 표 5행이 양쪽에서 정확히 일치 · `.claude/settings.json` 무변경(또는 최소)으로 유효.

### T5 — `/hooks`로 신뢰/활성화 (해시 트러스트)
- Codex repo-local 훅은 `.codex/` 레이어가 **trusted**이고 각 명령 훅이 **현재 해시로 검토·신뢰**될 때만
  로드/발화. `command`나 `tools/pab`가 바뀌면 **재검토 대상** → 재-trust 전까지 skip.
- `/hooks`로 5개 훅 검토·신뢰.

**ACCEPTANCE T5:** 5개 훅이 trusted로 표시되고 §5 스모크에서 발화 — **또는** trust 관련 알려진 버그로
막히면 정확한 에러와 함께 §8로 보고·중단(거짓 PASS 금지). *Codex 미설치면 보류.*

### T6 — `docs/hooks-setup.md` 갱신
- T1~T3 변경(표현 선택, 실측 도구명·좁힌 matcher, 검증된 최소 Codex 버전) 반영.
- 추가 명시: (a) repo 훅은 **trusted + 해시 트러스트** 후에만 로드되며 `pab` 수정 시 재-trust 필요,
  (b) `$PAB_LOG` 기본값을 정확히 `${PAB_LOG:-${TMPDIR:-/tmp}/pab-hooks.log}`로 표기(현재 docs가
  `:-/tmp` 폴백을 빠뜨렸으면 정정), (c) Windows bare-`bash` 주의.
- 기존 EN 요약·5개 훅 표·STUB 안내·불변식(G3/G5)은 유지.

**ACCEPTANCE T6:** docs가 실제 설정과 일치하고 §5d 링크가 모두 해석됨.

---

## 5. 검증·스모크 테스트 — **편집할 때마다·커밋 전 매번 실행**

> §5a(파싱)가 실패하면 **커밋 금지** — pab가 불리기도 전에 config 로드가 깨진 상태.

```bash
# (a) 구문 유효성
python3 -c "import tomllib; tomllib.load(open('.codex/config.toml','rb')); print('TOML OK')"
test -f .codex/hooks.json && python3 -c "import json;json.load(open('.codex/hooks.json'));print('hooks.json OK')"
python3 -c "import json;json.load(open('.claude/settings.json'));print('settings OK')"

# (b) pab 셸 문법 + 모든 분기가 여전히 exit 0 (자기 도구 brick 방지)
bash -n tools/pab && echo "pab syntax OK"
for s in compile-adapter "capture --from prompt" "capture --from tool" boundary-check mine-and-review; do
  bash tools/pab $s </dev/null; echo "$s -> $?";   # 모두 -> 0 이어야 함
done

# (c) 5개 이벤트 실제 발화 — 세션 격리된 전용 로그로 (공유 로그 거짓 PASS 방지)
export PAB_LOG="$(mktemp -t pab-smoke.XXXXXX.log)"; : > "$PAB_LOG"
#   ... 여기서 Codex 세션 1회: 프롬프트1 + 도구호출1 + 세션종료(Stop) ...
for pat in 'pab compile-adapter' 'pab capture --from prompt' 'pab capture --from tool' 'pab boundary-check' 'pab mine-and-review'; do
  printf '%2d  %s\n' "$(grep -cF "$pat" "$PAB_LOG")" "$pat"
done
#   PASS: compile-adapter=1, capture --from prompt=1, capture --from tool=1, boundary-check>=1, mine-and-review=1
```
- (d) **링크 검사:** `docs/hooks-setup.md`의 상대 링크가 실제 파일로 해석되는지 확인. **해석 안 되면
  `docs/hooks-setup.md`의 링크 텍스트만 고친다** — `spec/*`·`schemas/*`·`skills/*`의 **대상 파일은
  생성/이동/개명/편집 금지.** 대상이 실제로 없으면 보고만 하고 멈춘다(§8).

**스모크 PASS 기준:** TOML/JSON 유효 · `bash -n` 통과 · 모든 pab 분기 `-> 0` · 격리 로그에 5개 이벤트
규정 횟수 기록 · 모든 링크 해석. (Codex 미설치면 (c)는 보류·UNVERIFIED.)

---

## 6. 불변식 (절대 깨지면 안 됨)
- **capture = 스테이징만**(draft/pending) — 절대 승격 안 함 (**G3**).
- **승격(pending→confirmed)은 `Stop` 리뷰보드에서 사람 확인 후에만** (**G5**).
- `tools/pab`는 **항상 `exit 0`**, 어떤 도구/턴도 막지 않음 — **스텁 유지.**
- 민감 항목은 승격 전 경계 규칙 먼저 (**G5**).
- 정전 **14개 팩 이름**·**6개 게이트** 불변. `spec/*`·`schemas/*`·`skills/*` 변경 금지.
- 양쪽 호스트 **1:1**.

---

## 7. 산출물·커밋
**변경됐을 수 있는 파일(실제 변경분만):** `.codex/config.toml`(및/또는 신규 `.codex/hooks.json`),
`.claude/settings.json`(변경 시), `docs/hooks-setup.md`.
- 기본 브랜치가 아님을 확인하고(§3-1), 무관한 변경을 섞지 말 것.

**커밋 메시지 템플릿:**
```
chore(hooks): verify+fix Codex hook wiring against installed version

- Codex <codex --version>: verified hook FORMAT (<config.toml|hooks.json>) fires
- PreToolUse matcher: <kept ""|narrowed to <regex>> using real tool names (<list>)
- kept Claude<->Codex 1:1 (5 triggers -> same pab subcommands)
- trusted via /hooks (hash trust); pab unchanged (STUB, exit 0)
- updated docs/hooks-setup.md to match

Invariants intact: G3 stage-only, G5 promote-only-at-Stop, 14 packs, 6 gates.
```
**보고서(커밋 본문/PR 첨부):** `codex --version` 값(또는 `CODEX_ABSENT`) · `/hooks` 실측 도구명 목록 ·
바로잡은 것(포맷 유지/이전, matcher, `timeout` 확인, trust 상태) · 보류·UNVERIFIED 항목.

---

## 8. 막히면 (Escalation) — 멈추는 *방법*
막히면: **변경을 커밋하지 말고**, `STATUS: BLOCKED`로 시작하는 보고를 최종 출력으로 낸다 — 가정 vs
실제 diff, `codex --version` 결과(또는 `CODEX_ABSENT`), 보류 항목 목록. **같은 검증을 2회 이상
재시도하지 않는다(루프 금지).** 비인터랙티브 실행이라 "기다리지" 말고 보고 후 **종료**.

대표 차단 조건:
- **Codex 미설치 / `/hooks` 접근 불가** → 정적 검증만, 런타임 의존 변경 전부 보류, 보고 후 종료(1순위).
- 인라인 `config.toml` 훅 발화 여부 **불확정** → 이전하지 말고 유지, 보고.
- 실제 도구명 확정 불가 → `PreToolUse` matcher `""` 유지, 보고.
- `timeout` vs `timeoutSec` 동작 차이, trust가 worktree/clone 간 재사용 안 됨 등 알려진 버그.

---
*출처: Codex 훅 경로·이벤트·신뢰 모델은 OpenAI Codex 문서 및 openai/codex 이슈 트래커, Claude Code
훅 스키마는 Claude Code settings.json 사양에 근거. 버전별 동작은 반드시 실측으로 검증한다.*
