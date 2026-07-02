# 16 · ingest 판정 게이트 (Ingest Decision Gate)

> **EN:** Operating instructions for `skill.pab.ingest_decision_gate` — the run-level gate
> that forces every builder run to end with an explicit **ingest judgement**: `YES`, `NO`, or
> `WAITING_FOR_CONFIRMATION`, plus the **target project** the artifact belongs to. It exists
> because the reviewer of a builder run is not primarily asking whether the content looks
> interesting — they are deciding **whether a pack should be ingested, and into which layer**.
> Where skill 07 (confirmation gate) judges individual *records* (confirm/edit/reject/narrow),
> this skill judges the *run artifact* (a candidate board, a session pack, an apparatus
> update) against the project topology, so a task-summary pack can never slip into personal
> memory and personal data can never land in the builder project. Mirrored from the OpenCrab
> builder pack `skill.pab.ingest_decision_gate.v0.1`.

ingest 판정 게이트는 [07 확인 게이트](./07-confirmation-gate.md)의 **런-레벨 보완물**입니다.
07이 *레코드 하나하나*를 confirm/edit/reject/narrow 로 심사한다면, 16은 *런이 만든 산출물
전체*(후보 보드, 세션 팩, 장치 업데이트)가 **어느 프로젝트 층으로 들어가도 되는가**를 심사합니다.
토폴로지는 [07 크로스워크의 3-project 모델](../spec/07-opencrab-9space-crosswalk.md#프로젝트-토폴로지--빌더-장치-증거-아카이브-개인-에이전트-3-project)을
런-레벨 ingest 판정으로 적용합니다(§2).

---

## 1. 목적 (Purpose)

- **하는 일:** 모든 빌더 런의 끝에서 (1) ingest 판정(YES/NO/WAITING_FOR_CONFIRMATION),
  (2) 타깃 프로젝트, (3) 판정 근거를 명시한 최종 보고 블록을 산출한다.
- **하지 않는 일:** (1) 레코드 수준 심사를 대체하지 않는다 — 그것은 07의 일이다. (2) 판정
  없이 ingest 하지 않는다. (3) "내용이 흥미로운가"를 심사 기준으로 삼지 않는다 — 기준은
  토폴로지·템플릿·증거 결속·검토 상태다.

> 한 줄 계약: **빌더 런 → 명시적 ingest 판정 + 타깃 층.** 판정 블록이 없는 런은 미완성이다.

## 2. 3층 타깃 토폴로지 (Three-layer target topology)

| 산출물 | 타깃 프로젝트 | 판정 |
|--------|--------------|------|
| 빌더 장치 업데이트 (스킬/템플릿/트리거/QA 정책) | `personal agent builder skills` | YES (장치 검증 통과 시) |
| 세션 증거·후보 팩, pending 후보 보드 | `personal agent evidence` | `WAITING_FOR_CONFIRMATION` |
| **확정** 후보의 정식 14팩 upsert | `personal agent` | YES |
| 개인 기억을 가장한 작업-요약 팩 | `none` | NO |

**핵심 구분:** 세션 증거 팩을 만들거나 갱신하는 것은 **런타임 기억 갱신이 아닙니다.** 런타임
기억은 *확정된 레코드가 `personal agent`의 정식 14팩에 upsert 될 때만* 바뀝니다(증거 팩 =
비계, 14팩 = 건물). 사용자가 "인제스트 하냐 마냐"를 물으면 **어느 층에 대한 ingest인지**부터
답합니다.

## 3. YES 전 필수 점검 (Mandatory checks before YES)

1. **토폴로지** — 장치는 빌더 프로젝트로, 확정 인스턴스는 personal agent로; 개인 데이터가
   빌더 프로젝트에 저장되지 않았다(G6).
2. **템플릿** — 14 `user.*` 템플릿/스키마를 썼고, 필드가 정식 계약과 일치한다.
3. **증거 결속** — 모든 레코드/후보에 `evidence_refs`(G1); 암묵지 런이면 `episode_id`·
   `signal_text`([15 §5](./15-tacit-knowledge-mining.md)).
4. **검토 상태** — confirmed/narrowed/edited 만 승격 대상(G3); 보드가 필요한 런에서 보드가
   생성됐다.
5. **부류 순수성** — 작업-요약 서술이 개인 기억으로 위장하지 않았다(위장 시 즉시 NO).

## 4. WAITING_FOR_CONFIRMATION 조건

- 후보가 증거에 묶였고 템플릿과 호환되지만 `validation_status: pending`이다.
- 검토 보드는 생성됐으나 사용자가 confirm/edit/reject/narrow 를 아직 고르지 않았다.
- sensitive 후보가 BoundaryRule 확인을 기다린다(G5).
- scope가 너무 넓어 좁힘이 필요하다.

## 5. 최종 보고 블록 (Required final report format)

모든 런은 이 블록으로 끝납니다:

```text
Ingest judgement: YES | NO | WAITING_FOR_CONFIRMATION
Target project: personal agent builder skills | personal agent | personal agent evidence | none
Reason: one sentence
Template use: PASS | FAIL, list templates
Evidence binding: PASS | FAIL
Review board: generated | not generated | not required
Confirmed candidates: N
Pending candidates: N
Blocked candidates: N
Next action: ingest | rebuild | ask user to review board
```

**나쁜 출력 패턴(즉시 실패):** ZIP 유효성만 확인하고 ingest YES/NO에 답하지 않음 / pending
후보 보드에 `Target project: personal agent builder skills` 기재(빌더는 실행 *소스*지 개인
데이터 타깃이 아님) / 판정 블록 생략.

## 트리거 (Trigger)

> 이 스킬의 발화 조건. 전체 2계층 모델·호스트(훅) 매핑·게이트 보존은
> [../spec/09-triggers.md](../spec/09-triggers.md), 머신 스키마는
> [../schemas/trigger.schema.json](../schemas/trigger.schema.json) 참고.

```yaml
trigger:
  trigger_id: pab.ingest_decision_gate.on_run_artifact
  skill: ingest_decision_gate
  signal: candidate_created
  condition: "a builder run staged candidates or produced a pack artifact; judge ingest target/verdict before any routing"
  cadence: event
  host_hook: [chained, orchestrator]
  produces: review_requested
  requires_confirmation: true      # 판정이 승격을 좌우 — 사람 확인 없이 YES 승격 없음 (G3)
  default_state: enabled
  debounce: per_session
```

다른 스킬 뒤에 체인으로 발화하며, 판정 블록 없이는 런이 끝나지 않게 합니다.
