#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""convergence_report.py — Personal Agent 수렴 지표 / 성숙도 계산기 (spec v0.3).

> EN: Compute the six convergence indices and the maturity tier (L0..L4) for one
> subject from a directory of instance-record files plus an evaluation-cases file.
> Pure Python 3 stdlib — no third-party deps. Reads JSON natively and a *safe
> subset* of YAML (mappings, lists, scalars, comments) so the worked example in
> examples/logotekton/ runs unchanged. Robust to missing/partial files: an absent
> drift file means drift_stability=1.0, an absent correction field means NA, etc.
> This is the reference implementation cited by spec/06-convergence-model.md §5 and
> examples/logotekton/convergence-report.md §6 ("재현").

한국어 요약
-----------
한 사용자(subject)의 인스턴스 레코드 디렉터리와 평가 케이스 파일에서 6개 수렴 지표와
현재 성숙도 단계를 결정론적으로 산출합니다. 외부 의존성 없이 표준 라이브러리만 사용하며,
JSON과 YAML의 안전한 부분집합을 읽습니다.

정의 출처(SINGLE SOURCE OF TRUTH):
  - 수렴 모델   : ../spec/06-convergence-model.md   (§2 6지표, §3 L0..L4 단계)
  - 평가/드리프트: ../spec/05-evaluation-drift.md     (평가 케이스 결과 필드)
  - 커널 스키마 : ../spec/01-kernel-schema.md         (§5 14팩, §7 베이스 레코드)
  - 베이스 스키마: ../schemas/record.base.schema.json
  - 팩 카탈로그 : ../spec/03-pack-catalog.md

여섯 지표 (spec/06 §2):
  coverage            = 확인 레코드 ≥3개인 팩 수 / 14         (↑, 목표 1.0)
  confirmation_ratio  = confirmed / (confirmed+pending+rejected)  (↑, ≥0.6)
                        성숙도 게이트는 auto-confirm 을 제외한 human_confirmation_ratio 를 쓴다(§4.4)
  decision_fidelity   = 통과 평가 케이스 / 전체 평가 케이스    (↑, ≥0.8; partial=0.5)
  correction_cost     = 작업당 사용자 편집 비율 평균          (↓, ≤0.2; 없으면 NA)
  drift_stability     = 1 − (전기간 대체수 / 확인 레코드수)   (↑, ≥0.8; 드리프트 없으면 1.0)
  traceability        = 증거 보유 활성 규칙 / 활성 규칙       (= 1.0 필수)

성숙도 단계 (spec/06 §3):
  L0 Seed       : 시드 팩 < 3, 평가 케이스 없음
  L1 Sketch     : 시드 팩 ≥ 7, 평가 케이스 ≥ 3, traceability == 1.0, ≥1 팩이 ≥3 확인(깊이)
  L2 Working    : coverage ≥ 0.5, decision_fidelity ≥ 0.6, human_confirmation_ratio ≥ 0.6
  L3 Reliable   : coverage ≥ 0.8, decision_fidelity ≥ 0.8, correction_cost ≤ 0.3,
                  drift_stability ≥ 0.7
  L4 Convergent : coverage == 1.0, decision_fidelity ≥ 0.9, correction_cost ≤ 0.15,
                  drift_stability ≥ 0.85, traceability == 1.0  (N기간 지속은 외부 입력)

CLI:
  python tools/convergence_report.py <dir>
      <dir> 안의 *.yaml/*.yml/*.json 인스턴스 레코드와 평가 케이스를 모두 읽어
      지표 표와 성숙도 단계를 출력합니다.

  옵션:
      --json     사람이 읽는 표 대신 기계용 JSON 한 덩이로 출력

  coverage 는 spec §2 정의(확인 ≥3 팩 / 14, 깊이)를 그대로 게이트에 쓴다. 시드폭(보조)은 참고로만
  출력한다 — "Working"을 폭으로 따는 자기기만을 막기 위해(L2 게이트 결함 수정).

종료 코드: 0 = 정상 산출. 입력 디렉터리가 없거나 읽을 파일이 0개면 2.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys

# 정식 14 user 온톨로지 팩 이름 — spec/01-kernel-schema.md §5, CANONICAL_CONTRACT §5.
# 순서 = 카탈로그 번호. 구 코드명(pa.t03, t06, x12, .ba 등)은 폐기됨.
CANONICAL_PACKS = (
    "user.identity_roles",        # 1
    "user.persona_core",          # 2
    "user.communication_style",   # 3
    "user.artifact_policy",       # 4
    "user.decision_policy",       # 5
    "user.tacit_heuristics",      # 6
    "user.red_flags",             # 7
    "user.workflow_playbooks",    # 8
    "user.domain_overlays",       # 9
    "user.tool_stack",            # 10
    "user.boundary_authority",    # 11
    "user.memory_project_graph",  # 12
    "user.evaluation_cases",      # 13
    "user.drift_history",         # 14
)
TOTAL_PACKS = len(CANONICAL_PACKS)  # 14

# 메타/시스템 팩 — *내용 깊이*(L1 depth-vertical)를 만드는 콘텐츠 팩이 아니다.
# evaluation_cases·drift_history 는 평가/드리프트 장부라, 이들이 깊이 vertical 을 채우게 두면
# L1 의 'n_eval≥3' 게이트가 vertical 도 자동 충족시켜 깊이 요구가 공허해진다(적대적 검증 it.5).
META_PACKS = frozenset({"user.evaluation_cases", "user.drift_history"})
CONTENT_PACKS = tuple(p for p in CANONICAL_PACKS if p not in META_PACKS)  # 12 콘텐츠 팩

# 구 코드명 → 정식 이름. 입력이 폐기된 코드명을 키로 쓰면 정식 이름으로 정규화한다.
LEGACY_ALIASES = {
    "pa.roles": "user.identity_roles",
    "pa.core": "user.persona_core",
    "pa.t03": "user.communication_style",
    "pa.t04": "user.artifact_policy",
    "pa.t05": "user.decision_policy",
    "t06": "user.tacit_heuristics",
    "t07": "user.red_flags",
    "t08": "user.workflow_playbooks",
    "t09": "user.domain_overlays",
    "t10": "user.tool_stack",
    "t11": "user.boundary_authority",
    ".ba": "user.boundary_authority",
    "x12": "user.memory_project_graph",
    "x13": "user.evaluation_cases",
    "x14": "user.drift_history",
}

# review_status 열거 — base record (spec/01 §7).
CONFIRMED_STATES = {"confirmed", "narrowed"}  # 런타임 활성 (G3)
PENDING_STATES = {"pending", "sensitive", "deferred"}
REJECTED_STATES = {"rejected"}

COVERAGE_MIN_CONFIRMED = 3  # 팩이 coverage(엄격)에 기여하려면 확인 레코드 ≥3 (spec/06 §2)
PARTIAL_CREDIT = 0.5        # 평가 결과 partial 의 환산 가중치 (convergence-report §1.2)


# ───────────────────────────── 미니 YAML 파서 (stdlib only) ──────────────────────────
# PyYAML 없이 동작해야 하므로, 이 저장소의 인스턴스/평가 파일이 쓰는 YAML 부분집합만
# 지원한다: 2칸 들여쓰기 블록 매핑, "- " 블록 시퀀스, "[...]"/"{...}" 인라인 컬렉션,
# "key: value" 스칼라, # 주석, 따옴표 문자열. 앵커/멀티라인/태그 등 고급 문법은 미지원.

class MiniYAMLError(ValueError):
    """미니 YAML 파서가 지원하지 않는 구문을 만났을 때."""


def _strip_comment(line: str) -> str:
    """따옴표 밖의 '#' 이후를 주석으로 제거한다."""
    out = []
    quote = None
    i = 0
    while i < len(line):
        ch = line[i]
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
        elif ch in ('"', "'"):
            quote = ch
            out.append(ch)
        elif ch == "#":
            # 공백 뒤(또는 행 시작)의 # 만 주석으로 본다 (URL 등의 #는 보존).
            if i == 0 or line[i - 1] in (" ", "\t"):
                break
            out.append(ch)
        else:
            out.append(ch)
        i += 1
    return "".join(out)


# PyYAML 1.1 은 bare nan/inf/infinity 를 float 가 아니라 문자열로 해석한다
# (특수 부동소수는 `.nan`/`.inf` 표기를 요구). 미니 파서를 같은 규칙에 맞춘다.
_SPECIAL_FLOAT_WORDS = {
    "nan", "+nan", "-nan",
    "inf", "+inf", "-inf",
    "infinity", "+infinity", "-infinity",
}


def _parse_scalar(tok: str):
    """YAML 스칼라 토큰 → Python 값 (문자열/숫자/불리언/null/인라인 컬렉션)."""
    tok = tok.strip()
    if tok == "" or tok == "~" or tok.lower() == "null":
        return None
    if (len(tok) >= 2) and tok[0] == tok[-1] and tok[0] in ('"', "'"):
        return tok[1:-1]
    low = tok.lower()
    if low in ("true", "yes", "on"):
        return True
    if low in ("false", "no", "off"):
        return False
    if tok.startswith("[") or tok.startswith("{"):
        return _parse_inline(tok)
    # 특수 부동소수 워드(nan/inf/infinity, ± 포함)는 PyYAML 1.1 처럼 *문자열* 로 둔다.
    # Python float() 는 "nan"/"inf" 를 받아들이지만, 그러면 미니 파서가 PyYAML 과
    # 갈라져 NaN 이 조용히 수치 계산(평균·비율)에 스며든다 (적대적 검증 F4).
    if low in _SPECIAL_FLOAT_WORDS:
        return tok
    # 숫자?
    try:
        if any(c in tok for c in ".eE") and not tok.startswith("0x"):
            return float(tok)
        return int(tok)
    except ValueError:
        try:
            return float(tok)
        except ValueError:
            return tok


def _split_inline(body: str):
    """인라인 컬렉션 본문을 최상위 콤마로 분리 (중첩/따옴표 인식)."""
    parts, depth, quote, cur = [], 0, None, []
    for ch in body:
        if quote:
            cur.append(ch)
            if ch == quote:
                quote = None
        elif ch in ('"', "'"):
            quote = ch
            cur.append(ch)
        elif ch in "[{":
            depth += 1
            cur.append(ch)
        elif ch in "]}":
            depth -= 1
            cur.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    if "".join(cur).strip():
        parts.append("".join(cur))
    return parts


def _parse_inline(tok: str):
    """인라인 시퀀스 [a, b] / 인라인 매핑 {k: v, ...} 파싱."""
    tok = tok.strip()
    if tok.startswith("[") and tok.endswith("]"):
        body = tok[1:-1].strip()
        if not body:
            return []
        return [_parse_scalar(p) for p in _split_inline(body)]
    if tok.startswith("{") and tok.endswith("}"):
        body = tok[1:-1].strip()
        out = {}
        if not body:
            return out
        for p in _split_inline(body):
            if ":" not in p:
                continue
            k, v = p.split(":", 1)
            out[_parse_scalar(k)] = _parse_scalar(v)
        return out
    return _parse_scalar(tok)


def _tokenize(text: str):
    """(indent, content) 쌍의 리스트로 변환 — 빈 줄/주석 줄 제거."""
    rows = []
    for raw in text.splitlines():
        line = _strip_comment(raw.replace("\t", "  ")).rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        rows.append((indent, line.strip()))
    return rows


def _parse_block(rows, idx, indent):
    """rows[idx:] 에서 indent 수준의 블록(매핑 또는 시퀀스)을 파싱.

    반환: (value, next_idx).
    """
    if idx >= len(rows):
        return None, idx
    first_indent, first_content = rows[idx]
    is_seq = first_content.startswith("- ") or first_content == "-"

    if is_seq:
        seq = []
        while idx < len(rows):
            cur_indent, content = rows[idx]
            if cur_indent < indent or not (content.startswith("- ") or content == "-"):
                break
            if cur_indent > indent:
                raise MiniYAMLError(f"불규칙 시퀀스 들여쓰기: {content!r}")
            rest = content[1:].strip()  # "- " 제거
            if rest == "":
                # 다음 줄들이 더 들여쓰여진 블록 항목
                child, idx = _parse_block(rows, idx + 1, indent + 2)
                seq.append(child)
            elif ":" in rest and not rest.startswith(("[", "{", '"', "'")):
                # 시퀀스 항목이 곧 매핑의 첫 키 — 인라인 첫 키를 합쳐 미니 매핑으로.
                # rows 를 임시로 보정: 같은 줄의 key 를 매핑 블록으로 재해석.
                synthetic = [(indent + 2, rest)]
                # 이어지는, 더 깊게 들여쓴 줄들을 이 매핑에 귀속.
                j = idx + 1
                while j < len(rows) and rows[j][0] > indent:
                    synthetic.append((rows[j][0], rows[j][1]))
                    j += 1
                child, _ = _parse_block(synthetic, 0, indent + 2)
                seq.append(child)
                idx = j
            else:
                seq.append(_parse_scalar(rest))
                idx += 1
        return seq, idx

    # 매핑
    mapping = {}
    while idx < len(rows):
        cur_indent, content = rows[idx]
        if cur_indent < indent:
            break
        if cur_indent > indent:
            raise MiniYAMLError(f"불규칙 매핑 들여쓰기: {content!r}")
        if content.startswith("- ") or content == "-":
            break  # 같은 수준의 시퀀스로 넘어감
        if ":" not in content:
            raise MiniYAMLError(f"매핑이 아닌 줄: {content!r}")
        key_part, _, val_part = content.partition(":")
        key = _parse_scalar(key_part.strip())
        val_part = val_part.strip()
        if val_part:
            mapping[key] = _parse_scalar(val_part)
            idx += 1
        else:
            # 값이 다음 줄들의 블록
            if idx + 1 < len(rows) and rows[idx + 1][0] > indent:
                child, idx = _parse_block(rows, idx + 1, rows[idx + 1][0])
                mapping[key] = child
            elif (idx + 1 < len(rows) and rows[idx + 1][0] == indent
                  and (rows[idx + 1][1].startswith("- ") or rows[idx + 1][1] == "-")):
                child, idx = _parse_block(rows, idx + 1, indent)
                mapping[key] = child
            else:
                mapping[key] = None
                idx += 1
    return mapping, idx


def mini_yaml_load(text: str):
    """YAML 부분집합을 파싱해 dict/list/scalar 트리로 반환."""
    rows = _tokenize(text)
    if not rows:
        return None
    base_indent = rows[0][0]
    value, _ = _parse_block(rows, 0, base_indent)
    return value


def load_structured(path: str):
    """확장자에 따라 JSON 또는 미니 YAML 로 파싱. 실패하면 None 반환."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:  # noqa: BLE001
        sys.stderr.write(f"[warn] 읽기 실패 {path}: {exc}\n")
        return None
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".json":
            return json.loads(text)
        # .yaml/.yml 및 기타: 미니 YAML, 실패 시 JSON 재시도
        try:
            return mini_yaml_load(text)
        except MiniYAMLError as exc:
            sys.stderr.write(f"[warn] YAML 부분집합 파싱 실패 {path}: {exc}\n")
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return None
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"[warn] JSON 파싱 실패 {path}: {exc}\n")
        return None


# ───────────────────────────── 레코드 수집 ──────────────────────────────────────────

def _normalize_pack_name(name):
    if not isinstance(name, str):
        return None
    n = name.strip()
    if n in CANONICAL_PACKS:
        return n
    if n in LEGACY_ALIASES:
        return LEGACY_ALIASES[n]
    # personal.<subject>.<pack> 형태 꼬리도 허용
    for pack in CANONICAL_PACKS:
        tail = pack.split(".", 1)[1]  # e.g. identity_roles
        if n.endswith(tail):
            return pack
    return None


def _is_record(obj) -> bool:
    """레코드처럼 보이는 dict 인가 (베이스 레코드 신호 필드 존재)."""
    if not isinstance(obj, dict):
        return False
    keys = obj.keys()
    return any(k in keys for k in ("record_type", "review_status", "statement", "id"))


def _iter_records_from_value(value):
    """파싱된 한 파일 트리에서 모든 (pack_name_or_None, record_dict) 를 산출."""
    if isinstance(value, dict):
        # 케이스 A: 팩 이름으로 키된 매핑 (instance-records.yaml 형태)
        matched_pack_key = False
        for key, sub in value.items():
            pack = _normalize_pack_name(key)
            if pack is not None and isinstance(sub, list):
                matched_pack_key = True
                for rec in sub:
                    if isinstance(rec, dict):
                        yield pack, rec
        if matched_pack_key:
            return
        # 케이스 B: 단일 레코드 dict
        if _is_record(value):
            yield None, value
            return
        # 케이스 C: 'records'/'instance_records' 같은 래퍼
        for key in ("records", "instance_records", "items", "data"):
            if isinstance(value.get(key), list):
                for rec in value[key]:
                    if isinstance(rec, dict):
                        yield None, rec
                return
    elif isinstance(value, list):
        # 케이스 D: 레코드들의 평탄 리스트 (evaluation-cases.yaml 형태)
        for rec in value:
            if isinstance(rec, dict):
                yield None, rec


def _infer_pack_for_record(rec) -> str | None:
    """팩 키가 없을 때 레코드 자체에서 소속 팩을 추론."""
    rt = rec.get("record_type")
    if rt == "EvaluationCaseRecord":
        return "user.evaluation_cases"
    if rt == "DriftRecord" or rt == "DriftRecordRecord":
        return "user.drift_history"
    # 명시적 target_pack/pack 필드
    for fld in ("target_pack", "pack", "proposed_target_pack"):
        p = _normalize_pack_name(rec.get(fld))
        if p:
            return p
    # id 의 recordkind 조각으로 추론 (best-effort)
    rid = rec.get("id")
    if isinstance(rid, str):
        parts = rid.split(".")
        if len(parts) >= 2:
            kind = parts[1]
            guess = {
                "role": "user.identity_roles",
                "core": "user.persona_core",
                "comm": "user.communication_style",
                "artifact": "user.artifact_policy",
                "decision": "user.decision_policy",
                "heuristic": "user.tacit_heuristics",
                "redflag": "user.red_flags",
                "workflow": "user.workflow_playbooks",
                "domain": "user.domain_overlays",
                "tool": "user.tool_stack",
                "boundary": "user.boundary_authority",
                "memory": "user.memory_project_graph",
                "project": "user.memory_project_graph",
                "evalcase": "user.evaluation_cases",
                "drift": "user.drift_history",
            }.get(kind)
            if guess:
                return guess
    return None


def collect(directory: str):
    """디렉터리의 모든 구조화 파일에서 레코드를 모아 팩별로 분류.

    반환: (pack_records, eval_cases, drift_records, n_files)
      pack_records: {pack_name: [record, ...]}  (eval/drift 도 해당 팩에 포함)
      eval_cases  : [record, ...]   (record_type == EvaluationCaseRecord)
      drift_records: [record, ...]  (user.drift_history 소속)
      n_files     : 읽어들인 파일 수
    """
    pack_records = {p: [] for p in CANONICAL_PACKS}
    eval_cases = []
    drift_records = []
    n_files = 0

    entries = []
    for name in sorted(os.listdir(directory)):
        full = os.path.join(directory, name)
        if not os.path.isfile(full):
            continue
        if os.path.splitext(name)[1].lower() in (".yaml", ".yml", ".json"):
            entries.append(full)

    for path in entries:
        value = load_structured(path)
        if value is None:
            continue
        n_files += 1
        for pack_hint, rec in _iter_records_from_value(value):
            pack = pack_hint or _infer_pack_for_record(rec)
            if pack is None:
                # 분류 불가 — eval/ drift 신호만이라도 잡아본다
                if rec.get("record_type") == "EvaluationCaseRecord":
                    pack = "user.evaluation_cases"
                else:
                    continue
            pack_records.setdefault(pack, []).append(rec)
            if rec.get("record_type") == "EvaluationCaseRecord":
                eval_cases.append(rec)
            if pack == "user.drift_history":
                drift_records.append(rec)

    return pack_records, eval_cases, drift_records, n_files


# ───────────────────────────── 지표 계산 ────────────────────────────────────────────

def _status_of(rec) -> str:
    return str(rec.get("review_status", "")).strip().lower()


def _is_auto_confirmed(rec) -> bool:
    """이 confirmed 레코드가 auto_confirm_policy 로 승격됐는가 (사람 게이트를 거치지 않음).

    기본값은 False = 사람이 직접 확인. spec/12 §4.4 의 순환 차단을 위해, 성숙도 게이트가 세는
    'human_confirmation_ratio' 에서 auto-confirm 승격을 제외하는 데 쓰인다.
    """
    v = rec.get("auto_confirmed")
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.strip().lower() in ("true", "auto", "yes", "1")
    return False


def _is_self_reported(rec) -> bool:
    """이 레코드가 self_reported 채널인가 (자기서술, 저신뢰 — record.base §7.1).

    self_reported 는 draft-only 라 깊이(엄격 coverage)에 안 들어간다 — 깊이=신뢰는 관찰된
    행동(behavioral)에서만 나온다는 de-averaging·claim-layer 원칙(설계자 결정 C/#1). 기본값은
    behavioral = False (reliability 필드 부재 시).
    """
    v = rec.get("reliability")
    return isinstance(v, str) and v.strip().lower() == "self_reported"


def _eval_result_status(rec) -> str | None:
    """평가 케이스의 result.status (pass/partial/fail) 를 소문자로."""
    result = rec.get("result")
    if isinstance(result, dict):
        st = result.get("status")
        if st is not None:
            return str(st).strip().lower()
    # 평탄 result 필드 fallback
    st = rec.get("result_status") or rec.get("status")
    return str(st).strip().lower() if st is not None else None


def _correction_value(rec):
    """레코드에서 사용자 편집 비율(작업당)을 추출. 없으면 None.

    인식하는 필드 (우선순위): correction_cost, edit_fraction, correction_fraction,
    result.edit_fraction, result.correction_cost.
    """
    for fld in ("correction_cost", "edit_fraction", "correction_fraction"):
        v = rec.get(fld)
        if isinstance(v, (int, float)):
            return float(v)
    result = rec.get("result")
    if isinstance(result, dict):
        for fld in ("edit_fraction", "correction_cost", "correction_fraction"):
            v = result.get(fld)
            if isinstance(v, (int, float)):
                return float(v)
    return None


def _has_evidence(rec) -> bool:
    refs = rec.get("evidence_refs")
    return isinstance(refs, list) and len(refs) >= 1 and any(
        isinstance(r, str) and r.strip() for r in refs
    )


def _id_set(value):
    """supersedes 필드(문자열 또는 리스트)를 id 집합으로 정규화."""
    if isinstance(value, str):
        return {value.strip()} if value.strip() else set()
    if isinstance(value, list):
        return {str(v).strip() for v in value if str(v).strip()}
    return set()


def _collect_superseded(pack_records, drift_records):
    """폐기된(=대체된) 레코드 id 집합 — compile_adapter.collect_superseded 와 동일 규칙
    (drift_history 의 supersedes + 각 레코드 자체의 supersedes 대상). 두 도구가 '런타임 활성'
    슬라이스를 동일하게 정의하도록, convergence 도 폐기된(은퇴한) 레코드를 LIVE 집계에서 제외한다
    — 안 그러면 compile_adapter 는 빼는 레코드를 convergence 는 confirmed/active 로 세어
    coverage·confirmation_ratio·traceability·drift 가 불일치한다 (적대적 검증 it.3)."""
    ids = set()
    for d in drift_records:
        ids |= _id_set(d.get("supersedes"))
    for recs in pack_records.values():
        for r in recs:
            if isinstance(r, dict):
                ids |= _id_set(r.get("supersedes"))
    return ids


def compute_indices(pack_records, eval_cases, drift_records):
    """6개 지표 + 보조 카운트를 dict 로 반환."""
    # 폐기(supersede)된 레코드는 LIVE 자기지도에서 은퇴했으므로 활성 집계에서 제외 (compile_adapter 와 동일).
    superseded_ids = _collect_superseded(pack_records, drift_records)
    # 팩별 확인 레코드 수
    confirmed_by_pack = {}
    # 깊이(coverage)는 behavioral *그리고* 사람이 직접 게이트한(=auto-confirm 아닌) confirmed 만 센다.
    # self_reported(draft-only) 제외 + auto_confirmed 제외 — spec/12 §4.4 '순환 차단': 성숙도 게이트가
    # *그것이 통제하는* auto-confirm 으로 부풀려지면 독립 신뢰 신호가 못 된다. auto-confirm 무더기로
    # 깊이를 채워 L3/L4 를 따는 게이밍 경로 차단(적대적 검증 it.3 AC-COVERAGE-DF-GATE-POLLUTION).
    behavioral_confirmed_by_pack = {}
    seeded_packs = 0
    n_confirmed = n_pending = n_rejected = 0
    n_auto_confirmed = 0
    n_self_reported = 0
    for pack in CANONICAL_PACKS:
        recs = [r for r in pack_records.get(pack, [])
                if str(r.get("id", "")).strip() not in superseded_ids]
        c = sum(1 for r in recs if _status_of(r) in CONFIRMED_STATES)
        bc = sum(1 for r in recs
                 if _status_of(r) in CONFIRMED_STATES
                 and not _is_self_reported(r) and not _is_auto_confirmed(r))
        confirmed_by_pack[pack] = c
        behavioral_confirmed_by_pack[pack] = bc
        # 폭(seeded)도 *behavioral* 존재를 요구한다 — self_reported 만 든 팩은 행동 증거가 없어
        # off-frontier 이므로 L1 폭 게이트(seeded≥7)를 채우지 못한다(적대적 재검증 N2: 자기서술-only
        # 팩으로 폭 게이트를 따 "관찰된 행동 위에서만 측정"을 깨는 잔여 경로 차단).
        if any(not _is_self_reported(r) for r in recs):
            seeded_packs += 1
        for r in recs:
            st = _status_of(r)
            if _is_self_reported(r):
                # self_reported 는 draft-only 라 *모든* 성숙도 지표 집계에서 제외한다 — 깊이뿐 아니라
                # confirmation_ratio·human_confirmation_ratio·drift_stability·traceability 까지. 그러지
                # 않으면 자기서술 레코드를 무더기로 confirmed 시켜 깊이 외 지표로 성숙도를 부풀리는
                # 백도어가 열린다(적대적 검증 C1). 별도 카운트로만 가시화한다.
                n_self_reported += 1
                continue
            if st in CONFIRMED_STATES:
                n_confirmed += 1
                if _is_auto_confirmed(r):
                    n_auto_confirmed += 1
            elif st in PENDING_STATES:
                n_pending += 1
            elif st in REJECTED_STATES:
                n_rejected += 1

    # 깊이(엄격 coverage)는 behavioral confirmed 만 ≥3 으로 센다 — self_reported(자기서술)는
    # draft-only 라 신뢰 깊이를 만들지 못한다(설계자 결정 C/#1, spec/00 클레임-계층).
    packs_with_3 = sum(1 for p in CANONICAL_PACKS
                       if behavioral_confirmed_by_pack[p] >= COVERAGE_MIN_CONFIRMED)
    # L1 depth-vertical 은 *콘텐츠* 팩의 깊이여야 한다 — 평가/드리프트 장부(meta)가 vertical 을
    # 채우면 깊이 요구가 'n_eval≥3' 게이트로 자동 충족돼 공허해진다(it.5 L1-vertical-vacuous).
    content_packs_with_3 = sum(1 for p in CONTENT_PACKS
                               if behavioral_confirmed_by_pack[p] >= COVERAGE_MIN_CONFIRMED)

    coverage_strict = packs_with_3 / TOTAL_PACKS          # spec §2 정의: 확인 ≥3 팩 / 14 (깊이)
    coverage_seeded = seeded_packs / TOTAL_PACKS          # 시드 폭 (보조 신호 — 게이트엔 안 씀)
    # 성숙도 게이트가 쓰는 coverage 는 spec §2 정의(엄격 ≥3)다. 시드폭으로 게이팅하면 "Working"
    # 인증을 폭으로 따게 돼 de-averaging 명제(깊이=신뢰, §8)와 모순된다 — L2 게이트 결함 수정.
    coverage_gate = coverage_strict

    denom_cr = n_confirmed + n_pending + n_rejected
    confirmation_ratio = (n_confirmed / denom_cr) if denom_cr else None

    # human_confirmation_ratio: auto-confirm 으로 승격된 레코드를 분자·분모에서 제외한 '사람 게이트'
    # 흐름만 (spec/12 §4.4 순환 차단). 성숙도 게이트는 confirmation_ratio 가 아니라 이 값을 써야,
    # auto-confirm 이 confirmed 분자를 스스로 밀어올려 '떨어졌어야 할' 성숙도를 가리는 루프를 막는다.
    # auto-confirm 이 0건이면 human_confirmation_ratio == confirmation_ratio.
    n_human_confirmed = n_confirmed - n_auto_confirmed
    denom_hcr = n_human_confirmed + n_pending + n_rejected
    human_confirmation_ratio = (n_human_confirmed / denom_hcr) if denom_hcr else None

    # decision_fidelity·correction_cost 는 성숙도 게이트의 1차 신호다. spec/12 §4.4 는 이 둘이
    # 'auto-confirm 여부와 무관'하다고 약속한다 — 그러려면 평가 케이스도 self_reported(draft-only)뿐
    # 아니라 auto_confirmed(사람 미게이트) 도 제외해야 한다. 안 그러면 auto-confirm 한 pass 평가 케이스를
    # 무더기로 넣어 decision_fidelity 를 부풀려 L3/L4 를 따는 경로가 열린다(it.3 AC-* 게이밍 홀).
    behavioral_evals = [ec for ec in eval_cases
                        if not _is_self_reported(ec) and not _is_auto_confirmed(ec)]

    # decision_fidelity: pass=1, partial=0.5, fail/그외=0 (behavioral 평가 케이스만)
    n_eval = len(behavioral_evals)
    if n_eval:
        passed = 0.0
        n_pass = n_partial = n_fail = 0
        for ec in behavioral_evals:
            st = _eval_result_status(ec)
            if st == "pass":
                passed += 1.0
                n_pass += 1
            elif st == "partial":
                passed += PARTIAL_CREDIT
                n_partial += 1
            else:
                n_fail += 1
        decision_fidelity = passed / n_eval
    else:
        decision_fidelity = None
        n_pass = n_partial = n_fail = 0

    # correction_cost: *평가 케이스*의 편집 비율(result.edit_fraction 등)만의 평균. 없으면 NA.
    # 출처를 평가 케이스(behavioral_evals)로 한정한다 — 임의 레코드(페르소나·휴리스틱 등)에 edit_fraction=0
    # 을 무더기로 심어 평균을 0 으로 끌어내리는 게이밍 경로를 차단(적대적 검증 it.4 CORRECTION-COST-SEEDING).
    # correction_cost 는 본질적으로 *평가* 측정(런타임 출력을 사람이 얼마나 고쳤는가, spec/05)이므로
    # 평가 케이스 외 레코드를 출처로 삼는 것은 의미상으로도 틀리다. self_reported·auto_confirmed 평가는
    # 이미 behavioral_evals 에서 제외됨.
    corr_vals = []
    for ec in behavioral_evals:
        v = _correction_value(ec)
        if v is not None:
            corr_vals.append(v)
    correction_cost = (sum(corr_vals) / len(corr_vals)) if corr_vals else None

    # drift_stability = 1 − (전기간 대체수 / 확인 레코드수). 드리프트 없으면 1.0. (self_reported 드리프트 제외)
    # 주: 기간/타임스탬프 윈도우 모델이 아직 없어 *전 기간 누적* 대체수를 센다(spec/06 §1 표 주석).
    # '최근 기간' 윈도우는 계획된 정련 — 기간 필드 추가 시 도입.
    supersessions = 0
    for d in drift_records:
        if _is_self_reported(d):
            continue
        sup = d.get("supersedes")
        if isinstance(sup, list):
            supersessions += len([s for s in sup if s])
        elif sup:
            supersessions += 1
        else:
            # supersedes 미기재여도 드리프트 레코드 자체를 1건 대체로 셈
            supersessions += 1
    if n_confirmed > 0:
        drift_stability = 1.0 - (supersessions / n_confirmed)
        if drift_stability < 0.0:
            drift_stability = 0.0
    else:
        drift_stability = 1.0  # 확인 레코드가 없으면 흔들릴 대상 자체가 없음

    # traceability = 증거 보유 활성(confirmed) 규칙 / 활성 규칙. 활성 규칙 0이면 1.0.
    # self_reported 는 draft-only(런타임 활성 규칙이 아님)라 활성 집합에서 제외 (C1 백도어 차단).
    active = [r for recs in pack_records.values() for r in recs
              if _status_of(r) in CONFIRMED_STATES and not _is_self_reported(r)
              and str(r.get("id", "")).strip() not in superseded_ids]
    if active:
        with_ev = sum(1 for r in active if _has_evidence(r))
        traceability = with_ev / len(active)
    else:
        traceability = 1.0

    return {
        "coverage": coverage_gate,
        "coverage_seeded": coverage_seeded,
        "coverage_strict": coverage_strict,
        "confirmation_ratio": confirmation_ratio,
        "human_confirmation_ratio": human_confirmation_ratio,
        "decision_fidelity": decision_fidelity,
        "correction_cost": correction_cost,
        "drift_stability": drift_stability,
        "traceability": traceability,
        # 보조 카운트 (성숙도 판정·리포트용)
        "_seeded_packs": seeded_packs,
        "_packs_with_3": packs_with_3,
        "_content_packs_with_3": content_packs_with_3,
        "_n_confirmed": n_confirmed,
        "_n_auto_confirmed": n_auto_confirmed,
        "_n_human_confirmed": n_human_confirmed,
        "_n_self_reported": n_self_reported,
        "_n_pending": n_pending,
        "_n_rejected": n_rejected,
        "_n_eval": n_eval,
        "_eval_pass": n_pass,
        "_eval_partial": n_partial,
        "_eval_fail": n_fail,
        "_supersessions": supersessions,
        "_n_superseded_excluded": len(superseded_ids),
        "_n_active": len(active),
        "_confirmed_by_pack": confirmed_by_pack,
        "_behavioral_confirmed_by_pack": behavioral_confirmed_by_pack,
    }


# ───────────────────────────── 성숙도 단계 ──────────────────────────────────────────

def maturity_tier(ix):
    """지표 dict 에서 최고 충족 단계와 충족/미달 사유를 반환.

    반환: (tier_id, tier_name, reasons_dict)
    """
    coverage = ix["coverage"]
    cr = ix["confirmation_ratio"]
    # 성숙도 게이트는 auto-confirm 에 오염되지 않는 human_confirmation_ratio 를 쓴다 (spec/12 §4.4).
    # 값이 없으면(사람 게이트 흐름이 0건) None → 게이트 미충족: 사람 신호 없이는 성숙을 인증하지 않는다.
    hcr = ix.get("human_confirmation_ratio")
    df = ix["decision_fidelity"]
    cost = ix["correction_cost"]
    drift = ix["drift_stability"]
    trace = ix["traceability"]
    seeded = ix["_seeded_packs"]
    # L1 vertical 은 *콘텐츠* 팩의 깊이만 센다 — 평가/드리프트 메타 팩은 제외(it.5 L1-vertical-vacuous).
    verticals = ix.get("_content_packs_with_3", 0)   # ≥3 확인 레코드를 가진 *콘텐츠* 팩 수 (깊이)
    n_eval = ix["_n_eval"]

    def ge(a, b):  # None-안전 ≥
        return a is not None and a >= b

    def le(a, b):  # None-안전 ≤
        return a is not None and a <= b

    # 각 단계 진입 조건 (spec/06 §3)
    # L1 은 '폭'(≥7팩)뿐 아니라 '깊이' 한 칸(≥1 팩이 ≥3 확인 = vertical)도 요구한다 — 1레코드씩
    # 14팩에 흩뿌려 성숙도를 따는 breadth-first 게이밍을 막기 위해(#7, overfit-tiny-set-first).
    l1 = (seeded >= 7) and (n_eval >= 3) and (trace == 1.0) and (verticals >= 1)
    l2 = ge(coverage, 0.5) and ge(df, 0.6) and ge(hcr, 0.6)
    l3 = ge(coverage, 0.8) and ge(df, 0.8) and le(cost, 0.3) and ge(drift, 0.7)
    l4 = (
        coverage == 1.0
        and ge(df, 0.9)
        and le(cost, 0.15)
        and ge(drift, 0.85)
        and trace == 1.0
    )
    # L0 졸업 = 시드 팩 ≥3 또는 평가 케이스 존재
    graduated_l0 = (seeded >= 3) or (n_eval > 0)

    reached = "L0"
    if graduated_l0 and l1:
        reached = "L1"
    if reached == "L1" and l2:
        reached = "L2"
    if reached == "L2" and l3:
        reached = "L3"
    if reached == "L3" and l4:
        reached = "L4"

    names = {
        "L0": "Seed", "L1": "Sketch", "L2": "Working",
        "L3": "Reliable", "L4": "Convergent",
    }

    reasons = {
        "L0_graduated": graduated_l0,
        "L1_seeded>=7": seeded >= 7,
        "L1_eval>=3": n_eval >= 3,
        "L1_traceability==1.0": trace == 1.0,
        "L1_vertical>=1 (콘텐츠 팩 ≥3 확인)": verticals >= 1,
        "L2_coverage>=0.5": ge(coverage, 0.5),
        "L2_decision_fidelity>=0.6": ge(df, 0.6),
        "L2_human_confirmation_ratio>=0.6": ge(hcr, 0.6),
        "L3_coverage>=0.8": ge(coverage, 0.8),
        "L3_decision_fidelity>=0.8": ge(df, 0.8),
        "L3_correction_cost<=0.3": le(cost, 0.3),
        "L3_drift_stability>=0.7": ge(drift, 0.7),
        "L4_coverage==1.0": coverage == 1.0,
        "L4_decision_fidelity>=0.9": ge(df, 0.9),
        "L4_correction_cost<=0.15": le(cost, 0.15),
        "L4_drift_stability>=0.85": ge(drift, 0.85),
        "L4_traceability==1.0": trace == 1.0,
    }
    return reached, names[reached], reasons


# ───────────────────────────── 출력 ─────────────────────────────────────────────────

def _fmt(v):
    if v is None:
        return "  NA"
    if isinstance(v, float):
        if math.isnan(v):
            return "  NA"
        return f"{v:0.2f}"
    return str(v)


INDEX_META = [
    # (key, 표시명, 방향, 좋은값)
    ("coverage",           "coverage          ", "up",   "→1.0 (≥0.5 L2, ≥0.8 L3)"),
    ("confirmation_ratio", "confirmation_ratio", "up",   "≥0.6"),
    ("decision_fidelity",  "decision_fidelity ", "up",   "≥0.8"),
    ("correction_cost",    "correction_cost   ", "DOWN", "≤0.2  (낮을수록 좋음)"),
    ("drift_stability",    "drift_stability   ", "up",   "≥0.8"),
    ("traceability",       "traceability      ", "==",   "1.0 필수"),
]


def render_table(ix, tier_id, tier_name, directory, n_files):
    lines = []
    lines.append("=" * 72)
    lines.append("Personal Agent — 수렴 리포트 (Convergence Report)")
    lines.append(f"입력 디렉터리: {directory}  ·  읽은 파일: {n_files}개")
    lines.append("정의: spec/06-convergence-model.md §2(지표) · §3(단계)")
    lines.append("=" * 72)
    lines.append("")
    lines.append("[1] 시드 현황")
    lines.append(f"  시드된 팩            : {ix['_seeded_packs']} / {TOTAL_PACKS}")
    lines.append(f"  확인 레코드 ≥3 팩    : {ix['_packs_with_3']} / {TOTAL_PACKS}")
    lines.append(
        f"  레코드 상태          : confirmed {ix['_n_confirmed']} · "
        f"pending {ix['_n_pending']} · rejected {ix['_n_rejected']}"
    )
    if ix.get("_n_self_reported"):
        lines.append(
            f"  self_reported        : {ix['_n_self_reported']}건 (draft-only) — 저신뢰 채널이라 "
            f"모든 성숙도 지표(깊이·confirmation·drift·traceability)에서 제외 (C/#1, spec/00 클레임-계층)"
        )
    lines.append(
        f"  평가 케이스          : {ix['_n_eval']}개 "
        f"(pass {ix['_eval_pass']} · partial {ix['_eval_partial']} · fail {ix['_eval_fail']})"
    )
    lines.append(f"  대체(supersession)   : {ix['_supersessions']}건")
    lines.append("")
    lines.append("[2] 여섯 지표")
    lines.append(f"  {'지표':<19}{'값':>7}   {'방향':<5} 좋은 값")
    lines.append("  " + "-" * 68)
    for key, name, direction, good in INDEX_META:
        lines.append(f"  {name} {_fmt(ix[key]):>6}   {direction:<5} {good}")
    # coverage 보조값 (표면/엄격 둘 다)
    lines.append(
        f"    └ coverage 상세: 엄격(≥3) {ix['coverage_strict']:0.2f} ← 게이트 사용값(spec §2 정의) · "
        f"시드폭 {ix['coverage_seeded']:0.2f}(보조)"
    )
    lines.append(
        f"    └ confirmation: 전체 {_fmt(ix['confirmation_ratio'])} · "
        f"사람게이트 {_fmt(ix['human_confirmation_ratio'])}  "
        f"(성숙도 게이트 사용값: 사람게이트 — auto-confirm {ix['_n_auto_confirmed']}건 제외, spec/12 §4.4)"
    )
    lines.append("")
    lines.append("[3] 팩별 확인 레코드 수")
    bc_by_pack = ix.get("_behavioral_confirmed_by_pack", ix["_confirmed_by_pack"])
    for i, pack in enumerate(CANONICAL_PACKS, start=1):
        c = ix["_confirmed_by_pack"][pack]
        bc = bc_by_pack[pack]
        sr = c - bc  # 이 팩의 self_reported confirmed (draft-only)
        # ≥3 깊이 표시는 behavioral confirmed 기준 (self_reported 는 깊이를 못 만든다).
        mark = " (≥3 ✓)" if bc >= COVERAGE_MIN_CONFIRMED else (" (-)" if c == 0 else "")
        sr_note = f"  [self_reported {sr}, draft-only]" if sr else ""
        lines.append(f"  {i:>2}. {pack:<28} {c:>2}{mark}{sr_note}")
    # off-frontier 경고: behavioral 데이터가 없는 영역 — 에이전트가 *당신처럼* 행동할 근거가 없는 곳.
    # 성숙도가 폭으로 열려도, 여기서 권위 있게 행동하면 평균/일반값으로 둘러대는 가짜 자신이 된다 (#7·#6).
    # self_reported 만 있는 팩도 off-frontier — 자기서술은 행동 근거가 아니다 (C/#1).
    empty = [p for p in CANONICAL_PACKS if bc_by_pack[p] == 0]
    lines.append("")
    lines.append("[!] off-frontier (권위 있게 행동 금지 — draft-only)")
    if empty:
        lines.append(f"  behavioral 확인 0개 팩 {len(empty)}/{TOTAL_PACKS}: {', '.join(empty)}")
        lines.append("    → 이 영역엔 당신의 행동 데이터가 없다(자기서술만 있어도 여기 포함). 에이전트는")
        lines.append("      평균/일반값으로 답하지 말고 기권하거나 물어야 한다 (de-averaging, spec/06 §8 · spec/00).")
    else:
        lines.append("  behavioral 확인 0개 팩 없음 — off-frontier 공백 없음.")
    lines.append(
        f"  깊이(≥3 확인) 팩 {ix['_packs_with_3']}/{TOTAL_PACKS}"
        f"(이 중 콘텐츠 {ix.get('_content_packs_with_3', 0)} — L1 vertical 은 콘텐츠만 인정)  ·  "
        f"폭(시드) {ix['coverage_seeded']:0.2f} vs 깊이(엄격) {ix['coverage_strict']:0.2f}"
    )
    if ix["coverage_seeded"] - ix["coverage_strict"] >= 0.3:
        lines.append("    → 폭 ≫ 깊이: 성숙도는 폭으로도 열리지만 *신뢰는 깊이에서* 온다. 얕은 팩은 draft-only.")
    lines.append("")
    lines.append("[4] 성숙도 단계")
    lines.append(f"  >>> {tier_id} {tier_name} <<<")
    _, _, reasons = maturity_tier(ix)
    # 현재 단계의 바로 위 단계로 가기 위한 미달 조건만 보여준다
    next_tier = {"L0": "L1", "L1": "L2", "L2": "L3", "L3": "L4", "L4": None}[tier_id]
    if next_tier:
        unmet = [k for k, ok in reasons.items()
                 if k.startswith(next_tier + "_") and not ok]
        if unmet:
            lines.append(f"  다음 단계({next_tier})까지 미달 조건:")
            for k in unmet:
                lines.append(f"    - {k}")
        else:
            lines.append(f"  ({next_tier} 조건은 모두 충족 — 정수 카운트/지속기간 등 외부 조건 확인 필요)")
    else:
        lines.append("  최고 단계(L4 Convergent). 단, L4는 'N기간 지속'까지 만족해야 유지로 인정됩니다.")
    lines.append("=" * 72)
    return "\n".join(lines)


def render_json(ix, tier_id, tier_name, directory, n_files):
    _, _, reasons = maturity_tier(ix)
    public = {
        "directory": directory,
        "files_read": n_files,
        "indices": {
            "coverage": ix["coverage"],
            "coverage_seeded": ix["coverage_seeded"],
            "coverage_strict": ix["coverage_strict"],
            "confirmation_ratio": ix["confirmation_ratio"],
            "human_confirmation_ratio": ix["human_confirmation_ratio"],
            "decision_fidelity": ix["decision_fidelity"],
            "correction_cost": ix["correction_cost"],
            "drift_stability": ix["drift_stability"],
            "traceability": ix["traceability"],
        },
        "counts": {
            "seeded_packs": ix["_seeded_packs"],
            "packs_with_3_confirmed": ix["_packs_with_3"],
            "confirmed": ix["_n_confirmed"],
            "auto_confirmed": ix["_n_auto_confirmed"],
            "human_confirmed": ix["_n_human_confirmed"],
            "self_reported": ix["_n_self_reported"],
            "pending": ix["_n_pending"],
            "rejected": ix["_n_rejected"],
            "eval_total": ix["_n_eval"],
            "eval_pass": ix["_eval_pass"],
            "eval_partial": ix["_eval_partial"],
            "eval_fail": ix["_eval_fail"],
            "supersessions": ix["_supersessions"],
            "confirmed_by_pack": ix["_confirmed_by_pack"],
        },
        "maturity": {"tier": tier_id, "name": tier_name, "gate_checks": reasons},
    }
    return json.dumps(public, ensure_ascii=False, indent=2)


# ───────────────────────────── CLI ──────────────────────────────────────────────────

def build_arg_parser():
    p = argparse.ArgumentParser(
        prog="convergence_report.py",
        description=(
            "한 사용자의 인스턴스 레코드 + 평가 케이스 디렉터리에서 6개 수렴 지표와 "
            "성숙도 단계(L0..L4)를 계산합니다. spec/06-convergence-model.md 참조."
        ),
    )
    p.add_argument("directory", help="인스턴스 레코드/평가 케이스 파일이 든 디렉터리")
    p.add_argument("--json", action="store_true", dest="as_json",
                   help="사람용 표 대신 기계용 JSON 출력")
    return p


def main(argv=None):
    args = build_arg_parser().parse_args(argv)
    directory = args.directory

    if not os.path.isdir(directory):
        sys.stderr.write(f"[error] 디렉터리가 아님: {directory}\n")
        return 2

    pack_records, eval_cases, drift_records, n_files = collect(directory)
    if n_files == 0:
        sys.stderr.write(
            f"[error] {directory} 에서 읽을 수 있는 .yaml/.yml/.json 파일이 없습니다.\n"
        )
        return 2

    ix = compute_indices(pack_records, eval_cases, drift_records)
    tier_id, tier_name, _ = maturity_tier(ix)

    if args.as_json:
        print(render_json(ix, tier_id, tier_name, directory, n_files))
    else:
        print(render_table(ix, tier_id, tier_name, directory, n_files))
    return 0


if __name__ == "__main__":
    sys.exit(main())
