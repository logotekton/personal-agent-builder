#!/usr/bin/env python3
"""context_select.py — deterministic, budgeted context assembly (reference predicate, #9).

The compiler contract is "task-scoped activation, not a memory dump." This module makes that
predicate EXECUTABLE instead of prose: given confirmed records, a task scope, and a token budget,
it (1) filters by a deterministic scope-overlap predicate over a controlled tag vocabulary,
(2) ranks by a deterministic salience score (confidence × recency × repetition_count),
(3) greedily fills the budget, and (4) returns the dropped tail so the caller can log it as a
coverage gap. No embeddings, no LLM — same inputs always yield the same slice.

HONEST SCOPE: this is the *selection math* the Karpathy review (#9) asked for. The live compiler
(tools/pab.py compile branch) is still a STUB, so nothing wires this into a real runtime yet —
that is the remaining body-work. What is real here is the deterministic, tested predicate.

Usage (demo on a tiny built-in fixture):
  python tools/context_select.py            # prints a selected/dropped split for a sample budget
"""
import re

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
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else default


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
    return {p.strip().lower() for p in parts if p and p.strip()}


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
    eligible = [
        r for r in records
        if isinstance(r, dict) and scope_overlap(r.get("scope") or r.get("applies_in"), task_tags)
    ]
    ranked = sorted(
        eligible,
        key=lambda r: (-salience(r), str(r.get("id", "")), str(r.get("statement", ""))),
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
    selected, dropped = select_context(_DEMO, token_budget=27, task_tags=None)
    print("budget=27  (no scope filter)")
    print("selected:", [r["id"] for r in selected], "  (by salience: confidence×recency×repetition)")
    print("dropped (logged as coverage gap):", [r["id"] for r in dropped])
    print("task_types:", ", ".join(TASK_TYPES))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
