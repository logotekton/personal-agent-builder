# revolution-01 — 데이터-엔진을 한 바퀴 돌리다 (one turn of the wheel)

> **EN:** This is the first *actual revolution* of the Personal Agent data-engine flywheel on real
> records — not asserted by construction, but performed and measured. Before this, the loop had
> never turned once: there was no merge/upsert actuator, `drift_history` was empty, and convergence
> was hand-authored. Here we (1) run a real **dedup-judge + upsert actuator**
> ([`../../../tools/pab_merge.py`](../../../tools/pab_merge.py)) over a second session's candidates,
> (2) apply the correction that `eval.004` failure demanded, (3) record the resulting `DriftRecord`,
> and (4) re-measure. The numbers move on their own: **L0 → L2 Working**, `decision_fidelity`
> 0.75 → 0.92, `merge_rate` NA → 0.059, `drift_stability` 1.00(vacuous) → 0.94(earned). This
> converts the project's core claim — *"becoming me is a number you watch climb"* — from design
> into evidence. Every number below is reproducible by the commands in §4.

이 문서는 PAB 데이터-엔진 플라이휠을 **실제 레코드 위에서 처음으로 한 바퀴 돌린** 기록입니다.
이전까지 바퀴는 한 번도 돈 적이 없었습니다(merge actuator 부재, `drift_history` 비어 있음,
수렴은 수기 단언). 여기서 바퀴가 *스스로* 숫자를 올립니다.

---

## 1. 무엇이 한 바퀴인가 (the loop, spec/02)

```
포착(2번째 세션 후보)  →  dedup judge/upsert(pab_merge)  →  팩 갱신  →  재평가(eval.004)
        ↑                                                                      │
        └──────────────  실패는 "다음 증거"(drift_history)  ←──────────────────┘
```

세 가지 actuator 작동이 실제로 일어납니다:

1. **MERGE (재유도 흡수).** 같은 휴리스틱이 2번째 세션에서 또 떠받쳐짐
   ([`session-02-candidates.yaml`](./session-02-candidates.yaml)의 `logotekton.heuristic.201`).
   새 트윈을 찍지 않고 [`pab_merge.py`](../../../tools/pab_merge.py)가 `canonical_key` 충돌을
   잡아 기존 `logotekton.heuristic.001`에 **흡수**(`repetition_count` 1→2, 증거 누적,
   `confidence` 0.85→0.9, `merge_history`에 후보 id). → `merge_rate`가 NA에서 깨어남.
2. **INSERT (교정 산물).** `eval.004`가 외부 메일을 확인 없이 발송해 **FAIL**(score 0.3)했고,
   그 `correction_notes`가 처방한 `user.boundary_authority` `ConfirmationRuleRecord`
   (`logotekton.boundary.001`)를 judge가 **NOVEL→INSERT**로 적재.
3. **DRIFT (변경 기록).** 그 교정을 `user.drift_history`의 `DriftRecord`
   ([`../drift-history.yaml`](../drift-history.yaml), `logotekton.drift.001`)로 남김 →
   `drift_stability`가 비로소 의미를 가짐(흔들렸다가 회복).

그리고 규칙이 생기자 **`eval.004`가 재실행에서 PASS**로 전환 → `decision_fidelity` 상승.

## 2. T0 → T1 (도구가 출력한 실제 숫자)

| 지표 / 상태 | **T0 (before)** | **T1 (after)** | 무엇이 움직였나 |
|---|:---:|:---:|---|
| 성숙도 | **L0 Seed** | **L2 Working** | 7번째 시드 팩 + fidelity·coverage 통과 |
| 시드된 팩 | 6 / 14 | **8 / 14** | +`boundary_authority` +`drift_history` |
| `coverage` (시드폭) | 0.43 | **0.57** | 두 팩 추가 |
| `decision_fidelity` | 0.75 | **0.92** | eval.004 fail→pass `(5+0.5)/6` |
| `drift_stability` | 1.00 (공허) | **0.94** | 대체 1건 발생 후 회복 — 이제 *의미 있는* 값 |
| `merge_rate` | **NA** | **0.059** | merge actuator가 `repetition_count` 점화 |
| 대체(supersession) | 0 | **1** | `logotekton.drift.001` |
| 평가 (pass/partial/fail) | 4 / 1 / 1 | **5 / 1 / 0** | eval.004 교정 |
| `traceability` | 1.00 | **1.00** | 유지(새 레코드도 모두 증거 결속, G1) |
| `confirmation_ratio` | 1.00 | 1.00 | 유지 |

> **정직성 노트.** (a) 큰 도약(L0→L2)의 상당 부분은 "7팩 시드" 문턱을 넘은 것이며, 이 폭-우선
> 문턱이 관대하다는 점은 별도 개선과제(카파시 리뷰 #7)로 남아 있습니다. (b) `correction_cost`는
> 여전히 **NA**입니다 — 구조화된 작업별 편집 비율 필드가 아직 없습니다(개선 #3). (c) `eval.005`는
> 일부러 **partial 그대로** 두었습니다 — 한 바퀴는 모든 걸 완벽하게 만들지 않습니다. 이 스냅샷은
> *마법*이 아니라 *한 칸*입니다.

## 3. 무엇이 새로 생겼나 (the actuator + the data)

- **[`tools/pab_merge.py`](../../../tools/pab_merge.py)** — 결정론적 dedup judge + upsert/supersede
  actuator. `canonical_key = sha1(pack·record_type·normalize(statement)·normalize(scope))`로
  novel/duplicate/refinement/conflict를 분류하고 merge/insert/supersede/surface를 수행.
  **멱등**(같은 배치 재투입 → `already_merged` noop), 충돌은 절대 자동 적용 안 함(surface).
  이것이 카파시 리뷰가 "존재하지 않는다"고 지적한 바로 그 actuator입니다.
- **[`session-02-candidates.yaml`](./session-02-candidates.yaml)** — 2번째 세션의 인입 후보(merge 1 + insert 1).
- **[`../drift-history.yaml`](../drift-history.yaml)** — 교정의 `DriftRecord`(audit·되돌리기 가능).
- **인스턴스 갱신** — [`../instance-records.yaml`](../instance-records.yaml)의 `heuristic.001`(병합됨)과
  새 `user.boundary_authority` 섹션, [`../evaluation-cases.yaml`](../evaluation-cases.yaml)의 `eval.004`(pass 전환).

## 4. 재현 (reproduce — 모든 숫자는 결정론적)

> ⚠️ **왜 `.pre` 스냅샷을 쓰나.** 라이브 `../instance-records.yaml`는 이 바퀴(그리고 그 뒤 rev-02)가
> *이미 적용된* 상태라, 거기에 대고 plan 을 돌리면 `already_merged`만 나옵니다. 그래서 *이 바퀴
> 적용 전(T0)* 상태를 동결한 [`instance-records.pre.yaml`](./instance-records.pre.yaml)(픽스처)에 대고
> plan→apply 를 돌려 두 판정(merge/insert)을 글자 그대로 재현합니다. 그 apply 결과는 **T1 상태**
> (= [`../revolution-02/instance-records.pre.yaml`](../revolution-02/instance-records.pre.yaml))와 레코드
> 단위로 일치 — 즉 T0 →(rev-01)→ T1 →(rev-02)→ T2 의 사슬이 결정론적으로 이어집니다.

```bash
# (1) dedup judge 계획 — T0 스냅샷(.pre) 대비: duplicate→merge, novel→insert
python tools/pab_merge.py examples/logotekton/revolution-01/instance-records.pre.yaml \
       examples/logotekton/revolution-01/session-02-candidates.yaml
#   → [duplicate] merge logotekton.heuristic.201 -> logotekton.heuristic.001
#   → [    novel] insert logotekton.boundary.001

# (2) 적용 → 멱등성. 적용본(/tmp/t1.yaml)은 T1 상태(= ../revolution-02/instance-records.pre.yaml)와 일치.
python tools/pab_merge.py examples/logotekton/revolution-01/instance-records.pre.yaml \
       examples/logotekton/revolution-01/session-02-candidates.yaml \
       --apply --out /tmp/t1.yaml --stamp 2026-06-28T12:30:00Z
python tools/pab_merge.py /tmp/t1.yaml \
       examples/logotekton/revolution-01/session-02-candidates.yaml   # → already_merged ×2

# (3) 측정 — 주의: 라이브 디렉터리는 그 뒤 rev-02 로 한 바퀴 더 돌아 지금은 T2(df 1.00, coverage 0.71).
#     이 문서의 T0→T1 숫자(L0→L2, df 0.92, merge_rate 0.059)는 §2 표에 보존돼 있고, 현재
#     라이브 재측정은 ../revolution-02/README.md 를 보라.
python tools/convergence_report.py examples/logotekton    # 현재 라이브 = T2 (rev-01 당시엔 T1)
python tools/validate_packs.py     examples/logotekton     # 42 PASS (재귀: 라이브 25 + .pre 픽스처 17)
```

> T0 베이스라인 리포트(이 한 수를 *예측*했던 문서)는 [`../convergence-report.md`](../convergence-report.md).
> 그 문서 §5의 "다음 한 수"가 바로 이 revolution-01입니다 — 예측 → 실행 → 측정의 닫힌 고리.

## 인접 문서
- 데이터-엔진 루프: [`../../../spec/02-builder-pipeline.md`](../../../spec/02-builder-pipeline.md)
- 중복 억제·병합(merge/supersede): [`../../../spec/10-dedup-and-merge.md`](../../../spec/10-dedup-and-merge.md)
- 수렴 지표·성숙도: [`../../../spec/06-convergence-model.md`](../../../spec/06-convergence-model.md)
- actuator: [`../../../tools/pab_merge.py`](../../../tools/pab_merge.py)
