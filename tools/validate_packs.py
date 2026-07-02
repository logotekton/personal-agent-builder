#!/usr/bin/env python3
"""Personal Agent Builder — 인스턴스 레코드 코어 검증기 (dependency-light).

> **EN:** A stdlib-only validator for Personal Agent Builder *instance records*
> (the DATA layer, `personal.<subject>.*`). It checks each record against the
> core rules of the unified base record (``../schemas/record.base.schema.json``,
> spec/01-kernel-schema.md §7) WITHOUT the external ``jsonschema`` library, so it
> runs in any plain Python 3. YAML files need PyYAML (import is guarded); JSON
> always works. Use this in CI or before promotion to enforce the quality gates.

이 스크립트는 외부 ``jsonschema`` 의존성 없이, 통합 베이스 레코드의 **코어 규칙**만
순수 표준 라이브러리로 검사합니다. (전체 JSON Schema 검증이 아니라, 코드로 강제하기로
한 게이트/필드 규칙의 빠른 게이트키퍼입니다.)

검사 항목 (root of truth: ../schemas/record.base.schema.json, spec/01-kernel-schema.md):
  * 필수 베이스 필드 11개가 모두 존재하는가
  * confidence 가 0..1 범위의 숫자인가
  * evidence_refs 가 비어있지 않은가                  → 게이트 G1 (증거 없는 주장 금지)
  * scope 가 비어있지 않은가                          → 게이트 G2 (스코프 없는 규칙 금지)
  * review_status 가 enum 에 속하는가
  * sensitivity 가 enum 에 속하는가
  * confidence < 0.7 이면 counterexamples 가 존재하는가
  * (경고) review_status=confirmed(런타임 활성) 인데 evidence_refs 가 비면 G1/G3 위반 경고

입력 파일은 다음 세 가지 모양을 모두 허용합니다 (JSON 또는 YAML):
  1) 팩 이름을 키로 하는 매핑:  {"user.identity_roles": [rec, rec], ...}
     (examples/logotekton/instance-records.yaml 형태)
  2) 레코드들의 리스트:         [rec, rec, ...]
  3) 단일 레코드 객체:          {id: ..., record_type: ..., ...}

사용법 (CLI):
    python tools/validate_packs.py <path-or-dir> [<path-or-dir> ...]

  * 경로가 디렉터리면 그 아래 .json/.yaml/.yml 파일을 재귀적으로 검사합니다.
  * PASS/FAIL 요약과 레코드별 오류를 출력합니다.
  * 오류가 하나라도 있으면 비-0 코드로 종료합니다 (경고만 있으면 0).

크로스링크:
  * 베이스 스키마        : ../schemas/record.base.schema.json
  * 커널 스키마 / 게이트  : ../spec/01-kernel-schema.md  (§2 게이트, §7 레코드)
  * 팩 카탈로그          : ../spec/03-pack-catalog.md
"""

from __future__ import annotations

import json
import math
import os
import sys
from typing import Any, Iterable, List, Optional, Tuple

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

# PyYAML 은 선택 의존성입니다. 없으면 JSON 파일만 검사하고 YAML 은 친절히 건너뜁니다.
try:  # guarded optional import
    import yaml  # type: ignore

    _HAVE_YAML = True
except Exception:  # pragma: no cover - PyYAML 미설치 환경
    yaml = None  # type: ignore
    _HAVE_YAML = False


# ── 베이스 레코드 코어 계약 (record.base.schema.json §7 와 동기화) ──────────────
REQUIRED_FIELDS: Tuple[str, ...] = (
    "id",
    "record_type",
    "label",
    "statement",
    "evidence_refs",
    "confidence",
    "scope",
    "review_status",
    "sensitivity",
    "created_at",
    "updated_at",
)

REVIEW_STATUS_ENUM = {
    "pending",
    "confirmed",
    "rejected",
    "narrowed",
    "sensitive",
    "deferred",
}

SENSITIVITY_ENUM = {"public", "internal", "sensitive", "restricted"}

# [G5] 이 민감도는 exception_rules(BoundaryRule) 없이 승격할 수 없다
# (record.base.schema.json allOf 와 동기화).
SENSITIVITY_REQUIRES_EXCEPTION = {"sensitive", "restricted"}

# reliability 채널 — 증거 계층 (record.base.schema.json §7.1, spec/00 클레임-계층).
# behavioral = 관찰된 행동/산출물/교정 (G4, 신뢰 기본값). self_reported = 자기서술 (저신뢰).
RELIABILITY_ENUM = {"behavioral", "self_reported"}


def _truthy_auto_confirm(v) -> bool:
    """auto_confirmed 의 truthy 해석 — convergence_report._is_auto_confirmed 와 *동일* 규칙.

    두 도구가 같은 판정을 쓰게 해, 문자열 "true"/"auto" 로 self_reported auto-confirm 금지 규칙을
    우회하는 검증기/수렴기 드리프트를 없앤다 (적대적 검증 M2).
    """
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.strip().lower() in ("true", "auto", "yes", "1")
    return False

def _not_in_enum(v, enum):
    """enum 미포함 여부 — unhashable(list/dict) 값은 enum 멤버가 될 수 없으므로 TypeError 크래시
    대신 '미포함'(True)으로 본다(적대적 검증 it.13: 악성 list/dict 값이 검증 전체를 중단시키지 않게)."""
    try:
        return v not in enum
    except TypeError:
        return True

def _in_enum(v, enum):
    """포함 여부 — unhashable 값은 멤버가 아니므로 False (TypeError 크래시 방지)."""
    try:
        return v in enum
    except TypeError:
        return False

# 런타임 활성 상태: 이 상태의 레코드는 증거가 비면 안 됩니다 (G1 + G3).
RUNTIME_ACTIVE_STATUS = {"confirmed", "narrowed"}

# confidence < 이 값이면 counterexamples 필수.
COUNTEREXAMPLE_THRESHOLD = 0.7

YAML_EXTS = (".yaml", ".yml")
DATA_EXTS = (".json",) + YAML_EXTS


# ── 결과 컨테이너 ───────────────────────────────────────────────────────────────
class RecordResult:
    """단일 레코드의 검증 결과 (errors → FAIL, warnings → 통과하되 경고)."""

    def __init__(self, locator: str) -> None:
        self.locator = locator  # 사람이 읽는 위치 표시 (file::pack[idx] id=...)
        self.errors: List[str] = []
        self.warnings: List[str] = []

    @property
    def ok(self) -> bool:
        return not self.errors


# ── 평가 케이스 무결성 (검증자 검증, #3) ───────────────────────────────────────────
def _eval_integrity(record: Any, res: "RecordResult") -> None:
    """평가 케이스의 기록된 판정이 자기 채점 rubric 과 정합하는지 검사한다 (spec/05).

    `decision_fidelity` 는 `result.status` 를 읽어 충실도를 잰다. 그 status 가 *사람이 친 자유
    문자열*이고 아무도 rubric 과 대조하지 않으면, "보상이 검증이 아니라 기록"이 된다(카파시 #3).
    이 함수는 *라이브 채점기*(프로필을 실제 실행)는 아니지만 — 그건 컴파일된 런타임이 필요 — 기록의
    **내부 정합성**을 강제한다: 가중치 합·status↔score·하드페일·judge 결정성.
    """
    rubric = record.get("scoring_rubric")
    result = record.get("result")
    if not isinstance(rubric, dict) and not isinstance(result, dict):
        return  # 평가 케이스가 아님 (rubric/result 둘 다 없음)

    def _num(v):
        # NaN/inf 는 숫자로 보지 않는다 — NaN 비교가 전부 False 라 가중치합·점수 게이트를 조용히
        # 통과시켜 쓰레기 값이 합법 pass 로 받아들여진다(적대적 검증 it.13).
        return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)

    if isinstance(rubric, dict):
        # (a) criteria 가중치 합 ≈ 1.0 — 가중 평균 score 가 의미를 가지려면.
        crit = rubric.get("criteria")
        if isinstance(crit, list) and crit:
            weights = [c.get("weight") for c in crit if isinstance(c, dict)]
            if any(isinstance(w, (int, float)) and not isinstance(w, bool) and not math.isfinite(w)
                   for w in weights):
                res.errors.append("[EVAL] scoring_rubric.criteria 의 weight 에 비유한값(NaN/inf) 이 있습니다")
            # weight 는 스키마상 [0,1]. 범위 밖(예: 2.0 + (-1.0) = 1.0)은 합 게이트만으론 못 잡으므로 별도 강제(it.17).
            if any(_num(w) and not (0.0 <= float(w) <= 1.0) for w in weights):
                res.errors.append("[EVAL] scoring_rubric.criteria 의 weight 가 0..1 범위를 벗어났습니다")
            nums = [w for w in weights if _num(w)]
            if len(nums) == len(crit):  # 모든 criteria 에 숫자 weight 가 있을 때만 판정
                s = sum(nums)
                if abs(s - 1.0) > 0.01:
                    res.errors.append(
                        f"[EVAL] scoring_rubric 가중치 합이 1.0 이 아닙니다: {s:.3f}"
                    )

        # (a1) criteria 항목 품질 — 각 원소는 비어있지 않은 문자열 'check' 를 가진 dict 여야 한다.
        #      비-dict 원소(None·문자열·중첩리스트)는 (1) 스키마 위반이고 (2) 위 weights 리스트에서 조용히
        #      빠져 len(nums)==len(crit) 가드를 무너뜨려 가중치합 게이트 자체를 비활성화한다 — 한 원소만
        #      끼워넣어 합 5.0 짜리 쓰레기 루브릭이 통과(적대적 검증 it.16). G1/G5 항목-품질 검사와 대칭.
        def _bad_criterion(c):
            if not isinstance(c, dict):
                return True
            ch = c.get("check")
            return not (isinstance(ch, str) and ch.strip())
        if isinstance(crit, list) and crit and any(_bad_criterion(c) for c in crit):
            res.errors.append(
                "[EVAL] scoring_rubric.criteria 에 dict 가 아니거나 'check'(비어있지 않은 문자열)가 없는 "
                "항목이 있습니다 — 비-dict 항목은 가중치합 게이트까지 무력화합니다"
            )

        # (a2) 공허한 루브릭 차단 — criteria 가 비었거나 pass_threshold≤0 이면 *항상 통과*하는 루브릭이라
        #      decision_fidelity 를 공짜로 1.0 으로 밀어올린다("보상이 검증이 아니라 기록", 카파시 #3,
        #      적대적 검증 it.4 VACUOUS-RUBRIC-DF). 채점 기준이 실재해야 통과가 의미를 가진다.
        if not (isinstance(crit, list) and len(crit) >= 1):
            res.errors.append(
                "[EVAL] scoring_rubric.criteria 가 비어 있습니다 — 채점 기준 없는 루브릭은 "
                "무조건 통과라 decision_fidelity 를 공허하게 부풀립니다(채점=기록 금지)"
            )
        thr0 = rubric.get("pass_threshold")
        # 스키마상 (0,1]. 하한 0(score=0 도 통과 → 채점 무의미) + 상한 1(도달 불가능한 임계는 영구 fail)(it.17).
        if not (_num(thr0) and 0.0 < float(thr0) <= 1.0):
            res.errors.append(
                f"[EVAL] scoring_rubric.pass_threshold 는 (0,1] 범위여야 합니다: {thr0!r} "
                "— 임계 0 은 score=0 도 통과시켜 채점을 무의미하게, 임계>1 은 도달 불가능해 영구 fail"
            )

        # (d) llm_judge 결정성 — model·temperature·prompt(=prompt_id) 셋 다 고정해야 재현 가능
        #     (spec/05 §2 ④와 동기화). 셋 중 하나라도 빠지면 비결정 판정.
        judge = rubric.get("judge")
        jc = rubric.get("judge_config")
        jc_dict = jc if isinstance(jc, dict) else {}
        has_model_temp = bool(jc_dict.get("model")) and ("temperature" in jc_dict)
        has_prompt = bool(str(jc_dict.get("prompt_id", "")).strip())
        if judge == "llm_judge" and not (has_model_temp and has_prompt):
            res.errors.append(
                "[EVAL] judge=llm_judge 인데 judge_config 가 불완전합니다(model·temperature·prompt_id 셋 다 필요) "
                "— 순수 기계 판정이 비결정적(재현 불가)"
            )
        # mixed(사람+기계 혼합)는 기계 부분이 비결정적일 수 있으므로 judge_config 를 권한다(경고).
        # 스키마(user.evaluation_cases) 설명과 동기화: "warns when judge=mixed".
        if judge == "mixed" and not has_model_temp:
            res.warnings.append(
                "[EVAL] judge=mixed 인데 judge_config(model+temperature) 가 없습니다 "
                "— 혼합 판정의 기계 부분이 재현 불가할 수 있습니다. judge_config 를 고정하세요"
            )

    if isinstance(result, dict):
        status = str(result.get("status", "")).strip().lower()
        score = result.get("score")
        thr = rubric.get("pass_threshold") if isinstance(rubric, dict) else None
        fired = result.get("unacceptable_fired")
        fired_any = isinstance(fired, list) and any(isinstance(x, str) and x.strip() for x in fired)
        # unacceptable_fired 가 존재하는데 list[비어있지않은 str] 형태가 아니면 — 발동한 하드페일이
        # 조용히 무시되어(예: [{"rule":"leaked_pii"}] 같은 객체 리스트, 스칼라 문자열) RLVR 하드페일
        # 게이트를 우회한다. 형태를 강제해, 가장 안전-결정적인 게이트가 가장 쉽게 뚫리지 않게 한다.
        # (G1 evidence_refs 의 항목-품질 검사와 대칭; 스키마는 items:string 으로 선언.) (적대적 검증 it.15)
        if fired not in (None, []) and not (
            isinstance(fired, list) and all(isinstance(x, str) and x.strip() for x in fired)
        ):
            res.errors.append(
                "[EVAL] result.unacceptable_fired 는 비어있지 않은 문자열의 리스트여야 합니다 "
                f"— 발동한 하드페일이 조용히 무시되어선 안 됩니다: {fired!r}"
            )

        # score 가 숫자인데 비유한값(NaN/inf)이면 status↔score 정합 게이트가 조용히 통과하므로 거부.
        if isinstance(score, (int, float)) and not isinstance(score, bool) and not math.isfinite(score):
            res.errors.append(f"[EVAL] result.score 가 비유한값입니다(NaN/inf): {score!r}")
        # score 는 스키마상 [0,1]. 범위 밖(예: 5.0)은 status↔score 정합 게이트(score≥thr)를 무의미하게
        # 통과시켜 불가능한 점수가 'pass' 를 인증한다 — 스키마 선언 경계를 검증기도 강제(적대적 검증 it.17).
        if _num(score) and not (0.0 <= float(score) <= 1.0):
            res.errors.append(f"[EVAL] result.score 가 0..1 범위를 벗어났습니다: {score!r}")
        # edit_fraction 은 스키마상 [0,1]. 범위 밖(예: 50.0·-5.0)은 correction_cost 평균을 오염시켜
        # 성숙도 게이트를 헛되이 통과/실패시킨다(음수는 비용 과소→L3/L4 게이밍 벡터) — 경계 강제(it.17).
        ef = result.get("edit_fraction")
        if _num(ef) and not (0.0 <= float(ef) <= 1.0):
            res.errors.append(f"[EVAL] result.edit_fraction 이 0..1 범위를 벗어났습니다: {ef!r}")

        # (c) 하드페일: unacceptable 이 발동하면 점수와 무관하게 status 는 fail (RLVR).
        if fired_any and status != "fail":
            res.errors.append(
                f"[EVAL] unacceptable_behavior 발동(unacceptable_fired={fired})인데 status={status!r} "
                "— 하드페일은 점수와 무관하게 fail 이어야 합니다"
            )

        # (b) status=pass 면 score ≥ pass_threshold 여야 한다.
        if status == "pass" and _num(score) and _num(thr):
            if float(score) + 1e-9 < float(thr):
                res.errors.append(
                    f"[EVAL] status=pass 인데 score({score}) < pass_threshold({thr}) "
                    "— 기록된 pass 가 rubric 점수와 모순됩니다"
                )
        # status=fail 인데 점수는 통과선 이상이고 하드페일도 없으면 근거 불명확 (경고).
        if status == "fail" and _num(score) and _num(thr) and float(score) >= float(thr) and not fired_any:
            res.warnings.append(
                f"[EVAL] status=fail 인데 score({score}) ≥ pass_threshold({thr})·하드페일 없음 "
                "— fail 근거가 불명확합니다"
            )


# ── 검토 감사 흔적 (#8) ─────────────────────────────────────────────────────────
REVIEW_DECISIONS = {
    "confirm", "edit", "reject", "narrow_scope", "mark_sensitive", "defer", "merge", "supersede",
}


def _review_audit_check(record: Any, res: "RecordResult", require_audit: bool) -> None:
    """검토 감사 흔적(`review_audit`)을 검사한다 (카파시 #8).

    확정 레코드가 *고무도장*인지 *실제 검토*인지 기계적으로 구별하려면 reviewer·결정·diff 가
    스키마에 있어야 한다(없으면 `edit_rate` 같은 라벨 품질 신호를 계산할 수 없다). 있으면 항상
    형태를 검증하고, 없을 때 런타임 활성 레코드에 강제할지는 `--require-audit`(옵트인)로 정한다 —
    기본 비강제는 *예제에 감사 메타를 날조하지 않기* 위해서다.
    """
    ra = record.get("review_audit")
    rs = record.get("review_status")
    if isinstance(ra, dict):
        rid = ra.get("reviewer_id")
        if not (isinstance(rid, str) and rid.strip()):
            res.errors.append("[#8] review_audit 에 reviewer_id 가 없습니다 (누가 결정했는가)")
        dec = ra.get("decision")
        if dec is not None and dec not in REVIEW_DECISIONS:
            res.errors.append(
                f"[#8] review_audit.decision enum 위반: {dec!r} (허용: {sorted(REVIEW_DECISIONS)})"
            )
    elif ra is not None:
        res.errors.append(f"[#8] review_audit 는 객체여야 합니다: got {type(ra).__name__}")
    elif require_audit and _in_enum(rs, RUNTIME_ACTIVE_STATUS):
        res.errors.append(
            "[#8] 런타임 활성 레코드에 review_audit(reviewer_id·decision·diff) 가 없습니다 "
            "— 고무도장과 구별 불가, edit_rate 계산 불능 (--require-audit)"
        )


# ── 코어 레코드 검증 ────────────────────────────────────────────────────────────
def validate_record(record: Any, locator: str, require_audit: bool = False) -> RecordResult:
    """베이스 레코드 코어 규칙으로 단일 레코드를 검증합니다."""
    res = RecordResult(locator)

    if not isinstance(record, dict):
        res.errors.append(
            f"레코드가 객체(mapping)가 아닙니다: got {type(record).__name__}"
        )
        return res

    # 1) 필수 필드 존재 여부.
    for field in REQUIRED_FIELDS:
        if field not in record or record[field] is None:
            res.errors.append(f"필수 필드 누락: '{field}'")

    # 2) confidence 는 0..1 범위의 숫자 (bool 은 숫자 아님으로 취급).
    conf = record.get("confidence")
    conf_is_number = isinstance(conf, (int, float)) and not isinstance(conf, bool)
    if "confidence" in record:
        if not conf_is_number:
            res.errors.append(
                f"confidence 가 숫자가 아닙니다: {conf!r}"
            )
        elif not (0.0 <= float(conf) <= 1.0):
            res.errors.append(
                f"confidence 가 0..1 범위를 벗어났습니다: {conf}"
            )

    # 3) evidence_refs 비어있지 않은 리스트 (게이트 G1).
    ev = record.get("evidence_refs")
    if "evidence_refs" in record:
        if not isinstance(ev, list):
            res.errors.append(
                f"[G1] evidence_refs 는 리스트여야 합니다: got {type(ev).__name__}"
            )
        elif len(ev) < 1:
            res.errors.append("[G1] evidence_refs 가 비어 있습니다 (증거 없는 주장 금지)")
        elif any((not isinstance(x, str) or not x.strip()) for x in ev):
            res.errors.append("[G1] evidence_refs 에 비어있거나 문자열이 아닌 항목이 있습니다")

    # 4) scope 비어있지 않음 (게이트 G2).
    scope = record.get("scope")
    if "scope" in record:
        if not isinstance(scope, str) or not scope.strip():
            res.errors.append("[G2] scope 가 비어 있습니다 (스코프 없는 규칙 금지)")

    # 5) review_status enum.
    rs = record.get("review_status")
    if "review_status" in record and _not_in_enum(rs, REVIEW_STATUS_ENUM):
        res.errors.append(
            f"review_status 가 enum 에 없습니다: {rs!r} "
            f"(허용: {sorted(REVIEW_STATUS_ENUM)})"
        )

    # 6) sensitivity enum.
    sens = record.get("sensitivity")
    if "sensitivity" in record and _not_in_enum(sens, SENSITIVITY_ENUM):
        res.errors.append(
            f"sensitivity 가 enum 에 없습니다: {sens!r} "
            f"(허용: {sorted(SENSITIVITY_ENUM)})"
        )

    # 6a) [G5] sensitive/restricted 는 exception_rules(≥1) 필수 (BoundaryRule 없이 승격 금지).
    #     record.base.schema.json allOf 가 같은 규칙을 강제하지만, validate_packs 가
    #     단독으로(스키마 검증기 없이) 돌 때도 G5 구멍이 안 생기도록 여기서도 강제한다.
    if _in_enum(sens, SENSITIVITY_REQUIRES_EXCEPTION):
        exc = record.get("exception_rules")
        if not isinstance(exc, list) or len(exc) < 1:
            res.errors.append(
                f"[G5] sensitivity={sens!r} 레코드는 exception_rules(≥1) 가 필요합니다 "
                "— 민감/제한 레코드는 BoundaryRule(예외 규칙) 없이 승격 금지"
            )
        elif any((not isinstance(x, str) or not x.strip()) for x in exc):
            # 빈/널/비문자열 placeholder 로 G5 를 충족시키지 못하게 — G1 의 항목-품질 검사와 대칭.
            # 스키마는 items:string 이므로 [None]/[123]/[''] 는 무효이고 빈 문자열은 어떤 층도 못 잡는다.
            res.errors.append(
                "[G5] exception_rules 에 비어있거나 문자열이 아닌 항목이 있습니다 "
                "(placeholder BoundaryRule 로 민감/제한 레코드 승격 금지)"
            )

    # 6b) reliability 채널 enum + self_reported 는 auto_confirm 금지 (claim-layer 분리, C/#1).
    #     self_reported = 자기서술(저신뢰 InterpretationClaim) → 사람 게이트 없이 승격 불가.
    rel = record.get("reliability")
    if "reliability" in record and _not_in_enum(rel, RELIABILITY_ENUM):
        res.errors.append(
            f"reliability 가 enum 에 없습니다: {rel!r} "
            f"(허용: {sorted(RELIABILITY_ENUM)})"
        )
    # auto_confirmed 는 boolean 이어야 한다 (스키마 일치). 문자열 "true"/"auto" 등으로 아래 self_reported
    # auto-confirm 금지 규칙을 우회하는 검증기/수렴기 드리프트를 막는다 (적대적 검증 M2).
    ac = record.get("auto_confirmed")
    if "auto_confirmed" in record and not isinstance(ac, bool):
        res.errors.append(
            f"auto_confirmed 는 boolean 이어야 합니다: {ac!r} "
            "(문자열/숫자로 self_reported auto-confirm 금지 규칙 우회 금지)"
        )
    if rel == "self_reported" and _truthy_auto_confirm(ac):
        res.errors.append(
            "[C] reliability=self_reported 레코드는 auto_confirmed 될 수 없습니다 "
            "— 자기서술은 저신뢰 채널이라 사람 확인 없이 승격 금지 (draft-only)"
        )

    # 7) confidence < 0.7 이면 counterexamples 필수.
    if conf_is_number and float(conf) < COUNTEREXAMPLE_THRESHOLD:
        cx = record.get("counterexamples")
        if not isinstance(cx, list) or len(cx) < 1:
            res.errors.append(
                f"confidence={conf} < {COUNTEREXAMPLE_THRESHOLD} 이면 "
                "counterexamples(≥1) 가 필요합니다"
            )
        elif any((not isinstance(x, str) or not x.strip()) for x in cx):
            # 저신뢰 주장이 빈/널 placeholder 로 counterexamples 요건을 충족하지 못하게 — G1 과 대칭.
            res.errors.append(
                "counterexamples 에 비어있거나 문자열이 아닌 항목이 있습니다 "
                "(저신뢰 주장은 실제 반례가 ≥1 필요)"
            )

    # 8) (경고) 런타임 활성(confirmed/narrowed) 인데 증거가 없으면 경고.
    #    필수-필드 검사에서 이미 error 가 났을 수 있으나, 증거 부재는 런타임 활성
    #    레코드에서 특히 위험하므로 별도로 환기합니다 (G1 + G3).
    if _in_enum(rs, RUNTIME_ACTIVE_STATUS):
        if not isinstance(ev, list) or len(ev) < 1:
            res.warnings.append(
                f"런타임 활성(review_status={rs}) 레코드인데 evidence_refs 가 "
                "비어 있습니다 — 런타임에서 추적 불가 (G1/G3)"
            )

    # 9) 평가 케이스 무결성 (검증자 검증, #3) — rubric/result 를 가진 레코드에만 적용.
    _eval_integrity(record, res)

    # 10) 검토 감사 흔적 (#8) — 있으면 형태 검증, 없으면 (옵트인) 런타임활성 레코드에 요구.
    _review_audit_check(record, res, require_audit)

    return res


# ── 파일 → 레코드 추출 ──────────────────────────────────────────────────────────
def iter_records(payload: Any) -> Iterable[Tuple[str, Any]]:
    """파싱된 페이로드에서 (위치접미사, 레코드) 쌍을 산출합니다.

    세 가지 모양을 지원: 팩-키 매핑 / 레코드 리스트 / 단일 레코드.
    """
    if isinstance(payload, dict):
        # 단일 레코드처럼 보이면 (record_type 또는 id 보유) 그대로 하나로 취급.
        looks_like_record = "record_type" in payload or "id" in payload
        # 값이 전부 리스트인 매핑이면 팩-키 매핑으로 취급.
        values_all_lists = bool(payload) and all(
            isinstance(v, list) for v in payload.values()
        )
        if values_all_lists and not looks_like_record:
            for pack_name, recs in payload.items():
                for idx, rec in enumerate(recs):
                    yield f"{pack_name}[{idx}]", rec
        else:
            yield "<record>", payload
    elif isinstance(payload, list):
        for idx, rec in enumerate(payload):
            yield f"[{idx}]", rec
    else:
        # 스칼라/None: 검증 대상 아님 — 호출부에서 파일 오류로 처리하도록 빈 산출.
        return


def _is_candidate(rec: Any) -> bool:
    """이 레코드가 *후보*(CandidateAssertion)인가 — 베이스 레코드가 아니라 candidate.schema.json 대상.

    후보는 `candidate_type`(또는 `candidate_id`+`validation_status`)를 쓰고, 베이스 레코드는
    `record_type`/`id`/`statement`/`review_status` 를 쓴다(겹치지 않음). 확인 게이트(S07) 전의 후보
    파일은 베이스 코어 계약을 만족하지 않으므로 베이스 검증에서 *건너뛴다*(SKIP) — FAIL 이 아니다.

    중요: 후보-필드 *존재*만으로 판정하면, 승격 시 감사용으로 candidate_id/validation_status 를
    보존한(또는 candidate_type 이 끼어든) 베이스 레코드가 후보로 오분류돼 G1/G2/G5 를 전부 건너뛴다
    (적대적 검증 it.19). 따라서 베이스 형태(record_type·review_status, 또는 id+statement)를 가진
    레코드는 후보로 보지 않는다 — 베이스 계약으로 검증해 오염을 소리내어 잡는다.
    """
    if not isinstance(rec, dict):
        return False
    is_cand = ("candidate_type" in rec) or ("candidate_id" in rec and "validation_status" in rec)
    is_base = ("record_type" in rec) or ("review_status" in rec) or ("id" in rec and "statement" in rec)
    return is_cand and not is_base


def load_file(path: str) -> Tuple[Optional[Any], Optional[str]]:
    """파일을 파싱해 (payload, error) 를 돌려줍니다. error 가 None 이면 성공."""
    ext = os.path.splitext(path)[1].lower()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except (OSError, UnicodeDecodeError) as exc:  # 비-UTF8 파일도 그 파일만 오류로 보고(적대적 검증 it.14)
        return None, f"파일 열기 실패: {exc}"

    if ext in YAML_EXTS:
        if not _HAVE_YAML:
            return None, (
                "YAML 파일이지만 PyYAML 이 설치되지 않았습니다 "
                "(pip install pyyaml). 이 파일은 건너뜁니다."
            )
        try:
            return yaml.safe_load(text), None
        except yaml.YAMLError as exc:  # type: ignore[attr-defined]
            return None, f"YAML 파싱 오류: {exc}"
        except RecursionError as exc:  # 과도하게 중첩된 YAML 도 그 파일만 오류로(전체 실행 보호)
            return None, f"YAML 파싱 오류(중첩 과다): {exc}"
    else:
        # .json (및 확장자 미지정) 은 JSON 으로 시도.
        try:
            return json.loads(text), None
        except json.JSONDecodeError as exc:
            return None, f"JSON 파싱 오류: {exc}"
        except RecursionError as exc:  # 과도하게 중첩된 JSON 도 그 파일만 오류로(전체 실행 보호)
            return None, f"JSON 파싱 오류(중첩 과다): {exc}"


# ── 경로 수집 ───────────────────────────────────────────────────────────────────
def collect_files(paths: Iterable[str]) -> Tuple[List[str], List[str]]:
    """입력 경로들에서 검사 대상 파일 목록과 누락 경로 목록을 만듭니다."""
    files: List[str] = []
    missing: List[str] = []
    for p in paths:
        if os.path.isdir(p):
            for root, _dirs, names in os.walk(p):
                for name in sorted(names):
                    if name.lower().endswith(DATA_EXTS):
                        files.append(os.path.join(root, name))
        elif os.path.isfile(p):
            files.append(p)
        else:
            missing.append(p)
    # 결정적 순서.
    return sorted(set(files)), missing


# ── 파일 단위 검증 ──────────────────────────────────────────────────────────────
def validate_file(path: str, require_audit: bool = False) -> Tuple[List[RecordResult], List[str]]:
    """한 파일을 검증해 (레코드 결과들, 파일레벨 메시지들) 을 돌려줍니다.

    파일레벨 메시지는 파싱 실패나 '검증할 레코드 없음' 같은 상황을 담습니다.
    YAML+PyYAML 미설치 같은 건너뜀은 파일레벨 메시지로 표면화하되 FAIL 로 치지
    않도록 호출부에서 구분합니다.
    """
    results: List[RecordResult] = []
    payload, err = load_file(path)
    if err is not None:
        return results, [err]

    found = False
    n_candidates = 0
    for suffix, rec in iter_records(payload):
        if _is_candidate(rec):
            n_candidates += 1   # 후보 파일 — 베이스 검증 대상 아님 (candidate.schema.json), 건너뜀
            continue
        found = True
        results.append(validate_record(rec, f"{path}::{suffix}", require_audit))

    msgs: List[str] = []
    if n_candidates:
        msgs.append(
            f"후보 레코드 {n_candidates}건 건너뜀 (candidate.schema.json 대상 — 베이스 레코드 아님)"
        )
    if not found and not n_candidates:
        msgs.append("검증할 레코드를 찾지 못했습니다 (지원되는 모양이 아님)")
    return results, msgs


# ── 출력 / 실행 ─────────────────────────────────────────────────────────────────
def _is_skip_message(msg: str) -> bool:
    """파일레벨 메시지가 '건너뜀'(에러 아님)인지 판별합니다."""
    return ("PyYAML 이 설치되지 않았습니다" in msg) or ("후보 레코드" in msg and "건너뜀" in msg)


def run(paths: List[str]) -> int:
    """검증을 수행하고 종료 코드를 돌려줍니다 (0=성공, 1=실패, 2=사용법)."""
    # --require-audit: 런타임 활성 레코드에 review_audit(#8) 강제. 기본 off (예제 날조 방지).
    require_audit = "--require-audit" in paths
    paths = [p for p in paths if not p.startswith("--")]
    if not paths:
        print("사용법: python tools/validate_packs.py [--require-audit] <path-or-dir> [...]")
        return 2

    files, missing = collect_files(paths)

    total_records = 0
    total_pass = 0
    total_fail = 0
    total_warn = 0
    file_errors = 0
    skipped = 0
    unreadable_skips = 0   # PyYAML 부재 등으로 *읽지 못해* 건너뛴 파일(후보 스킵과 구분, 클러스터3)

    for m in missing:
        print(f"FILE-ERROR  {m}: 경로를 찾을 수 없습니다")
        file_errors += 1

    if not files and not missing:
        print("검사할 .json/.yaml/.yml 파일이 없습니다.")
        return 1

    for path in files:
        results, file_msgs = validate_file(path, require_audit)

        for msg in file_msgs:
            if _is_skip_message(msg):
                print(f"SKIP        {path}: {msg}")
                skipped += 1
                if "PyYAML 이 설치되지 않았습니다" in msg:
                    unreadable_skips += 1
            else:
                print(f"FILE-ERROR  {path}: {msg}")
                file_errors += 1

        for r in results:
            total_records += 1
            if r.ok:
                total_pass += 1
                status = "PASS"
            else:
                total_fail += 1
                status = "FAIL"
            if r.warnings:
                total_warn += len(r.warnings)

            if r.errors or r.warnings:
                print(f"{status}        {r.locator}")
                for e in r.errors:
                    print(f"    ERROR   {e}")
                for w in r.warnings:
                    print(f"    WARN    {w}")

    # ── 요약 ──
    print("")
    print("─" * 60)
    print(
        f"요약: {total_records} 레코드  |  "
        f"PASS {total_pass}  FAIL {total_fail}  "
        f"WARN {total_warn}  SKIP {skipped}  FILE-ERROR {file_errors}"
    )

    # 파일은 있었으나 *읽지 못해* 레코드를 하나도 검증 못 했으면 공허한 PASS 를 내지 않는다 —
    # PyYAML 부재로 모든 YAML 이 SKIP 되면 "검증한 것 0건"이므로 PASS 가 아니라 실패로 보고(클러스터3/CI-2b).
    vacuous = (total_records == 0 and unreadable_skips > 0)
    failed = total_fail > 0 or file_errors > 0 or vacuous
    if failed:
        if vacuous and total_fail == 0 and file_errors == 0:
            print("결과: FAIL (검증된 레코드 0 — 읽지 못한 파일이 있습니다; PyYAML 설치 필요)")
        else:
            print("결과: FAIL")
        return 1
    print("결과: PASS")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    # 간단한 도움말 플래그.
    if args and args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
