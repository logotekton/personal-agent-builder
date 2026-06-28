# tests/ — regression lock for the deterministic tools

> **EN:** stdlib-only (`unittest`) regression tests that pin every number the project's claims
> rest on, so a future change cannot silently move them. The repo's thesis is *"becoming me is a
> number you watch climb"* and *"every figure is reproduced by the commands"* — these tests make
> that contract executable.

순수 표준 라이브러리 테스트입니다(외부 의존성 없음; PyYAML이 있으면 재귀 CLI 경로까지 검사). 프로젝트가
의존하는 *모든 숫자*를 회귀로 잠급니다.

## 무엇을 잠그나 (`test_tools.py`, 30 tests)

- **`tools/pab_merge.py`** — `canonical_key` 결정성 + 알려진 값(`3cabb5142158`); 네 판정
  (`novel→insert` · `duplicate→merge` · `refinement→supersede` · `conflict→surface`) + `already_merged`;
  `apply_plan`의 병합 누적(트윈 안 찍음)·삽입·**충돌 절대 미적용(안전 불변식)**·대체 은퇴+drift·**멱등성**.
- **`tools/convergence_report.py`** — logotekton 예제의 6지표·성숙도 잠금: **L2**, coverage `0.714`,
  decision_fidelity `1.0`, correction_cost `0.0833`, drift_stability `0.8947`, traceability `1.0`;
  카운트(시드 10·확인 19·대체 2·평가 6/0/0); **NA correction_cost가 L3를 막음**; 남은 L3 빗장이
  `coverage`뿐임.
- **`tools/validate_packs.py`** — 게이트: 정상 레코드 통과, G1(증거)·G2(스코프)·confidence 범위·
  `confidence<0.7→counterexamples`·필수필드·enum 위반 거부.
- **`tools/dedup_check.py`** — 예제 `merge_rate` `0.095`.
- **end-to-end** — `examples/logotekton` 전체 검증 **42 PASS**, 그리고 `revolution-01/02`의 `.pre`
  픽스처가 문서화된 merge/insert/conflict 판정을 그대로 재현.

## 실행

```bash
python3 -m unittest discover -s tests        # 또는
python3 tests/test_tools.py                  # verbose
```

종료 코드 0 = 모든 숫자가 잠긴 그대로. 어떤 테스트라도 깨지면, 그 숫자를 인용하는 문서
(`examples/logotekton/convergence-report.md` · `revolution-01/02/README.md` 등)도 함께 갱신해야 한다는
신호입니다 — 숫자와 산문이 갈라지지 않게.
