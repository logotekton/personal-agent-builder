# Changelog

> **EN:** All notable changes to the Personal Agent Builder specification are recorded
> here. The format follows [Keep a Changelog](https://keepachangelog.com/) and the project
> adheres to semantic-ish spec versioning (`v0.MAJOR.MINOR`). **v0.3 is the first public
> release**: it reconciles every inconsistency found across the earlier private `v0.1`
> (13 skill packs) and `v0.2` (template-schema reinforcement) drafts into one canonical
> contract. The single source of truth is [`spec/01-kernel-schema.md`](./spec/01-kernel-schema.md);
> per-pack definitions live in [`spec/03-pack-catalog.md`](./spec/03-pack-catalog.md).

이 문서는 Personal Agent Builder **사양(spec)**의 주요 변경을 기록합니다. 형식은
[Keep a Changelog](https://keepachangelog.com/) 규칙을 따르며, 버전은 `v0.MAJOR.MINOR`
체계를 씁니다. 변경 항목은 `Added`(추가) · `Changed`(변경) · `Reconciled`(정합화) ·
`Deprecated`(폐기) · `Removed`(제거) · `Fixed`(수정)로 분류합니다.

용어의 정식 정의는 [커널 스키마](./spec/01-kernel-schema.md)와
[팩 카탈로그](./spec/03-pack-catalog.md)를 기준으로 삼습니다. 이 변경 기록은 그 정의를
요약·추적할 뿐, 새 어휘를 만들지 않습니다.

---

## [Unreleased]

### 다중 에이전트 적대적 검증 스윕 — it.21 (운영·온보딩 레이어 — 실 버그 7건 + 설계판단 2건)
> it.14–20 이 안 건드린 운영/온보딩 레이어(CI 커버리지 · 튜토리얼 정확성 · governance 정합 · traversal
> 결정성 · 교차-도구 유니코드 정규화)를 5렌즈로 스윕. **9 확인 / 0 기각**. 잠금 숫자 전부 불변.
- **[Fixed] (MEDIUM) 교차-도구 NFC 정규화 누락 — 은퇴 레코드가 LIVE 로 남음.** convergence·compile 의
  superseded-id 비교(집합 + 조회)와 context_select 스코프 매칭이 NFC 정규화를 안 해서, NFD supersedes 참조
  vs NFC 대상 id(또는 NFD 스코프 vs NFC 작업 태그)가 시각적으로 같은데 매칭 실패 → 폐기 레코드가 활성으로
  남아 이중집계되거나 in-scope 레코드가 선택에서 누락. 세 도구 모두 `unicodedata.normalize("NFC", …)` 통일
  (pab_merge canonical_key NFC, it.13 과 같은 취지). 예제 id 는 ASCII 라 잠금값 불변.
- **[Fixed] (MEDIUM) CI 가 schemas/*.json 을 전혀 검사 안 함.** 17개 스키마(레코드 계약의 root-of-truth)가
  깨지거나 record.base 로의 `$ref` 가 끊겨도 CI 가 녹색으로 머지됨(주입 실험으로 재현). 새 `tools/check_schemas.py`
  (stdlib: JSON 형식 + draft 2020-12 + `$ref` 해결성 + per-pack allOf+$ref-to-record.base 강제)를 추가하고
  CI 게이트로 배선.
- **[Fixed] (MEDIUM) dedup_check 비결정 출력.** 디렉터리 입력을 `glob`(파일시스템 순서) 그대로 집계해 near-dup
  pair 목록·방향이 흔들림 → `sorted(files)` 로 결정론화.
- **[Fixed] (LOW·문서) 튜토리얼 L1 정의 불완전.** build-your-personal-agent.md §7 의 L1 기준이 '≥3 평가
  케이스'·'콘텐츠 팩(메타 제외)' 한정자를 빠뜨려 번들 예제가 거짓으로 L1 처럼 보였음 — spec/06·도구 게이트에 맞춤.
- **[Fixed] (LOW·문서) 튜토리얼 'L0→L1' 과대표현.** 같은 §7 이 예제 스냅샷을 'L0→L1'이라 했으나 예제·도구는
  내내 L0 → '현재 L0, 다음 한 수=L1 조건'으로 정정.
- **[Fixed] (LOW·문서) GOVERNANCE 잘못된 섹션 참조.** 구 코드명 규칙을 `[08 §3]`(ID 형식)으로 가리켰으나 실제
  규칙은 `08 §5`(코드명→정식이름 마이그레이션 표) → 정정.
- **[Fixed] (LOW·문서) CI stdlib-only 주석 부정확.** 매트릭스가 'stdlib-only portability 를 보증'한다 했으나
  모든 레그가 PyYAML 설치 → 버전 이식성만 커버하고 no-PyYAML 경로는 안 돈다고 정정.
- **[Added] 회귀 테스트 4건**(`TestUnicodeAndOperationalIt21`) + `tools/check_schemas.py`. 총 160→164.
- **[NOTE] (보고만·미적용 — 설계판단 2건):** (1) `validate_packs` 가 모든 파일 SKIP(레코드 0건 검증)시
  `결과: PASS` exit 0 — 공허한 녹색(클러스터 3 합류). (2) `.gitignore` 가 CONTRIBUTING 이 약속한 개인 인스턴스
  경로를 실제로 무시하지 않음 — 안전 약속이 거짓(docs/open-design-decisions.md 클러스터 4).

### 다중 에이전트 적대적 검증 스윕 — it.20 (캡스톤: 통합 재감사 + 설계판단 종합 — 실 버그 2건)
> 캡스톤 스윕: it.1–19 수정들의 상호 정합성 재감사 + 파이프라인-통합 버그헌트 + 테스트-주장 커버리지 감사 +
> 9개 보고된 설계판단을 3 클러스터로 종합. **2 확인 / 0 기각**. 누적 수정 상호 모순·무회귀 0건 확인.
- **[Fixed] (HIGH) pab_merge `--out *.yaml` 가 자기 리더가 못 읽는 YAML 을 출력.** PyYAML 기본 width=80
  이 긴 스칼라를 다음 줄로 접는데(folded continuation), 번들 mini-YAML 파서(convergence_report·
  compile_adapter)는 접힌 스칼라를 못 읽어 *그 파일을 통째로 None 으로 떨군다* → 머지→컴파일→수렴
  파이프라인이 조용히 빈 인스턴스 집합이 됨(예: drift_stability 0.89→0.75, n_active_packs 8→0, 둘 다 exit 0).
  `yaml.safe_dump(..., width=10**9)` 로 쓰는 쪽이 자기 리더가 읽을 수 있게 출력. (남은 'exit 0 while
  dropping a file' 측면은 docs/open-design-decisions.md 클러스터 3 으로 보고.)
- **[Fixed] (MEDIUM) 성숙도 게이트 절들에 경계 테스트 부재.** it.18 의 L3 `drift_stability≥0.7` 절(및 L2/L3/L4
  의 다른 모든 절)을 mutation 으로 지워도 150 테스트 전부 통과 — 어떤 테스트도 티어를 L3/L4 로 몰지 않았음.
  `TestMaturityLadderGatesIt20` 가 각 절을 경계에서 잠금(mutation 으로 FAIL 확인).
- **[Added] docs/open-design-decisions.md** — it.16–20 에서 보고된 9개 설계판단을 3 클러스터(pab_merge
  intra-batch 결정성 · convergence/maturity 게이밍 · CLI 종료코드 계약)로 종합. 각 클러스터에 핵심 의미
  질문·권고 해소책·잠금 숫자 영향을 명시 — 메인테이너가 한 번에 결정할 수 있는 단일 결정 문서.
- **[Added] 회귀 테스트 10건**(`TestMaturityLadderGatesIt20` 9 + `TestPabMergeYamlRoundTripIt20` 1). 총 150→160.

### 다중 에이전트 적대적 검증 스윕 — it.19 (라이프사이클·체커 자기정합·게이밍 — 실 버그 3건 + 설계판단 2건)
> 5렌즈(candidate 라이프사이클 · reliability 클레임계층 · 체커 자기정합 · salience 수치 · 게이밍 v2)로
> **5 확인 / 0 기각**. 검증기 라이프사이클 구멍 1건과 정직성-체커 가짜음성 2건을 닫음. 잠금 숫자 불변.
- **[Fixed] (MEDIUM) 베이스 레코드가 후보로 오분류돼 모든 게이트 우회.** `_is_candidate` 가 후보-필드
  *존재*만으로 판정해, 승격 시 감사용 candidate_id/validation_status 를 보존한(또는 candidate_type 이 끼어든)
  베이스 레코드가 후보로 분류돼 SKIP → G1/G2/G5/반례 게이트를 *전부* 건너뜀(민감·무증거·무스코프 confirmed
  레코드가 조용히 통과). 베이스 형태(record_type·review_status·id+statement)면 후보로 보지 않도록 부정게이트.
- **[Fixed] (LOW) check_anchors gh_slug 가짜음성.** Python `\w` 가 No/Nl(½ ① ² Ⅻ 등)을 유지하는데
  github-slugger 는 제거 → 도구가 GitHub 이 안 만드는 슬러그를 인정해 그 #fragment 가 통과하고도 실제 404.
  (저장소에 실제 `S10½` 헤딩 존재.) No/Nl 만 추가 제거(Nd 십진수·한글 유지).
- **[Fixed] (LOW) check_commands 가짜음성.** TOOL_INVOCATION 이 줄 시작만 매칭해 `$ python …`/`> python …`
  프롬프트 붙은 호출은 추출조차 안 돼 실행성 미검증 → 명령 시작 줄의 셸 프롬프트 마커를 떼고 매칭(연속줄 제외).
- **[Added] 회귀 테스트 4건**(`TestLifecycleAndCheckersIt19`). 총 146→150.
- **[NOTE] (보고만·미적용 — 설계판단 2건):**
  (1) **(HIGH) drift_stability 대체-카운트 비대칭 게이밍.** drift_stability 는 대체수를 user.drift_history
  레코드에서만 세지만, 레코드 은퇴(_collect_superseded)는 *모든 팩*의 supersedes 엣지로 일어난다 — 반전을
  DriftRecord 대신 콘텐츠-팩 supersedes 엣지로 기재하면 동일 런타임 효과로 레코드는 은퇴하되 대체수는 안 늘어
  drift_stability 가 부풀려짐(0.684→1.0, L2→L3). 단, 예제의 DriftRecord 2건은 supersedes 필드가 없어
  *이벤트*로 세어지므로(supersessions 2), 단순히 _collect_superseded 로 바꾸면 잠금값 0.8947→1.0 로 깨진다 —
  이벤트와 id-타깃을 중복없이 합치는 *카운팅 모델 설계*가 필요해 보고.
  (2) **(MEDIUM) decision_fidelity 희석.** 최소-비공허 always-pass 평가 케이스를 다량 넣으면 진짜 실패가
  희석돼 df 가 오름(0.6→0.92, L2→L3; trivial 케이스 edit_fraction=0 이라 correction_cost 도 동반 하락).
  it.4 공허-루브릭 방어를 우회 — '충분히 실질적'의 경계가 모호해 의미적 선택이라 보고.

### 다중 에이전트 적대적 검증 스윕 — it.18 (성숙도 사다리 red-team + 문서 정합 — 문서수정 2건 + 설계판단 2건)
> 5렌즈(성숙도 사다리 합성 게이밍 · 지표별 조작 · 스키마/스펙 내부 정합 · 어댑터 충실도)로 **4 확인 / 1 기각**.
> 이번엔 개별 게이트가 아니라 *사다리 전체*를 red-team — 핵심 게이밍 벡터 2건은 정체성/분모 의미가 걸려
> 보고만, 문서 모순 2건은 표·도구·정전 정의에 맞춰 정합화. 잠금 숫자 불변.
- **[Fixed] (LOW·문서) skills/12 역할 수 모순.** §3 본문이 "9개 상태를 소유하는 12개 실행 역할"이라 했으나
  같은 문서의 표·§3 주석·spec/02 §4 는 상태 소유 역할이 11개(Evidence…Evaluator), Pack Architect 는 상태
  미소유 척추 역할이라고 명시 — 본문을 표에 맞춰 "11개 실행 역할 + Orchestrator + Pack Architect(척추)"로 정정.
- **[Fixed] (LOW·문서) spec/05 §4 L3 게이트 누락.** spec/05(드리프트 문서)의 L3 요약이 정작 `drift_stability`≥0.7
  을 빠뜨려, spec/06 §3·skill 11·convergence_report 도구(L3=coverage≥0.8·df≥0.8·cost≤0.3·drift≥0.7)와 불일치 —
  드리프트≥0.7 을 추가하고 "헤드라인 요약, 전체 조건은 §6 §3" 명시.
- **[NOTE] (보고만·미적용 — 설계판단 2건, 핵심 게이밍 벡터):**
  (1) **교차-팩 id 중복집계 → 성숙도 L0→L3 게이밍.** 같은 record `id` 를 12개 팩 키 아래 복사하면 각 팩에서
  깊이로 세어 coverage 0.14→0.93, 성숙도 L0→L3(메타변형 L4)로 부풀려짐(실 CLI 재현). validate_packs 에 전역
  id-유일성 게이트가 없고 convergence 가 팩별로 독립 집계. 단, spec/10 canonical_key 가 target_pack 을 정체성에
  포함하는 반대해석이 있어 *의미적 선택*(전역 id 유일성 강제 vs (id,pack) 정체성 용인) 필요 — 보고. de-averaging
  논제(§8: 흩뿌려 가짜 성숙도 따는 것 차단)와 정면 충돌하는 벡터라 우선 보고.
  (2) **correction_cost 선택적 누락 게이밍.** edit_fraction 이 있는 케이스만 평균에 들어가, 비용 큰 케이스에서
  필드를 빼면 지수가 내려가 L3→L4. 누락 edit_fraction 의 의미(필수화 vs 0 vs 분모 공개)가 *의미적 선택*이라 보고.

### 다중 에이전트 적대적 검증 스윕 — it.17 (스키마-검증기 경계 정합 — 실 버그 4건 + 설계판단 4건)
> 5렌즈(스키마↔검증기 정합 · 성숙도 게이트 경계 · 문서수치↔도구 드리프트 · intra-batch 결정성 심화 ·
> 퇴화입력 CLI)로 **8 확인 / 1 기각**. 검증기가 스키마가 선언한 수치 경계([0,1]·(0,1])를 강제하지 않아
> 불가능한 값이 통과·지표를 오염시키던 부류를 닫음. 잠금 숫자 전부 불변. + 설계판단 4건은 보고만(아래).
- **[Fixed] (MEDIUM) result.score 가 [0,1] 밖이어도 통과.** score=5.0 이 status↔score 정합 게이트(score≥thr)를
  무의미하게 통과시켜 불가능한 점수가 'pass' 를 인증. 스키마(result.score min0 max1)대로 경계 강제(it.13 NaN/inf 와 대칭).
- **[Fixed] (MEDIUM) result.edit_fraction 이 [0,1] 밖이어도 통과 + correction_cost 오염.** 50.0 이 검증기를
  통과하고 평균에 그대로 들어가 correction_cost=50.0. *음수*는 비용을 과소평가해 L3/L4 게이트를 헛되이
  통과시키는 게이밍 벡터. 검증기에서 경계 강제 + convergence `_finite_num` 도 [0,1] 분수만 받도록 방어(원시 레코드).
- **[Fixed] (LOW) criteria weight 가 [0,1] 밖이어도 합만 맞으면 통과.** 2.0+(-1.0)=1.0 이 가중치합 게이트를
  통과 → 음수/초과 weight 명시 거부(스키마 weight 0..1).
- **[Fixed] (LOW) pass_threshold 상한 미강제.** 임계>1 은 도달 불가능해 영구 fail 인데 통과됨 → (0,1] 로 강제(스키마 max1).
- **[Added] 회귀 테스트 5건**(`TestSchemaBoundParityIt17`). 총 141→146.
- **[NOTE] (보고만·미적용 — 설계판단 4건):**
  (1) **pab_merge supersede-chain 순서 의존** — 같은 identity·다른 scope 클러스터가 한 배치에 오면 어느
  레코드가 narrowed(은퇴)되고 어떤 SupersessionRecord 가 나오는지 입력순서에 의존(it.16 충돌밴드와 동류 —
  pab_merge intra-batch 결정성을 통합 결정 필요).
  (2) **dedup_check 멀티문서 YAML 오파싱** — `---` 분리 다문서를 한 'unknown' 팩으로 뭉개 id=None·유령
  redundancy 생성, --strict 종료코드 0→1 뒤집힘(병합 vs 거부 선택 필요).
  (3) **dedup_check 누락/손상 경로에 --strict 여도 exit 0** — I/O 오류를 삼켜 형제 도구와 종료코드 계약 불일치.
  (4) **convergence_report null-파싱 파일에 exit 2** — 주석만 있는(파싱=None) 파일을 '읽기불가'와 혼동해
  '읽을 파일 없음'으로 중단(load_structured 신호 분리 필요).

### 다중 에이전트 적대적 검증 스윕 — it.16 (it.15 패턴 일반화 — 실 버그 6건 + 설계판단 1건)
> it.15 가 드러낸 두 패턴(리스트형 게이트의 항목-품질 누락 · 저장된 파생값 신뢰)을 *체계적으로* 추적한
> 5렌즈 스윕으로 **6 확인 / 0 기각**. 잠금 숫자(6지표·canonical_key·merge_rate 0.095·supersessions 2)는
> 전부 불변. + 적용하지 않고 사용자에게 보고한 설계판단 1건(아래 NOTE).
- **[Fixed] (MEDIUM) scoring_rubric.criteria 항목-품질 누락 + 가중치합 게이트 무력화.** criteria 에 비-dict
  원소 하나만 끼우면 `weights` 리스트에서 조용히 빠져 `len(nums)==len(crit)` 가드가 무너지고 합 5.0 짜리
  쓰레기 루브릭이 통과(decision_fidelity 공허하게 부풀림). 항목-품질 검사 추가(it.15 게이트 패밀리의 마지막).
- **[Fixed] (MEDIUM) dedup_check merge_rate 가 provenance 무시.** merge_rate 가 저장된 repetition_count
  카운터만 보고 merge_history(출처 추적)를 안 읽어, 카운터가 stale 면 수렴을 0 으로 오보·inflated 면 과대보고.
  `max(len(merge_history), repetition_count-1)` 로 둘 중 큰 값 사용(clean 예제에선 둘이 일치 → 0.095 불변).
- **[Fixed] (MEDIUM) superseded-id 정규화가 두 도구에서 갈림.** convergence._id_set 과 compile_adapter._as_id_set
  가 비문자열 supersedes 원소(리스트 속 None·비-리스트 스칼라)를 다르게 정규화 → 같은 입력에서 runtime-active
  집합이 갈라짐(docstring 은 '동일 규칙'이라 주장). _id_set 을 _as_id_set 와 원소-단위로 일치.
- **[Fixed] (LOW) compile_adapter 정렬이 id+statement 동률에서 입력순서 의존.** it.14 의 (id,statement) 키도
  scope 만 다른 동일-id+statement 레코드에서 동률 → scope 를 보조키로 추가(전순서).
- **[Fixed] (LOW) context_select 정렬이 id+statement 동률에서 입력순서 의존.** selected/dropped 분할이 입력순서로
  뒤집힘 → (-salience,id,statement,scope,est_tokens) 전순서.
- **[Added] 회귀 테스트 7건**(`TestSystemicConsistencyIt16`). 총 134→141.
- **[NOTE] (보고만·미적용) pab_merge 충돌밴드 intra-batch 순서 의존.** 같은 배치의 두 후보가 충돌밴드(0.5~0.85)
  에 들면 입력 순서에 따라 *다른* 후보가 confirmed 로 저장되고 다른 쪽은 surface 로 드롭됨 — 결정론 도구가
  순서 의존 출력을 내는 모순. 수정에 의미적 선택(canonical-순서 생존 vs 양쪽 surface)이 걸려 있어 설계 판단으로
  사용자에게 보고(미적용).

### 다중 에이전트 적대적 검증 스윕 — it.15 (게이트 우회 + 병합-정체성 — 실 버그 8건)
> 5렌즈(수렴-수학 0-나눗셈/빈집합 · 게이트 타입혼동 우회 · it.14 가드 자체 공격 · 어댑터 라우팅 ·
> 병합 분류 결정성)로 **8 확인 / 0 기각**. 이번엔 크래시가 아니라 *조용히 통과/오판하는* 게이트·정체성
> 버그가 핵심. 잠금 숫자(예제 6지표·canonical_key·merge_rate)는 전부 불변.
- **[Fixed] (HIGH) RLVR 하드페일 게이트 타입혼동 우회.** `unacceptable_fired` 가 list[비어있지않은 str]
  가 *아니면*(예: `[{"rule":"leaked_pii"}]` 객체 리스트·스칼라 문자열) 발동한 하드페일이 조용히 무시되어
  status='pass' 가 통과 → 가장 안전-결정적 게이트가 가장 쉽게 뚫림. 형태를 강제(G1 항목-품질 검사와 대칭).
- **[Fixed] (HIGH) 병합 정체성에 stale canonical_key 신뢰.** classify 가 기존 레코드의 *저장된*
  canonical_key 를 매칭에 쓰는데, 후보는 내용에서 재계산 → 비대칭. stale 키가 (a) 진짜 중복을 놓쳐 쌍둥이
  삽입(G1 위반) 또는 (b) 무관한 레코드에 잘못 병합(조용한 손상). 항상 내용에서 재계산(spec/10 §2 불변식).
- **[Fixed] (MEDIUM) G5 exception_rules placeholder 우회.** `[None]`/`['']`/`[123]` 같은 placeholder 가
  BoundaryRule 요건을 충족 → 민감/제한 레코드가 빈 예외규칙으로 승격. 항목-품질 검사 추가(G1 대칭).
- **[Fixed] (MEDIUM) counterexamples placeholder 우회.** 저신뢰(<0.7) 레코드가 빈/널 placeholder 로
  반례 요건 충족 → 실제 반례 ≥1 강제(G1 대칭).
- **[Fixed] (MEDIUM) apply_plan 무한 repetition_count 크래시.** `int(inf)` 는 OverflowError(it.14 가드는
  TypeError·ValueError 만 잡음) → 무한값도 1 로 보고 진행하도록 except 확장.
- **[Fixed] (MEDIUM) compile_adapter 가 applies_in 스코프 무시.** `--task` 필터가 `scope` 만 읽어
  applies_in-스코프 레코드가 모든 작업류 어댑터에 새어듦 → context_select 와 갈라짐(runtime-active 불일치).
  `scope or applies_in` 로 일치(두 결정론 도구 합의 불변식 유지).
- **[Fixed] (MEDIUM) 충돌 분류가 untyped 레코드 누락.** conflict 패스가 bare `r.get('record_type')`(None)
  를 후보 기본값 `''` 과 비교 → record_type 없는 레코드의 진짜 충돌을 'novel' 로 오판. 정규화(duplicate/
  refinement 패스와 대칭).
- **[Added] 회귀 테스트 7건**(`TestGateQualityIt15`). 총 127→134.

### 다중 에이전트 적대적 검증 스윕 — it.14 (2차 퍼징 — 실 코드버그 13건)
> it.13 에 이어 *입출력·로더·병합 경계*를 집중 퍼징한 2차 스윕으로 **13 확인 / 1 기각**. 손상/비-UTF8/
> 과중첩 입력 파일 하나가 디렉터리 전체 실행을 죽이거나, 비결정 정렬·비숫자 예산·중복-id 병합이 조용히
> 데이터를 망치던 경로들을 각 도구 경계에서 봉쇄. 잠금 숫자(예제 지표·canonical_key)는 전부 불변.
- **[Fixed] (HIGH) 손상 입력 1개가 전체 실행 중단.** `convergence_report.load_structured`·
  `validate_packs.load_file`·`pab_merge._load` 가 비-UTF8(UnicodeDecodeError)·과중첩 JSON/YAML
  (RecursionError) 에서 추적역추적으로 죽어 디렉터리 전체 수렴/검증/병합을 중단 → 각 로더가 *그 파일만*
  경고-건너뜀(수렴) 또는 깔끔한 오류/SystemExit 로 보고하고 나머지는 계속.
- **[Fixed] (MEDIUM) pab_merge 중복-id 후보 데이터 손실.** `apply_plan` 이 `{id: cand}` 사전으로 후보를
  찾아, 같은 id 후보가 둘이면 한쪽이 덮어써져 *서로 다른 진술이 유실*. plan_batch 출력은 후보와 1:1·동순서
  이므로 위치(zip)로 짝짓도록 변경 + 길이 불일치는 명시적 ValueError.
- **[Fixed] (MEDIUM) pab_merge 비정수 repetition_count 크래시.** `int("oops")` 가 병합 누적에서
  ValueError → 관용적 코어션(비정수는 1 로 보고 +1).
- **[Fixed] (MEDIUM) pab_merge 문자열 evidence_refs 문자분해.** `evidence_refs` 가 리스트 아닌 문자열이면
  `for ev in "ref"` 가 글자 단위로 쪼개져 가짜 참조 생성 → `_as_ref_list` 가 문자열을 단일 원소로 정규화.
- **[Fixed] (MEDIUM) context_select 비숫자 예산.** `token_budget` 이 None·문자열·NaN·bool 이면 전부드롭/
  전부선택의 조용한 오작동이나 TypeError → 입력 단계에서 숫자·유한 검증.
- **[Fixed] (LOW) compile_adapter 비문자열 id 크래시.** `render_summary` 의 `", ".join(r["id"] ...)` 가
  정수 id 에서 TypeError → `str()` 강제(섹션·project_context 둘 다).
- **[Fixed] (LOW) compile_adapter 동일-id 비결정 정렬.** id 단독 정렬은 동일-id 레코드에서 안정정렬이
  입력순서에 의존 → `(id, statement)` 전순서로 입력순서와 무관한 어댑터 보장.
- **[Fixed] (LOW) pab_merge._load 파일핸들 누수.** `open(...).read()` 가 핸들을 안 닫음 → with 컨텍스트.
- **[Added] 회귀 테스트 10건**(`TestRobustnessFuzzingIt14`): 위 각 수정 + 로더 봉쇄(비-UTF8·과중첩) +
  길이 불일치 가드. 총 117→127.

### 다중 에이전트 적대적 검증 스윕 — it.13 (엣지케이스 퍼징 — 실 코드버그 9건)
> 전 도구 엣지케이스 퍼징(NaN/inf/None/bool/유니코드/대용량/악성 YAML) 4렌즈로 **9 확인 / 0 기각**.
> it.12 의 NaN-비결정 버그가 *다른 부류*가 더 있음을 시사 → 퍼징이 11회 못 잡던 실 버그 9개를 노출.
- **[Fixed] (HIGH) canonical_key NFD 유니코드 충돌.** 분해형(NFD) 한글은 결합 자모(가-힣 밖)라 토큰이
  통째로 사라져 *서로 다른 한글 진술이 같은 키로 충돌 → 잘못된 병합*. `_norm_tokens` 가 NFC 정규화 후
  토큰화하도록 수정(NFC≡NFD 같은 키, 다른 진술은 분리). 잠금값 3cabb5142158 불변.
- **[Fixed] (MEDIUM) NaN/inf correction_cost 오염.** NaN edit_fraction → correction_cost=NaN → 무효 JSON·
  NA-가장·성숙도 오강등 → `_correction_value` 가 비유한값·bool 거부.
- **[Fixed] (MEDIUM) validate NaN score 게이트 우회.** NaN score 가 status↔score 정합 게이트를 조용히 통과 →
  `_num` 이 math.isfinite 요구 + NaN weight/score 명시 거부.
- **[Fixed] (MEDIUM) enum 검사 unhashable 크래시.** sensitivity/review_status/reliability 가 list/dict 면
  `x in SET` 이 TypeError 로 검증 전체 중단 → `_in_enum`/`_not_in_enum` 안전 래퍼.
- **[Fixed] (MEDIUM) pab_merge 비문자열 크래시.** scope/statement 가 list/int 면 `.lower()` AttributeError →
  `_norm_tokens` 가 str 강제.
- **[Fixed] (MEDIUM) mini-YAML 무한재귀.** 닫히지 않은 `[`/`{` 가 `_parse_scalar↔_parse_inline` 무한재귀
  (RecursionError) → 깔끔한 MiniYAMLError.
- **[Fixed] (LOW) bool edit_fraction=True 가 1.0 으로 셈** (위 비유한값 수정에 포함).
- 7개 회귀 테스트 추가(110→117). 예제·잠금값 전부 불변.

### 다중 에이전트 적대적 검증 스윕 — it.12 (수렴 확정 검사 — 실 코드버그 1 + stale 1)
> 게이밍5·코드로직·중심명제·과대주장 최고가치 4렌즈 엄격 재실행으로 2 확인 / 1 기각. **게이밍5 0 발견**
> (게이밍 완전 방어), **중심명제 0**(L2 주장은 공개된 노트라 기각). 코드로직 렌즈가 11회 못 잡던 *실 버그* 포착.
- **[Fixed] context_select NaN 비결정 정렬 (MEDIUM, 실 코드버그).** NaN confidence → `salience()`=NaN →
  NaN 비교가 전부 False라 정렬이 *입력 순서에 의존*(비결정) → "동일 입력 → 동일 슬라이스" 보장 위반.
  `_num` 이 비유한값(NaN/inf)을 default(0.0)로 거부하게 수정(validate_packs 가 NaN confidence 를 이미
  거부하는 것과 동일 방어). 회귀 테스트로 순서-독립 슬라이스 잠금.
- **[Fixed] test_tools 독스트링 stale.** 모듈 헤더가 예제를 "L2; coverage 0.714"로 적었으나 잠금 테스트·
  도구는 L0 Seed·0.0714(게이트) → L0 으로 정정(tests/README 와 일치).
- **1 기각**: 예제 README "L2 Working" 현재형 → 상단 ⚙️ 노트가 명시 공개한 사항이라 적대적 검증이 기각.

### 다중 에이전트 적대적 검증 스윕 — it.11 (프라이버시 E2E 무결 + 스키마-도구 잔여 정합)
> 회귀·프라이버시E2E·심층스키마·EN/KR 4렌즈로 3 확인 / 0 기각. **프라이버시 E2E 렌즈 0 발견**(민감/제한
> →런타임 경로 무결). 코드/설계 0 — 스키마-설명·중첩별칭·EN초록뿐.
- **[Fixed] 스키마 설명의 유령 'edited' 상태.** record.base·candidate 가 "confirmed/narrowed/edited 가
  런타임 활성"이라 적었으나 enum·도구엔 'edited' 없음(편집은 review_audit.decision=edit 로 기록, 상태는
  confirmed/narrowed 유지) → 설명을 enum·도구와 일치시킴.
- **[Fixed] result 중첩 별칭 스키마 무효.** convergence_report 가 result.correction_cost/correction_fraction
  을 읽었으나 eval 스키마 result 는 additionalProperties:false → 그 두 중첩 읽기 제거(result.edit_fraction 만),
  스키마 별칭 설명도 "top-level 에서만 유효"로 정정. 예제 0.0833 불변.
- **[Fixed] EN 초록 T0/T2 혼선.** 라이브 도구 배치(L0)를 폭 미달(6<7)로 귀속했으나 라이브 T2 는 10팩(폭 통과)·
  깊이만 미달 → 한글 ⚙️ 노트·라이브 도구와 일치(폭 통과, 깊이 vertical 0; 본문은 T0 베이스라인).
- **0 기각. 프라이버시 경로 무결 확인.**

### 다중 에이전트 적대적 검증 스윕 — it.10 (최종 수렴 검사 — 잔여 false-green + stale 숫자)
> 회귀·전수숫자감사·잔여-false-green·완결성 4렌즈로 5 확인 / 0 기각. 코드/설계 0 — 검증기 강건성·숫자뿐.
- **[Fixed] compile_adapter false-green (MEDIUM).** 입력 경로가 없어도(혹은 0팩 로드) exit 0 →
  check_commands 의 exit-0 판정이 "예제가 실제 해석됨"을 증명 못 함. 경로 부재→exit 2, 0레코드 로드→exit 1
  로 강건화(예제·revolution 픽스처는 그대로 0). 회귀 테스트 추가.
- **[Fixed] check_commands 독스트링 과대주장.** "every figure is reproduced" 라 했으나 실제론 exit-0 만
  검사 → *runnability* 만 보증하고 *숫자*는 test_tools 가 잠근다고 정직하게 한정.
- **[Fixed] check_anchors 제목 링크 누락.** `[text](path "title")` 형식을 존재·앵커 검사 양쪽에서 건너뜀 →
  정규식에 선택적 title 허용(현재 미사용이나 표준 형식 대비).
- **[Fixed] stale 숫자 2건.** tests/README 98→108(현 109), CHANGELOG 앵커 "167개"는 문서 증가로 변하므로
  고정 해제. README·tests/README 테스트 수 109 로 동기화.
- **0 기각.**

### 다중 에이전트 적대적 검증 스윕 — it.9 (메타-체커 false-green + 신규자-문서 과대주장)
> dedup_check·CI·체커도구·초기스킬·미공개과대주장 5렌즈로 7 확인 / 0 기각. 발견이 *체커 자신*(모든
> "0 broken" 주장을 떠받치는 도구)과 신규자 문서로 이동 — 진짜 새 영역.
- **[Fixed] check_anchors false-green.** 확장자 화이트리스트(.md/.json/.yaml/.yml/.py/.txt)만 존재검사해
  `.codex/config.toml`·`.sh`·디렉터리 링크는 검증 안 됐음 → *모든* 상대 링크(파일+디렉터리) 존재검사로 강화.
  독스트링도 "inline-style 링크만 스캔"으로 정직하게 한정(reference-style·autolink·HTML href 미스캔 명시).
- **[Fixed] check_commands 가 pab_merge 미실행.** RUNNABLE_TOOLS 에서 pab_merge.py 누락 → 추가(드리프트
  방지). /tmp 입력(이전 --apply 산출물) 명령은 skip:transient-path 로 분리. ~~~ 펜스도 인식(``` 만 인식하던 비대칭 수정).
  독스트링의 runnable 목록도 실제(6→7 도구)와 일치시킴.
- **[Fixed] 신규자 문서 과대주장 (MEDIUM).** docs/build-your-personal-agent §단계1 이 앰비언트 포착을
  "설치 후 할 일 없음/자동"으로 제시하나 STUB 공개 0 → README·hooks-setup 와 동일한 정직한-한계 주석 추가.
- **[Fixed] llm_judge 결정성 강제 강화.** spec/05 ④는 "model·temperature·prompt 고정"이라는데 validate 는
  model+temperature 만 확인 → prompt_id 까지 요구하도록 강화(스키마 prompt_id 필드와 일치). 테스트 갱신.
- **0 기각.**

### 다중 에이전트 적대적 검증 스윕 — it.8 (미탐색 영역 심층 — 문서-정확성 4건)
> 트리거스키마·context_select·후보라우팅·어댑터·전체스펙재독 5렌즈로 4 확인 / 2 기각. *새 영역*에서
> 진짜 새 발견(전부 LOW 문서-정확성, 코드 버그 아님) — 도구는 정확, 문서가 약간 어긋났던 것.
- **[Fixed] salience 곱→가중합 오기.** 5개 문서가 salience 를 `confidence×recency×repetition`(곱)로 적었으나
  구현은 *가중합* `0.5·conf+0.3·rec+0.2·rep(정규화)` — 다른 랭킹 함수. 5곳(context_select 독스트링·CLI·
  tools/README·skills/10·CHANGELOG)을 실제 식으로 정정(코드·테스트 불변).
- **[Fixed] context_select 데모 off-by-one.** 주석은 budget=27 이 "두 레코드"를 담는다 했으나 a+b=28>27 라
  하나만 선택 → budget=28 로 올려 데모가 실제로 둘을 담게(주석과 일치).
- **[Fixed] gap-table 섹션 표기.** runtime-adapter gap 표가 boundary_authority→"섹션 7·8" 인데 도구
  feeds_sections=[7](§8 은 SECTION8_INPUT_PACKS 파생 경로) → "섹션 7 (+8 파생)"으로 정정(타 행은 전부 일치).
- **[Fixed] spec/05 §2 result 필드 누락.** `unacceptable_fired`(하드페일·무결성 게이트 ③)·`edit_fraction`
  (correction_cost 출처)이 result 하위필드 열거에서 빠져 있어 추가(스키마·게이트와 일치).
- **2 기각**: pab_merge 라우팅·Tier A "동치" 주장 — 둘 다 적대적 검증이 기각.

### 다중 에이전트 적대적 검증 스윕 — it.7 (L1→L0 연쇄 꼬리 정리 — 코드 수렴)
> 회귀·전체정합·신규사용자 온보딩·결정론·정직한-한계 5렌즈로 5 확인 / 2 기각. **5개 전부 문서-정합
> 꼬리**(L1→L0 잔여 + stale 숫자 2건), **새 코드/설계 결함 0** — 코드 수준 수렴 확인.
- **[Fixed] convergence-report 헤더 자기모순.** 같은 헤더가 라이브 티어를 L0(10-14행)와 L0→L1/L1 유지
  (15-17행)로 동시 주장 → L0 으로 통일(형제 revolution 문서·도구와 일치).
- **[Fixed] §4 L1-row 판정 + breadth-only 프레이밍.** T0 는 폭(6<7) *그리고* 콘텐츠 깊이 0 *둘 다* 미달인데
  "팩 1개 미달"로만 표기 → 둘 다 명시. §5 "다음 한 수"(1 레코드로 L1)도 정정: L1 은 콘텐츠 ≥3 깊이를 요구
  (7번째 팩 시드만으론 부족); climb-plan item 1 의 시드폭 산식(2팩→0.57)을 엄격-깊이로 교정.
- **[Fixed] QUICKSTART 온보딩.** 인트로(20행)·섹션헤더(147)·다회전 마일스톤(235)이 첫 세션 L1 도달이라 주장 →
  L0 시드 도착, L1 은 콘텐츠 깊이 필요로 정정. step-6 표의 `coverage ~0.14` 를 엄격(게이트)=0.00 / 시드폭 0.14 로 분리.
- **[Fixed] drift_stability "최근 대체" 잔여.** tools/README 표가 아직 "최근 대체수" → "전기간 대체수"(impl·spec 일치).
- **2 기각**: confirmation_ratio~0.75 예측, README L2-Working 잔존 주장 — 둘 다 적대적 검증이 기각(후자는 정직성 노트).

### 다중 에이전트 적대적 검증 스윕 — it.6 (it.5 회귀 정리 + 분모 한계 명시)
> 회귀·게이밍·예제재현·스킬일관성·수렴비평 5렌즈로 5 확인 / 1 기각. 대부분 *내 it.5 변경*의 마무리.
- **[Fixed] it.5 L1→L0 누락 정정.** L1→L0 연쇄가 세 파일을 놓침: `tools/README.md`(라이브 출력 블록·
  산문), `tests/README.md`(잠금 티어 서술), `spec/06 §8`(구체 예시 문장). 모두 L0 Seed·콘텐츠 깊이 0 으로 정정.
- **[Fixed] T0/T2 혼선(내가 it.5 에서 유발).** convergence-report.md 는 *T0 베이스라인* 문서인데 §4 를
  라이브 T2 수치로 덮어써 §1(6팩)·§1.3(대체 0)·§5 와 모순됐다 → §4 를 T0 으로 되돌리고(L1 정의는 콘텐츠-
  vertical 로 갱신 유지) 라이브 T2=L0(다른 빗장) 포인터를 명시.
- **[명시] confirmation_ratio 분모 한계.** 비율 분모는 `confirmed+pending+rejected` — 거부/보류를 한 번도
  기록 안 하면 1.0 으로 공짜 통과. 이 지표는 *워크플로가 잡음을 솔직히 남길 때만* 의미가 있음을 spec/06 §1 에
  명시(단, L2 는 coverage≥0.5 콘텐츠 깊이도 요구하므로 이 비율만으로 티어가 열리진 않음).
- **1 기각**: "hcr 이 L3/L4 의 숨은 전제" 주장은 적대적 검증이 기각.

### 다중 에이전트 적대적 검증 스윕 — it.5 (L1 깊이 게이트 공허성 + 예제 정직 재분류)
> 게이밍 3라운드·README 주장·스키마↔도구상수·성숙도 수학·회귀 5렌즈로 4 확인 / 0 기각.
- **[Fixed] L1 깊이-vertical 공허성 (중심 명제 결함).** L1 의 깊이 요구('≥1 팩 ≥3 확인')가 *메타* 팩
  `user.evaluation_cases` 로 자동 충족됐다 — L1 이 이미 'n_eval≥3' 을 요구하므로 vertical 이 0 제약.
  결과: 7개 얕은 팩 + 평가 3개로 L1 도달(흩뿌리기 게이밍을 막겠다던 §8 약속이 거짓). vertical 을
  *콘텐츠* 팩(메타 제외)으로 한정 → 같은 프로파일이 L0. spec/06 §3·§8 명문화, 회귀 테스트.
- **[Fixed] 워크된 예제 정직 재분류 L1 → L0 Seed.** 위 수정으로 logotekton 의 유일한 ≥3 팩이 메타 eval
  이라 **콘텐츠 깊이 0** → 정직한 티어는 **L0 Seed**(폭 10팩 ≥7 이나 콘텐츠 깊이 없음). 이는 de-averaging
  명제의 산 예시 — *폭은 넓되 깊이 없으면 Seed*. 예제 convergence-report §4 를 라이브 T2 수치로 갱신
  (stale 0.43/0.75/NA → 0.07/1.00/0.08), revolution-01/02·runtime-adapter·README·QUICKSTART 의 L1 표기
  정정. 2회전 뒤에도 L0 인 것이 "여러 지표가 올라도 콘텐츠 깊이 없이는 Seed"를 보여줌.
- **[Fixed] 공허 루브릭 스키마 드리프트(R1).** it.4 의 validate_packs 강화(빈 criteria·임계0 거부)와
  eval 스키마가 어긋남 → 스키마에 `criteria.minItems:1`·`pass_threshold.exclusiveMinimum:0` 추가로 정합.
- **[Fixed] README 테스트 수 98 → 108.**
- **[명시] 깊이 카운터는 내용 중복 비검사.** ≥3 깊이 칸은 동일 진술 사본 3개로도 채워짐 — 근접중복 탐지는
  별도 `dedup_check.py`(redundancy_ratio) 책임임을 spec/06 §8 에 명시(깊이 게이트 ≠ 중복 게이트).

### 다중 에이전트 적대적 검증 스윕 — it.4 (게이밍 2라운드 + 정직한 한계 명시)
> 게이밍 저항 2라운드·미구현 주장·OpenCrab 크로스워크·G6·회귀 5렌즈로 6 확인 / 1 기각. it.3 가 닫은
> 게이밍 홀 *다음 층*을 채굴.
- **[Fixed] 공허한 루브릭 (decision_fidelity 게이밍).** `criteria:[]` + `pass_threshold:0` + `status:pass`
  가 검증 통과 후 decision_fidelity 를 1.0 으로 부풀림 — _eval_integrity 가 빈 criteria·임계0 을 막게 함.
- **[Fixed] correction_cost 시딩 게이밍.** 임의 레코드에 `edit_fraction:0` 무더기로 평균을 0 으로 끌어내림 —
  출처를 *평가 케이스*로 한정(임의 레코드 폴백 제거). 예제 0.0833 불변, 50× 시딩이 더는 안 통함.
- **[Fixed] OpenCrab 9-space 크로스워크 완성.** "모든 노드 사상" 주장과 달리 4개 팩(ArtifactPolicy·
  TacitHeuristic·ProjectMemory·DriftRecord) 누락 → 각각 policy·concept·resource·outcome 에 추가.
  DriftRecord→outcome 은 skills/11 의 drift_history→outcome 인용도 참으로 만듦.
- **[정직한 한계 명시] 섀도 캘리브레이션 (spec/12 §4.3).** 불일치율 측정→임계 보정 루프가 현재형으로
  기술됐으나 미구현 → "설계 단계" 주석(spec/02 S10½ 와 동일 상태): 목표 행동의 명세이지 구현 아님.
- **[정직한 한계 명시] 증거 해석 vs 존재.** G1·traceability 는 `evidence_refs` *존재*만 막고 실재
  EvidenceItem 으로 *해석*하진 않음(레지스트리 미존재) → 날조 ref 가 traceability=1.0 을 통과. 스키마·spec/06
  에 기계검사 범위 명시(해석은 향후/거버넌스 과제). 코드 미변경 — 잠금 숫자 불변.
- **1 기각**: "drift 레코드 0개로 drift_stability 게이밍" 은 적대적 검증이 기각(0=정직한 무churn 상태).

### 다중 에이전트 적대적 검증 스윕 — it.3 (수렴 게이밍 홀 + 라이프사이클 정합)
> 더 깊은 5렌즈(라이프사이클 상태기계·의미적 교차참조·예제 E2E·프라이버시 완전성·수렴 게이밍 저항)로
> 7 확인 / 5 기각. **헤드라인은 실증된 게이밍 홀**: auto-confirm 무더기 + 사람 3건으로 L4 도달 가능했음.
- **[Fixed] auto-confirm 게이밍 홀 (HIGH).** auto_confirmed 를 `human_confirmation_ratio` 에서만 제외하고
  coverage 깊이·`decision_fidelity`·`correction_cost` 에선 안 했음 → 14팩×3 auto + 5 auto 평가 + 사람 3건이
  **L4 Convergent** 산출(검증자 실증). spec/12 §4.4 의 "게이트는 auto-confirm 이 건드릴 수 없다" 약속 위반.
  coverage 깊이·평가셋에서 auto_confirmed 제외 → 같은 공격이 이제 L0. 예제는 auto_confirmed 0건이라 잠금
  숫자 불변. 회귀 테스트 3개.
- **[Fixed] 폐기 레코드 활성 불일치 (convergence↔compiler).** compile_adapter 는 superseded 레코드를 활성에서
  빼는데 convergence 는 confirmed/active 로 세어 coverage·confirmation_ratio·traceability·drift 가 어긋남.
  `_collect_superseded`(동일 규칙) 추가로 두 도구가 '런타임 활성'을 동일 정의. 예제 supersession 0건 → 숫자 불변.
- **[Fixed] 예제 팩 수.** README "9개 팩" → instance-records.yaml 은 8팩, 수렴 기준 10팩(+eval·drift). 3곳 정정.
- **[Fixed] 깨진 교차참조.** spec/05·eval 스키마가 "01 커널 스키마 §10" 인용(스펙01 은 §9 까지) → 실제 계약 위치
  (spec/05 §1–2·spec/02 S11·커널 §3)로 재지정. "계약 §10" 라벨 자체는 프로젝트 전역 안정 명칭이라 유지.
- **[Fixed] G5 기계검사 범위.** 검증기는 레코드 적재 `exception_rules`(≥1)만 막음 — "BoundaryRule 존재"는
  거버넌스 단계임을 스키마 필드·spec/01 §2 에 명시(과대주장 제거).
- **[보고만/설계판단] `narrowed` 상태 과부하.** `narrowed` 가 *활성 좁힘 규칙* 과 *대체되어 은퇴한 레코드* 둘 다를
  의미(pab_merge 가 구 레코드를 `narrowed`로 은퇴시킴). 현재는 supersedes-엣지 제외로 동작하나 취약 — 별도
  `superseded` 상태 신설은 스키마+전 도구+스펙 변경이라 사용자 판단 대기.

### 다중 에이전트 적대적 검증 스윕 — it.1 (13 확인 발견 → 도구 정합)
> 사용자 요청으로 *오케스트레이터+다수 서브에이전트* 검증 루프를 돌려, 결정론적 도구와 스펙/스키마/문서
> 사이의 모순을 채굴·적대적 확인했다. 확인된 발견은 작고 명백히 안전한 것만 수정(나머지는 보고). 잠금 숫자는
> 불변, 테스트만 추가(88 → 98).
- **[Fixed] G5 강제 구멍 (validate_packs).** `sensitivity ∈ {sensitive, restricted}` 면 `exception_rules`
  필수(record.base allOf)인데 validate_packs 가 다른 allOf 규칙은 다 강제하면서 이것만 누락 — 스키마 검증기
  없이 단독 실행 시 G5 구멍. 검사 추가 + 테스트 2개.
- **[Fixed] 미니 YAML 의 NaN/inf 주입 (convergence_report).** 폴백 파서가 bare `nan`/`inf` 를 float 로
  강제(PyYAML 은 문자열)해 평균·비율에 조용히 NaN 이 스밀 수 있었음 — PyYAML 1.1 규칙에 맞춰 문자열로.
- **[Fixed] 배치 내부 중복 미제거 (pab_merge).** `classify` 를 정적 스냅샷에 매핑해 *같은 배치의* 동일 후보
  둘이 모두 novel→insert(쌍둥이). `plan_batch` 로 배치-내부 인지 추가 — 둘째가 첫째로 merge(멱등성 회복).
- **[Fixed] persona ↔ project_context 혼입 (compile_adapter).** `memory_project_graph` 가 섹션 1 의
  persona list 에 평면 병합되어 전이성 경계(skills/10 §4) 위반 — 별도 `project_context` 하위블록으로 분리.
- **[Fixed] eval 스키마 거짓 주장 (judge=mixed 경고).** 스키마가 "validate_packs warns when judge=mixed"
  라 적었으나 그런 경고가 없었음 — 경고를 실제 구현해 주장과 일치.
- **[Fixed] drift_stability '최근 기간' 과대주장.** 정의·주석·예제가 *최근 기간* 윈도우를 적었으나 구현은
  전 기간 누적 — 정의를 구현(전 기간)에 맞추고 윈도우는 *계획된 정련*으로 명시.
- **[Fixed] 표시 버그 (pab_merge "(none)").** 연산자 우선순위로 빈 배치의 `verdicts: (none)` 폴백이 사문화 —
  그룹화 수정.
- **[Fixed] 문서 드리프트.** L2 게이트 지표명 `confirmation_ratio`→`human_confirmation_ratio`(spec/06 §3
  정합) — skills/11·QUICKSTART·예제. README 테스트 수 88→98.

### 텔로스 정렬 후 논리-빈틈 봉합 (수렴 = 거울 층 + 대리인 층)
> 텔로스 재구성을 *프로세스 전수 논리 검토*한 결과, 진짜 구멍 하나가 드러남: 수렴을 "자기지도 충실도"로
> 재서술했는데 `decision_fidelity`·`correction_cost`(L2+ 게이트)는 *컴파일된 에이전트 행동*을 재므로,
> **거울만 원하는 사용자는 L1에 갇히고** "거울 먼저, 대리인 선택"과 모순. (기계장치는 불변이라 프로세스
> 서술이 새 텔로스를 못 따라간 것.)
- **수렴을 *두 층*으로 명문화(C1).** spec/06 §1: **지도 수렴(거울, 일차)** = 확인 레코드 누적 + off-frontier
  축소 + traceability — *에이전트 없이* 측정(coverage·confirmation·traceability). **대리인 수렴(선택, 컴파일 후)**
  = `decision_fidelity`↑·`correction_cost`↓ — *컴파일된 프로필 실행 필요*. §3에 **거울 티어(L0–L1) vs 대리인
  티어(L2+)** 명시: `L1→L2` 전이 = README 의 *거울→대리인 교차점*. 거울만 원하면 L0–L1 에서 지도를 무한히
  깊게 채우면 됨. 또 그 전이를 막는 게이트는 *기술적*(shadow=무회귀)일 뿐, "내 이름으로 행동해도 되는가"의
  *결과적* 판단은 게이트가 대신 안 함을 명시(m1).
- **정의 불일치·잔여 영문 봉합(M1·M2·m2).** §1/§6의 두 수렴 정의를 두-층으로 화해. spec/06 EN 상단·§8,
  spec/05 EN 의 "becoming me" 표현을 거울-우선/대리인-층으로 정정. README 6단계를 "(선택) 대리인 층"으로,
  1–4단계(거울)에서 멈춰도 됨을 명시. 기계장치·게이트·숫자 불변(88 tests·42 PASS).

### 텔로스 정렬 — 자기명시화가 먼저, 대리인은 별개 단계 (거울 vs 대리인)
> 교차모델 검증(Opus+Sonnet)이 짚은 가장 깊은 구멍: 시스템은 *당신이 하는 것*에의 충실도만 재고
> *그게 좋은가*(규범 축)는 안 잰다 → 배포된 에이전트는 편향을 자신감 있게 증폭. 설계자 확인 결과,
> 이 프로젝트의 *진짜 배경*은 판매·배포가 아니라 **"나도 모르는 나"의 자기명시화**다. 그 프레이밍에선
> "충실도만 잰다"가 결함이 아니라 설계(거울은 있는 그대로 비추고 규범 판단은 사람 몫)다.
- **프레이밍을 "행동하는 대리인" → "증거 기반 자기지도(거울)"로 정렬.** 일차 산출물은 *행동하는
  에이전트*가 아니라 *읽을 수 있는 명시적 자기지도*이며, 그 지도를 대리인으로 *배포*하는 것은 사람
  검토를 요하는 **별개의 더 무거운 단계**임을 명시. README에 "거울이냐 대리인이냐" 절(거울/대리인 대비
  표 + 정직한 경계: 배포 시 편향 증폭·의존·책임 같은 *인간적 결과*가 들어옴), spec/00 핵심 명제·
  spec/06 자기-정량화 텔로스를 자기명시화 중심으로 재서술. 기계장치(14팩·수렴·전이성·게이트)는 불변 —
  *목적(텔로스)*만 정렬. 이로써 dimension-5(파생 결과) 비판을 *배포 경계*로 정직하게 흡수.

### 전이성 테스트 — 주체를 캐고 주제를 캐지 마라 (실데이터 피드백)
> 첫 실세션 추출에서 드러난 갭: 세션이 *프로젝트*에 관한 것일 때, 추출이 프로젝트 사실("X는 ~한
> 아키텍처다")과 암묵지(당신이 *어떻게* 결정·판단하는가)를 섞었다. 개인 에이전트는 *당신이 무엇을
> 만드는가*가 아니라 *당신이 어떻게 생각하는가*여야 한다.
- **전이성 테스트를 제1 추출 필터로 정식화.** 한 신호가 암묵지 팩(페르소나·결정·암묵·스타일·산출물·
  위험·워크플로 + 역할 페르소나)으로 가려면 *"프로젝트를 바꿔도 참인가"*를 통과해야 한다. 프로젝트
  사실은 `memory_project_graph`(단일 프로젝트)나 `domain_overlays`(지속 도메인 지식)로만. 가장 날카로운
  리트머스: "같은 프로젝트를 *다른 사람*이 해도 똑같이 말할 내용이면 → 프로젝트 사실". 박은 곳:
  [S02 §1.1](./skills/02-session-mining.md)(원칙)·[S04](./skills/04-diff-mining.md)·[S05](./skills/05-candidate-extraction.md)
  체크리스트·[S07 확인 게이트](./skills/07-confirmation-gate.md)(사람 최종 방어선)·[03 카탈로그](./spec/03-pack-catalog.md)·
  [00 de-averaging 입구](./spec/00-overview.md). 사람 판단 필터(G4 처럼 코드가 아닌)임을 명시.
- **적대적 평가 후속 — 갭 봉합.** 평가가 잡은: 확인 게이트(S07)·diff마이닝(S04)·7개 암묵지 팩 항목에
  규칙 부재, domain_overlays↔memory_project_graph 회색지대, 그리고 *프로젝트 사실이 어댑터 섹션1
  (정체성)에 재주입되는 모순*(skills/10) — 전부 봉합. memory_project_graph 는 섹션1·6에 *맥락 피연산자*로
  (persona 와 섞이지 않는 별도 하위블록) 합류하도록 reconcile.
- **worked example** [`examples/logotekton/ecwm-session/`](./examples/logotekton/ecwm-session/) — 실제 ECWM
  세션 추출을 이 테스트로 정규화(프로젝트 사실 2개 강등·패턴 2개 재스코프·6개 유지). 후보 8개가
  candidate.schema.json 정합. **validate_packs 가 후보 파일을 SKIP**(베이스 아님)하도록 수정 — 예제는
  42 PASS 불변. 테스트 88(84→88).

### 참조 컴파일러 — 8섹션 런타임 어댑터 조립을 코드로 (compile 단계 실재화)
- **[`tools/compile_adapter.py`](./tools/compile_adapter.py) 추가.** skill 10의 "읽기 전용 8섹션 조립"을
  *산문*에서 **결정론적·테스트된 참조 컴파일러**로 옮겼습니다 — `pab_merge`(병합)·`context_select`(선택)에
  이은 세 번째 참조 술어. G3 활성 필터(`confirmed`/`narrowed`) + `reliability` draft-only 제외(C) +
  supersession(drift_history) 제외 + 팩→8섹션 라우팅(§4) + 경계 레이어(인스턴스/기본정책) + 갭 로깅(G1).
  손-작성 [`runtime-adapter.md`](./examples/logotekton/runtime-adapter.md)의 **T0(5팩·기본정책)→T1(6팩·
  인스턴스)→T2(8팩)** 섹션 멤버십을 *그대로 재현* — 어댑터가 이제 기계 재현 가능(단언이 아님). 테스트
  +8(73→81), skill 10·tools/README·runtime-adapter 에 배선. *정직한 한계:* 라이브 호스트 런타임
  (`pab.py`)은 STUB이며 검증된 것은 섹션 멤버십·갭·경계 수학(섹션 8·응답 정책은 파생 뷰).

### 설계자 결정 반영 — claim-layer 분리 + '일하는 자아' 스코프 (philosophy 팩 대조 후속)
> philosophy_for_ai_ontology 팩(OpenCrab)과의 정밀대조에서 드러난 간극 — PAB가 *증거 계층*(G4)은
> 지키지만 *적용/해석 계층*('이 에이전트가 당신이다')을 표시·검토하는 장치가 없다는 점 — 을 설계자
> 결정 4개(A/B/C/D)로 보완. 모든 변경은 무가공·증거결속이며 기존 예제 숫자는 전부 보존(logotekton
> 여전히 L1, 엄격 0.07, confirmed 19, validate 42 PASS).
- **C · `reliability` 채널 티어 추가 (claim-layer 분리, #1).** 베이스/후보 스키마에 `reliability`
  ∈ {`behavioral`(기본), `self_reported`}. self_reported(자기서술 = InterpretationClaim)는 ① auto-confirm
  **금지**(allOf 규칙 + [`validate_packs.py`](./tools/validate_packs.py) 에러, auto_confirmed 는 boolean
  강제), ② draft-only — [`context_select.py`](./tools/context_select.py)가 권위 컨텍스트에서 제외하고
  draft 로만 노출, ③ **모든 성숙도 지표에서 제외**([`convergence_report.py`](./tools/convergence_report.py):
  여섯 지표(coverage·confirmation_ratio·decision_fidelity·correction_cost·drift_stability·traceability)+게이트
  변형 human_confirmation_ratio+폭(seeded) 전부 *behavioral* 만 집계).
  자기서술이 행동 증거로 둔갑하는 것을 구조로 차단. 스펙: [01 §7.1](./spec/01-kernel-schema.md).
  예제 숫자 불변(예제는 전부 behavioral).
  - *적대적 검증(Opus) 2라운드 후 경화:* 최초 구현은 깊이축에서만 제외해, self_reported 를 무더기
    confirmed 시키면 hcr/drift 로 L1→L2 를 딸 수 있는 백도어(C1)가 있었다 — 6개 지표 *전부* 제외로 차단.
    문자열 `auto_confirmed:"true"` 로 금지 규칙을 우회하던 검증기/수렴기 드리프트(M2), draft-only 런타임
    권위 차단이 미강제이던 점(M1), 재검증이 잡은 *self_reported 평가 케이스가 `decision_fidelity`
    (하드 게이트)를 부풀리는 잔여 경로*(N1), 그리고 3라운드가 잡은 *self_reported-only 팩이 L1 폭
    게이트(seeded≥7)를 따는 경로*(N2)까지 닫음 — 이제 self_reported 는 여섯 지표 전부·드리프트·폭(seeded)
    에서 빠져 "성숙도는 관찰된 행동 위에서만 측정"이 글자 그대로 참이다. 테스트 +15(58→73).
- **A · '위임가능한 일하는 자아' 스코프 명시 + #4 행동주의 입장 선언.** [spec/00](./spec/00-overview.md)에
  "무엇이 *아닌가*" 절 추가: PAB는 **전인격 트윈이 아니라** 행동 증거가 있는 일·판단 영역의 위임가능한
  자아다. 내면 배제는 *암묵 기본값*이 아니라 **선언된 방법론적 입장**(G4)임을 명문화.
- **D · 채널 한계 + off-ontology 기권 선언.** 증거가 주로 AI 작업 세션에서 오므로 관계·정서·미적·서사적
  자아는 *채널의 구조적 한계*로 off-ontology — 에이전트는 그곳에서 평균값으로 흉내내지 않고 기권한다
  (de-averaging 의 채널 차원 확장). 채널 확대는 별도 로드맵.
- **B · 'persona' = 행동 페르소나(mask) 고정.** persona_core 의 'persona'는 *연기된 관찰 패턴*이지 내면
  자아가 아님 — value/priority 조차 행동으로 드러난 안정 패턴만 적재. 카탈로그·스키마·템플릿(×2)에 명시.
- **#2 · "becoming you" = 적용주장(AIApplicationClaim) 명시.** 프로젝트 표어는 증거가 아니라 *증거를
  에이전트에 적용한, 사람 검토를 요하는* 주장으로 읽혀야 하며 행동 레코드의 신뢰도를 자동 상속하지
  않음을 [01 §7.1](./spec/01-kernel-schema.md)에 명문화. de-averaging·off-frontier·reliability 가 그 검토를
  기계적으로 떠받친다.

### Karpathy review 후속 — 자기기만 방지 (실행 게이트 강화)
- **L2 게이트 결함 수정 — 성숙도를 폭이 아니라 깊이로 게이팅.** 적대적 검토에서 드러난 내부 모순:
  spec/06 §2가 `coverage`를 *엄격(≥3 확인 = 깊이)*으로 **정의**하는데, [`convergence_report.py`](./tools/convergence_report.py)의
  성숙도 게이트는 *시드폭*(0.71)으로 판정해 logotekton을 **L2 Working**으로 인증했습니다 — 정작
  de-averaging 명제가 사는 깊이값은 0.07인데. 즉 "Working"을 *폭으로* 따는, 이 프로젝트가 막으려는
  바로 그 자기기만. 게이트가 spec §2 정의(엄격 깊이)를 쓰도록 수정하고 `--strict` 토글을 제거(이제
  항상 엄격). **logotekton은 정직하게 `L1 Sketch`로 내려갑니다**(깊은 팩 1개뿐 — 남은 L2 빗장은
  coverage 0.07→0.5). df·merge_rate·시드폭 등 다른 숫자는 불변. spec/06 §3에 "폭=Sketch vs 깊이=Working+"
  명문화, 회귀 테스트·tools/README·tests/README·예제/revolution 문서의 라이브 티어 표기를 L1로 정정
  (revolution 문서는 시드폭 게이트 당시 측정이라 상단 노트로 보존+정정). 테스트 58개 그대로 그린.
- **#9 결정론적 컨텍스트 조립(참조 술어).** 컴파일러 계약이 "메모리 덤프 아닌 작업별 활성화"라면서도
  토큰 예산·overlap 알고리즘·task_type 분류가 없어 *산문으로만* 시연되던 문제에, **실행 가능한 참조
  술어** [`tools/context_select.py`](./tools/context_select.py)를 추가했습니다: 통제 `task_type` 어휘 +
  결정론적 scope-overlap 술어 + `salience`(0.5·confidence + 0.3·recency + 0.2·repetition, 가중합) 내림차순 + **토큰 예산**
  채움 + *탈락분을 갭으로 반환*(조용한 절단 금지). skills/10 §3 [2]가 이 술어를 가리킵니다. 테스트
  +5(58개). *정직한 한계: 라이브 컴파일러(`pab.py` compile 분기)는 스텁이라 아직 아무도 이 술어를 호출
  하지 않습니다 — 실런타임 배선이 남은 몸-작업. 여기 있는 건 검증된 **선택 수학**입니다.*
- **#8 검토 감사 흔적 — 고무도장 vs 실제 검토 구별.** reviewer·결정·diff 가 스키마에 없어 *편집된
  레코드*가 *고무도장 confirmed*와 기계적으로 구별 불능(→`edit_rate` 계산 불가)이던 문제에,
  베이스 레코드에 **`review_audit`**(`reviewer_id`·`decided_at`·`decision`(enum, `edit` 포함)·
  `decision_reason`·`diff`·`board_id`)을 추가했습니다([`record.base.schema.json`](./schemas/record.base.schema.json)).
  [`validate_packs.py`](./tools/validate_packs.py)는 audit 가 있으면 항상 형태를 검증하고,
  **`--require-audit`** 옵트인으로 런타임 활성 레코드에 강제합니다. *기본 비강제*는 — 19개 확정
  레코드에 *없던 검토 메타를 날조하지 않기* 위해서이며, 그래서 예제 기본 검증은 **42 PASS 불변**
  (`--require-audit`면 정직하게 42 FAIL = "감사 흔적 없음"). skills/07 [D]가 산문 대신 이 구조화
  필드를 가리킵니다. 테스트 +5(53개).
- **#5 런타임 shadow-activation 한 칸 (설계).** 평가가 *루프의 끝*이라 컴파일된 어댑터가 이미 라이브가
  된 *뒤*에 검증되던 문제에 대해, 라이프사이클에 `shadow_validated` 상태를 추가했습니다
  ([`spec/01 §1`](./spec/01-kernel-schema.md)·[`spec/02 S10½`](./spec/02-builder-pipeline.md)·
  [`skills/10`](./skills/10-agent-compiler.md)): 새 프로필을 활성 *전* `regression_for` 케이스·과거
  세션에 **NO-ACT(예측만)** 로 재생해 회귀가 없을 때만 `runtime_activated`로 승격. Tesla shadow mode
  차용([spec/12 §4.3]). *정직한 한계: 라이브 런타임/컴파일러가 스텁이라 **설계 전용** — 실행되는 건
  없습니다.*
- **#7 + #6 깊이·de-averaging — "모르는 곳을 아는 것이 수렴" (off-frontier 정직성).** 리뷰가 *프로젝트의
  진짜 핵심 명제*라 한 de-averaging을 명문화·게이트화했습니다. (a) [`spec/00`](./spec/00-overview.md)에
  **핵심 명제**로, [`spec/06 §8`](./spec/06-convergence-model.md)에 측정 모델로 추가 — "증거 있는 곳에서만
  당신처럼, 없는 곳에선 평균으로 둘러대지 말고 기권". (b) **성숙도 L1이 폭(≥7팩)뿐 아니라 깊이 한 칸
  (≥1 팩이 ≥3 확인 = `vertical`)도 요구** → 1레코드씩 흩뿌려 성숙도를 따는 breadth-first 게이밍 차단
  (overfit-tiny-set-first). (c) [`convergence_report.py`](./tools/convergence_report.py)가 **off-frontier
  경고**(확인 0개 팩 + 폭≫깊이 간극 → draft-only)를 실데이터 위에 출력 — logotekton은 4/14 팩이 비어
  있음을 정직하게 표시(에이전트가 그 영역에서 권위 있게 행동 금지). logotekton은 깊은 팩 1개
  (evaluation_cases)가 있어 **티어 L2 불변**. 테스트 +2(48개). *데이터 시드(RedFlag/Avoidance 실레코드)는
  실데이터가 필요해 제외* — 게이트·신호·스펙만.
- **#3 채점 무결성 게이트 — "보상이 검증이 아니라 기록"의 부분 해소.** `decision_fidelity`가 읽는
  `result.status`가 *사람이 친 자유 문자열*이라 아무도 루브릭과 대조하지 않던 문제에 대해,
  [`validate_packs.py`](./tools/validate_packs.py)가 평가 케이스의 **기록 내부 정합성**을 강제하도록
  했습니다: 가중치 합=1 · `status=pass`면 `score≥pass_threshold` · `unacceptable_fired`면 status=`fail`
  (하드페일) · `judge=llm_judge`면 `judge_config`(model·temperature) 필수. 스키마에 `judge_config`·
  `result.unacceptable_fired` 추가. logotekton 예제는 모두 정합이라 **42 PASS 불변**. 테스트 +6(46개).
  *정직한 한계:* 프로필을 실제 실행해 status를 도출하는 **라이브 채점기**는 컴파일된 런타임(현 스텁)이
  필요해 별개이며, 이 게이트는 그 전제인 "기록이 자기 루브릭과 모순되지 않음"만 보장합니다.
  → [`spec/05`](./spec/05-evaluation-drift.md), [`schemas/user.evaluation_cases.schema.json`](./schemas/user.evaluation_cases.schema.json).
- **#4 자율성 자기인증 차단 — `human_confirmation_ratio`.** spec/12 §4.4가 정의만 해 둔 *사람 게이트 흐름만
  세는* 비율을 [`convergence_report.py`](./tools/convergence_report.py)에 구현하고, **성숙도 L2 게이트가
  `confirmation_ratio` 대신 이 값을 쓰도록** 바꿨습니다(베이스 레코드 `auto_confirmed` 플래그 → 자동확정
  승격은 분자·분모에서 제외). auto-confirm을 켜도 시스템이 *제 성숙도를 자기인증*(목줄이 스스로 풀림)하지
  못합니다. auto-confirm 0건인 logotekton 예제는 값·티어 불변(L2). 회귀 테스트가 "confirmation_ratio 0.75는
  통과하나 human_confirmation_ratio 0.30은 L2를 막음"을 잠금. → [`spec/06`](./spec/06-convergence-model.md)·
  [`spec/12 §4.4`](./spec/12-confirmation-policy.md), [`schemas/record.base.schema.json`](./schemas/record.base.schema.json).

### Added
- **`result.edit_fraction`(0..1) — `correction_cost` 계측.** `user.evaluation_cases`의 `result`에
  작업별 사용자 편집 비율 필드를 형식화해, `correction_cost` 지표가 NA에서 *측정값*으로 전환됩니다
  (미측정 NA는 L3/L4 게이트를 통과하지 못함). → [`spec/05-evaluation-drift.md`](./spec/05-evaluation-drift.md),
  [`schemas/user.evaluation_cases.schema.json`](./schemas/user.evaluation_cases.schema.json).
- **dedup/merge actuator + 데이터-엔진 플라이휠.** 결정론적 dedup judge + upsert/supersede/surface
  액추에이터([`tools/pab_merge.py`](./tools/pab_merge.py))와, 실제 레코드 위에서 바퀴를 두 번 돌린
  worked example([`examples/logotekton/revolution-01`](./examples/logotekton/revolution-01/) ·
  [`revolution-02`](./examples/logotekton/revolution-02/), `.pre` 재현 픽스처 포함).
- **`spec/01` §9 프라이버시·권한 모델 요약** — 다른 문서들이 가리키던 "커널 §9"에 실재하는 섹션을
  부여(정식 정의는 spec/04). §7 베이스 레코드에 병합 필드 `canonical_key`·`repetition_count`·
  `merge_history`(선택) 명시.
- **회귀 테스트 스위트** [`tests/`](./tests/README.md) — 도구가 산출하는 *모든 숫자*(canonical_key·
  네 판정·6 수렴 지표·`merge_rate`·게이트·예제 42 PASS)를 잠그는 stdlib 36 테스트. **CI**
  ([`.github/workflows/ci.yml`](./.github/workflows/ci.yml))가 push·PR마다 게이트+테스트 실행.
- **문서 링크 무결성 게이트** [`tools/check_anchors.py`](./tools/check_anchors.py) — 저장소 전체
  교차문서 Markdown 링크·`#앵커`가 실재 헤딩(GitHub 슬러그)으로 해소되는지 검사하는 stdlib 도구.
  CI 게이트로 편입(broken≠0이면 빌드 실패)되어, 헤딩 rename이 참조를 조용히 끊는 것을 막습니다.
  (이 도구가 skills/08의 깨진 자기 앵커 3건을 발견 — 아래 Fixed.)
- **문서 명령 무결성 게이트** [`tools/check_commands.py`](./tools/check_commands.py) — 문서에 적힌
  이 저장소 도구의 안전·읽기전용 명령(validate/convergence/dedup/check_anchors)을 실제로 실행해
  하나라도 실패하면 빌드를 깨는 stdlib 도구. "**모든 figure는 명령으로 재현된다**"는 명제를 *실행 가능한
  게이트*로 만들어, CLI 시그니처가 바뀌어 문서의 명령이 조용히 깨지는 것을 막습니다(아래 it.13 회귀
  클래스). 플레이스홀더·부수효과(`--apply`/`--out`)·테스트 스위트·버전 의존 `python -c` 점검(예:
  3.11+ `tomllib`)은 범위 밖으로 건너뜁니다. 테스트는 38개로 늘어 두 가드(앵커·명령)와 디렉터리-형
  CLI까지 잠급니다.

### Reconciled (정합화)
- **13개 빌더 스킬(+ 호스트 배선 어댑터 skill 14)을 병합 층(spec/10)과 정합화.** 확인 게이트의 검토 액션은 *여섯 기본 + dedup judge의
  merge/supersede*이고, `conflict`는 사람에게 노출(자동 적용 금지, G3/G5 2차 게이트)임을 skills
  `02·04·05·06·07·08·09·10·11·12·13`에 일관 반영. skill 09는 빌드타임(dedup conflict→surface)과
  런타임(더 엄격한 규칙 합성)을 분리. skill 01은 교차세션 재유도가 *중복이 아니라 병합 연료*임을 명확화.
- **빌더 파이프라인 문서(spec/02)를 병합 층과 정합화.** S07 확인 게이트 기술에 dedup judge의 추천 액션
  (`duplicate→merge`·`refinement→supersede`)과 `conflict→surface`(자동 적용 금지, 2차 관문)를 명시하고,
  다이어그램 각주·"관련 문서"에 [spec/10] 링크를 추가. `review_status` enum은 그대로 둠(merge/supersede는
  *상태*가 아니라 *게이트 액션* — 어드버서리얼 검증으로 확인). → [`spec/02-builder-pipeline.md`](./spec/02-builder-pipeline.md).

### Fixed
- **systemic "커널 §9" dangling 참조.** spec/01엔 §8까지뿐이었는데 schema·spec/03·skills가 권한
  모델을 "kernel §9"로 가리켰음 → spec/01 §9 추가로 일괄 해소.
- skills 곳곳의 잘못된 교차참조(예: 후보 필드의 "커널 §8"→`candidate.schema.json`, 컴파일러 갭
  로그의 metric `correction_cost`→`coverage`, `§3 [B]`→`§3 [3]`)와 깨진 라벨 정정.
- **깨진 자기 앵커 링크 정정(skills/08).** `§3 라우팅 표`를 가리키는 세 개의 자기 링크가
  `#3-라우팅-표-1-1-전수`로 잘못 작성되어 실제 헤딩 슬러그(`#3-라우팅-표-11-전수`, `(1:1, 전수)`의
  `1:1`이 `11`로 정규화)와 어긋났음 → 다른 모든 링크가 쓰는 `11` 규약으로 통일. 저장소 전체 앵커
  링크를 GitHub 슬러그 알고리즘으로 일괄 점검(전 저장소 broken=0; CI가 매번 재확인 — 정확한 링크 수는
  문서가 늘며 변하므로 고정하지 않음).
- **실행되지 않던 문서 명령·낡은 라이브 출력 정정("모든 figure는 명령으로 재현"의 위반).**
  `convergence_report.py`는 *디렉터리 하나*를 받는데 문서 세 곳이 깨진 형태였음 — `tools/README.md`
  §2의 두-파일 형태, `CONTRIBUTING.md`의 인자 없는 형태, `templates/QUICKSTART.md`의 존재하지 않는
  `--subject` 플래그(모두 exit 2). 디렉터리 형태로 통일. 더불어 `tools/README.md` §2의 "기대 출력"이
  플라이휠 이전(T0: L1·coverage 0.43·df 0.75·correction_cost 0.21)을 *라이브*인 양 제시 → 실제 라이브
  **T2(L2·0.71·1.00·0.08·drift 0.89)** 로 교정하고 T0 베이스라인은 `convergence-report.md`,
  델타는 revolution-01/02가 보존함을 명시. 회귀 테스트로 디렉터리-형 CLI를 잠금(36 tests).

### Added (예정)
- 더 많은 평가 케이스(EvaluationCase) 시드 및 다중 사용자 예제.
- 자동 채굴 도구(session_mining / diff_mining)의 참조 구현.
- 수렴 지표 대시보드(longitudinal convergence tracking).

> 변경 제안은 [`CONTRIBUTING.md`](./CONTRIBUTING.md) · 거버넌스는
> [`GOVERNANCE.md`](./GOVERNANCE.md)를 참고하세요.

---

## [0.3.0] — 2026-06-28

**첫 공개 릴리스.** `v0.1`/`v0.2`에서 누적된 불일치를 하나의 정식 계약(canonical contract)으로
정합화했습니다. 이번 릴리스의 핵심은 *새 기능*보다 **정합화(reconciliation)**입니다 — 흩어져
있던 어휘·필드·라우팅을 단일 기준으로 묶었습니다.

### Reconciled (정합화 — v0.1/v0.2 불일치 해소)

- **후보 타입 11 → 14, 라우팅 1:1 전수화.** `v0.1`은 후보 타입 11개 vs 라우팅 13개로
  불일치했습니다. v0.3은 **14개 후보 타입을 14개 `user.*` 팩에 1:1 전수(total) 매핑**하여
  라우터를 완전하게 만들었습니다. 신규 `IdentityRoleCandidate → user.identity_roles`(누락이었음),
  개명 `DomainSpecificCandidate → DomainOverlayCandidate`,
  `ProjectGoalCandidate → ProjectMemoryCandidate`.
  → [`spec/01-kernel-schema.md`](./spec/01-kernel-schema.md) §6.
- **통합 베이스 레코드: 필드 표류 해소.** `v0.1`은 `score`, `v0.2`는 `confidence`를 썼고,
  주장 본문은 팩마다 `claim`/`rule_statement`/`instruction`/`output_rule`로 갈렸습니다.
  v0.3은 **`score` → `confidence`(0..1)**, 그리고 위 본문 필드를 모두 **`statement`**
  하나로 통일했습니다(팩 문서는 표시용 별칭만 둘 수 있음). 모든 인스턴스 레코드는 단일
  베이스를 `allOf`로 확장합니다.
  → [`schemas/record.base.schema.json`](./schemas/record.base.schema.json),
  [`spec/01-kernel-schema.md`](./spec/01-kernel-schema.md) §7.
- **정식 팩 이름이 코드명을 대체.** 구 코드명(`pa.t03`, `t06`, `x12`, `.ba`, `pa.roles`,
  `pa.core` 등)을 **폐기**하고 14개 정식 이름(`user.identity_roles` …
  `user.drift_history`)으로 통일했습니다. 구 코드명은 추적용으로만 표에 병기됩니다.
  → [`spec/01-kernel-schema.md`](./spec/01-kernel-schema.md) §5,
  [`spec/03-pack-catalog.md`](./spec/03-pack-catalog.md).
- **컴파일러 입력에 `identity_roles` 추가.** 에이전트 컴파일러(skill 10)가 읽는 확정 슬라이스
  목록에 `user.identity_roles`를 포함시켜, 정체성·역할 맥락이 런타임 프로필 생성에 반영되도록
  했습니다(이전엔 누락).
  → [`skills/10-agent-compiler.md`](./skills/10-agent-compiler.md).
- **`review_status` / `sensitivity` enum 고정.** 검토 상태는
  `{pending, confirmed, rejected, narrowed, sensitive, deferred}`, 민감도는
  `{public, internal, sensitive, restricted}`로 고정. 게이트 G3(확정/축소/편집만 런타임
  활성)과 G5(민감 항목은 경계 규칙 선행)를 스키마로 강제합니다.

### Added (신규)

- **수렴 모델(convergence model).** "더 나아졌다"를 느낌이 아니라 6개 지표
  (coverage, confirmation_ratio, decision_fidelity, correction_cost, drift_stability,
  traceability)와 5단계 성숙도(L0 Seed → L4 Convergent)로 측정합니다. 참여 후크이자
  품질의 객관적 기준입니다.
  → [`spec/06-convergence-model.md`](./spec/06-convergence-model.md).
- **OpenCrab 9-space 크로스워크.** 노드 타입을 MetaOntology OS의 9개 공간
  (subject, resource, evidence, concept, claim, community, outcome, lever, policy)에
  매핑하는 `maps_to` 엣지와 정합 표를 추가했습니다.
  → [`spec/07-opencrab-9space-crosswalk.md`](./spec/07-opencrab-9space-crosswalk.md).
- **6개 품질 게이트(G1–G6) 명문화.** 증거 없는 주장 금지(G1), 스코프 없는 휴리스틱 금지(G2),
  대기 후보의 런타임 활성 금지(G3), 행동 기반 언어만(G4), 승격 전 프라이버시(G5),
  템플릿/인스턴스 분리(G6). 코드로도 강제 →
  [`tools/validate_packs.py`](./tools/validate_packs.py).
- **4개 팩 클래스 거버넌스 규칙.** skill(방법) · template(스키마) · instance(데이터) ·
  adapter(런타임)는 절대 섞지 않습니다.
  → [`spec/00-overview.md`](./spec/00-overview.md),
  [`spec/08-naming-and-ids.md`](./spec/08-naming-and-ids.md).
- **14개 `user.*` 팩 JSON Schema 전부.** 통합 베이스를 확장하는 14개 인스턴스 스키마와
  후보 스키마, 평가 케이스 스키마를 추가했습니다(draft 2020-12).
  → [`schemas/`](./schemas).

### Changed (변경)

- **명제 표현 강화.** 핵심 명제를 "포착하면 쌓여 **수렴**한다"로 통일하고, 라이프사이클을
  단일 spine(`raw_signal → … → runtime_activated`)으로 표준화했습니다.
- **언어 정책 명문화.** Korean 우선, 각 상위 문서는 짧은 영어 요약 블록(`> **EN:**`)으로
  시작합니다. 스키마·JSON 키·코드 식별자는 영어를 유지합니다.

### Deprecated (폐기)

- 필드: `score`(→ `confidence`), bare `claim` / `rule_statement` / `instruction` /
  `output_rule`(→ 모두 `statement`로 통일; 팩은 표시용 별칭만 허용).
- 코드명: `pa.t03`, `t06`, `t07`, `t08`, `t09`, `t10`, `t11`, `.ba`, `x12`, `x13`,
  `x14`, `pa.roles`, `pa.core`(→ 14개 `user.*` 정식 이름). 추적용 병기 외 사용 금지.
- 후보 타입명: `DomainSpecificCandidate`(→ `DomainOverlayCandidate`),
  `ProjectGoalCandidate`(→ `ProjectMemoryCandidate`).

---

## [0.2.0] — *historical (비공개 초안)*

> 템플릿 스키마 강화 단계. 공개되지 않은 내부 초안입니다.

- **Changed** — 14개 `user.*.template` 스키마의 형태(SHAPE)를 보강하고 필드 제약을
  강화했습니다(템플릿 팩 클래스의 기반 정립).
- **Changed** — 주장 본문 필드를 `confidence` 기반으로 전환하기 시작했으나,
  `v0.1`의 `score`와 혼재하여 **필드 표류**가 남았습니다(→ v0.3에서 정합화).
- **Known issue** — 후보 타입(11)과 라우팅 대상 팩(13) 수의 불일치가 미해결로 남음.

## [0.1.0] — *historical (비공개 초안)*

> 최초 초안. **13개 skill 팩**(빌더 파이프라인)을 정의한 방법론 중심 버전입니다.

- **Added** — 13개 빌더 스킬(`skill.pab.*`): evidence_capture … kernel_schema.
  암묵지를 팩으로 바꾸는 *방법*을 정의했습니다.
- **Added** — 증거 기반 라이프사이클과 노드/엣지 그래프 모델 초안.
- **Known issue** — 레코드 점수 필드로 `score`를 사용했고, 코드명(`pa.t03`, `t06`,
  `x12`, `.ba` 등)이 정식 이름 없이 혼용됨(→ v0.3에서 정합화).

---

[Unreleased]: https://github.com/logotekton/personal-agent-builder/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/logotekton/personal-agent-builder/releases/tag/v0.3.0
