# revolution-02 — 바퀴를 한 번 더 돌리다, 이번엔 안전성을 시험하며 (a second turn, stress-testing safety)

> **EN:** The *second* actual revolution of the Personal Agent data-engine flywheel on real records.
> revolution-01 proved the wheel *can* turn (merge + insert). revolution-02 turns it again and, this
> time, stresses what a skeptic actually doubts: not "does it move?" but **"is it safe, and does it
> tell the truth when it stalls?"** Three things happen here that revolution-01 did not show:
> (1) the same heuristic is re-derived a **third** time and MERGES again (`repetition_count` 2→3 —
> the "becoming core" signal accumulating); (2) the `eval.005` **partial** is corrected by inserting
> a `user.artifact_policy` rule, taking `decision_fidelity` **0.92 → 1.00**; and most importantly
> (3) a *confirmed* candidate is **BLOCKED by the actuator** — it conflicts with existing confirmed
> knowledge, so the judge **surfaces it for human review and refuses to auto-apply** (`conflict →
> surface`, never silently overwrites). The honest headline: **the maturity tier does NOT advance
> (L2 → L2).** The wheel turned, fidelity hit 1.0, coverage climbed 0.57→0.71 — yet the report
> refuses to promote, and *names exactly why*: `coverage < 0.8` and `correction_cost = NA`. Turning
> the wheel did not fake a jump; it **isolated the next bottleneck to a single number**. Every figure
> below is reproduced by the commands in §4.

이 문서는 PAB 데이터-엔진 플라이휠을 **실제 레코드 위에서 두 번째로 돌린** 기록입니다.
revolution-01 이 "바퀴가 돈다"(merge + insert)를 증명했다면, revolution-02 는 회의론자가
정말로 의심하는 것 — *"움직이느냐"가 아니라 "안전하냐, 그리고 멈출 때 정직하냐"* — 를
시험합니다. 그리고 이 한 바퀴의 정직한 헤드라인은 **성숙도 단계가 오르지 않았다는 것**입니다
(L2 → L2). 바퀴는 돌았고 fidelity 는 1.0 에 닿았지만, 리포트는 승급을 거부하며 *왜 거부하는지*
정확히 짚습니다. 가짜 도약 대신 **다음 병목을 숫자 하나로 좁혀** 보여줍니다.

---

## 1. 무엇이 한 바퀴인가 (the loop, spec/02 — 네 판정을 모두 밟다)

```
포착(3번째 세션 후보 ×4)  →  dedup judge(pab_merge)  →  팩 갱신(3 적용)  →  재평가(eval.005)
        ↑                         │ merge / insert / insert / SURFACE                  │
        │                         └────── conflict 는 적용 안 함(사람 검토 대기) ──┐  │
        └──────────  partial/충돌은 "다음 증거"(drift_history, surface 큐)  ←──────┴──┘
```

[`session-03-candidates.yaml`](./session-03-candidates.yaml)의 후보 4개를 actuator
([`../../../tools/pab_merge.py`](../../../tools/pab_merge.py))에 투입하면 **네 판정이 모두** 나옵니다.
revolution-01 은 `novel`+`duplicate` 두 가지를 보였고, revolution-02 가 `conflict` 를 추가합니다
(`refinement→supersede` 는 아직 실레코드에서 미실행 — §5 정직성 노트):

1. **MERGE (재유도, 3번째).** 같은 휴리스틱이 세 번째 세션에서 또 떠받쳐짐
   (`logotekton.heuristic.301`). 새 트윈을 찍지 않고 actuator 가 `canonical_key` 충돌
   (`3cabb5142158`)을 잡아 기존 `logotekton.heuristic.001`에 **흡수**: `repetition_count`
   **2→3**, evidence 3개 세션으로 누적, `confidence` **0.9→0.95**, `merge_history`에 후보 id.
   → `merge_rate` 가 **0.059→0.095** 로 상승. "core 가 되어 가는" 신호가 강해짐.
2. **INSERT (eval.005 교정 산물).** `eval.005`가 보고에서 next action 슬롯을 빠뜨려
   **PARTIAL**(score 0.7)했고, 그 `correction_notes`가 처방한 `user.artifact_policy`
   `ReviewArtifactRecord`(`logotekton.artifact.001`, next action 필수)를 judge 가
   **NOVEL→INSERT**로 적재. 빈 팩 #4 시드. → `eval.005`가 재실행에서 **PASS**,
   `decision_fidelity` **0.92→1.00**.
3. **INSERT (세션 3 도구 선호).** 관찰된 도구 선택(`logotekton.tool.001` — 수렴/검증 숫자는
   단언하지 말고 결정론적 도구를 돌려 산출)을 빈 팩 #10(`user.tool_stack`)에 **NOVEL→INSERT**.
   → 시드 8→10팩, `coverage` **0.57→0.71**.
4. **CONFLICT → SURFACE (자동 적용 거부 = 이번 바퀴의 핵심).** `logotekton.style.301`은 컴팩트
   보고 규칙(`style.001`)을 살짝 다르게 재진술함("result 를 먼저, defect 생략"). 같은
   `record_type`·같은 `scope`이고 토큰 중첩 **Jaccard 0.6 ∈ [0.5, 0.85)** 이라 actuator 는 이를
   refinement 인지 모순인지 **단정할 수 없어** `conflict`로 분류하고 **surface** 합니다 —
   **절대 자동 적용하지 않음**(spec/10 §3). 이 후보는 *확인된* 후보임에도 instance-records 에
   적재되지 않고 사람 검토 대기로 남습니다. **merge 층이 확인 게이트(G3/G5)의 두 번째 관문**임을
   증명하는, revolution-02 가 보여주는 새 안전 속성입니다.

## 2. T1 → T2 (도구가 출력한 실제 숫자)

| 지표 / 상태 | **T1 (rev-01 후)** | **T2 (rev-02 후)** | 무엇이 움직였나 |
|---|:---:|:---:|---|
| 성숙도 | **L2 Working** | **L2 Working** | **오르지 않음 — 정직한 헤드라인** (아래 정직성 노트) |
| 시드된 팩 | 8 / 14 | **10 / 14** | +`artifact_policy`(#4) +`tool_stack`(#10) |
| `coverage` (시드폭) | 0.57 | **0.71** | 두 팩 추가 |
| `coverage` (엄격 ≥3) | 0.07 | 0.07 | 변화 없음 — 깊이는 아직 (#7) |
| `decision_fidelity` | 0.92 | **1.00** | eval.005 partial→pass `6/6` |
| `merge_rate` | 0.059 | **0.095** | heuristic.001 `repetition_count` 2→3 |
| `drift_stability` | 0.94 | **0.89** | **두 번째** 실제 움직임 — 이제 *살아 있는* 값(↓이 정상) |
| 대체(supersession) | 1 | **2** | `drift.001` + `drift.002` |
| 평가 (pass/partial/fail) | 5 / 1 / 0 | **6 / 0 / 0** | eval.005 교정 |
| 확인 레코드 | 16 | **19** | +artifact.001 +tool.001 +drift.002 |
| `confirmation_ratio` | 1.00 | 1.00 | 유지(충돌 후보는 적재 안 함 → 지표 무영향) |
| `traceability` | 1.00 | **1.00** | 유지(새 레코드도 모두 증거 결속, G1) |
| `correction_cost` | **NA** | **NA** | **여전히 NA — 구조화 필드 부재(#3), L3 를 막는 둘째 빗장** |
| validate_packs (라이브) | 18 PASS | **25 PASS** | top 19 + rev-01 2 + rev-02 4 (재귀 명령은 .pre 픽스처 9 포함 **34**) |

> **읽는 법.** `decision_fidelity`가 1.00, `coverage`가 0.71 로 올랐는데도 성숙도는 L2 그대로입니다.
> 이것이 핵심입니다 — 리포트의 "다음 단계(L3)까지 미달 조건"이 정확히 두 줄을 가리킵니다:
> `L3_coverage>=0.8` 과 `L3_correction_cost<=0.3`. 한 바퀴는 마법이 아니라 **다음 병목을 가리키는
> 나침반**입니다.

## 3. 무엇이 새로 생겼나 (the data + the safety proof)

- **[`session-03-candidates.yaml`](./session-03-candidates.yaml)** — 3번째 세션의 인입 후보 4개
  (merge 1 + insert 2 + **conflict 1**). 네 판정을 한 배치에서 모두 산출.
- **[`../instance-records.yaml`](../instance-records.yaml)** — `heuristic.001`(3번째 병합),
  새 `user.artifact_policy` 섹션(#4, `artifact.001`), 새 `user.tool_stack` 섹션(#10, `tool.001`).
  `style.301`은 **여기 없음** — 충돌이라 적용되지 않았다는 증거 그 자체.
- **[`../evaluation-cases.yaml`](../evaluation-cases.yaml)** — `eval.005` partial→pass 전환,
  `regression_for`로 회귀 고정.
- **[`../drift-history.yaml`](../drift-history.yaml)** — 두 번째 `DriftRecord`(`drift.002`,
  eval.005 교정·audit·되돌리기 가능). 두 번 움직였으므로 `drift_stability`가 비로소 *살아 있는*
  숫자(1.0 의 공허함을 벗어남).
- **안전 증명(C4).** *확인된* 후보가 actuator 에 의해 차단되어 surface 됨. 멱등성 검사(§4 (2))에서
  보듯 충돌은 재투입해도 자동 해소되지 않습니다 — 사람이 해결할 때까지 영구히 surface 상태.

## 4. 재현 (reproduce — 모든 숫자는 결정론적)

> ⚠️ **왜 `.pre` 스냅샷을 쓰나.** `../instance-records.yaml`는 이미 *병합 후(T2)* 상태입니다 —
> 거기에 대고 plan 을 돌리면 `already_merged`만 나옵니다. 그래서 *병합 전(T1)* 상태를 동결한
> [`instance-records.pre.yaml`](./instance-records.pre.yaml)(픽스처)에 대고 plan→apply 를 돌려
> **네 판정(merge/insert/insert/conflict)을 글자 그대로 재현**하고, 그 apply 결과가 출하된
> `../instance-records.yaml`와 레코드 단위로 같음을 보입니다.

```bash
# (1) dedup judge 계획 — T1 스냅샷(.pre) 대비 네 판정: merge / insert / insert / conflict(surface)
python tools/pab_merge.py examples/logotekton/revolution-02/instance-records.pre.yaml \
       examples/logotekton/revolution-02/session-03-candidates.yaml
#   → [    duplicate]   merge  logotekton.heuristic.301 -> logotekton.heuristic.001
#   → [        novel]  insert  logotekton.artifact.001
#   → [        novel]  insert  logotekton.tool.001
#   → [     conflict] surface  logotekton.style.301 -> logotekton.style.001 sim=0.6   (적용 안 함)

# (2) 적용 → 멱등성 + 충돌 영속성. 적용본(/tmp/merged.yaml)에 재투입: C1~C3 noop, C4 는 여전히 conflict.
python tools/pab_merge.py examples/logotekton/revolution-02/instance-records.pre.yaml \
       examples/logotekton/revolution-02/session-03-candidates.yaml \
       --apply --out /tmp/merged.yaml --stamp 2026-06-28T18:00:00Z
python tools/pab_merge.py /tmp/merged.yaml \
       examples/logotekton/revolution-02/session-03-candidates.yaml
#   → already_merged×3 (noop), conflict×1 (surface) — 충돌은 사람 검토 전까지 자동 해소 안 됨
#   그리고 /tmp/merged.yaml 의 적용 결과 = 출하된 ../instance-records.yaml (heuristic rep=3, artifact/tool 시드, style.301 없음)

# (3) T2 측정 — L2 그대로, df 1.00 / coverage 0.71 / merge_rate 0.095 / drift_stability 0.89
python tools/convergence_report.py examples/logotekton    # L2; df 1.00; coverage 0.71; drift 0.89
python tools/dedup_check.py        examples/logotekton     # merge_rate 0.095
python tools/validate_packs.py     examples/logotekton     # 34 PASS (라이브 25 + .pre 픽스처 9; 재귀)
```

> 이전 바퀴: [`../revolution-01/README.md`](../revolution-01/README.md) (L0→L2, merge actuator 도입).
> T0 베이스라인: [`../convergence-report.md`](../convergence-report.md).

## 5. 정직성 노트 (what did NOT move — and why that's the point)

revolution-02 의 가치는 *움직인* 숫자만큼 *움직이지 않은* 숫자에 있습니다. 한 바퀴는 한 칸이지,
완성이 아닙니다.

- **(a) 성숙도는 L2 그대로 — 의도된 결과.** `decision_fidelity`가 1.0 에 닿고 `coverage`가 0.71 로
  올랐어도 L3 는 두 빗장으로 막혀 있습니다: `coverage ≥ 0.8`(아직 0.71)과 `correction_cost ≤ 0.3`
  (아직 **NA**). 우리는 L3 를 *연출*하지 않았습니다. 도구가 승급을 거부하는 그대로 보고합니다.
- **(b) `coverage`를 0.8 로 *채워 넣지* 않았다 — 이것이 #7 에 대한 응답.** 시드폭 문턱이 관대하다는
  지적(revolution-01 정직성 노트 #7)을 알기에, **얇은 팩을 4개 우겨넣어 0.8 을 만드는 게이밍을
  의도적으로 거부**했습니다. 세션 3 에 *실제 증거가 있는* 두 팩(artifact_policy, tool_stack)만
  시드했고, 나머지 4개 팩(red_flags, workflow_playbooks, domain_overlays, memory_project_graph)은
  **정직하게 비어 있습니다**(G1: 증거 없는 팩은 채우지 않는다). 엄격 `coverage`(≥3)는 여전히
  0.07 — 폭은 늘었으나 깊이는 그대로이며, 이것이 #7 의 핵심입니다.
- **(c) `correction_cost`는 여전히 NA — 이제 L3 의 *가장 날카로운* 단일 레버.** 설령 `coverage`가
  0.8 을 넘겨도, 구조화된 작업별 편집비율 필드가 없어(`le(None, 0.3)=False`) L3 는 열리지 않습니다.
  eval.006 의 관측 편집비율(≈0.12)은 산문에만 있고 도구가 읽는 필드가 아닙니다. 사용자는 이번
  세션에서 revolution-02 를 택했고 #3 은 보류했으므로, 우리는 그것을 **고치지 않고 정직하게
  NA 로 둡니다.** 플라이휠은 #3 을 다음의 단일 최고 레버리지 작업으로 *가리킵니다.*
- **(d) `drift_stability`가 *내렸다*(0.94→0.89) — 좋은 신호.** 두 번째 실제 교정이 일어나며 안정도가
  내려갔습니다. 1.0 에 고정된 값은 아무것도 교정되지 않는다는 뜻이라 무의미합니다(revolution-01
  노트 #5). 이제 값은 *살아서* 움직이며 L3 바닥(0.7)을 여유 있게 상회합니다. 다만 여러 기간에
  걸쳐 0.7 이상으로 *유지*되는지는 여전히 시간이 필요한 일입니다.
- **(e) `refinement→supersede` 판정은 아직 실레코드에서 미실행.** 네 판정 중 셋
  (`novel`·`duplicate`·`conflict`)을 두 바퀴에 걸쳐 실제로 밟았으나, "같은 정체성·다른 scope →
  대체" 경로는 아직입니다(억지로 만들지 않았습니다 — 동일 statement·scope 변경 이벤트는 드뭅니다).
  실제 그런 교정이 관측되면 그때 밟습니다.
- **(f) `tool_stack`은 시드됐으나 아직 eval 미결속.** `artifact_policy`는 eval.005 가 능동적으로
  시험하지만, `tool_stack`의 평가 케이스는 아직 작성하지 않았습니다 — 평가 케이스도 *증거*이며
  에이전트를 관측해서 나오는 것이지 책상에서 지어내는 게 아니기 때문입니다. 그것이 다음 eval.

> 이 스냅샷은 한 칸입니다. 위 (a)~(f)는 결함이 아니라 *상태*이며, 다음 바퀴들이 무엇을 해야 하는지
> 정확히 정의합니다. 그것이 수렴을 *보는* 방법입니다 — 숫자가 오르는 것을 보고, **다음에 어느
> 숫자를 고쳐야 하는지** 도구가 가리키는 것을 보는 것.

## 인접 문서
- 이전 바퀴: [`../revolution-01/README.md`](../revolution-01/README.md)
- 데이터-엔진 루프: [`../../../spec/02-builder-pipeline.md`](../../../spec/02-builder-pipeline.md)
- 중복 억제·병합·충돌(merge/supersede/surface): [`../../../spec/10-dedup-and-merge.md`](../../../spec/10-dedup-and-merge.md)
- 수렴 지표·성숙도: [`../../../spec/06-convergence-model.md`](../../../spec/06-convergence-model.md)
- actuator: [`../../../tools/pab_merge.py`](../../../tools/pab_merge.py)
