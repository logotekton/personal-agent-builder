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
import os
import sys
from typing import Any, Iterable, List, Optional, Tuple

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


# ── 코어 레코드 검증 ────────────────────────────────────────────────────────────
def validate_record(record: Any, locator: str) -> RecordResult:
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
    if "review_status" in record and rs not in REVIEW_STATUS_ENUM:
        res.errors.append(
            f"review_status 가 enum 에 없습니다: {rs!r} "
            f"(허용: {sorted(REVIEW_STATUS_ENUM)})"
        )

    # 6) sensitivity enum.
    sens = record.get("sensitivity")
    if "sensitivity" in record and sens not in SENSITIVITY_ENUM:
        res.errors.append(
            f"sensitivity 가 enum 에 없습니다: {sens!r} "
            f"(허용: {sorted(SENSITIVITY_ENUM)})"
        )

    # 7) confidence < 0.7 이면 counterexamples 필수.
    if conf_is_number and float(conf) < COUNTEREXAMPLE_THRESHOLD:
        cx = record.get("counterexamples")
        if not isinstance(cx, list) or len(cx) < 1:
            res.errors.append(
                f"confidence={conf} < {COUNTEREXAMPLE_THRESHOLD} 이면 "
                "counterexamples(≥1) 가 필요합니다"
            )

    # 8) (경고) 런타임 활성(confirmed/narrowed) 인데 증거가 없으면 경고.
    #    필수-필드 검사에서 이미 error 가 났을 수 있으나, 증거 부재는 런타임 활성
    #    레코드에서 특히 위험하므로 별도로 환기합니다 (G1 + G3).
    if rs in RUNTIME_ACTIVE_STATUS:
        if not isinstance(ev, list) or len(ev) < 1:
            res.warnings.append(
                f"런타임 활성(review_status={rs}) 레코드인데 evidence_refs 가 "
                "비어 있습니다 — 런타임에서 추적 불가 (G1/G3)"
            )

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


def load_file(path: str) -> Tuple[Optional[Any], Optional[str]]:
    """파일을 파싱해 (payload, error) 를 돌려줍니다. error 가 None 이면 성공."""
    ext = os.path.splitext(path)[1].lower()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
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
    else:
        # .json (및 확장자 미지정) 은 JSON 으로 시도.
        try:
            return json.loads(text), None
        except json.JSONDecodeError as exc:
            return None, f"JSON 파싱 오류: {exc}"


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
def validate_file(path: str) -> Tuple[List[RecordResult], List[str]]:
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
    for suffix, rec in iter_records(payload):
        found = True
        results.append(validate_record(rec, f"{path}::{suffix}"))

    if not found:
        return results, ["검증할 레코드를 찾지 못했습니다 (지원되는 모양이 아님)"]

    return results, []


# ── 출력 / 실행 ─────────────────────────────────────────────────────────────────
def _is_skip_message(msg: str) -> bool:
    """파일레벨 메시지가 '건너뜀'(에러 아님)인지 판별합니다."""
    return "PyYAML 이 설치되지 않았습니다" in msg


def run(paths: List[str]) -> int:
    """검증을 수행하고 종료 코드를 돌려줍니다 (0=성공, 1=실패, 2=사용법)."""
    if not paths:
        print("사용법: python tools/validate_packs.py <path-or-dir> [...]")
        return 2

    files, missing = collect_files(paths)

    total_records = 0
    total_pass = 0
    total_fail = 0
    total_warn = 0
    file_errors = 0
    skipped = 0

    for m in missing:
        print(f"FILE-ERROR  {m}: 경로를 찾을 수 없습니다")
        file_errors += 1

    if not files and not missing:
        print("검사할 .json/.yaml/.yml 파일이 없습니다.")
        return 1

    for path in files:
        results, file_msgs = validate_file(path)

        for msg in file_msgs:
            if _is_skip_message(msg):
                print(f"SKIP        {path}: {msg}")
                skipped += 1
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

    failed = total_fail > 0 or file_errors > 0
    if failed:
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
