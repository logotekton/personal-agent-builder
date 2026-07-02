#!/usr/bin/env python3
"""임베디드 트리거 블록 무결성 게이트 (it.25 / open-design-decisions 클러스터 5).

EN: each builder skill doc embeds a ```yaml `trigger:` block that the skill says is "in
trigger.schema.json format", but nothing validated them — 7 of them shipped a composite host_hook
the single-token enum could not represent (it.22). This stdlib-only checker extracts every embedded
trigger block from skills/*.md and validates it against trigger.schema.json's OWN enums (derived
from the schema, so they never drift): required fields present, skill/signal/cadence/produces/
default_state in enum, and host_hook a single token OR a list of tokens (the multi-hook binding).

Needs PyYAML to parse the blocks (guarded import; without it the check is skipped, like the sibling
tools). Exit 0 = every embedded trigger validates; exit 1 = at least one violation (each printed).

Usage:
  python tools/check_triggers.py            # checks ./skills against ./schemas/trigger.schema.json
  python tools/check_triggers.py <skills_dir> <schema.json>
"""
import sys
import os
import re
import json
import glob

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import yaml  # type: ignore
    _HAVE_YAML = True
except Exception:
    yaml = None  # type: ignore
    _HAVE_YAML = False

FENCE = re.compile(r"^```(\w*)\s*$")


def _schema_enums(schema_path):
    """Pull the enums the trigger blocks must satisfy straight from the schema (single source)."""
    schema = json.load(open(schema_path, encoding="utf-8"))
    props = schema.get("properties", {})
    enums = {f: set(props.get(f, {}).get("enum", [])) for f in
             ("skill", "signal", "cadence", "produces", "default_state")}
    hook_tokens = set(schema.get("$defs", {}).get("host_hook_token", {}).get("enum", []))
    required = list(schema.get("required", []))
    return enums, hook_tokens, required


def _yaml_blocks(path):
    """Yield the raw text of every ```yaml fenced block in a markdown file."""
    in_yaml, buf = False, []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            m = FENCE.match(line.rstrip("\n"))
            if m:
                if not in_yaml and m.group(1).lower() in ("yaml", "yml"):
                    in_yaml, buf = True, []
                elif in_yaml:
                    yield "".join(buf)
                    in_yaml = False
                continue
            if in_yaml:
                buf.append(line)


def _triggers_in(path):
    """Yield each trigger dict embedded in a skill doc (the `trigger:` mapping, or a bare block)."""
    for block in _yaml_blocks(path):
        if "trigger_id" not in block:
            continue
        try:
            data = yaml.safe_load(block)
        except yaml.YAMLError:
            yield None  # malformed YAML in a trigger block is itself a violation
            continue
        if isinstance(data, dict):
            yield data.get("trigger", data) if isinstance(data.get("trigger"), dict) else data


def _validate(trig, enums, hook_tokens, required):
    """Return a list of error strings for one trigger dict."""
    errs = []
    if not isinstance(trig, dict):
        return ["트리거 블록이 매핑이 아니거나 YAML 파싱 실패"]
    for f in required:
        if f not in trig:
            errs.append(f"필수 필드 누락: {f}")
    for f, allowed in enums.items():
        if f in trig and trig[f] not in allowed:
            errs.append(f"{f} 가 enum 밖입니다: {trig[f]!r}")
    hh = trig.get("host_hook")
    if hh is not None:
        tokens = hh if isinstance(hh, list) else [hh]
        bad = [t for t in tokens if t not in hook_tokens]
        if not tokens:
            errs.append("host_hook 리스트가 비어 있습니다")
        if bad:
            errs.append(f"host_hook 토큰이 enum 밖입니다: {bad}")
    return errs


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    skills_dir = argv[0] if len(argv) >= 1 else "skills"
    schema_path = argv[1] if len(argv) >= 2 else os.path.join("schemas", "trigger.schema.json")

    if not _HAVE_YAML:
        print("note: PyYAML not installed; embedded trigger blocks not parsed (skipped).")
        return 0
    if not os.path.exists(schema_path):
        sys.stderr.write(f"[error] 스키마가 없습니다: {schema_path}\n")
        return 2

    enums, hook_tokens, required = _schema_enums(schema_path)
    paths = sorted(glob.glob(os.path.join(skills_dir, "*.md")))
    total_triggers = total_errors = 0
    for path in paths:
        for trig in _triggers_in(path):
            total_triggers += 1
            for e in _validate(trig, enums, hook_tokens, required):
                tid = trig.get("trigger_id", "?") if isinstance(trig, dict) else "?"
                print(f"FAIL {os.path.basename(path)} [{tid}]: {e}")
                total_errors += 1

    print("=" * 60)
    print(f"{total_triggers} embedded trigger(s) checked; {total_errors} problem(s).")
    return 1 if total_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
