# 10 · 중복 억제와 병합 (Dedup & Merge — accumulate, don't duplicate)

> **EN:** As ambient capture runs across many sessions, the same pattern gets re-derived and
> restated. Left unchecked, near-duplicate records and per-session packs pile up — and a graph
> with *many nodes can still retrieve badly* (redundant context drowns the signal), which hurts
> `decision_fidelity`. So records are **upserted, not appended**: a dedup judge at the
> confirmation gate classifies each confirmed candidate as **novel / duplicate / refinement /
> conflict** and routes it to insert / **merge** / **supersede** / surface-to-user. Repetition
> becomes accumulated evidence on one canonical record — which is exactly *convergence*, not waste.

핵심 한 줄:

> **새 레코드를 찍어내지 말고, 비슷한 기존 레코드에 증거를 누적(upsert)한다.**
> 반복은 버리는 게 아니라 *하나의 정식 레코드에 쌓이는 신뢰*다.

## 1. 왜 필요한가 — 중복은 *효율*이 아니라 *충실도* 문제

세션이 누적되면 같은 휴리스틱이 조금씩 다르게 재서술되고, 같은 규칙이 또 후보로 재유도됩니다.
방치하면 세 가지가 쌓입니다:

1. **레코드 근접중복** — "도구 있으면 실행"을 매번 살짝 다르게 저장
2. **재유도(redundant re-derivation)** — 이미 확정된 규칙을 또 후보로 생성
3. **팩 증식** — 세션마다 새 인스턴스 팩을 찍어냄(안티패턴)

문제의 본질은 저장 낭비가 아니라 **검색 충실도 저하**입니다. *노드가 많은 게 품질이 아닙니다* —
중복이 retrieval에 끼면 관련 없는 덩어리까지 끌려와(컨텍스트 덤프) 컴파일러가 엉뚱한 슬라이스를
활성화하고, 그 결과 [수렴 지표](./06-convergence-model.md)의 `decision_fidelity`가 떨어집니다.

## 2. 원리 — 레코드는 append가 아니라 **upsert**

각 레코드는 **의미적 정체성(semantic identity)** 을 가집니다. 같은 정체성의 후보가 다시 오면
새로 만들지 않고 *기존 레코드를 갱신*합니다(멱등). 정체성 키:

```
canonical_key = hash( target_pack · record_type · normalize(statement) · scope )
```

- `normalize(statement)` = 어휘 정규화(공백·표기·동의어 흡수)된 주장 핵심.
- **scope는 정체성의 일부입니다** — 같은 주장이라도 *다른 스코프*면 다른 레코드입니다(§5 과-제지 경계).
- 근접중복(정확히 같진 않지만 매우 유사) 판정은 같은 `target_pack·record_type·scope` 안에서
  임베딩 유사도 임계(예: cosine ≥ 0.9)로 후보를 좁힌 뒤 judge가 최종 분류합니다.

## 3. dedup judge — 확인 게이트(S07) 직전 한 스텝

승격 전, 새 후보를 대상 팩의 기존 레코드와 비교해 **3-렌즈 critic 루프**로 분류합니다(새 아키텍처가
아니라 게이트에 judge 한 스텝 추가):

1. **identity** — 같은 `canonical_key`의 레코드가 있는가?
2. **scope** — 같은 스코프인가, 더 좁히는(refinement) 것인가?
3. **conflict** — 기존 *확정* 레코드와 모순되는가?

판정 → 처리:

| 판정 | 조건 | 처리 | 게이트 액션 | 기존 자산 |
|------|------|------|-------------|-----------|
| **novel** | 같은 정체성 없음 | 삽입 | `confirm` | [pack_router](../skills/08-pack-router.md) |
| **duplicate** | 같은 정체성·같은 스코프 | **병합** — `evidence_refs` 추가, `repetition_count`↑, `confidence` 갱신, `updated_at` 갱신. 새 레코드 만들지 않음 | `merge` | 멱등 upsert |
| **refinement** | 같은 정체성·더 좁은/갱신된 스코프 | **대체** — 새 레코드 + `supersedes` 엣지, 구 레코드 은퇴 | `supersede` | [`drift_history` 팩](./03-pack-catalog.md) |
| **conflict** | 기존 확정과 모순 | **사용자에게 노출**(조용히 덮어쓰지 않음) | (사용자 결정) | [confirmation_gate](../skills/07-confirmation-gate.md) |

→ confirmation_gate의 리뷰 액션에 **`merge`·`supersede`** 가 추가됩니다(기존 confirm/edit/reject/
narrow/sensitive/defer에 더해). judge가 미리 분류해 *추천 액션*을 제시하므로, 사용자는 한 줄로 승인만.

## 4. 병합 의미론 (멱등 = 누적)

병합은 **멱등**입니다 — 같은 규칙을 N번 재유도하면 레코드 하나로 수렴하고 `repetition_count = N`,
`evidence_refs`는 누적됩니다. `repetition_count`는 [confidence 입력](./01-kernel-schema.md) 중
하나이므로, 반복은 *그 정식 레코드의 신뢰를 올립니다*(단, `counterexamples`가 상한을 건다).
이것이 사용자가 말한 *"비슷한 기존 팩에 새 증거가 누적되어 저장"* 의 정확한 구현입니다.

베이스 레코드 선택 필드: `canonical_key`, `repetition_count`, `merge_history`
([record.base.schema.json](../schemas/record.base.schema.json)).

## 5. 과(過)-제지 경계 — 무엇이 중복이 *아닌가*

**중복 삭제가 목표가 아닙니다.** 두 가지를 반드시 지킵니다:

- **반복은 신호다.** 같은 신호의 반복은 버리는 게 아니라 *하나로 병합해 confidence를 올리는* 자산.
- **다른 스코프는 중복이 아니다.** 같은 주장이라도 *다른 맥락/조건*에서 왔다면 그건 **스코프
  정밀화**일 수 있습니다. judge는 `duplicate`(병합)와 `refinement`(스코프 narrowing)를 반드시
  구분해야 하며, 서로 다른 스코프를 뭉개면 G2(스코프 보존)를 깹니다.

## 6. 팩 카디널리티 규칙

- 한 주체의 인스턴스 팩은 **정확히 14개**(`personal.<주체>.<14팩>`). 포착은 이 14개에 *append/
  upsert*하고, **세션마다 새 팩을 만들지 않습니다.**
- staging(draft)은 *임시 큐*이지 영구 팩이 아닙니다 — 리뷰 후 14개 정식 팩으로 흡수되고 비워집니다.

## 7. 측정 (중복을 숫자로)

[수렴 모델 §7](./06-convergence-model.md)에 효율/수렴 신호로 추가됩니다. 도구:
[`../tools/dedup_check.py`](../tools/dedup_check.py).

| 지표 | 정의 | 방향 | 의미 |
|------|------|------|------|
| `redundancy_ratio` | 근접중복 레코드 쌍 / 전체 레코드 | ↓ (→0) | 높으면 블로트 경보 |
| `pack_cardinality` | 주체의 인스턴스 팩 수 / 14 | =1.0 | >1 이면 팩 증식 |
| `merge_rate` | 병합 / (병합+삽입) | ↑ (성숙 신호) | 재유도가 점점 기존에 흡수됨 = *수렴의 직접 신호* |

> **`merge_rate`가 핵심 통찰입니다.** 에이전트가 성숙할수록 새 포착이 *새 레코드가 아니라 기존
> 레코드로 병합*되는 비율이 올라갑니다 — "아직 발견 중"에서 "채워 넣는 중"으로 넘어갔다는 뜻.
> 즉 중복 억제는 단순 청소가 아니라 **수렴을 보는 또 하나의 창**입니다.

## 8. 게이트 보존

병합은 G1(증거 누적), G2(스코프 보존), G3(여전히 게이트), G5(민감은 경계 먼저)를 모두 지키며,
오히려 traceability를 *강화*합니다(한 정식 레코드에 증거가 모임). 대체는 `drift_history`가 흡수합니다.

## 인접 문서
- 확인 게이트(merge/supersede 액션): [07 confirmation_gate](../skills/07-confirmation-gate.md)
- 수렴/효율 지표: [06 수렴 모델](./06-convergence-model.md) · 도구 [`dedup_check.py`](../tools/dedup_check.py)
- 베이스 레코드(canonical_key·repetition_count): [record.base.schema.json](../schemas/record.base.schema.json)
- 드리프트(대체 이력): [03 팩 카탈로그 · user.drift_history](./03-pack-catalog.md)
