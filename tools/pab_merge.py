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
import unicodedata

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

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
    # NFC 정규화 — 분해형(NFD) 한글/악센트는 결합 자모(가-힣 밖)라 그대로 두면 토큰이 통째로 사라져
    # 서로 다른 진술이 *빈 토큰셋*으로 충돌(같은 canonical_key → 잘못된 병합)한다(적대적 검증 it.13 HIGH).
    # 또 비문자열 입력에 .lower() 가 터지지 않게 str 로 강제한다.
    if not isinstance(s, str):
        s = "" if s is None else str(s)
    s = unicodedata.normalize("NFC", s).lower()
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
    parts = [str(pack or ""), str(record_type or ""), " ".join(_norm_tokens(statement)), _norm_scope(scope)]
    return hashlib.sha1("\x1f".join(parts).encode("utf-8")).hexdigest()[:12]


def identity_key(pack, record_type, statement):
    """Identity WITHOUT scope — same identity, different scope = refinement (spec/10 §5)."""
    parts = [str(pack or ""), str(record_type or ""), " ".join(_norm_tokens(statement))]
    return hashlib.sha1("\x1f".join(parts).encode("utf-8")).hexdigest()[:12]


def _as_ref_list(v):
    """evidence_refs 를 항상 리스트로 정규화 — 문자열 하나는 [그 문자열](문자 단위 분해 방지),
    리스트는 복사, 그 외(None·숫자 등)는 빈 리스트(적대적 검증 it.14)."""
    if isinstance(v, str):
        return [v]
    if isinstance(v, list):
        return list(v)
    return []


def _load(path):
    # 손상/비-UTF8/과중첩 입력은 추적역추적 대신 깔끔한 SystemExit 으로 보고한다(적대적 검증 it.14).
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except (OSError, UnicodeDecodeError) as exc:
        raise SystemExit(f"cannot read {path}: {exc}")
    parse_errors = (json.JSONDecodeError, RecursionError, ValueError)
    if _HAVE_YAML:
        parse_errors = parse_errors + (yaml.YAMLError,)
    try:
        if path.endswith((".yaml", ".yml")):
            if not _HAVE_YAML:
                raise SystemExit(f"PyYAML required to read {path} (pip install pyyaml)")
            return yaml.safe_load(text)
        return json.loads(text)
    except parse_errors as exc:
        raise SystemExit(f"cannot parse {path}: {exc}")


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


def _survivor_key(c):
    """중복/동일-identity 그룹에서 *결정론적 생존자*를 뽑기 위한 전순서 키(입력 순서 무관).

    같은 canonical_key(순수 중복) 또는 같은 identity(다른 scope refinement) 후보가 한 배치에 여럿
    오면, 첫-도착(입력 순서)이 아니라 (canonical_key, id) 최소값을 생존자로 고정한다 — 그래야 배치를
    셔플해도 같은 id 가 남고 나머지가 그쪽으로 병합돼 최종 집합이 입력 순서와 무관해진다(적대적 검증
    it.24; open-design-decisions 클러스터 1). 예제엔 intra-batch 중복 그룹이 없어 잠금값 불변."""
    pack = _pack_of_candidate(c)
    ck = canonical_key(pack, c.get("record_type", ""), c.get("statement", ""), c.get("scope", ""))
    return (ck, str(c.get("id", "")))


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
        # 정체성은 *내용*에서 파생한다(spec/10 §2: sha1(pack·type·norm(statement)·norm(scope))).
        # 저장된 canonical_key 는 출력/감사용 캐시일 뿐 — 매칭에 신뢰하면 stale 키가 (a) 진짜 중복을
        # 놓쳐 쌍둥이를 삽입(G1 위반)하거나 (b) 무관한 레코드에 잘못 병합(조용한 손상)한다. 항상 재계산. (it.15)
        r_ck = canonical_key(pack, r.get("record_type", ""), r.get("statement", ""), r.get("scope", ""))
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
        # record_type 누락(None)을 후보 기본값('')과 동일하게 정규화 — 위 duplicate/refinement 패스와 대칭.
        # bare r.get("record_type")(None) vs rt('') 비교는 untyped 레코드의 진짜 충돌을 놓친다. (it.15)
        if r.get("record_type", "") == rt and _norm_scope(r.get("scope", "")) == _norm_scope(scope):
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
    # _survivor_key 전순서로 처리 — 같은 그룹(중복·refinement)에서 canonical 생존자가 항상 먼저 투영돼
    # 나머지가 그쪽으로 병합된다. 결과 plan 목록은 이 정렬 순서이며 apply_plan 도 같은 키로 정렬해 짝짓는다.
    for c in sorted(candidates, key=_survivor_key):
        plan = classify(working, c)
        plans.append(plan)
        _project_candidate(working, plan, c)
    return plans


def apply_plan(existing_by_pack, candidates, plans, stamp):
    """Apply non-conflict plans, returning a new {pack:[records]} and a list of DriftRecords.

    plans 는 plan_batch 가 candidates 를 _survivor_key 전순서로 정렬해 1:1 로 만든다 — 여기서도 같은
    키로 정렬해 위치(zip)로 짝짓는다(둘이 동일 키를 쓰므로 순서가 일치). id 사전 매핑은 동일-id 후보
    (중복)에서 한쪽을 덮어써 데이터를 잃으므로 쓰지 않는다(적대적 검증 it.14; 정렬 결정론 it.24).
    """
    out = {p: [dict(r) for r in recs] for p, recs in existing_by_pack.items()}
    if len(plans) != len(candidates):
        raise ValueError(
            f"plans/candidates length mismatch ({len(plans)} vs {len(candidates)}); "
            "apply_plan expects the plan_batch output for exactly these candidates"
        )
    drifts = []
    for plan, cand in zip(plans, sorted(candidates, key=_survivor_key)):
        pack, cid = plan["pack"], plan["candidate"]
        if not isinstance(cand, dict):
            cand = {}
        if plan["action"] == "merge":
            for r in out.get(pack, []):
                if r.get("id") == plan["target"]:
                    try:
                        base = int(r.get("repetition_count", 1))
                    except (TypeError, ValueError, OverflowError):
                        base = 1  # 비정수·무한값 repetition_count 도 1 로 보고 진행(it.14; OverflowError it.15)
                    r["repetition_count"] = base + 1
                    refs = _as_ref_list(r.get("evidence_refs"))
                    for ev in _as_ref_list(cand.get("evidence_refs")):
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
                    # width=10**9: PyYAML 기본 width=80 은 긴 스칼라를 다음 줄로 접는데(folded
                    # continuation), 이 프로젝트의 번들 mini-YAML 파서(convergence_report/compile_adapter)는
                    # 접힌 스칼라를 못 읽어 그 파일을 통째로 None 으로 떨군다 → 머지→컴파일→수렴 파이프라인이
                    # 조용히 빈 인스턴스 집합이 된다. 쓰는 쪽이 자기 리더가 읽을 수 있는 형태로 내보낸다(it.20).
                    yaml.safe_dump(payload, fh, allow_unicode=True, sort_keys=False,
                                   default_flow_style=False, width=10**9)
                else:
                    json.dump(payload, fh, ensure_ascii=False, indent=2)
            print(f"applied -> {args.out}")

    if args.strict and counts.get("conflict"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
