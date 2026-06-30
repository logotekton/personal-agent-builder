#!/usr/bin/env python3
"""pab_merge.py — the dedup-judge + upsert/supersede ACTUATOR (spec/10-dedup-and-merge.md).

> **EN:** This is the missing actuator that makes one turn of the data-engine flywheel real:
> it takes a batch of *incoming candidates* (e.g. a session's mined, confirmed candidates) and
> *upserts* them into a subject's existing instance records instead of appending duplicate twins.
> It implements the dedup judge of spec/10 deterministically (no embeddings, stdlib-only):
>
>   canonical_key = sha1( pack · record_type · normalize(statement) · normalize(scope) )
>
>   verdict          condition                                   action
>   ---------------  ------------------------------------------  ------------------------------
>   novel            no existing record shares the identity      INSERT (repetition_count=1)
>   duplicate        same pack·type·norm(statement)·scope        MERGE  (repetition_count++,
>                                                                  evidence_refs ∪, merge_history+)
>   refinement       same pack·type·norm(statement), new scope   SUPERSEDE (new record + supersedes
>                                                                  edge; old retired; DriftRecord)
>   conflict         same pack·type·scope, similar-not-equal     SURFACE (never auto-applied)
>
> MERGE is idempotent: a candidate already named in a record's merge_history is a no-op, so
> re-running the same batch converges (re-derivation = accumulated evidence, not a new twin —
> the exact behavior spec/10 §4 prescribes and dedup_check.py measures as merge_rate).
>
> This is a *measurement-free* counterpart to dedup_check.py (which only *reports* redundancy):
> pab_merge actually performs the upsert. Conflicts are surfaced, never silently overwritten (G3/G5
> preserved: this operates on already-confirmed candidates; it does not promote pending ones).

Usage:
  # dry-run: classify the batch and print the plan (no writes) — DEFAULT
  python tools/pab_merge.py examples/logotekton/instance-records.yaml INCOMING.yaml

  # apply: write the upserted record set (pack->[records] mapping) to OUT (YAML or JSON by ext)
  python tools/pab_merge.py instance-records.yaml INCOMING.yaml --apply --out merged.yaml

  # emit the JSON plan for tooling
  python tools/pab_merge.py instance-records.yaml INCOMING.yaml --json

INCOMING is a YAML/JSON list of candidate records (each with target_pack|pack, record_type,
statement, scope, evidence_refs, id, ...), or a pack->[candidates] mapping. Exit code is 0 unless
a conflict is found and --strict is passed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

try:
    import yaml  # optional; needed for YAML in/out
    _HAVE_YAML = True
except Exception:
    _HAVE_YAML = False

CANONICAL_PACKS = [
    "user.identity_roles", "user.persona_core", "user.communication_style",
    "user.artifact_policy", "user.decision_policy", "user.tacit_heuristics",
    "user.red_flags", "user.workflow_playbooks", "user.domain_overlays",
    "user.tool_stack", "user.boundary_authority", "user.memory_project_graph",
    "user.evaluation_cases", "user.drift_history",
]

# record_type -> owning pack (spec/03), used to infer the pack of a flat candidate.
_PACK_RECORD_TYPES = {
    "user.identity_roles": ["RoleRecord", "ContextRecord", "AttributionRecord", "ScopeRecord"],
    "user.persona_core": ["PreferenceRecord", "AvoidanceRecord", "PriorityRecord", "ValueRecord", "StablePatternRecord"],
    "user.communication_style": ["ResponseFormatRecord", "LanguageRecord", "StructureRecord", "DensityRecord", "RevisionCueRecord"],
    "user.artifact_policy": ["ArtifactFormatRecord", "FileOutputRecord", "TablePolicyRecord", "DiagramPolicyRecord", "ReviewArtifactRecord"],
    "user.decision_policy": ["PriorityRuleRecord", "TradeoffRuleRecord", "ApprovalConditionRecord", "RejectionRuleRecord", "EscalationThresholdRecord"],
    "user.tacit_heuristics": ["HeuristicRecord", "ContrastiveRuleRecord", "TriggerActionRecord"],
    "user.red_flags": ["RiskSignalRecord", "WeakStructureRecord", "EvidenceGapRecord"],
    "user.workflow_playbooks": ["WorkflowRecord", "StepSequenceRecord", "PlaybookRecord"],
    "user.domain_overlays": ["DomainKnowledgeRecord", "DomainAttentionRecord", "DomainTermRecord"],
    "user.tool_stack": ["ToolPreferenceRecord", "ToolUsageRecord", "ToolAvoidanceRecord"],
    "user.boundary_authority": ["BoundaryRuleRecord", "AuthorityLevelRecord", "ConfirmationRuleRecord", "SensitivityRecord"],
    "user.memory_project_graph": ["ProjectRecord", "GoalRecord", "MemoryLinkRecord"],
    "user.evaluation_cases": ["EvaluationCaseRecord"],
    "user.drift_history": ["DriftRecord", "SupersessionRecord", "VersionRecord"],
}
RECORD_TYPE_TO_PACK = {rt: p for p, rts in _PACK_RECORD_TYPES.items() for rt in rts}

# Jaccard band for "similar but not the same" -> possible conflict (surface, don't apply).
CONFLICT_LOW = 0.5
CONFLICT_HIGH = 0.85
CONF_BUMP = 0.05      # per-merge confidence increment
CONF_CAP = 0.99       # capped (counterexamples set the true ceiling; see spec/10 §4)


def _norm_tokens(s):
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9가-힣\s]", " ", s)
    return [t for t in s.split() if t]


def _norm_scope(s):
    return " ".join(_norm_tokens(s))


def _jaccard(a, b):
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / len(sa | sb) if (sa | sb) else 0.0


def canonical_key(pack, record_type, statement, scope):
    """sha1( pack · record_type · normalize(statement) · normalize(scope) )[:12] (spec/10 §2)."""
    parts = [pack or "", record_type or "", " ".join(_norm_tokens(statement)), _norm_scope(scope)]
    return hashlib.sha1("\x1f".join(parts).encode("utf-8")).hexdigest()[:12]


def identity_key(pack, record_type, statement):
    """Identity WITHOUT scope — same identity, different scope = refinement (spec/10 §5)."""
    parts = [pack or "", record_type or "", " ".join(_norm_tokens(statement))]
    return hashlib.sha1("\x1f".join(parts).encode("utf-8")).hexdigest()[:12]


def _load(path):
    text = open(path, encoding="utf-8").read()
    if path.endswith((".yaml", ".yml")):
        if not _HAVE_YAML:
            raise SystemExit(f"PyYAML required to read {path} (pip install pyyaml)")
        return yaml.safe_load(text)
    return json.loads(text)


def _records_by_pack(data):
    """Return {pack: [records]} from a pack-keyed mapping or a flat list (pack inferred)."""
    out = {}
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, list):
                out.setdefault(k, []).extend([r for r in v if isinstance(r, dict)])
    elif isinstance(data, list):
        for r in data:
            if isinstance(r, dict):
                pack = (r.get("pack") or r.get("target_pack") or r.get("proposed_target_pack")
                        or RECORD_TYPE_TO_PACK.get(r.get("record_type"), "unknown"))
                out.setdefault(pack, []).append(r)
    return out


def _pack_of_candidate(c):
    return (c.get("pack") or c.get("target_pack") or c.get("proposed_target_pack")
            or RECORD_TYPE_TO_PACK.get(c.get("record_type"), "unknown"))


def classify(existing_by_pack, candidate):
    """Return a plan dict for one candidate: verdict + target + the field deltas."""
    pack = _pack_of_candidate(candidate)
    rt = candidate.get("record_type", "")
    stmt = candidate.get("statement", "")
    scope = candidate.get("scope", "")
    cid = candidate.get("id", "<no-id>")
    ck = canonical_key(pack, rt, stmt, scope)
    ik = identity_key(pack, rt, stmt)
    existing = existing_by_pack.get(pack, [])

    # exact-identity (same scope) -> duplicate -> merge (idempotent on merge_history)
    for r in existing:
        r_ck = r.get("canonical_key") or canonical_key(pack, r.get("record_type", ""), r.get("statement", ""), r.get("scope", ""))
        if r_ck == ck:
            # already present (this candidate WAS this record, e.g. a prior insert) -> noop
            if r.get("id") == cid or cid in (r.get("merge_history") or []):
                return {"candidate": cid, "pack": pack, "verdict": "already_merged",
                        "action": "noop", "target": r.get("id"), "canonical_key": ck}
            return {"candidate": cid, "pack": pack, "verdict": "duplicate",
                    "action": "merge", "target": r.get("id"), "canonical_key": ck}

    # same identity, different scope -> refinement -> supersede
    for r in existing:
        r_ik = identity_key(pack, r.get("record_type", ""), r.get("statement", ""))
        if r_ik == ik and _norm_scope(r.get("scope", "")) != _norm_scope(scope):
            return {"candidate": cid, "pack": pack, "verdict": "refinement",
                    "action": "supersede", "target": r.get("id"), "canonical_key": ck}

    # similar-but-not-equal within same (type, scope) -> possible conflict -> surface
    cand_tok = _norm_tokens(stmt)
    for r in existing:
        if r.get("record_type") == rt and _norm_scope(r.get("scope", "")) == _norm_scope(scope):
            sim = _jaccard(cand_tok, _norm_tokens(r.get("statement", "")))
            if CONFLICT_LOW <= sim < CONFLICT_HIGH:
                return {"candidate": cid, "pack": pack, "verdict": "conflict",
                        "action": "surface", "target": r.get("id"), "similarity": round(sim, 2),
                        "canonical_key": ck}

    return {"candidate": cid, "pack": pack, "verdict": "novel", "action": "insert",
            "target": None, "canonical_key": ck}


def _project_candidate(working, plan, candidate):
    """Make a candidate that will land in the set visible to *later* candidates in
    the same batch, so the batch dedups against itself — not just against the
    pre-existing snapshot."""
    if plan["action"] not in ("insert", "supersede"):
        return  # merge → target already visible; conflict/noop → intentionally not added
    pack = plan["pack"]
    working.setdefault(pack, []).append({
        "id": candidate.get("id"),
        "record_type": candidate.get("record_type", ""),
        "statement": candidate.get("statement", ""),
        "scope": candidate.get("scope", ""),
        "canonical_key": plan["canonical_key"],
        "merge_history": [],
    })


def plan_batch(existing_by_pack, candidates):
    """Classify a whole incoming batch with intra-batch awareness.

    classify() compares one candidate against a fixed existing-set. Mapping it over
    a batch against the *static* snapshot is blind to duplicates *within* the batch:
    two identical incoming candidates both score 'novel' and get inserted as twins,
    breaking the dedup/idempotency guarantee (spec/10). Here each candidate is
    classified against the snapshot PLUS the records projected by earlier candidates
    in the same batch, so the second of a pair dedups (merge) into the first."""
    working = {p: [dict(r) for r in recs] for p, recs in existing_by_pack.items()}
    plans = []
    for c in candidates:
        plan = classify(working, c)
        plans.append(plan)
        _project_candidate(working, plan, c)
    return plans


def apply_plan(existing_by_pack, candidates, plans, stamp):
    """Apply non-conflict plans, returning a new {pack:[records]} and a list of DriftRecords."""
    out = {p: [dict(r) for r in recs] for p, recs in existing_by_pack.items()}
    cand_by_id = {c.get("id"): c for c in candidates}
    drifts = []
    for plan in plans:
        pack, cid = plan["pack"], plan["candidate"]
        cand = cand_by_id.get(cid, {})
        if plan["action"] == "merge":
            for r in out.get(pack, []):
                if r.get("id") == plan["target"]:
                    r["repetition_count"] = int(r.get("repetition_count", 1)) + 1
                    refs = list(r.get("evidence_refs", []))
                    for ev in cand.get("evidence_refs", []):
                        if ev not in refs:
                            refs.append(ev)
                    r["evidence_refs"] = refs
                    mh = list(r.get("merge_history", []))
                    if cid not in mh:
                        mh.append(cid)
                    r["merge_history"] = mh
                    r["canonical_key"] = plan["canonical_key"]
                    try:
                        r["confidence"] = min(CONF_CAP, round(float(r.get("confidence", 0.8)) + CONF_BUMP, 4))
                    except Exception:
                        pass
                    r["updated_at"] = cand.get("updated_at", stamp)
                    break
        elif plan["action"] == "insert":
            rec = dict(cand)
            rec.setdefault("repetition_count", 1)
            rec["canonical_key"] = plan["canonical_key"]
            rec.setdefault("review_status", "confirmed")
            out.setdefault(pack, []).append(rec)
        elif plan["action"] == "supersede":
            rec = dict(cand)
            rec["supersedes"] = sorted(set(list(rec.get("supersedes", [])) + [plan["target"]]))
            rec.setdefault("repetition_count", 1)
            rec["canonical_key"] = plan["canonical_key"]
            rec.setdefault("review_status", "confirmed")
            out.setdefault(pack, []).append(rec)
            for r in out.get(pack, []):
                if r.get("id") == plan["target"]:
                    r["review_status"] = "narrowed"  # retired into the narrowed lineage
            drifts.append({
                "record_type": "SupersessionRecord", "superseded_id": plan["target"],
                "change_type": "supersession", "from_id": plan["target"], "to_id": cand.get("id"),
                "affected_pack": pack,
            })
        # already_merged / conflict / noop -> nothing applied
    return out, drifts


def main(argv=None):
    ap = argparse.ArgumentParser(description="Deterministic dedup-judge + upsert/supersede (spec/10).")
    ap.add_argument("instance", help="existing instance records (pack->[records] YAML/JSON)")
    ap.add_argument("incoming", help="incoming candidates (list or pack->[candidates] YAML/JSON)")
    ap.add_argument("--apply", action="store_true", help="apply the plan (else dry-run)")
    ap.add_argument("--out", help="when --apply, write the upserted record set here (.yaml/.json)")
    ap.add_argument("--json", action="store_true", help="emit the plan as JSON")
    ap.add_argument("--strict", action="store_true", help="exit nonzero if a conflict is surfaced")
    ap.add_argument("--stamp", default="1970-01-01T00:00:00Z", help="updated_at stamp for merges/inserts")
    args = ap.parse_args(argv)

    existing_by_pack = _records_by_pack(_load(args.instance))
    incoming_raw = _load(args.incoming)
    candidates = [r for recs in _records_by_pack(incoming_raw).values() for r in recs]

    plans = plan_batch(existing_by_pack, candidates)
    counts = {}
    for p in plans:
        counts[p["verdict"]] = counts.get(p["verdict"], 0) + 1

    if args.json:
        print(json.dumps({"plan": plans, "counts": counts}, ensure_ascii=False, indent=2))
    else:
        print("=" * 64)
        print("PAB MERGE — dedup judge + upsert plan  (spec/10-dedup-and-merge.md)")
        print("=" * 64)
        print(f"existing records : {sum(len(v) for v in existing_by_pack.values())}  "
              f"across {len([p for p in existing_by_pack if existing_by_pack[p]])} pack(s)")
        print(f"incoming         : {len(candidates)} candidate(s)")
        verdict_summary = ", ".join(f"{k}={v}" for k, v in sorted(counts.items())) or "(none)"
        print(f"verdicts         : {verdict_summary}")
        print("-" * 64)
        for p in plans:
            extra = f" sim={p['similarity']}" if "similarity" in p else ""
            tgt = f" -> {p['target']}" if p.get("target") else ""
            print(f"  [{p['verdict']:>13}] {p['action']:>9}  {p['candidate']}{tgt}{extra}")
        print("=" * 64)

    if args.apply:
        merged, drifts = apply_plan(existing_by_pack, candidates, plans, args.stamp)
        if drifts and not args.json:
            print(f"note: {len(drifts)} supersession(s) -> author a user.drift_history DriftRecord for each.")
        if args.out:
            payload = {p: merged[p] for p in CANONICAL_PACKS if merged.get(p)}
            payload.update({p: v for p, v in merged.items() if p not in CANONICAL_PACKS and v})
            with open(args.out, "w", encoding="utf-8") as fh:
                if args.out.endswith((".yaml", ".yml")):
                    if not _HAVE_YAML:
                        raise SystemExit("PyYAML required to write YAML output")
                    yaml.safe_dump(payload, fh, allow_unicode=True, sort_keys=False, default_flow_style=False)
                else:
                    json.dump(payload, fh, ensure_ascii=False, indent=2)
            print(f"applied -> {args.out}")

    if args.strict and counts.get("conflict"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
