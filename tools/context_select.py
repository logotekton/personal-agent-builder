#!/usr/bin/env python3
"""context_select.py — deterministic, budgeted context assembly (reference predicate, #9).

The compiler contract is "task-scoped activation, not a memory dump." This module makes that
predicate EXECUTABLE instead of prose: given confirmed records, a task scope, and a token budget,
it (1) filters by a deterministic scope-overlap predicate over a controlled tag vocabulary,
(2) ranks by a deterministic salience score (weighted sum:
    0.5·confidence + 0.3·recency + 0.2·(repetition_count/REP_CAP)),
(3) greedily fills the budget, and (4) returns the dropped tail so the caller can log it as a
coverage gap. No embeddings, no LLM — same inputs always yield the same slice.

It also enforces the reliability claim-layer (decision C, spec/01 §7.1): self_reported records are
draft-only and are NEVER selected as authoritative context — they are returned by the separate
draft_only() helper so a caller can show them as unconfirmed drafts, never as runtime authority.

HONEST SCOPE: this is the *selection math* the Karpathy review (#9) asked for, and the predicate
that makes "self_reported stays draft-only at runtime" real rather than aspirational. The live
compiler (tools/pab.py compile branch) is still a STUB, so nothing wires this into a real runtime
yet — that is the remaining body-work. What is real here is the deterministic, tested predicate.

Usage (demo on a tiny built-in fixture):
  python tools/context_select.py            # prints a selected/dropped split for a sample budget
"""
import math
import re
import unicodedata

# Controlled task_type vocabulary (#9): a task is classified into exactly one of these.
TASK_TYPES = (
    "code", "writing", "review", "decision", "research", "communication", "planning", "other",
)

# Deterministic salience weights. repetition_count is normalized by REP_CAP.
W_CONFIDENCE = 0.5
W_RECENCY = 0.3
W_REPETITION = 0.2
REP_CAP = 5


def _num(v, default=0.0):
    # 비유한값(NaN/inf)은 default 로 둔다 — NaN salience 는 비교가 전부 False 라 정렬이
    # 입력 순서에 의존(비결정)해져 "동일 입력 → 동일 슬라이스" 보장을 깬다(적대적 검증 it.12).
    # validate_packs 가 이미 NaN confidence 를 범위검사로 거부하는 것과 같은 방어.
    if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v):
        return float(v)
    return default


def normalize_tags(value):
    """Normalize a scope / applies_in value into a set of lowercase controlled tags."""
    if value is None:
        return set()
    if isinstance(value, str):
        parts = re.split(r"[\s,;]+", value.strip())
    elif isinstance(value, (list, tuple)):
        parts = [str(x) for x in value]
    else:
        parts = [str(value)]
    # NFC 정규화 후 비교 — 시각적으로 같은 NFC 작업 태그와 NFD 레코드 스코프가 서로 달라 보여 in-scope
    # 레코드가 선택에서 누락되지 않게(적대적 검증 it.21; convergence/compile 의 id NFC 정규화와 같은 취지).
    return {unicodedata.normalize("NFC", p).strip().lower()
            for p in parts if p and p.strip()}


def scope_overlap(record_scope, task_tags):
    """Deterministic overlap predicate.

    A record applies to the task if it shares >=1 tag with the task, OR it carries no scope tags
    (universally applicable). An empty task tag set means 'no scope filter' (everything applies).
    """
    rt = normalize_tags(record_scope)
    tt = normalize_tags(task_tags)
    if not tt:
        return True
    if not rt:
        return True
    return bool(rt & tt)


def _is_draft_only(record):
    """self_reported records are draft-only (decision C, spec/01 §7.1): they may be SHOWN as drafts
    but must NEVER be selected as authoritative runtime context. behavioral (default) is eligible."""
    return str(record.get("reliability", "behavioral")).strip().lower() == "self_reported"


def salience(record):
    """Deterministic salience 0..1 from confidence, recency, repetition_count."""
    conf = _num(record.get("confidence"))
    rec = _num(record.get("recency"))                       # 0..1 if present, else 0
    rep = min(_num(record.get("repetition_count"), 1.0), REP_CAP) / REP_CAP
    return W_CONFIDENCE * conf + W_RECENCY * rec + W_REPETITION * rep


def est_tokens(record):
    """Cheap deterministic token estimate for a record's payload (~4 chars/token)."""
    text = " ".join(str(record.get(k, "")) for k in ("statement", "label", "scope"))
    return max(1, len(text) // 4)


def select_context(records, token_budget, task_tags=None):
    """Return (selected, dropped) — records chosen within budget by salience, scope-filtered.

    Deterministic: ties are broken by record id then statement, so identical inputs always yield
    the identical slice. `dropped` is the in-scope tail that did not fit the budget — log it as a
    coverage gap (#9) rather than silently truncating.
    """
    # token_budget 는 비교(used + t <= token_budget)에 쓰이므로 숫자여야 한다 — None·문자열·NaN·bool 은
    # 조용한 오작동(전부 드롭/전부 선택)이나 TypeError 로 번지기 전에 입력 단계에서 막는다(적대적 검증 it.14).
    if isinstance(token_budget, bool) or not isinstance(token_budget, (int, float)):
        raise TypeError(f"token_budget must be a number, got {type(token_budget).__name__}")
    if not math.isfinite(token_budget):
        raise ValueError(f"token_budget must be finite, got {token_budget!r}")
    eligible = [
        r for r in records
        if isinstance(r, dict)
        and not _is_draft_only(r)  # self_reported is draft-only — never authoritative (decision C)
        and scope_overlap(r.get("scope") or r.get("applies_in"), task_tags)
    ]
    # (-salience, id, statement, scope, est_tokens) 전순서 — id+statement 까지 같고 scope/크기만 다른
    # 레코드도 입력순서에 의존하면 selected/dropped 분할이 입력순서로 뒤집힌다(적대적 검증 it.16).
    ranked = sorted(
        eligible,
        key=lambda r: (-salience(r), str(r.get("id", "")), str(r.get("statement", "")),
                       str(r.get("scope", "")), est_tokens(r)),
    )
    selected, dropped, used = [], [], 0
    for r in ranked:
        t = est_tokens(r)
        if used + t <= token_budget:
            selected.append(r)
            used += t
        else:
            dropped.append(r)
    return selected, dropped


def draft_only(records, task_tags=None):
    """In-scope self_reported records — draft-only, for surfacing as DRAFTS (never authority).

    Kept separate from select_context so a self-report can be shown to the user as an unconfirmed
    draft without ever being mistaken for authoritative runtime context (decision C, spec/01 §7.1).
    """
    return [
        r for r in records
        if isinstance(r, dict) and _is_draft_only(r)
        and scope_overlap(r.get("scope") or r.get("applies_in"), task_tags)
    ]


_DEMO = [
    {"id": "a", "statement": "prefer subprocess.run over os.system", "confidence": 0.95,
     "repetition_count": 3, "scope": "context.task.code"},
    {"id": "b", "statement": "lead replies with the conclusion first", "confidence": 0.9,
     "repetition_count": 2, "scope": "context.task.writing"},
    {"id": "c", "statement": "ask before sending external email", "confidence": 0.85,
     "repetition_count": 1, "scope": "context.task.communication"},
]


def main():
    # no scope filter, a budget that fits the two most salient records and drops the tail
    selected, dropped = select_context(_DEMO, token_budget=28, task_tags=None)
    print("budget=28  (no scope filter)")
    print("selected:", [r["id"] for r in selected],
          "  (by salience: 0.5·confidence + 0.3·recency + 0.2·repetition)")
    print("dropped (logged as coverage gap):", [r["id"] for r in dropped])
    print("task_types:", ", ".join(TASK_TYPES))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
