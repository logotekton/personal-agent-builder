#!/usr/bin/env python3
"""schemas/ 무결성 게이트 — 스키마 파일이 trusted 계약인데 CI 가 검사하지 않던 구멍을 막는다(it.21).

EN: the per-pack JSON schemas are the documented "root-of-truth" record contract (tools/README,
validate_packs docstring, CONTRIBUTING PR checklist), yet nothing in CI loaded them — a malformed
schema or a broken $ref to record.base merged green. This stdlib-only checker fails the build when:

  1. any schemas/*.json is not well-formed JSON,
  2. a schema declares no `$schema` draft (CONTRIBUTING requires draft 2020-12),
  3. a `$ref` to a sibling file points at a path that does not exist, or
  4. a per-pack `user.*` schema does not extend record.base via allOf + $ref
     (the exact pattern CONTRIBUTING.md mandates).

stdlib only (no jsonschema dependency) — it checks structural well-formedness + $ref resolvability,
not full draft-2020-12 conformance. Exit 0 = every schema is well-formed and wired correctly;
exit 1 = at least one violation (each printed). This is a gate, not a signal.

Usage:
  python tools/check_schemas.py            # checks ./schemas
  python tools/check_schemas.py <dir>      # checks <dir>/*.json
"""
import sys
import os
import json
import glob

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE = "record.base.schema.json"
DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"


def _iter_refs(node):
    """Yield every $ref string anywhere in the schema tree."""
    if isinstance(node, dict):
        if isinstance(node.get("$ref"), str):
            yield node["$ref"]
        for v in node.values():
            yield from _iter_refs(v)
    elif isinstance(node, list):
        for v in node:
            yield from _iter_refs(v)


def check_schema(path):
    """Return a list of error strings for one schema file (empty = clean)."""
    errors = []
    name = os.path.basename(path)
    try:
        with open(path, encoding="utf-8") as fh:
            schema = json.load(fh)
    except (OSError, UnicodeDecodeError) as exc:
        return [f"읽기 실패: {exc}"]
    except json.JSONDecodeError as exc:
        return [f"JSON 형식 오류: {exc}"]

    if not isinstance(schema, dict):
        return ["스키마 최상위가 객체가 아닙니다"]

    # 1) draft 선언 (CONTRIBUTING: draft 2020-12).
    if schema.get("$schema") != DRAFT_2020_12:
        errors.append(f"$schema 가 draft 2020-12 가 아닙니다: {schema.get('$schema')!r}")
    # 2) 메타 필드 채움 (CONTRIBUTING: $id/title/description).
    for field in ("$id", "title", "description"):
        v = schema.get(field)
        if not (isinstance(v, str) and v.strip()):
            errors.append(f"{field} 가 비어 있습니다")

    # 3) $ref 경로 해결성 — 상대-파일 참조 대상이 실제로 존재해야 한다.
    here = os.path.dirname(os.path.abspath(path))
    for ref in _iter_refs(schema):
        target = ref.split("#", 1)[0]   # drop the JSON-pointer fragment
        if not target or target.startswith(("http://", "https://")):
            continue                    # 내부 fragment(#/...) · 원격 ref 는 파일존재 검사 대상 아님
        if not os.path.exists(os.path.join(here, target)):
            errors.append(f"$ref 대상 파일이 없습니다: {ref}")

    # 4) per-pack(user.*) 스키마는 record.base 를 allOf+$ref 로 확장해야 한다.
    if name.startswith("user."):
        all_of = schema.get("allOf")
        extends_base = isinstance(all_of, list) and any(
            isinstance(b, dict) and isinstance(b.get("$ref"), str) and BASE in b["$ref"]
            for b in all_of
        )
        if not extends_base:
            errors.append(f"user.* 스키마인데 allOf+$ref 로 {BASE} 를 확장하지 않습니다")
    return errors


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    root = argv[0] if argv else "schemas"
    if os.path.isdir(root):
        paths = sorted(glob.glob(os.path.join(root, "*.json")))
    else:
        paths = [root]
    if not paths:
        sys.stderr.write(f"검사할 스키마(.json)가 없습니다: {root}\n")
        return 2

    total_errors = 0
    base_present = any(os.path.basename(p) == BASE for p in paths)
    for path in paths:
        errs = check_schema(path)
        for e in errs:
            print(f"FAIL {os.path.basename(path)}: {e}")
        total_errors += len(errs)
    if not base_present:
        print(f"FAIL: {BASE} 가 {root} 에 없습니다 (모든 per-pack 스키마의 확장 기반)")
        total_errors += 1

    print("=" * 60)
    print(f"{len(paths)} schema(s) checked; {total_errors} problem(s).")
    return 1 if total_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
