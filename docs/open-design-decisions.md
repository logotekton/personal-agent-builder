# 미해결 설계 결정 (Open design decisions)

> **EN:** Design judgments surfaced by the multi-agent adversarial verification sweeps (CHANGELOG
> [Unreleased], it.16–it.20) that were **reported, not applied**, because each turns on a semantic
> choice the maintainer must make rather than a mechanical correction. They are grouped into three
> coherent clusters so all can be resolved with a few decisions instead of one-by-one. Every cluster
> notes its impact on the locked example numbers; **none has been applied**, so the locked invariants
> (6 indices, `canonical_key 3cabb5142158`, `merge_rate 0.095`, `supersessions 2`,
> `drift_stability 0.8947`, L0 Seed) currently still hold.

이 문서는 적대적 검증 스윕(it.16–it.20)이 **보고만 하고 적용하지 않은** 설계 판단들을 모은 것입니다. 각
항목은 기계적 수정이 아니라 *의미적 선택*이 필요해 단독으로 적용하지 않았습니다. 세 클러스터로 묶었으니,
클러스터별로 한 번씩 결정하면 모두 해소됩니다. 잠금 숫자에 미치는 영향을 각 클러스터에 명시했습니다.

소스 추적: 각 항목의 `it.N` 표기는 [CHANGELOG.md](../CHANGELOG.md) `[Unreleased]` 의 해당 스윕 항목과
대응합니다. 게이트·지표 정의의 정전(正典)은 [spec/06](../spec/06-convergence-model.md) ·
[spec/10](../spec/10-dedup-and-merge.md) 입니다.

---

## 클러스터 1 — pab_merge intra-batch 결정성 (✅ 해결됨 — canonical-survivor tie-break, it.25)

**증상.** 결정론 도구인 `pab_merge` 가 입력 *순서*에 의존하는 출력을 낸다 — "같은 입력 → 같은 출력"
불변식과 모순.

- **it.16** — 충돌밴드(Jaccard 0.5–0.85) intra-batch 순서 의존: 같은 배치의 두 후보가 충돌밴드에 들면
  입력 순서에 따라 *다른* 후보가 `confirmed` 로 저장되고 다른 쪽은 `surface` 로 드롭됨.
- **it.17** — supersede-chain 순서 의존: 같은 identity·다른 scope 클러스터가 한 배치에 오면 어느
  레코드가 `narrowed`(은퇴)되고 어떤 `SupersessionRecord` 가 나오는지 입력 순서에 의존.
- **it.24** — **순수 중복(duplicate) 경로**(Jaccard 1.0, 같은 scope, verdict `duplicate`/`merge`)도
  같은 결함: 같은 canonical_key 후보 2개가 한 배치에 오면 둘 다 1 레코드로 올바르게 합쳐지고 멱등이지만
  (트윈 없음·rep=2), *어느 id 가 생존자로 남고 어느 id 가 merge_history 에 들어가는지*가 첫-도착(입력
  순서)으로 결정됨(75k 속성 케이스 중 516/516 중복 케이스에서 재현). it.16/it.17 은 충돌밴드·다른-scope
  refinement 만 다뤄 이 경로를 빠뜨렸다 — 동일 'canonical 생존자' 결정이 *세 verdict(duplicate·
  refinement·conflict) 전부*에 걸쳐 있음이 이로써 완성됨.

**핵심 질문.** 충돌·체인·**중복** 전반에서 *어느 후보가 권위(confirmed/생존)로 선택되는가*:
(a) canonical 순서(`canonical_key` 또는 `(record_type, statement, scope, id)` 전순서)로 결정론적 단일
생존자를 뽑는다, vs (b) 자동 해소하지 않고 *양쪽을 surface* 로 남겨 사람이 판단한다.

**권고.** 세 사례를 **하나의 'intra-batch 결정성 정책'** 으로 묶는다(단일 canonical-survivor tie-break 이
세 verdict 전부를 해소한다).
- **중복(duplicate)** → (a) canonical 생존자 고정: 같은 canonical_key 그룹에서 `(canonical_key, id)`(또는
  `(record_type, statement, scope, id)`) 최소값을 생존자로 뽑고, 더 일찍 도착한 것 포함 나머지를 그쪽으로
  병합 → 생존 id·merge_history 멤버집합이 입력 순서와 무관.
- **supersede-chain** → (a) 같은 canonical 생존자 규칙.
- **충돌밴드** → (b) 양쪽 surface(자동 `confirmed` 금지) + SURFACE 레코드의 primary 만 canonical 순서로
  결정론화. (충돌밴드는 설계상 'never auto-applied' 카테고리라 자동 승격 자체가 의심스럽다.)
- 셋 다 회귀 테스트로 **입력 순열 불변**(셔플해도 동일 최종 집합, merge_history 는 list 순서만 허용)을 잠근다.

**잠금 숫자 영향.** 예제 logotekton 에는 충돌밴드/동일-identity-다른-scope 다중 후보 클러스터가 없으므로
(`merge_rate 0.095` · `supersessions 2` 는 깨끗한 1:1 경로에서 나옴) canonical tie-break 도입은 잠금값에
영향이 없을 것으로 보임 — **수정 후 예제 재실행으로 확인 필수**. '양쪽 surface' 변형은 surface 카운트를
늘릴 수 있으니 예제가 충돌밴드를 안 타는지 먼저 검증(현재 안 탐).

---

## 클러스터 2 — convergence/maturity 게이밍 벡터 (우선순위: HIGH)

**증상.** 성숙도 지표가 *관찰된 행동의 실질(substance)* 이 아니라 *레코드/케이스의 형식적 존재* 를 세므로,
흩뿌리기·패딩·선택적 누락으로 분모·분자를 조작해 성숙도를 부풀릴 수 있다. de-averaging 명제(spec/06 §8:
흩뿌려 가짜 성숙도 따는 것 차단)와 정면 충돌.

- **it.18(1)** — 교차-팩 id 중복집계: 같은 record `id` 를 12개 팩 키 아래 복사하면 각 팩에서 깊이로 세어
  `coverage 0.14→0.93`, 성숙도 `L0→L3`(L4)로 부풀려짐(실 CLI 재현). `validate_packs` 에 전역 id-유일성
  게이트 없음.
- **it.18(2)** — `correction_cost` 선택적 누락: `edit_fraction` 이 있는 케이스만 평균에 들어가, 비용 큰
  케이스에서 필드를 빼면 `correction_cost` 가 내려가 `L3→L4`.
- **it.19(2)** — `decision_fidelity` 희석: 최소-비공허 always-pass 평가 케이스를 다량 넣으면 진짜 실패가
  희석돼 df 가 오름(`0.6→0.92`, `L2→L3`).
- **it.19(1)** *(HIGH)* — `drift_stability` 대체-카운트 비대칭: 대체수를 `user.drift_history` 의
  supersedes 엣지/이벤트로만 세지만 레코드 은퇴(`_collect_superseded`)는 *모든 팩*의 supersedes 엣지로
  일어남 → 반전을 콘텐츠-팩 supersedes 로 기재하면 레코드는 은퇴하되 대체수는 안 늘어 `drift_stability` 가
  부풀려짐(`0.684→1.0`, `L2→L3`).

**핵심 질문.** 네 벡터 모두 같은 메타-결함의 변종이다. 단일 원리 **"성숙도는 *고유한 실질적 행동 단위*
위에서만 집계한다"** 를 채택하면 함께 닫힌다. 각 fix 의 의미 선택: (a) id 정체성 — 전역 id 유일성 강제 vs
spec/10 `canonical_key` 가 `target_pack` 을 정체성에 포함하는 '(id,pack) 정체성' 해석, (b) '실질적 평가
케이스'의 형식 경계, (c) 누락 `edit_fraction` 의 의미, (d) drift 대체수의 카운팅 모델(이벤트 vs id-타깃).

**권고.** 한 PR 로 묶어 일관되게 적용.
- **(it.18-1)** convergence 가 깊이/coverage 를 집계하기 전에 전역 `canonical_key` 단위로 dedup — 같은
  내용 정체성이 여러 팩에 나타나면 1회만 카운트. spec/10 의 (id,pack) 저장 키는 유지하되 *성숙도 집계*는
  내용 정체성으로 통일한다고 spec/06 §8 에 명문화(흩뿌리기 차단이 de-averaging 의 핵심).
- **(it.18-2 · it.19-2)** `correction_cost` · `decision_fidelity` 분모를 평가 케이스 셋에 고정하고,
  평가 케이스에 `edit_fraction` *필수*화(누락=검증 실패) + '실질적 평가 케이스' 하한 정의(criteria≥N · 서로
  다른 statement · non-trivial pass_threshold)를 `validate_packs` 게이트로 강제. trivial-항등 케이스는 df 에서 제외.
- **(it.19-1)** drift 대체수를 `_collect_superseded` 와 동일 소스(모든 팩 supersedes 엣지 + drift_history
  이벤트)에서 세되, **'대상 id 집합의 합집합 크기'로 중복없이 합치는 단일 카운팅 모델**을 정의.

**잠금 숫자 영향.** 예제는 깨끗(id 중복 없음, behavioral-only, trivial 케이스 없음)하므로 (it.18-1)·
(it.18-2)·(it.19-2) fix 는 잠금 6지표·`coverage`·`merge_rate` 에 영향 없을 가능성이 높음 — 단 재실행 필수.
**(it.19-1) 은 위험**: 예제의 `DriftRecord` 2건이 supersedes 필드가 없어 *이벤트*로 세어져
`supersessions=2`, `drift_stability=0.8947` 이 나오는데, 단순히 `_collect_superseded` 로 전환하면 대체수가
달라져 **`0.8947→1.0` 으로 잠금값이 깨진다**. 따라서 '이벤트 + id-타깃 합집합' 카운팅 모델을 설계할 때
반드시 예제에서 `supersessions 2` · `drift_stability 0.8947` 이 보존되도록 캘리브레이트해야 한다(이것이
it.19-1 이 HIGH 이면서도 단순 적용 불가인 이유).

---

## 클러스터 3 — CLI 종료코드·로더 신호 계약 (✅ 해결됨 — it.25)

**증상.** 도구가 입력의 '부재/손상/빈 콘텐츠'를 종료코드와 결과에 일관되게 사상하지 못한다.

- **it.17(2)** — `dedup_check` 멀티문서 YAML 오파싱: `---` 분리 다문서를 한 'unknown' 팩으로 뭉개
  `id=None`·유령 redundancy 생성, `--strict` 종료코드 0→1 뒤집힘.
- **it.17(3)** — `dedup_check` 누락/손상 경로에 `--strict` 여도 exit 0: I/O 오류를 삼켜(`except: pass`)
  형제 도구와 종료코드 계약 불일치.
- **it.17(4)** — `convergence_report` null-파싱 파일에 exit 2: 주석만 있는(파싱=None) 파일을 '읽기불가'와
  혼동해 '읽을 파일 없음'으로 중단. (it.20 의 pab_merge YAML-fold 발견에서도 이 'exit 0 while silently
  dropping a file' 가 재확인됨 — 같은 계약 결함.)

**핵심 질문.** (a) 다문서 YAML 을 *문서별 분리 파싱* vs *거부(에러)*, (b) '파일 부재/손상'을 `--strict`
에서 nonzero 로 할지(형제 도구 `validate_packs`·`compile_adapter` 의 'path 부재→2, 0레코드→1' 계약과
정합), (c) '읽었으나 파싱=None(빈/주석-only)'을 '읽을 파일 없음'(exit 2)과 *다른* 상태로 분리.

**권고.** 프로젝트 전역 **'CLI 종료코드·로더 신호 계약'** 을 하나로 정의(it.10 의 compile_adapter
false-green 강건화가 세운 'path 부재→2, 0레코드→1' 패턴을 표준으로 승격)하고 세 사례를 일괄 정합.
- **(it.17-2)** `dedup_check` 로더가 `---` 다문서를 *문서별로 분리* 적재(한 'unknown' 팩으로 안 뭉갬).
- **(it.17-3)** 광역 `except: pass` 제거 → I/O·디코드 오류는 `--strict` 에서 nonzero, 비-strict 에서는
  경고-스킵(it.14 per-file 봉쇄 패턴과 일치).
- **(it.17-4)** `convergence_report.load_structured` 가 '읽기 실패(예외)'와 '읽었으나 파싱=None'을 *별도
  sentinel* 로 반환 → None-파싱 파일은 빈 집계로 정상 스킵, exit 2 는 진짜 '읽을 파일 없음'에만 예약.
- **(it.21, CI-2b)** `validate_packs` 가 *모든* 파일이 SKIP(예: PyYAML 부재로 YAML 파일 전부 못 읽음)되어
  검증한 레코드가 0건일 때 `결과: PASS` exit 0 을 낸다(빈-파일 가드는 파일이 0개일 때만 발동) — 공허한 녹색.
  같은 'degenerate 입력 → 종료코드' 계약 결함이므로 클러스터 3 으로 합류: 파일은 있으나 0건 검증이면
  nonzero/FAIL 로 보고할지 결정.

**잠금 숫자 영향.** 네 사례 전부 *퇴화/비정상 입력* 경로에만 작용하며 예제 logotekton 의 정상 입력에는
다문서 YAML·누락 경로·주석-only 파일이 없고 PyYAML 도 설치돼 있으므로 잠금 숫자에 영향 없음. 새 회귀 테스트만 추가됨.

---

## 클러스터 4 — 문서 안전성 주장 vs 실제 (우선순위: MEDIUM)

**증상.** 기여 문서가 *실제로 강제되지 않는* 안전장치를 약속한다.

- **it.21 (OPS-1)** — `CONTRIBUTING.md` 가 "`.gitignore` 가 개인 인스턴스 경로를 무시하므로 실수로라도
  커밋하지 마세요"라고 약속하지만, `.gitignore` 에는 그 인스턴스 경로 패턴이 실제로 없어 약속이 거짓이다.

**핵심 질문.** 두 방향의 fix 중 선택: (a) 문서가 약속한 인스턴스 경로 스킴을 `.gitignore` 에 *실제로 추가*
(단, 패턴을 잘못 잡으면 `examples/`·공개 자산까지 무시할 위험 — 의도된 인스턴스 경로 스킴 확정 필요), vs
(b) 강제되지 않는 안전 약속을 `CONTRIBUTING` 에서 *제거/완화* 하고 수동 주의 지침으로 대체.

**권고.** 인스턴스 경로 스킴이 스펙에 명확히 정의돼 있으면 (a)(예: `personal.*` 패턴을 `.gitignore` 에
추가하되 공개 자산은 negate)로 실제 안전장치를 만들고, 모호하면 (b)로 거짓 약속을 먼저 제거. 어느 쪽이든
문서의 주장과 저장소 현실을 일치시킨다.

**잠금 숫자 영향.** 없음(문서·`.gitignore` 만 변경, 도구·예제 무관).

---

## 클러스터 5 — 스키마↔문서 트리거/경계 계약 (우선순위: MEDIUM)

**증상.** 머신 스키마가 *자기 문서가 선언하는 값을 표현하지 못하거나*, 문서가 *스키마에 없는 강제를
주장한다*.

- **it.22 (host_hook)** — `trigger.schema.json` 의 `host_hook` 은 단일-토큰 enum(9개)인데, 11개 스킬
  트리거 블록 중 **7개**가 `'UserPromptSubmit · PostToolUse'` 같은 `·`-결합 복합값을 싣고(각 스킬은
  "머신 스키마는 ../schemas/trigger.schema.json" 이라 명시), spec/09 §2 정식 표의 signal/cadence 열도 동일.
  jsonschema 로 7/11 블록이 **검증 실패**(재현). 즉 정식 머신 계약이 자기 문서가 싣는 값을 못 담는다.
  추가로 *임베디드 트리거 블록을 검증하는 도구가 없다*(check_schemas 는 스키마 *파일* 만 검사) — 이 결정
  후 트리거-블록 검증기를 추가하면 좋다.
- **it.22 (confirmation_trigger)** — spec/04 가 `confirmation_trigger` 를 스키마 enum 인 것처럼 기술하나
  `user.boundary_authority.schema.json` 은 제약 없는 문자열 배열로 둠 → 머신 강제를 과대표현.

**핵심 질문.** (a) `host_hook`/signal/cadence 를 *enum-토큰 배열*(`type:array, items:{enum:[…]}`)로
모델링해 복합값을 표현할 것인가, vs 각 문서 값을 단일 토큰 + 산문으로 축약할 것인가. (b)
`confirmation_trigger` 에 실제 enum 을 *추가*(스키마 강화)할 것인가 vs 문서 주장을 *완화*(enum 아님 명시)할
것인가. (b)에서 enum 추가는 기존 예제 boundary 레코드 값이 enum 밖이면 validate 를 깰 수 있으니 예제값 먼저
점검 필요.

**권고.** `host_hook` 등은 (a) 배열-enum 으로 — 다중-훅 바인딩(skills/14 §2: turn→UserPromptSubmit,
tool_result→PostToolUse)이 실재 의미라 단일 토큰으로 못 담기 때문. 스키마·11 스킬 블록·spec/09 표를 YAML
리스트로 한 PR 에 맞춘다. `confirmation_trigger` 는 예제값을 점검해 enum 으로 좁히거나(전부 포함되면)
문서를 완화. 임베디드 트리거 블록 검증기(check_triggers)를 함께 추가해 회귀를 잠근다.

**잠금 숫자 영향.** 없음 — `host_hook`/`confirmation_trigger` 는 잠금 지표·예제 validate(42 PASS, logotekton
은 트리거 블록·boundary enum 경로를 안 탐)와 무관. 단 confirmation_trigger enum 추가 시 boundary 예제 재검증.

---

## 참고 — 같은 스윕에서 *적용된* 항목

이 문서는 *미적용* 항목만 모읍니다. 같은 스윕에서 기계적·안전하다고 판단해 *적용된* 약 40건의 수정은
[CHANGELOG.md](../CHANGELOG.md) `[Unreleased]` 의 it.14–it.20 항목에 있습니다(스키마 경계 강제, 게이트
항목-품질 검사, stale-key·정렬·로더 견고성, pab_merge YAML round-trip 등). it.20 의
`pab_merge --out` YAML width-fold(파이프라인이 조용히 빈 집합이 되던 HIGH 버그)는 writer 측 최소 수정으로
*적용* 되었습니다 — 위 클러스터 3 의 'exit 0 while dropping a file' 측면만 설계 결정으로 남습니다.
