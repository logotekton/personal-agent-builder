#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tests/test_tools.py — regression lock for the deterministic Personal Agent Builder tools.

> **EN:** stdlib-only (unittest) regression tests that LOCK every number the project's claims
> rest on. The repo's whole thesis is "becoming me is a number you watch climb" and "every
> figure is reproduced by the commands" — so these tests pin those figures so a future change
> cannot silently move them:
>   - tools/pab_merge.py       — canonical_key determinism, the four verdicts (novel/duplicate/
>                                refinement/conflict → insert/merge/supersede/surface), idempotence,
>                                and the safety invariant (conflict is NEVER auto-applied).
>   - tools/convergence_report.py — the six indices + maturity tier on the logotekton example
>                                (L2; coverage 0.714; decision_fidelity 1.0; correction_cost 0.0833;
>                                drift_stability 0.8947; traceability 1.0).
>   - tools/validate_packs.py  — gate checks (G1 evidence, G2 scope, confidence range,
>                                counterexamples<0.7) accept good records and reject bad ones.
>   - tools/dedup_check.py     — merge_rate on the example (0.095).
>   - end-to-end: examples/logotekton validates (42 records PASS) and the revolution .pre fixtures
>                                reproduce their documented merge/insert/conflict plans.

순수 표준 라이브러리(unittest) 회귀 테스트. 프로젝트가 의존하는 *모든 숫자*를 잠가, 미래의 변경이
그 숫자를 조용히 움직이지 못하게 한다. PyYAML이 있으면 더 많은 경로를 검사하고, 없으면 미니-YAML
파서를 쓰는 convergence_report 경로만으로도 핵심 지표를 검증한다.

Run:  python3 -m unittest discover -s tests   (또는)  python3 tests/test_tools.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(REPO, "tools")
EXAMPLE = os.path.join(REPO, "examples", "logotekton")
sys.path.insert(0, TOOLS)

import pab_merge          # noqa: E402
import convergence_report as cr   # noqa: E402
import validate_packs as vp       # noqa: E402
import check_anchors as ca        # noqa: E402
import context_select as cs        # noqa: E402
import compile_adapter as comp     # noqa: E402

try:
    import yaml  # noqa: F401
    HAVE_YAML = True
except Exception:
    HAVE_YAML = False


def almost(a, b, places=4):
    return round(a - b, places) == 0


# ───────────────────────── pab_merge: identity keys ─────────────────────────
class TestCanonicalKey(unittest.TestCase):
    def test_deterministic(self):
        k1 = pab_merge.canonical_key("user.tacit_heuristics", "HeuristicRecord", "Do the thing.", "work")
        k2 = pab_merge.canonical_key("user.tacit_heuristics", "HeuristicRecord", "Do the thing.", "work")
        self.assertEqual(k1, k2)
        self.assertEqual(len(k1), 12)

    def test_normalization_stable(self):
        # case / punctuation / extra whitespace must not change the key
        a = pab_merge.canonical_key("p", "T", "Do the THING!!!", "s")
        b = pab_merge.canonical_key("p", "T", "do   the thing", "s")
        self.assertEqual(a, b)

    def test_scope_changes_key_but_not_identity(self):
        ck1 = pab_merge.canonical_key("p", "T", "same statement", "scope-a")
        ck2 = pab_merge.canonical_key("p", "T", "same statement", "scope-b")
        self.assertNotEqual(ck1, ck2)  # scope is part of canonical_key
        ik1 = pab_merge.identity_key("p", "T", "same statement")
        ik2 = pab_merge.identity_key("p", "T", "same statement")
        self.assertEqual(ik1, ik2)     # identity ignores scope

    def test_known_value_locked(self):
        # The logotekton example stores canonical_key 3cabb5142158 for heuristic.001;
        # lock the exact normalization so a refactor cannot silently shift stored keys.
        ck = pab_merge.canonical_key(
            "user.tacit_heuristics", "HeuristicRecord",
            "If tools are available and the request is operational, perform the concrete action and report the actual result.",
            "opencrab_work")
        self.assertEqual(ck, "3cabb5142158")


# ───────────────────────── pab_merge: the four verdicts ─────────────────────
def _existing():
    base = {
        "id": "x.h.001", "record_type": "HeuristicRecord",
        "statement": "the agent should always confirm before sending external email",
        "scope": "email", "evidence_refs": ["e1"], "repetition_count": 1, "confidence": 0.8,
    }
    return {"user.tacit_heuristics": [dict(base)]}


def _cand(**kw):
    c = {"id": "x.h.900", "record_type": "HeuristicRecord",
         "statement": "the agent should always confirm before sending external email",
         "scope": "email", "evidence_refs": ["e2"]}
    c.update(kw)
    return c


class TestVerdicts(unittest.TestCase):
    def test_duplicate_merges(self):
        p = pab_merge.classify(_existing(), _cand())
        self.assertEqual(p["verdict"], "duplicate")
        self.assertEqual(p["action"], "merge")
        self.assertEqual(p["target"], "x.h.001")

    def test_novel_inserts(self):
        p = pab_merge.classify(_existing(), _cand(statement="use ripgrep for fast code search across the repo"))
        self.assertEqual(p["verdict"], "novel")
        self.assertEqual(p["action"], "insert")

    def test_refinement_supersedes(self):
        # same identity (same normalized statement), different scope
        p = pab_merge.classify(_existing(), _cand(scope="external_email"))
        self.assertEqual(p["verdict"], "refinement")
        self.assertEqual(p["action"], "supersede")

    def test_conflict_surfaces(self):
        # same type+scope, similar-but-not-equal statement (Jaccard in [0.5, 0.85))
        p = pab_merge.classify(
            _existing(),
            _cand(statement="the agent should always confirm before sending external email or messages"))
        self.assertEqual(p["verdict"], "conflict")
        self.assertEqual(p["action"], "surface")
        self.assertTrue(0.5 <= p["similarity"] < 0.85)

    def test_already_merged_is_noop(self):
        # a candidate already named in merge_history is idempotent
        ex = _existing()
        ex["user.tacit_heuristics"][0]["merge_history"] = ["x.h.900"]
        p = pab_merge.classify(ex, _cand())
        self.assertEqual(p["verdict"], "already_merged")
        self.assertEqual(p["action"], "noop")


# ───────────────────────── pab_merge: apply + safety ────────────────────────
class TestApplyPlan(unittest.TestCase):
    def test_merge_accumulates_not_duplicates(self):
        ex = _existing()
        cands = [_cand()]
        plans = [pab_merge.classify(ex, cands[0])]
        out, drifts = pab_merge.apply_plan(ex, cands, plans, "2026-01-01T00:00:00Z")
        recs = out["user.tacit_heuristics"]
        self.assertEqual(len(recs), 1)                       # no twin record
        self.assertEqual(recs[0]["repetition_count"], 2)     # rep++
        self.assertIn("e2", recs[0]["evidence_refs"])        # evidence union
        self.assertIn("x.h.900", recs[0]["merge_history"])

    def test_insert_adds_record(self):
        ex = _existing()
        cands = [_cand(id="x.h.901", statement="prefer subprocess.run over os.system for shelling out")]
        plans = [pab_merge.classify(ex, cands[0])]
        out, _ = pab_merge.apply_plan(ex, cands, plans, "2026-01-01T00:00:00Z")
        self.assertEqual(len(out["user.tacit_heuristics"]), 2)

    def test_conflict_is_never_applied(self):
        ex = _existing()
        cands = [_cand(id="x.h.902",
                       statement="the agent should always confirm before sending external email or messages")]
        plans = [pab_merge.classify(ex, cands[0])]
        self.assertEqual(plans[0]["action"], "surface")
        out, _ = pab_merge.apply_plan(ex, cands, plans, "2026-01-01T00:00:00Z")
        ids = [r["id"] for r in out["user.tacit_heuristics"]]
        self.assertNotIn("x.h.902", ids)                     # SAFETY: conflict not written
        self.assertEqual(len(out["user.tacit_heuristics"]), 1)

    def test_supersede_retires_old_and_emits_drift(self):
        ex = _existing()
        cands = [_cand(id="x.h.903", scope="external_email")]
        plans = [pab_merge.classify(ex, cands[0])]
        out, drifts = pab_merge.apply_plan(ex, cands, plans, "2026-01-01T00:00:00Z")
        recs = {r["id"]: r for r in out["user.tacit_heuristics"]}
        self.assertIn("x.h.903", recs)
        self.assertIn("x.h.001", recs["x.h.903"].get("supersedes", []))
        self.assertEqual(recs["x.h.001"]["review_status"], "narrowed")  # old retired
        self.assertEqual(len(drifts), 1)

    def test_idempotent_reapply(self):
        ex = _existing()
        cands = [_cand()]
        plans = [pab_merge.classify(ex, cands[0])]
        merged, _ = pab_merge.apply_plan(ex, cands, plans, "2026-01-01T00:00:00Z")
        # feed the SAME candidate against the merged set → already_merged (noop)
        p2 = pab_merge.classify(merged, cands[0])
        self.assertEqual(p2["verdict"], "already_merged")


# ───────────────────────── validate_packs: gates ───────────────────────────
def _good():
    return {
        "id": "x.r.001", "record_type": "HeuristicRecord", "label": "ok",
        "statement": "do the thing", "evidence_refs": ["e1"], "confidence": 0.9,
        "scope": "work", "review_status": "confirmed", "sensitivity": "internal",
        "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z",
    }


class TestValidateGates(unittest.TestCase):
    def test_good_record_passes(self):
        self.assertTrue(vp.validate_record(_good(), "t").ok)

    def test_g1_empty_evidence_fails(self):
        r = _good(); r["evidence_refs"] = []
        self.assertFalse(vp.validate_record(r, "t").ok)

    def test_g2_empty_scope_fails(self):
        r = _good(); r["scope"] = "  "
        self.assertFalse(vp.validate_record(r, "t").ok)

    def test_confidence_out_of_range_fails(self):
        r = _good(); r["confidence"] = 1.5
        self.assertFalse(vp.validate_record(r, "t").ok)

    def test_low_confidence_requires_counterexamples(self):
        r = _good(); r["confidence"] = 0.5
        self.assertFalse(vp.validate_record(r, "t").ok)   # missing counterexamples
        r["counterexamples"] = ["here it does not hold"]
        self.assertTrue(vp.validate_record(r, "t").ok)

    def test_missing_required_field_fails(self):
        r = _good(); del r["statement"]
        self.assertFalse(vp.validate_record(r, "t").ok)

    def test_bad_enum_fails(self):
        r = _good(); r["review_status"] = "approved"  # not in enum
        self.assertFalse(vp.validate_record(r, "t").ok)


def _good_eval():
    r = _good()
    r["id"] = "x.evalcase.001"
    r["record_type"] = "EvaluationCaseRecord"
    r["scoring_rubric"] = {
        "criteria": [
            {"check": "a", "weight": 0.6, "kind": "must"},
            {"check": "b", "weight": 0.4, "kind": "prefer"},
        ],
        "pass_threshold": 0.8,
        "judge": "human",
    }
    r["result"] = {"status": "pass", "score": 0.9}
    return r


class TestEvalIntegrity(unittest.TestCase):
    """#3: a recorded eval verdict must be self-consistent with its own rubric (validate gate)."""

    def test_consistent_eval_passes(self):
        self.assertTrue(vp.validate_record(_good_eval(), "t").ok)

    def test_pass_below_threshold_fails(self):
        # the headline catch: a human typed status=pass while the rubric score says fail
        r = _good_eval(); r["result"]["score"] = 0.5
        res = vp.validate_record(r, "t")
        self.assertFalse(res.ok)
        self.assertTrue(any("status=pass" in e for e in res.errors), res.errors)

    def test_weight_sum_not_one_fails(self):
        r = _good_eval(); r["scoring_rubric"]["criteria"][0]["weight"] = 0.9  # 0.9 + 0.4 = 1.3
        res = vp.validate_record(r, "t")
        self.assertFalse(res.ok)
        self.assertTrue(any("가중치 합" in e for e in res.errors), res.errors)

    def test_hardfail_must_be_fail(self):
        r = _good_eval(); r["result"]["unacceptable_fired"] = ["leaked a secret"]  # but status=pass
        res = vp.validate_record(r, "t")
        self.assertFalse(res.ok)
        self.assertTrue(any("하드페일" in e for e in res.errors), res.errors)

    def test_hardfail_with_fail_status_is_consistent(self):
        r = _good_eval()
        r["result"] = {"status": "fail", "score": 0.9, "unacceptable_fired": ["x"]}
        self.assertTrue(vp.validate_record(r, "t").ok)  # hard-fail sinks a high score → fail is right

    def test_llm_judge_requires_determinism_config(self):
        r = _good_eval(); r["scoring_rubric"]["judge"] = "llm_judge"
        res = vp.validate_record(r, "t")
        self.assertFalse(res.ok)
        self.assertTrue(any("judge_config" in e for e in res.errors), res.errors)
        r["scoring_rubric"]["judge_config"] = {"model": "claude-opus-4-8", "temperature": 0}
        self.assertTrue(vp.validate_record(r, "t").ok)


class TestReviewAudit(unittest.TestCase):
    """#8: review_audit makes a real review mechanically distinguishable from a rubber-stamp."""

    def test_absent_passes_by_default(self):
        # default does NOT require audit — so the worked example needn't fabricate review metadata
        self.assertTrue(vp.validate_record(_good(), "t").ok)

    def test_absent_fails_when_required(self):
        res = vp.validate_record(_good(), "t", require_audit=True)
        self.assertFalse(res.ok)
        self.assertTrue(any("review_audit" in e for e in res.errors), res.errors)

    def test_valid_audit_passes_even_when_required(self):
        r = _good()
        r["review_audit"] = {
            "reviewer_id": "logotekton", "decision": "edit",
            "decided_at": "2026-06-28T00:00:00Z", "diff": "before->after",
        }
        self.assertTrue(vp.validate_record(r, "t", require_audit=True).ok)

    def test_audit_missing_reviewer_fails(self):
        r = _good(); r["review_audit"] = {"decision": "confirm"}  # who decided?
        self.assertFalse(vp.validate_record(r, "t").ok)

    def test_audit_bad_decision_enum_fails(self):
        r = _good(); r["review_audit"] = {"reviewer_id": "x", "decision": "approve"}
        self.assertFalse(vp.validate_record(r, "t").ok)


# ───────────────────────── convergence: locked example numbers ─────────────
class TestConvergenceExample(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pack_records, eval_cases, drift_records, n = cr.collect(EXAMPLE)
        cls.ix = cr.compute_indices(pack_records, eval_cases, drift_records)
        cls.tier, cls.tname, _ = cr.maturity_tier(cls.ix)
        cls.n_files = n

    def test_maturity_is_L1(self):
        # gate keys on coverage = strict depth (spec §2). logotekton has depth in only 1 pack
        # (evaluation_cases), so it is honestly L1 Sketch (broad, shallow) — not L2 Working.
        self.assertEqual(self.tier, "L1")

    def test_six_indices_locked(self):
        ix = self.ix
        # coverage IS the strict (≥3 depth) value now — the gate uses spec §2's definition
        self.assertTrue(almost(ix["coverage"], 0.071428, 3), ix["coverage"])
        self.assertTrue(almost(ix["coverage_strict"], 0.071428, 3), ix["coverage_strict"])
        self.assertTrue(almost(ix["coverage_seeded"], 0.714285, 3), ix["coverage_seeded"])
        self.assertEqual(ix["confirmation_ratio"], 1.0)
        self.assertEqual(ix["human_confirmation_ratio"], 1.0)  # example has 0 auto-confirm
        self.assertEqual(ix["decision_fidelity"], 1.0)
        self.assertTrue(almost(ix["correction_cost"], 0.083333, 4), ix["correction_cost"])
        self.assertTrue(almost(ix["drift_stability"], 0.894736, 4), ix["drift_stability"])
        self.assertEqual(ix["traceability"], 1.0)

    def test_counts_locked(self):
        ix = self.ix
        self.assertEqual(ix["_seeded_packs"], 10)
        self.assertEqual(ix["_n_confirmed"], 19)
        self.assertEqual(ix["_n_auto_confirmed"], 0)
        self.assertEqual(ix["_n_human_confirmed"], 19)
        self.assertEqual(ix["_supersessions"], 2)
        self.assertEqual((ix["_eval_pass"], ix["_eval_partial"], ix["_eval_fail"]), (6, 0, 0))

    def test_correction_cost_NA_blocks_L3_helper(self):
        # the le() helper must treat NA (None) as NOT passing the gate
        _, _, reasons = cr.maturity_tier({**self.ix, "correction_cost": None})
        self.assertFalse(reasons["L3_correction_cost<=0.3"])

    def test_only_L2_blocker_is_coverage(self):
        # decision_fidelity (1.0) and human_confirmation_ratio (1.0) pass L2; the sole gap is the
        # strict-coverage gate (0.07 < 0.5) — i.e. the agent lacks DEPTH, exactly as de-averaging says.
        _, _, reasons = cr.maturity_tier(self.ix)
        unmet = [k for k, ok in reasons.items() if k.startswith("L2_") and not ok]
        self.assertEqual(unmet, ["L2_coverage>=0.5"])

    def test_example_has_one_vertical(self):
        # the example's single deep pack (evaluation_cases, 6 confirmed) is what keeps it at L1+
        self.assertEqual(self.ix["_packs_with_3"], 1)

    def test_l1_requires_depth_not_just_breadth(self):
        # #7: 7 packs each seeded with 1 record (no depth) must NOT reach L1 (breadth-gaming blocked)
        base = {
            "coverage": 0.5, "confirmation_ratio": 1.0, "human_confirmation_ratio": 1.0,
            "decision_fidelity": 0.9, "correction_cost": 0.1, "drift_stability": 1.0,
            "traceability": 1.0, "_seeded_packs": 7, "_packs_with_3": 0, "_n_eval": 3,
        }
        tier, _, reasons = cr.maturity_tier(base)
        self.assertFalse(reasons["L1_vertical>=1 (한 팩 ≥3 확인)"])
        self.assertEqual(tier, "L0")  # stuck at L0 despite 7 seeded packs
        # one pack with ≥3 confirmed (a "vertical") opens the ladder
        tier2, _, _ = cr.maturity_tier({**base, "_packs_with_3": 1})
        self.assertIn(tier2, ("L1", "L2"))


class TestHumanConfirmationRatio(unittest.TestCase):
    """spec/12 §4.4 circularity break: auto-confirm must NOT inflate the maturity gate (#4)."""

    def test_auto_confirm_excluded_from_human_ratio(self):
        # 1 human-confirmed + 5 auto-confirmed + 2 human-rejected, all in one pack
        recs = {"user.identity_roles": (
            [{"review_status": "confirmed"}]
            + [{"review_status": "confirmed", "auto_confirmed": True}] * 5
            + [{"review_status": "rejected"}] * 2
        )}
        ix = cr.compute_indices(recs, [], [])
        self.assertEqual(ix["_n_confirmed"], 6)
        self.assertEqual(ix["_n_auto_confirmed"], 5)
        self.assertEqual(ix["_n_human_confirmed"], 1)
        # confirmation_ratio counts auto-confirms → looks healthy (0.75)
        self.assertAlmostEqual(ix["confirmation_ratio"], 6 / 8)
        # human-only ratio tells the truth: only 1 of 3 HUMAN-gated decisions was a confirm
        self.assertAlmostEqual(ix["human_confirmation_ratio"], 1 / 3)

    def test_gate_blocks_self_certification(self):
        # confirmation_ratio 0.75 would pass L2, but the human stream (0.30) must not →
        # the gate reads human_confirmation_ratio, so auto-confirm cannot unlock its own maturity.
        base = {
            "coverage": 0.6, "confirmation_ratio": 0.75, "human_confirmation_ratio": 0.30,
            "decision_fidelity": 0.9, "correction_cost": 0.1, "drift_stability": 0.9,
            "traceability": 1.0, "_seeded_packs": 8, "_packs_with_3": 8, "_n_eval": 3,
        }
        tier, _, reasons = cr.maturity_tier(base)
        self.assertFalse(reasons["L2_human_confirmation_ratio>=0.6"])
        self.assertNotEqual(tier, "L2")  # blocked despite confirmation_ratio 0.75
        # had the same confirms been human-gated (hcr 0.75), L2 legitimately opens
        tier2, _, _ = cr.maturity_tier({**base, "human_confirmation_ratio": 0.75})
        self.assertEqual(tier2, "L2")


class TestReliabilityTier(unittest.TestCase):
    """Designer decision C / claim-layer #1: self_reported is a low-trust, draft-only channel
    that must not be auto-confirmed and must not earn maturity DEPTH (only behavioral does)."""

    # --- validate_packs enforcement ---
    def test_behavioral_default_passes(self):
        r = _good(); r["reliability"] = "behavioral"
        self.assertTrue(vp.validate_record(r, "t").ok)

    def test_self_reported_alone_passes(self):
        # a human-confirmed self-report is allowed to EXIST (carried signal) — just low-trust
        r = _good(); r["reliability"] = "self_reported"
        self.assertTrue(vp.validate_record(r, "t").ok)

    def test_bad_reliability_enum_fails(self):
        r = _good(); r["reliability"] = "hearsay"
        self.assertFalse(vp.validate_record(r, "t").ok)

    def test_self_reported_cannot_be_auto_confirmed(self):
        # the headline rule: a self-description can't be machine-promoted past the human gate
        r = _good(); r["reliability"] = "self_reported"; r["auto_confirmed"] = True
        res = vp.validate_record(r, "t")
        self.assertFalse(res.ok)
        self.assertTrue(any("self_reported" in e for e in res.errors), res.errors)

    def test_behavioral_can_be_auto_confirmed(self):
        r = _good(); r["reliability"] = "behavioral"; r["auto_confirmed"] = True
        self.assertTrue(vp.validate_record(r, "t").ok)

    def test_auto_confirmed_must_be_boolean(self):
        # M2: a string "true" must NOT pass validation — else it bypasses the self_reported ban
        # while convergence still reads it as auto-confirmed (validator/convergence drift).
        r = _good(); r["auto_confirmed"] = "true"
        self.assertFalse(vp.validate_record(r, "t").ok)

    def test_self_reported_string_auto_confirm_is_caught(self):
        # the headline ban must not be evadable via a truthy string
        r = _good(); r["reliability"] = "self_reported"; r["auto_confirmed"] = "auto"
        res = vp.validate_record(r, "t")
        self.assertFalse(res.ok)
        self.assertTrue(any("self_reported" in e for e in res.errors), res.errors)

    # --- convergence: maturity DEPTH counts behavioral confirmed only ---
    def test_self_reported_does_not_count_toward_depth(self):
        # 3 confirmed but all self_reported → NOT a vertical; depth must stay 0 (draft-only)
        recs = {"user.persona_core": [
            {"review_status": "confirmed", "reliability": "self_reported"} for _ in range(3)
        ]}
        ix = cr.compute_indices(recs, [], [])
        self.assertEqual(ix["_n_self_reported"], 3)
        self.assertEqual(ix["_packs_with_3"], 0)       # no behavioral depth
        # C1: self_reported is excluded from ALL maturity aggregates, not just depth — so the
        # behavioral confirmed count is 0 here (it must NOT feed confirmation_ratio/hcr/drift).
        self.assertEqual(ix["_n_confirmed"], 0)

    def test_self_reported_excluded_from_all_maturity_indices(self):
        # C1 back door (adversarial finding): self_reported must move NONE of the gate-driving
        # indices — not hcr, not confirmation_ratio, not drift_stability, not traceability, not
        # coverage. Build a behavioral baseline, flood it with 20 confirmed self_reports, assert
        # every index is byte-identical.
        behavioral = (
            [{"review_status": "confirmed", "evidence_refs": ["e"]} for _ in range(5)]
            + [{"review_status": "pending"} for _ in range(5)]
        )
        drift = [{"supersedes": ["a"]}]
        base_ix = cr.compute_indices({"user.persona_core": list(behavioral)}, [], drift)
        flooded = behavioral + [
            {"review_status": "confirmed", "reliability": "self_reported", "evidence_refs": ["e"]}
            for _ in range(20)
        ]
        flood_ix = cr.compute_indices({"user.persona_core": flooded}, [], drift)
        for k in ("confirmation_ratio", "human_confirmation_ratio", "drift_stability",
                  "traceability", "coverage", "_n_confirmed"):
            self.assertEqual(flood_ix[k], base_ix[k], f"{k} moved when self_reported was added")
        self.assertEqual(flood_ix["_n_self_reported"], 20)
        self.assertEqual(flood_ix["_n_confirmed"], 5)   # behavioral only

    def test_behavioral_confirmed_counts_toward_depth(self):
        recs = {"user.persona_core": [
            {"review_status": "confirmed"} for _ in range(3)   # behavioral by default
        ]}
        ix = cr.compute_indices(recs, [], [])
        self.assertEqual(ix["_packs_with_3"], 1)
        self.assertEqual(ix["_n_self_reported"], 0)

    def test_mixed_pack_counts_only_behavioral_for_depth(self):
        # 2 behavioral + 2 self_reported confirmed → behavioral depth = 2 < 3 → not a vertical
        recs = {"user.persona_core":
            [{"review_status": "confirmed"} for _ in range(2)]
            + [{"review_status": "confirmed", "reliability": "self_reported"} for _ in range(2)]
        }
        ix = cr.compute_indices(recs, [], [])
        self.assertEqual(ix["_packs_with_3"], 0)
        self.assertEqual(ix["_behavioral_confirmed_by_pack"]["user.persona_core"], 2)

    def test_self_reported_eval_and_drift_excluded(self):
        # N1 (adversarial re-verify): the "all six indices" claim must be literally true.
        # (a) a self_reported eval case must NOT inflate decision_fidelity (a hard L2/L3/L4 gate):
        # 1 behavioral FAIL + 4 self_reported PASS → fidelity 0.0 (behavioral only), not 0.8.
        evals = (
            [{"result": {"status": "fail"}}]
            + [{"result": {"status": "pass"}, "reliability": "self_reported"} for _ in range(4)]
        )
        ix = cr.compute_indices({}, evals, [])
        self.assertEqual(ix["decision_fidelity"], 0.0)
        self.assertEqual(ix["_n_eval"], 1)            # only the behavioral eval counts
        # (b) a self_reported drift record must NOT move drift_stability either
        behavioral = {"user.persona_core": [
            {"review_status": "confirmed", "evidence_refs": ["e"]} for _ in range(4)]}
        base = cr.compute_indices(behavioral, [], [])
        withsr = cr.compute_indices(behavioral, [],
                                    [{"supersedes": ["x"], "reliability": "self_reported"}])
        self.assertEqual(base["drift_stability"], withsr["drift_stability"])

    def test_self_reported_only_pack_does_not_count_as_seeded(self):
        # N2 (adversarial re-verify): a pack seeded with ONLY self_reports has no behavioral
        # evidence, so it must not satisfy the L1 breadth gate (seeded>=7). Breadth is behavioral
        # breadth — otherwise "maturity is measured only on observed behavior" would be false.
        recs = {"user.persona_core": [
                    {"review_status": "confirmed", "evidence_refs": ["e"]} for _ in range(3)]}
        for p in ["user.identity_roles", "user.communication_style", "user.artifact_policy",
                  "user.decision_policy", "user.tacit_heuristics", "user.red_flags"]:
            recs[p] = [{"review_status": "confirmed", "reliability": "self_reported",
                        "evidence_refs": ["e"]}]
        ix = cr.compute_indices(recs, [], [])
        self.assertEqual(ix["_seeded_packs"], 1)   # only the behavioral pack counts as seeded

    def test_example_has_no_self_reported(self):
        # locks that the worked example is all-behavioral, so the C change preserves every number
        pack_records, eval_cases, drift_records, _ = cr.collect(EXAMPLE)
        ix = cr.compute_indices(pack_records, eval_cases, drift_records)
        self.assertEqual(ix["_n_self_reported"], 0)


class TestCandidateSkip(unittest.TestCase):
    """validate_packs skips candidate files (candidate.schema.json), never FAILs them as base records."""

    def test_candidate_record_detected(self):
        cand = {"candidate_id": "x.decision_cand.001", "candidate_type": "DecisionPolicyCandidate",
                "validation_status": "pending"}
        self.assertTrue(vp._is_candidate(cand))

    def test_candidate_by_id_and_status_alone(self):
        self.assertTrue(vp._is_candidate({"candidate_id": "x.h.001", "validation_status": "pending"}))

    def test_base_record_is_not_candidate(self):
        self.assertFalse(vp._is_candidate(_good()))

    @unittest.skipUnless(HAVE_YAML, "PyYAML needed to parse the candidate fixture")
    def test_candidate_only_file_is_skipped_not_failed(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "cands.yaml")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write("candidates:\n"
                         "  - candidate_id: x.decision_cand.001\n"
                         "    candidate_type: DecisionPolicyCandidate\n"
                         "    validation_status: pending\n")
            results, msgs = vp.validate_file(p)
        self.assertEqual(results, [])  # not validated as base records (no FAIL)
        self.assertTrue(any("후보" in m and "건너뜀" in m for m in msgs), msgs)
        self.assertTrue(all(vp._is_skip_message(m) for m in msgs))  # counts as SKIP, not FILE-ERROR


# ───────────────────────── end-to-end CLI (subprocess) ─────────────────────
def _run(*args):
    return subprocess.run([sys.executable, *args], cwd=REPO, capture_output=True, text=True)


@unittest.skipUnless(HAVE_YAML, "PyYAML needed for the full recursive validate/dedup CLI run")
class TestEndToEnd(unittest.TestCase):
    def test_validate_packs_42_pass(self):
        r = _run("tools/validate_packs.py", "examples/logotekton")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PASS 42", r.stdout)
        self.assertIn("FAIL 0", r.stdout)

    def test_dedup_merge_rate_locked(self):
        r = _run("tools/dedup_check.py", "examples/logotekton")
        self.assertIn("0.095", r.stdout)

    def test_convergence_report_cli_directory_form(self):
        # the single-directory form documented in tools/README §2, CONTRIBUTING, QUICKSTART and CI
        # (the broken two-file / --subject / no-arg forms are what this guards against). Locks that
        # the documented command runs AND prints the tier/coverage the README now advertises.
        r = _run("tools/convergence_report.py", "examples/logotekton")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("L1 Sketch", r.stdout)   # honest: gate on strict coverage (depth)
        self.assertIn("0.07", r.stdout)        # coverage = strict (spec §2), not the 0.71 breadth

    def test_documented_commands_all_run(self):
        # every safe, read-only command printed in the docs must actually run (the it.13 bug class:
        # a documented invocation that errors). check_commands.py runs them and fails on any break.
        r = _run("tools/check_commands.py", ".")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("0 broken", r.stdout)

    def test_rev02_pre_reproduces_four_verdicts(self):
        r = _run("tools/pab_merge.py",
                 "examples/logotekton/revolution-02/instance-records.pre.yaml",
                 "examples/logotekton/revolution-02/session-03-candidates.yaml")
        out = r.stdout
        self.assertIn("duplicate", out)
        self.assertIn("novel", out)
        self.assertIn("conflict", out)
        self.assertIn("surface", out)

    def test_rev01_pre_reproduces_merge_insert(self):
        r = _run("tools/pab_merge.py",
                 "examples/logotekton/revolution-01/instance-records.pre.yaml",
                 "examples/logotekton/revolution-01/session-02-candidates.yaml")
        self.assertIn("duplicate", r.stdout)
        self.assertIn("novel", r.stdout)


class TestAnchorSlug(unittest.TestCase):
    """Lock the GitHub-slug algorithm on the exact cases this repo's links depend on."""

    def test_colon_one_to_one_collapses(self):
        # "(1:1, 전수)" -> the heading slug used by spec/01 §6 and skills/08 §3
        self.assertEqual(ca.gh_slug("3. 라우팅 표 (1:1, 전수)"), "3-라우팅-표-11-전수")

    def test_symbol_between_spaces_yields_double_hyphen(self):
        # a symbol dropped from between two spaces leaves two spaces -> two hyphens
        self.assertEqual(ca.gh_slug("6. 후보 타입 ↔ 라우팅 (1:1 전수)"),
                         "6-후보-타입--라우팅-11-전수")

    def test_middle_dot_is_removed_not_hyphenated(self):
        self.assertEqual(ca.gh_slug("9. 프라이버시·권한 모델 (요약)"), "9-프라이버시권한-모델-요약")


class TestAnchorIntegrity(unittest.TestCase):
    """The repo's cross-document links are a claim; this gate keeps them true."""

    def test_repo_has_no_broken_anchors(self):
        r = _run("tools/check_anchors.py", ".")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("0 broken", r.stdout)

    def test_checker_actually_catches_a_break(self):
        # prove the guard guards: a planted bad anchor must make it exit nonzero
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "a.md"), "w", encoding="utf-8") as fh:
                fh.write("# Hello World\n\n[bad](#does-not-exist)\n[good](#hello-world)\n")
            r = _run("tools/check_anchors.py", d)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("1 broken", r.stdout)


class TestContextSelect(unittest.TestCase):
    """#9: deterministic, budgeted, scope-filtered context assembly (reference predicate)."""

    def _recs(self):
        return [
            {"id": "hi", "statement": "x", "confidence": 0.95, "repetition_count": 3, "scope": "context.task.code"},
            {"id": "mid", "statement": "y", "confidence": 0.9, "repetition_count": 2, "scope": "context.task.code"},
            {"id": "lo", "statement": "z", "confidence": 0.6, "repetition_count": 1, "scope": "context.task.code"},
        ]

    def test_salience_orders_by_confidence_then_repetition(self):
        recs = self._recs()
        sel, _ = cs.select_context(recs, token_budget=999)
        self.assertEqual([r["id"] for r in sel], ["hi", "mid", "lo"])

    def test_budget_drops_the_tail_as_gap(self):
        recs = self._recs()
        per = cs.est_tokens(recs[0])           # all three have equal-length payloads
        sel, dropped = cs.select_context(recs, token_budget=2 * per)
        self.assertEqual([r["id"] for r in sel], ["hi", "mid"])
        self.assertEqual([r["id"] for r in dropped], ["lo"])  # the dropped tail is returned, not silent

    def test_scope_overlap_filters_off_task_records(self):
        recs = self._recs() + [{"id": "other", "statement": "w", "confidence": 1.0, "scope": "context.task.writing"}]
        sel, _ = cs.select_context(recs, token_budget=999, task_tags="context.task.code")
        self.assertNotIn("other", [r["id"] for r in sel])  # writing-scoped record excluded for a code task

    def test_untagged_record_is_universally_applicable(self):
        self.assertTrue(cs.scope_overlap(None, "context.task.code"))
        self.assertTrue(cs.scope_overlap("context.task.code", None))   # empty task filter => all apply
        self.assertFalse(cs.scope_overlap("context.task.writing", "context.task.code"))

    def test_deterministic_same_input_same_slice(self):
        recs = self._recs()
        budget = 2 * cs.est_tokens(recs[0])
        a, _ = cs.select_context(recs, token_budget=budget)
        b, _ = cs.select_context(list(reversed(recs)), token_budget=budget)  # order-independent
        self.assertEqual([r["id"] for r in a], [r["id"] for r in b])

    def test_self_reported_never_selected_as_authority(self):
        # M1: a confirmed, high-salience self_reported record must NOT enter authoritative context,
        # even with unlimited budget and matching scope — draft-only at runtime (decision C).
        recs = self._recs() + [{
            "id": "sr", "statement": "I am a careful reviewer", "confidence": 1.0,
            "repetition_count": 5, "scope": "context.task.code", "reliability": "self_reported",
        }]
        sel, dropped = cs.select_context(recs, token_budget=999, task_tags="context.task.code")
        self.assertNotIn("sr", [r["id"] for r in sel])      # not authoritative
        self.assertNotIn("sr", [r["id"] for r in dropped])  # not a budget drop either — filtered as draft
        # it IS retrievable as a draft, so it is surfaced (not silently lost)
        drafts = cs.draft_only(recs, task_tags="context.task.code")
        self.assertEqual([r["id"] for r in drafts], ["sr"])


class TestCompileAdapter(unittest.TestCase):
    """S10 reference compiler: deterministic 8-section assembly honoring G3 + reliability +
    supersession, reproducing the hand-authored runtime-adapter.md membership."""

    def test_live_example_eight_active_packs(self):
        pack_records, drift = comp.load(EXAMPLE)
        a = comp.compile_adapter(pack_records, drift)
        self.assertEqual(a["coverage"]["n_active_packs"], 8)   # T2 live (after rev-01/02)
        self.assertEqual(a["coverage"]["n_compile_packs"], 12) # 14 packs − eval_cases − drift_history
        self.assertEqual(a["boundary_source"], "instance")     # boundary.001 present at T2
        gap_packs = {g["pack"] for g in a["gap_log"]}
        self.assertEqual(gap_packs, {"user.red_flags", "user.workflow_playbooks",
                                     "user.domain_overlays", "user.memory_project_graph"})

    def test_section1_identity_membership(self):
        pack_records, drift = comp.load(EXAMPLE)
        a = comp.compile_adapter(pack_records, drift)
        ids = {r["id"] for r in a["sections"]["identity_role"]}
        self.assertEqual(ids, {"logotekton.role.001", "logotekton.role.002",
                               "logotekton.trait.001", "logotekton.trait.002"})

    def test_t0_fixture_reproduces_hand_authored_adapter(self):
        # the hand-authored runtime-adapter.md is a T0 snapshot: 5 active packs, no instance
        # boundary → default safe policy. The compiler reproduces that membership from the frozen
        # T0 fixture, so the doc is machine-reproducible, not asserted by construction.
        pre = os.path.join(EXAMPLE, "revolution-01", "instance-records.pre.yaml")
        pack_records, drift = comp.load(pre)
        a = comp.compile_adapter(pack_records, drift)
        self.assertEqual(a["coverage"]["n_active_packs"], 5)
        self.assertEqual(a["boundary_source"], "default_safe_policy")

    def test_boundary_progression_t0_to_t1(self):
        # T0 (no instance boundary) → T1 (rev-01 added boundary.001) flips the boundary source
        t0, t0d = comp.load(os.path.join(EXAMPLE, "revolution-01", "instance-records.pre.yaml"))
        t1, t1d = comp.load(os.path.join(EXAMPLE, "revolution-02", "instance-records.pre.yaml"))
        self.assertEqual(comp.compile_adapter(t0, t0d)["boundary_source"], "default_safe_policy")
        self.assertEqual(comp.compile_adapter(t1, t1d)["boundary_source"], "instance")

    def test_self_reported_not_compiled(self):
        # decision C: a confirmed self_reported record is draft-only — never compiled into a section
        recs = {"user.tacit_heuristics": [
            {"id": "x.h.1", "review_status": "confirmed", "statement": "behavioral", "scope": "s"},
            {"id": "x.h.2", "review_status": "confirmed", "reliability": "self_reported",
             "statement": "self", "scope": "s"},
        ]}
        a = comp.compile_adapter(recs, [])
        ids = {r["id"] for r in a["sections"]["heuristics_red_flags"]}
        self.assertEqual(ids, {"x.h.1"})

    def test_pending_not_compiled_g3(self):
        recs = {"user.decision_policy": [
            {"id": "x.d.1", "review_status": "confirmed", "statement": "a", "scope": "s"},
            {"id": "x.d.2", "review_status": "pending", "statement": "b", "scope": "s"},
        ]}
        a = comp.compile_adapter(recs, [])
        ids = {r["id"] for r in a["sections"]["decision_policy"]}
        self.assertEqual(ids, {"x.d.1"})

    def test_superseded_record_excluded(self):
        # a record named in a drift_history supersedes is the retired old version — excluded
        recs = {"user.persona_core": [
            {"id": "x.t.1", "review_status": "confirmed", "statement": "old", "scope": "s"},
            {"id": "x.t.2", "review_status": "confirmed", "statement": "new", "scope": "s"},
        ]}
        drift = [{"id": "x.drift.1", "supersedes": ["x.t.1"]}]
        a = comp.compile_adapter(recs, drift)
        ids = {r["id"] for r in a["sections"]["identity_role"]}  # persona_core feeds sections 1 & 3
        self.assertEqual(ids, {"x.t.2"})
        self.assertIn("x.t.1", a["superseded_excluded"])

    def test_narrowed_is_included_other_statuses_excluded(self):
        # confirmed + narrowed compile in (G3 §8 table); rejected/sensitive/deferred never do
        recs = {"user.decision_policy": [
            {"id": "x.d.conf", "review_status": "confirmed", "statement": "a", "scope": "s"},
            {"id": "x.d.narr", "review_status": "narrowed", "statement": "b", "scope": "s"},
            {"id": "x.d.rej", "review_status": "rejected", "statement": "c", "scope": "s"},
            {"id": "x.d.sens", "review_status": "sensitive", "statement": "d", "scope": "s"},
            {"id": "x.d.def", "review_status": "deferred", "statement": "e", "scope": "s"},
        ]}
        a = comp.compile_adapter(recs, [])
        ids = {r["id"] for r in a["sections"]["decision_policy"]}
        self.assertEqual(ids, {"x.d.conf", "x.d.narr"})

    def test_own_supersedes_field_excludes_old_version(self):
        # the retired old version can be named in a record's OWN supersedes (no drift record present)
        recs = {"user.persona_core": [
            {"id": "x.t.old", "review_status": "confirmed", "statement": "old", "scope": "s"},
            {"id": "x.t.new", "review_status": "confirmed", "statement": "new", "scope": "s",
             "supersedes": ["x.t.old"]},
        ]}
        a = comp.compile_adapter(recs, [])   # NO drift records — exclusion must come from own field
        ids = {r["id"] for r in a["sections"]["identity_role"]}
        self.assertEqual(ids, {"x.t.new"})
        self.assertIn("x.t.old", a["superseded_excluded"])

    def test_task_scope_filter_selects_matching_only(self):
        # --task tag routes through scope_overlap: only review-scoped (or no-scope) records survive
        recs = {"user.communication_style": [
            {"id": "x.s.rev", "review_status": "confirmed", "statement": "r", "scope": "review"},
            {"id": "x.s.ext", "review_status": "confirmed", "statement": "e", "scope": "external_email"},
        ]}
        a = comp.compile_adapter(recs, [], task_tags="review")
        ids = {r["id"] for r in a["sections"]["active_patterns"]}
        self.assertEqual(ids, {"x.s.rev"})   # external-scoped record dropped for a review task

    def test_deterministic_same_input_same_adapter(self):
        pack_records, drift = comp.load(EXAMPLE)
        self.assertEqual(comp.compile_adapter(pack_records, drift),
                         comp.compile_adapter(pack_records, drift))


class TestCommandGuard(unittest.TestCase):
    """check_commands.py must actually fail when a documented command errors (not a no-op)."""

    def test_guard_catches_a_failing_command(self):
        # plant a documented *tool* command that errors (validate_packs with no path -> exit 2).
        # the guard must run it (it is a RUNNABLE tool, no placeholder/side-effect) and fail.
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "a.md"), "w", encoding="utf-8") as fh:
                fh.write('```bash\npython tools/validate_packs.py\n```\n')
            r = _run("tools/check_commands.py", d)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("1 broken", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
