#!/usr/bin/env python3
"""dedup_check.py — measure redundancy / pack proliferation in a subject's instance records.

Operationalizes spec/10-dedup-and-merge.md §7: records should be upserted (merged), not
duplicated. This is a dependency-light check (stdlib + optional PyYAML) that flags near-duplicate
records WITHIN a pack and reports three signals:

  redundancy_ratio = near-duplicate record pairs / total records      (lower is better, ->0)
  pack_cardinality = distinct instance packs / 14                      (target = 1.0; >1 = sprawl)
  merge_rate       = merges / (merges + inserts)                        (rising = convergence signal)
                     computed from repetition_count/merge_history when present (else NA)

"Near-duplicate" without embeddings: same (pack, record_type, scope) AND high token-overlap
(Jaccard >= THRESHOLD) on the normalized statement. This is a proxy for the embedding-based
judge described in spec/10 §2 — good enough to catch obvious bloat in a record set.

Usage:
  python tools/dedup_check.py examples/logotekton/
  python tools/dedup_check.py path/to/instance-records.yaml --threshold 0.8

Exit code is 0 always (this is a *signal*, not a gate); use --strict to exit nonzero when
redundancy_ratio > 0 or pack_cardinality > 1.
"""
import sys, os, json, re, argparse, glob

CANONICAL_PACKS = [
    "user.identity_roles", "user.persona_core", "user.communication_style",
    "user.artifact_policy", "user.decision_policy", "user.tacit_heuristics",
    "user.red_flags", "user.workflow_playbooks", "user.domain_overlays",
    "user.tool_stack", "user.boundary_authority", "user.memory_project_graph",
    "user.evaluation_cases", "user.drift_history",
]

# Each record_type belongs to exactly one canonical pack (spec/03-pack-catalog.md).
# Used to infer the pack for flat record lists (e.g. evaluation-cases.yaml) not keyed by
# pack name. No record_type is shared across packs.
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
RECORD_TYPE_TO_PACK = {rt: pack for pack, rts in _PACK_RECORD_TYPES.items() for rt in rts}

try:
    import yaml  # optional
    _HAVE_YAML = True
except Exception:
    _HAVE_YAML = False


def _load(path):
    """Return list of (pack, record) tuples from a YAML/JSON file.
    Accepts either a mapping keyed by pack name -> [records], or a flat list of records
    (pack taken from a 'pack'/'target_pack' field or inferred as 'unknown')."""
    text = open(path, encoding="utf-8").read()
    data = None
    if path.endswith((".yaml", ".yml")):
        if not _HAVE_YAML:
            return []  # silently skip yaml when PyYAML missing
        docs = [d for d in yaml.safe_load_all(text) if d]
        data = docs[0] if len(docs) == 1 else docs
    else:
        data = json.loads(text)
    out = []
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, list):
                for r in v:
                    if isinstance(r, dict):
                        out.append((k, r))
    elif isinstance(data, list):
        for r in data:
            if isinstance(r, dict):
                pack = (r.get("pack") or r.get("target_pack")
                        or RECORD_TYPE_TO_PACK.get(r.get("record_type"), "unknown"))
                out.append((pack, r))
    return out


def _norm(s):
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9가-힣\s]", " ", s)
    return [t for t in s.split() if t]


def _jaccard(a, b):
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / len(sa | sb) if (sa | sb) else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="instance-records file or a directory containing them")
    ap.add_argument("--threshold", type=float, default=0.8, help="Jaccard near-dup threshold")
    ap.add_argument("--strict", action="store_true", help="exit nonzero if redundancy/sprawl found")
    args = ap.parse_args()

    files = []
    if os.path.isdir(args.path):
        for ext in ("*.yaml", "*.yml", "*.json"):
            files += glob.glob(os.path.join(args.path, ext))
    else:
        files = [args.path]

    pairs = []  # (pack, record)
    for f in files:
        try:
            pairs += _load(f)
        except Exception as e:
            print(f"  (skip {os.path.basename(f)}: {e})")

    if not pairs:
        print("no instance records found (need a YAML mapping pack->[records] or a record list).")
        if not _HAVE_YAML:
            print("note: PyYAML not installed; only .json files were read.")
        return 0

    total = len(pairs)
    packs_seen = sorted({p for p, _ in pairs if p in CANONICAL_PACKS})
    noncanon = sorted({p for p, _ in pairs if p not in CANONICAL_PACKS})

    # near-duplicate pairs within same (pack, record_type, scope)
    buckets = {}
    for pack, r in pairs:
        key = (pack, r.get("record_type", ""), str(r.get("scope", "")))
        buckets.setdefault(key, []).append(r)

    dup_pairs = []
    for key, recs in buckets.items():
        toks = [(_norm(r.get("statement", "")), r) for r in recs]
        for i in range(len(toks)):
            for j in range(i + 1, len(toks)):
                sim = _jaccard(toks[i][0], toks[j][0])
                if sim >= args.threshold:
                    dup_pairs.append((key[0], toks[i][1].get("id"), toks[j][1].get("id"), round(sim, 2)))

    redundancy_ratio = round(len(dup_pairs) / total, 3) if total else 0.0
    # pack_cardinality: how many *distinct instance packs* exist for the subject vs the 14.
    # >1.0 means proliferation (non-canonical packs); here we approximate by distinct pack keys / 14.
    distinct_packs = len(packs_seen) + len(noncanon)
    pack_cardinality = round(distinct_packs / 14.0, 3)

    # merge_rate from the provenance trail (merge_history) OR the denormalized counter
    # (repetition_count), whichever records MORE merges. Trusting the stored counter alone lets a
    # stale/empty merge_history — or an inflated counter — misreport convergence (적대적 검증 it.16).
    # spec/10 §4: repetition_count = 1 + len(merge_history), so on a clean set the two agree.
    def _merge_count(r):
        mh = r.get("merge_history")
        n_mh = len(mh) if isinstance(mh, list) else 0
        try:
            rc = int(r.get("repetition_count", 1)) - 1
        except (TypeError, ValueError, OverflowError):
            rc = 0  # 비정수/무한 카운터는 무시하고 provenance(merge_history)에 맡긴다
        return max(0, n_mh, rc)
    merges = sum(_merge_count(r) for _, r in pairs)
    inserts = total
    merge_rate = round(merges / (merges + inserts), 3) if (merges + inserts) else 0.0
    has_merge_data = any(("repetition_count" in r or "merge_history" in r) for _, r in pairs)

    print("=" * 60)
    print("DEDUP / REDUNDANCY CHECK  (spec/10-dedup-and-merge.md §7)")
    print("=" * 60)
    print(f"records scanned     : {total}  across {distinct_packs} pack(s)")
    print(f"redundancy_ratio    : {redundancy_ratio:>6}   (near-dup pairs {len(dup_pairs)} / {total}; lower→better)")
    print(f"pack_cardinality    : {pack_cardinality:>6}   (distinct packs {distinct_packs} / 14; =1.0 ideal, >1 sprawl)")
    print(f"merge_rate          : {('  ' + str(merge_rate)) if has_merge_data else '    NA'}   (rising = convergence; from merge_history/repetition_count)")
    if noncanon:
        print(f"non-canonical packs : {noncanon}  <-- not one of the 14; fold into a canonical pack")
    if dup_pairs:
        print("\nnear-duplicate pairs (merge candidates):")
        for pack, a, b, sim in dup_pairs:
            print(f"  [{pack}] {a}  ~~  {b}   (jaccard {sim}) -> consider `merge`")
    else:
        print("\nno near-duplicates above threshold — clean.")
    print("=" * 60)

    if args.strict and (redundancy_ratio > 0 or pack_cardinality > 1.0):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
