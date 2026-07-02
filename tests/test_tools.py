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
>                                (L0 Seed; coverage 0.0714 gate/strict, seeded-breadth 0.714;
>                                decision_fidelity 1.0; correction_cost 0.0833; drift_stability
>                                0.8947; traceability 1.0).
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

import json
import math
import os
import subprocess
import sys
import tempfile
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

CLI_ENV = os.environ.copy()
CLI_ENV.setdefault("PYTHONUTF8", "1")
CLI_ENV.setdefault("PYTHONIOENCODING", "utf-8")


def run_cli(argv, **kwargs):
    return subprocess.run(
        argv,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=CLI_ENV,
        **kwargs,
    )


def almost(a, b, places=4):
    return round(a - b, places) == 0


# ─────────────────────── convergence_report: mini-YAML ──────────────────────
class TestMiniYAMLScalars(unittest.TestCase):
    """미니 YAML 폴백 파서가 PyYAML 과 갈라지지 않게 잠근다 (특히 NaN/inf 주입 방지)."""

    def test_bare_nan_inf_stay_strings(self):
        # PyYAML 1.1 은 bare nan/inf/infinity 를 *문자열* 로 본다(.nan/.inf 만 float).
        # 미니 파서가 float NaN 을 만들면 평균·비율에 조용히 NaN 이 스며든다.
        for word in ("nan", "inf", "-inf", "+inf", "infinity", "NaN", "Inf"):
            v = cr._parse_scalar(word)
            self.assertIsInstance(v, str, f"{word!r} should parse as str, got {v!r}")
            self.assertEqual(v, word)

    def test_real_numbers_still_parse(self):
        self.assertEqual(cr._parse_scalar("0.43"), 0.43)
        self.assertEqual(cr._parse_scalar("7"), 7)
        self.assertEqual(cr._parse_scalar("1e3"), 1000.0)

    @unittest.skipUnless(HAVE_YAML, "PyYAML not installed")
    def test_matches_pyyaml_on_special_words(self):
        import yaml
        for word in ("nan", "inf", "-inf", "infinity"):
            self.assertEqual(cr._parse_scalar(word), yaml.safe_load("x: " + word)["x"])


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

    def test_intra_batch_duplicates_dedup_not_twin(self):
        # Two identical incoming candidates (distinct ids) in ONE batch, against an
        # EMPTY existing set. Static-snapshot classification would call both 'novel'
        # and insert twins. plan_batch must dedup: first inserts, second merges.
        ex = {}
        cands = [_cand(id="x.h.910"), _cand(id="x.h.911")]
        plans = pab_merge.plan_batch(ex, cands)
        self.assertEqual(plans[0]["verdict"], "novel")
        self.assertEqual(plans[1]["verdict"], "duplicate")     # sees the first in-batch
        self.assertEqual(plans[1]["target"], "x.h.910")
        out, _ = pab_merge.apply_plan(ex, cands, plans, "2026-01-01T00:00:00Z")
        recs = out["user.tacit_heuristics"]
        self.assertEqual(len(recs), 1)                         # ONE record, not twins
        self.assertEqual(recs[0]["id"], "x.h.910")
        self.assertEqual(recs[0]["repetition_count"], 2)       # the merge accumulated
        self.assertIn("x.h.911", recs[0]["merge_history"])

    def test_intra_batch_dedup_still_inserts_distinct(self):
        # Two DIFFERENT candidates in one batch both insert (no false dedup).
        ex = {}
        cands = [_cand(id="x.h.920"),
                 _cand(id="x.h.921", statement="prefer ripgrep over grep for repo search", scope="search")]
        plans = pab_merge.plan_batch(ex, cands)
        self.assertEqual(plans[0]["verdict"], "novel")
        self.assertEqual(plans[1]["verdict"], "novel")
        out, _ = pab_merge.apply_plan(ex, cands, plans, "2026-01-01T00:00:00Z")
        self.assertEqual(len(out["user.tacit_heuristics"]), 2)


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

    def test_g5_sensitive_requires_exception_rules(self):
        # 민감/제한 레코드는 exception_rules(BoundaryRule) 없이 통과하면 안 된다 (G5).
        # 스키마 allOf 와 동기화 — validate_packs 단독 실행에서도 구멍이 없어야.
        for sens in ("sensitive", "restricted"):
            r = _good(); r["sensitivity"] = sens
            self.assertFalse(vp.validate_record(r, "t").ok,
                             f"{sens} without exception_rules should fail")
            r["exception_rules"] = ["only with explicit consent"]
            self.assertTrue(vp.validate_record(r, "t").ok,
                            f"{sens} with exception_rules should pass")

    def test_g5_public_internal_need_no_exception_rules(self):
        # public/internal 은 exception_rules 가 없어도 통과해야 한다 (과도강제 방지).
        for sens in ("public", "internal"):
            r = _good(); r["sensitivity"] = sens
            self.assertTrue(vp.validate_record(r, "t").ok)


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
        # model+temperature alone is NOT enough — prompt_id must be pinned too (spec/05 §2 ④)
        r["scoring_rubric"]["judge_config"] = {"model": "claude-opus-4-8", "temperature": 0}
        self.assertFalse(vp.validate_record(r, "t").ok)
        # full determinism config (model · temperature · prompt_id) passes
        r["scoring_rubric"]["judge_config"]["prompt_id"] = "judge-prompt-v1"
        self.assertTrue(vp.validate_record(r, "t").ok)

    def test_empty_criteria_rubric_fails(self):
        # 공허한 루브릭(채점 기준 없음)은 무조건 통과라 decision_fidelity 를 부풀린다 (it.4).
        r = _good_eval(); r["scoring_rubric"]["criteria"] = []
        res = vp.validate_record(r, "t")
        self.assertFalse(res.ok)
        self.assertTrue(any("criteria 가 비어" in e for e in res.errors), res.errors)

    def test_zero_pass_threshold_fails(self):
        # pass_threshold=0 은 score=0 도 통과시켜 채점을 무의미하게 만든다 (it.4).
        r = _good_eval(); r["scoring_rubric"]["pass_threshold"] = 0
        res = vp.validate_record(r, "t")
        self.assertFalse(res.ok)
        self.assertTrue(any("pass_threshold" in e for e in res.errors), res.errors)

    def test_mixed_judge_warns_without_config(self):
        # 스키마 설명("warns when judge=mixed")이 실제 동작과 일치해야 한다 (적대적 검증 F7).
        # mixed 는 error 가 아니라 warning — 레코드는 통과하되 재현성 경고를 남긴다.
        r = _good_eval(); r["scoring_rubric"]["judge"] = "mixed"
        res = vp.validate_record(r, "t")
        self.assertTrue(res.ok, res.errors)  # warning, not error
        self.assertTrue(any("judge=mixed" in w for w in res.warnings), res.warnings)
        # judge_config 를 고정하면 경고가 사라진다.
        r["scoring_rubric"]["judge_config"] = {"model": "claude-opus-4-8", "temperature": 0}
        res2 = vp.validate_record(r, "t")
        self.assertFalse(any("judge=mixed" in w for w in res2.warnings), res2.warnings)


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

    def test_maturity_is_L0(self):
        # The L1 depth-vertical must come from a CONTENT pack (it.5): logotekton has depth in only
        # ONE pack — user.evaluation_cases (a META pack) — and ZERO content packs reach ≥3, so its
        # "depth" is the eval ledger, not knowledge of the person. It is honestly L0 Seed (broad,
        # shallow), not L1 Sketch. (Counting the eval pack as the vertical made L1's depth gate
        # vacuous — the eval≥3 gate would auto-satisfy it.)
        self.assertEqual(self.tier, "L0")
        self.assertEqual(self.ix["_content_packs_with_3"], 0)   # no content-pack depth

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

    def test_example_vertical_is_meta_not_content(self):
        # the example's single ≥3 pack is user.evaluation_cases (a META pack, 6 confirmed) — it does
        # NOT count as a content depth-vertical, which is why the example is L0, not L1 (it.5).
        self.assertEqual(self.ix["_packs_with_3"], 1)            # all-pack count (incl. eval)
        self.assertEqual(self.ix["_content_packs_with_3"], 0)    # but 0 CONTENT verticals

    def test_l1_requires_content_depth_not_just_breadth(self):
        # #7 + it.5: 7 packs each seeded with 1 record (no depth) must NOT reach L1, AND the depth
        # vertical must be a CONTENT pack — a vertical that is only the eval/drift meta pack does
        # NOT open L1 (else the eval≥3 gate would auto-satisfy the depth requirement).
        base = {
            "coverage": 0.5, "confirmation_ratio": 1.0, "human_confirmation_ratio": 1.0,
            "decision_fidelity": 0.9, "correction_cost": 0.1, "drift_stability": 1.0,
            "traceability": 1.0, "_seeded_packs": 7, "_content_packs_with_3": 0,
            "_packs_with_3": 0, "_n_eval": 3,
        }
        tier, _, reasons = cr.maturity_tier(base)
        self.assertFalse(reasons["L1_vertical>=1 (콘텐츠 팩 ≥3 확인)"])
        self.assertEqual(tier, "L0")  # stuck at L0 despite 7 seeded packs
        # the eval pack alone reaching ≥3 (meta vertical) must NOT open L1
        meta_only = {**base, "_packs_with_3": 1, "_content_packs_with_3": 0}
        self.assertEqual(cr.maturity_tier(meta_only)[0], "L0")
        # one CONTENT pack with ≥3 confirmed opens the ladder
        tier2, _, _ = cr.maturity_tier({**base, "_content_packs_with_3": 1, "_packs_with_3": 1})
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
            "traceability": 1.0, "_seeded_packs": 8, "_packs_with_3": 8,
            "_content_packs_with_3": 8, "_n_eval": 3,
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


class TestSupersededExclusionConsistency(unittest.TestCase):
    """it.3 lifecycle: a superseded (retired) record must be excluded from the LIVE slice by
    BOTH compile_adapter and convergence_report — else the two tools disagree on runtime-active."""

    def _recs(self):
        return {"user.persona_core": [
            {"id": "R1", "review_status": "narrowed", "statement": "old", "scope": "s",
             "evidence_refs": ["e"]},
            {"id": "R2", "review_status": "confirmed", "statement": "new", "scope": "s",
             "supersedes": ["R1"], "evidence_refs": ["e"]},
        ]}

    def test_convergence_excludes_superseded(self):
        ix = cr.compute_indices(self._recs(), [], [])
        self.assertEqual(ix["_n_confirmed"], 1)             # only R2 (R1 retired)
        self.assertEqual(ix["_n_superseded_excluded"], 1)
        self.assertEqual(ix["_n_active"], 1)                # traceability active set excludes R1

    def test_both_tools_agree_on_superseded(self):
        recs = self._recs()
        sup = comp.collect_superseded(recs, [])
        ix = cr.compute_indices(recs, [], [])
        self.assertEqual(sup, {"R1"})
        self.assertEqual(ix["_n_superseded_excluded"], len(sup))   # same retired set
        a = comp.compile_adapter(recs, [])
        compiled_ids = {r["id"] for r in a["sections"]["identity_role"]}
        self.assertNotIn("R1", compiled_ids)                # compiler also excludes R1

    def test_example_has_no_supersessions(self):
        # locks that the worked example is supersession-free, so this change preserves every number
        pr, ev, dr, _ = cr.collect(EXAMPLE)
        ix = cr.compute_indices(pr, ev, dr)
        self.assertEqual(ix["_n_superseded_excluded"], 0)


class TestAutoConfirmGateImmunity(unittest.TestCase):
    """spec/12 §4.4 순환 차단: auto-confirm 은 성숙도 게이트 신호를 '건드릴 수 없다'. hcr 뿐 아니라
    coverage 깊이·decision_fidelity·correction_cost 도 auto-confirm 면역이어야 한다 (it.3 게이밍 홀)."""

    def test_auto_confirmed_excluded_from_coverage_depth(self):
        # 3 auto_confirmed behavioral confirmed in a pack → NOT a depth vertical (human depth 0).
        recs = {"user.persona_core": [
            {"review_status": "confirmed", "reliability": "behavioral", "auto_confirmed": True,
             "evidence_refs": ["e"]} for _ in range(3)]}
        ix = cr.compute_indices(recs, [], [])
        self.assertEqual(ix["_behavioral_confirmed_by_pack"]["user.persona_core"], 0)
        self.assertEqual(ix["_packs_with_3"], 0)          # auto-confirm can't build depth
        self.assertEqual(ix["_n_auto_confirmed"], 3)

    def test_auto_confirmed_evals_excluded_from_fidelity(self):
        # auto_confirmed pass eval cases must NOT inflate decision_fidelity (the §4.4 promise).
        evals = (
            [{"result": {"status": "fail"}}]                                  # 1 human behavioral FAIL
            + [{"result": {"status": "pass"}, "auto_confirmed": True} for _ in range(4)]  # 4 auto PASS
        )
        ix = cr.compute_indices({}, evals, [])
        self.assertEqual(ix["_n_eval"], 1)               # only the human-gated eval counts
        self.assertEqual(ix["decision_fidelity"], 0.0)   # not 0.8

    def test_correction_cost_only_from_eval_cases_not_seedable(self):
        # it.4: correction_cost must come ONLY from eval-case edit fractions — seeding many
        # non-eval records with edit_fraction=0 must not drag the average down.
        evals = [{"result": {"status": "pass", "edit_fraction": 0.3}}]
        base = cr.compute_indices({}, evals, [])
        seeded = {"user.tacit_heuristics": [
            {"review_status": "confirmed", "statement": "x", "scope": "s",
             "evidence_refs": ["e"], "edit_fraction": 0.0} for _ in range(50)]}
        flooded = cr.compute_indices(seeded, evals, [])
        self.assertEqual(base["correction_cost"], 0.3)
        self.assertEqual(flooded["correction_cost"], 0.3)   # non-eval seeds ignored

    def test_correction_cost_na_without_eval_provenance(self):
        # a record carrying edit_fraction but NO eval cases → correction_cost stays NA
        recs = {"user.tacit_heuristics": [
            {"review_status": "confirmed", "statement": "x", "scope": "s",
             "evidence_refs": ["e"], "edit_fraction": 0.0}]}
        ix = cr.compute_indices(recs, [], [])
        self.assertIsNone(ix["correction_cost"])

    def test_autoconfirm_flood_plus_three_human_records_cannot_reach_L4(self):
        # The empirically-reproduced it.3 attack: flood all 14 packs with auto-confirmed records
        # + 3 human records → must NOT reach a high tier (was L4 before the fix).
        packs = {p: [{"review_status": "confirmed", "reliability": "behavioral",
                      "auto_confirmed": True, "evidence_refs": ["e"]} for _ in range(3)]
                 for p in cr.CANONICAL_PACKS}
        packs["user.persona_core"] += [
            {"review_status": "confirmed", "reliability": "behavioral", "evidence_refs": ["e"]}
            for _ in range(3)]
        evals = [{"result": {"status": "pass"}, "auto_confirmed": True, "edit_fraction": 0.05}
                 for _ in range(5)]
        ix = cr.compute_indices(packs, evals, [])
        tier, _, _ = cr.maturity_tier(ix)
        self.assertEqual(ix["coverage"], 1 / 14)          # only the 1 human-depth pack counts
        self.assertNotIn(tier, ("L3", "L4"))              # flood cannot self-certify maturity


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
    return run_cli([sys.executable, *args], cwd=REPO)


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
        self.assertIn("L0 Seed", r.stdout)     # honest: no CONTENT depth-vertical (eval pack ≠ depth)
        self.assertIn("0.07", r.stdout)        # coverage = strict (spec §2), not the 0.71 breadth

    def test_documented_commands_all_run(self):
        # every safe, read-only command printed in the docs must actually run (the it.13 bug class:
        # a documented invocation that errors). check_commands.py runs them and fails on any break.
        r = _run("tools/check_commands.py", ".")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("0 broken", r.stdout)

    def test_compile_adapter_fails_loudly_on_missing_input(self):
        # it.10: compile_adapter must NOT exit 0 on a missing/unreadable input — else the
        # check_commands exit-code gate would stay green even if the example were deleted/renamed.
        r = _run("tools/compile_adapter.py", "examples/does-not-exist-dir")
        self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
        # the real example still compiles and exits 0
        ok = _run("tools/compile_adapter.py", "examples/logotekton")
        self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)

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

    def test_nonfinite_confidence_keeps_slice_deterministic(self):
        # it.12: a NaN/inf confidence must not make salience NaN — NaN comparisons are all False,
        # so the sort would depend on input order, breaking the "same input → same slice" guarantee.
        nan = float("nan")
        r1 = {"id": "a", "statement": "x" * 5, "confidence": nan}
        r2 = {"id": "b", "statement": "y" * 5, "confidence": 0.5}
        self.assertTrue(math.isfinite(cs.salience(r1)))   # finite, not NaN
        budget = cs.est_tokens(r2)                         # fits exactly one record
        sel_ab, _ = cs.select_context([r1, r2], token_budget=budget)
        sel_ba, _ = cs.select_context([r2, r1], token_budget=budget)
        self.assertEqual([r["id"] for r in sel_ab], [r["id"] for r in sel_ba])  # order-independent

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

    def test_project_context_not_blended_into_persona(self):
        # 전이성 경계 (skills/10 §4): memory_project_graph 는 섹션 1 에 들어오되 persona 와
        # 섞이지 않고 별도 project_context 하위블록으로 — persona list 에 새면 안 된다 (F5).
        recs = {
            "user.persona_core": [
                {"id": "x.trait.1", "review_status": "confirmed", "statement": "values clarity", "scope": "s"},
            ],
            "user.memory_project_graph": [
                {"id": "x.proj.1", "review_status": "confirmed",
                 "statement": "payments-svc is in launch-hardening phase", "scope": "s"},
            ],
        }
        a = comp.compile_adapter(recs, [])
        persona_ids = {r["id"] for r in a["sections"]["identity_role"]}
        ctx_ids = {r["id"] for r in a["project_context"]}
        self.assertEqual(persona_ids, {"x.trait.1"})       # project memory NOT in persona
        self.assertEqual(ctx_ids, {"x.proj.1"})            # it IS in the separate sub-block
        self.assertNotIn("x.proj.1", persona_ids)

    def test_project_memory_still_feeds_workflow(self):
        # 섹션 6 합류는 정상(워크플로의 프로젝트 단계) — 분리는 섹션 1 에만 적용.
        recs = {"user.memory_project_graph": [
            {"id": "x.proj.9", "review_status": "confirmed", "statement": "phase 2", "scope": "s"},
        ]}
        a = comp.compile_adapter(recs, [])
        wf_ids = {r["id"] for r in a["sections"]["workflow"]}
        self.assertIn("x.proj.9", wf_ids)

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


class TestRobustnessFuzzing(unittest.TestCase):
    """it.13: malformed/edge inputs must not crash, leak NaN/inf into indices, silently pass a
    gate, collide dedup keys, or recurse forever — robustness of the deterministic tools."""

    def _evalcase(self, **result):
        return {"id": "x.evalcase.1", "record_type": "EvaluationCaseRecord", "label": "l",
                "statement": "s", "evidence_refs": ["e"], "confidence": 0.9, "scope": "w",
                "review_status": "confirmed", "sensitivity": "internal",
                "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z",
                "scoring_rubric": {"criteria": [{"check": "a", "weight": 1.0}], "pass_threshold": 0.8},
                "result": result}

    def test_nan_inf_edit_fraction_does_not_poison_correction_cost(self):
        for bad in (float("nan"), float("inf"), float("-inf")):
            ev = [{"record_type": "EvaluationCaseRecord", "id": "e", "review_status": "confirmed",
                   "result": {"status": "pass", "edit_fraction": bad}}]
            cc = cr.compute_indices({}, ev, [])["correction_cost"]
            self.assertTrue(cc is None or math.isfinite(cc), f"{bad} leaked: {cc}")

    def test_bool_edit_fraction_ignored(self):
        ev = [{"record_type": "EvaluationCaseRecord", "id": "e", "review_status": "confirmed",
               "result": {"status": "pass", "edit_fraction": True}}]
        self.assertIsNone(cr.compute_indices({}, ev, [])["correction_cost"])

    def test_nan_weight_and_score_are_rejected(self):
        r = self._evalcase(status="pass", score=0.9)
        r["scoring_rubric"]["criteria"] = [{"check": "a", "weight": float("nan")}]
        self.assertFalse(vp.validate_record(r, "t").ok)
        r2 = self._evalcase(status="pass", score=float("nan"))
        self.assertFalse(vp.validate_record(r2, "t").ok)

    def test_unhashable_enum_value_does_not_crash(self):
        for fld, val in [("sensitivity", ["public"]), ("review_status", ["pending"]),
                         ("reliability", ["behavioral"]), ("sensitivity", {"a": 1})]:
            r = _good(); r[fld] = val
            res = vp.validate_record(r, "t")   # must not raise
            self.assertFalse(res.ok)           # and must be flagged, not accepted

    def test_pab_merge_nonstring_fields_do_not_crash(self):
        for bad in (["list"], 5, {"k": "v"}):
            cand = {"id": "a", "record_type": "HeuristicRecord", "statement": "x", "scope": bad}
            pab_merge.classify({}, cand)       # must not raise
        # non-string statement also tolerated
        pab_merge.canonical_key("p", "T", ["a", "b"], "s")

    def test_canonical_key_nfc_nfd_equivalent_and_no_collision(self):
        import unicodedata as ud
        k_nfc = pab_merge.canonical_key("p", "T", ud.normalize("NFC", "한국어 규칙"), "s")
        k_nfd = pab_merge.canonical_key("p", "T", ud.normalize("NFD", "한국어 규칙"), "s")
        self.assertEqual(k_nfc, k_nfd)         # same statement, any norm form → same key
        other = pab_merge.canonical_key("p", "T", ud.normalize("NFD", "전혀 다른 문장"), "s")
        self.assertNotEqual(k_nfd, other)      # distinct NFD statements must NOT collide

    def test_mini_yaml_unclosed_bracket_raises_clean_error(self):
        with self.assertRaises(cr.MiniYAMLError):
            cr.mini_yaml_load("x: [a, b")       # not RecursionError


class TestRobustnessFuzzingIt14(unittest.TestCase):
    """it.14: a second fuzzing pass — non-string ids in summaries, non-deterministic sort on
    duplicate ids, non-numeric token budgets, corrupt/non-UTF8/over-nested input files, and
    malformed merge payloads must each be contained at the tool boundary, never crashing a whole
    directory run nor silently corrupting data."""

    def _confirmed(self, pack, **extra):
        r = {"id": "r1", "pack": pack, "record_type": "StylePreference",
             "statement": "prefer subprocess.run over os.system",
             "review_status": "confirmed", "scope": "context.global"}
        r.update(extra)
        return {pack: [r]}

    def test_render_summary_tolerates_nonstring_section_ids(self):
        recs = {"user.identity_roles": [
            {"id": 999, "statement": "primary self-map author",
             "review_status": "confirmed", "scope": "context.global"}]}
        out = comp.render_summary(comp.compile_adapter(recs, {}), ".")  # must not raise
        self.assertIn("999", out)

    def test_render_summary_tolerates_nonstring_project_context_ids(self):
        recs = {"user.memory_project_graph": [
            {"id": 777, "statement": "repo uses pytest",
             "review_status": "confirmed", "scope": "context.global"}]}
        out = comp.render_summary(comp.compile_adapter(recs, {}), ".")  # must not raise
        self.assertIn("777", out)

    def test_compile_adapter_sort_is_total_order_on_duplicate_ids(self):
        # same id, different statement → ordering must be input-independent (statement as tiebreak)
        a = comp.compile_adapter({"user.identity_roles": [
            {"id": "x", "statement": "zeta", "review_status": "confirmed", "scope": "context.global"},
            {"id": "x", "statement": "alpha", "review_status": "confirmed", "scope": "context.global"}]}, {})
        b = comp.compile_adapter({"user.identity_roles": [
            {"id": "x", "statement": "alpha", "review_status": "confirmed", "scope": "context.global"},
            {"id": "x", "statement": "zeta", "review_status": "confirmed", "scope": "context.global"}]}, {})
        order_a = [r["statement"] for r in a["sections"][comp.SECTION_NAMES[1]]]
        order_b = [r["statement"] for r in b["sections"][comp.SECTION_NAMES[1]]]
        self.assertEqual(order_a, ["alpha", "zeta"])
        self.assertEqual(order_a, order_b)      # reordered input → identical adapter

    def test_select_context_rejects_nonnumeric_or_nonfinite_budget(self):
        for bad in (None, "28", float("nan"), float("inf")):
            with self.assertRaises((TypeError, ValueError)):
                cs.select_context(cs._DEMO, token_budget=bad)
        with self.assertRaises(TypeError):
            cs.select_context(cs._DEMO, token_budget=True)   # bool is not a budget

    def _write(self, tmp, name, data, binary=False):
        path = os.path.join(tmp, name)
        mode = "wb" if binary else "w"
        with open(path, mode) as fh:
            fh.write(data)
        return path

    def test_loaders_contain_nonutf8_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write(tmp, "bad.json", b"\xff\xfe\x00bad", binary=True)
            payload, err = vp.load_file(p)
            self.assertIsNone(payload); self.assertTrue(err)        # validate: clean error
            self.assertIsNone(cr.load_structured(p))                # convergence: warn+skip
            with self.assertRaises(SystemExit):                     # merge: clean exit
                pab_merge._load(p)

    def test_loaders_contain_overnested_json(self):
        deep = "[" * 60000 + "]" * 60000
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write(tmp, "deep.json", deep)
            payload, err = vp.load_file(p)
            self.assertIsNone(payload); self.assertTrue(err)        # validate: clean error
            self.assertIsNone(cr.load_structured(p))                # convergence: warn+skip
            with self.assertRaises(SystemExit):                     # merge: clean exit
                pab_merge._load(p)

    def test_apply_plan_tolerates_nonint_repetition_count(self):
        pack = "user.style_preferences"
        existing = self._confirmed(pack, id="r1", repetition_count="oops",
                                   record_type="StylePreference")
        cands = [{"id": "c1", "pack": pack, "record_type": "StylePreference",
                  "statement": "prefer subprocess.run over os.system", "scope": "context.global"}]
        plans = pab_merge.plan_batch(existing, cands)
        self.assertEqual(plans[0]["action"], "merge")   # same scope+statement → dedup-merge
        merged, _ = pab_merge.apply_plan(existing, cands, plans, "1970-01-01T00:00:00Z")
        r1 = [r for r in merged[pack] if r["id"] == "r1"][0]
        self.assertEqual(r1["repetition_count"], 2)     # "oops" treated as 1, then +1

    def test_apply_plan_string_evidence_refs_does_not_char_explode(self):
        pack = "user.style_preferences"
        existing = self._confirmed(pack, id="r1", evidence_refs="single-ref",
                                   record_type="StylePreference")
        cands = [{"id": "c1", "pack": pack, "record_type": "StylePreference",
                  "statement": "prefer subprocess.run over os.system",
                  "scope": "context.global", "evidence_refs": "incoming-ref"}]
        plans = pab_merge.plan_batch(existing, cands)
        self.assertEqual(plans[0]["action"], "merge")   # same scope+statement → dedup-merge
        merged, _ = pab_merge.apply_plan(existing, cands, plans, "1970-01-01T00:00:00Z")
        refs = [r for r in merged[pack] if r["id"] == "r1"][0]["evidence_refs"]
        self.assertIn("single-ref", refs)
        self.assertIn("incoming-ref", refs)
        self.assertTrue(all(len(x) > 1 for x in refs))   # no 's','i','n','g'... fragments

    def test_apply_plan_duplicate_candidate_ids_preserved_positionally(self):
        # two distinct candidates sharing an id must NOT collapse to one (id-keyed dict data loss)
        pack = "user.style_preferences"
        cands = [
            {"id": "dup", "pack": pack, "record_type": "StylePreference",
             "statement": "first unique claim alpha"},
            {"id": "dup", "pack": pack, "record_type": "StylePreference",
             "statement": "second unique claim beta"}]
        plans = pab_merge.plan_batch({}, cands)
        merged, _ = pab_merge.apply_plan({}, cands, plans, "1970-01-01T00:00:00Z")
        stmts = sorted(r["statement"] for r in merged.get(pack, []))
        self.assertEqual(stmts, ["first unique claim alpha", "second unique claim beta"])

    def test_apply_plan_length_mismatch_is_explicit_error(self):
        cands = [{"id": "a", "pack": "user.style_preferences", "statement": "x"}]
        with self.assertRaises(ValueError):
            pab_merge.apply_plan({}, cands, [], "1970-01-01T00:00:00Z")  # plans != candidates


class TestGateQualityIt15(unittest.TestCase):
    """it.15: gate bypasses + merge-identity correctness. List-shaped gates must reject
    placeholder/malformed elements (a fired hard-fail or a missing BoundaryRule cannot be hidden
    behind a non-list-of-strings), and duplicate detection must derive identity from content, never
    a possibly-stale stored canonical_key."""

    def _eval_fired(self, fired, status="pass", score=0.95):
        r = _good_eval()
        r["scoring_rubric"]["pass_threshold"] = 0.7
        r["result"] = {"status": status, "score": score, "unacceptable_fired": fired}
        return r

    def test_rlvr_hardfail_not_bypassed_by_malformed_fired_shapes(self):
        # a fired hard-fail recorded as objects / scalar / non-strings must still FAIL a 'pass'
        for shape in ([{"rule": "leaked_pii"}], "leaked_pii", {"0": "pii"}, [1, 2], ["   "]):
            self.assertFalse(vp.validate_record(self._eval_fired(shape), "t").ok,
                             f"malformed fired {shape!r} bypassed the hard-fail gate")
        self.assertFalse(vp.validate_record(self._eval_fired(["leaked_pii"]), "t").ok)  # control: enforced
        self.assertTrue(vp.validate_record(self._eval_fired(["leaked_pii"], status="fail", score=0.1), "t").ok)
        self.assertTrue(vp.validate_record(self._eval_fired([]), "t").ok)               # empty: nothing fired

    def test_g5_exception_rules_rejects_placeholder_elements(self):
        for exc in ([None], [""], ["   "], [123], [{}]):
            r = _good(); r["sensitivity"] = "sensitive"; r["record_type"] = "BoundaryRule"
            r["exception_rules"] = exc
            errs = vp.validate_record(r, "t").errors
            self.assertTrue(any("exception_rules 에 비어" in e for e in errs),
                            f"G5 accepted placeholder {exc!r}")
        # a real rule does not trip the element-quality check
        r = _good(); r["sensitivity"] = "sensitive"; r["record_type"] = "BoundaryRule"
        r["exception_rules"] = ["allow if user confirms"]
        self.assertFalse(any("exception_rules 에 비어" in e for e in vp.validate_record(r, "t").errors))

    def test_counterexamples_rejects_placeholder_elements(self):
        for cx in ([None], [""], [123]):
            r = _good(); r["confidence"] = 0.5; r["counterexamples"] = cx
            errs = vp.validate_record(r, "t").errors
            self.assertTrue(any("counterexamples 에 비어" in e for e in errs),
                            f"low-conf gate accepted placeholder {cx!r}")
        r = _good(); r["confidence"] = 0.5; r["counterexamples"] = ["fails when X"]
        self.assertTrue(vp.validate_record(r, "t").ok)   # real counterexample passes

    def test_apply_plan_infinite_repetition_count_does_not_crash(self):
        pack = "user.persona_core"
        existing = {pack: [{"id": "r1", "pack": pack, "record_type": "PreferenceRecord",
                            "statement": "prefer dark mode", "scope": "code",
                            "review_status": "confirmed", "repetition_count": float("inf")}]}
        cands = [{"id": "c1", "pack": pack, "record_type": "PreferenceRecord",
                  "statement": "prefer dark mode", "scope": "code"}]
        plans = pab_merge.plan_batch(existing, cands)
        merged, _ = pab_merge.apply_plan(existing, cands, plans, "1970-01-01T00:00:00Z")  # no OverflowError
        self.assertEqual([r for r in merged[pack] if r["id"] == "r1"][0]["repetition_count"], 2)

    def test_duplicate_detection_ignores_stale_stored_canonical_key(self):
        pack = "user.persona_core"
        base = dict(pack=pack, record_type="PreferenceRecord",
                    statement="prefer concise answers", scope="general")
        ck = pab_merge.canonical_key(base["pack"], base["record_type"], base["statement"], base["scope"])
        # false-negative: a true duplicate whose STORED key is stale must still be a duplicate
        ex_fn = {pack: [dict(base, id="R1", canonical_key="deadbeef0000",
                             review_status="confirmed", repetition_count=3, evidence_refs=["e1"])]}
        c = dict(base, id="C1", evidence_refs=["e2"])
        self.assertEqual(pab_merge.classify(ex_fn, c)["verdict"], "duplicate")
        # false-positive: an UNRELATED record whose stored key equals the candidate key must NOT match
        ex_fp = {pack: [{"id": "R1", "pack": pack, "record_type": "AvoidanceRecord",
                         "statement": "never force push on shared branches", "scope": "production",
                         "canonical_key": ck, "review_status": "confirmed"}]}
        self.assertEqual(pab_merge.classify(ex_fp, c)["verdict"], "novel")

    def test_conflict_fires_for_untyped_records(self):
        # existing record with no record_type (None) must still conflict-match a candidate with rt=''
        ex = {"unknown": [{"id": "R1", "pack": "unknown",
                           "statement": "prefer concise answers always", "scope": "general",
                           "review_status": "confirmed"}]}
        c = {"id": "C1", "pack": "unknown", "statement": "prefer concise short answers", "scope": "general"}
        self.assertEqual(pab_merge.classify(ex, c)["verdict"], "conflict")

    def test_compile_adapter_honors_applies_in_scope_source(self):
        # a record scoped only via applies_in must be excluded from an out-of-scope task adapter,
        # matching context_select's scope-source resolution (the two tools must not diverge)
        recs = {"user.tacit_heuristics": [
            {"id": "via_applies_in", "review_status": "confirmed", "statement": "A",
             "applies_in": ["context.task.code_review"]},
            {"id": "via_scope", "review_status": "confirmed", "statement": "B",
             "scope": ["context.task.code_review"]}]}
        adapter = comp.compile_adapter(recs, [], task_tags=["context.task.writing"])
        leaked = [r["id"] for refs in adapter["sections"].values() for r in refs]
        self.assertEqual(leaked, [])   # both out-of-scope; neither leaks into the writing adapter
        # context_select agrees: same records, same task -> nothing selected
        selected, _ = cs.select_context(
            [recs["user.tacit_heuristics"][0], recs["user.tacit_heuristics"][1]],
            token_budget=10000, task_tags=["context.task.writing"])
        self.assertEqual(selected, [])


class TestSystemicConsistencyIt16(unittest.TestCase):
    """it.16: generalize the it.15 families — the last list-shaped gate (criteria), the merge_rate
    provenance source, cross-tool superseded-id normalization parity, and dup-id sort total order."""

    def _eval(self, crit):
        r = _good_eval()
        r["scoring_rubric"] = {"criteria": crit, "pass_threshold": 0.5}
        r["result"] = {"status": "pass", "score": 0.95}
        return r

    def test_criteria_junk_element_cannot_disable_weight_sum_gate(self):
        # weight 5.0 alone fails; appending a non-dict element must NOT make it pass
        self.assertFalse(vp.validate_record(self._eval([{"check": "a", "weight": 5.0}]), "t").ok)
        self.assertFalse(vp.validate_record(self._eval([{"check": "a", "weight": 5.0}, "JUNK"]), "t").ok)
        self.assertFalse(vp.validate_record(self._eval([{"check": "a", "weight": 0.5}] * 3 + [None]), "t").ok)

    def test_criteria_rejects_malformed_elements(self):
        for crit in ([{"weight": 1.0}], [{"check": "", "weight": 1.0}],
                     [{"check": 99, "weight": 1.0}], [[["a"]]]):
            self.assertFalse(vp.validate_record(self._eval(crit), "t").ok, f"accepted {crit!r}")
        self.assertTrue(vp.validate_record(self._eval([{"check": "a", "weight": 1.0}]), "t").ok)

    def test_superseded_id_normalization_matches_compile_adapter(self):
        # cr._id_set must agree with compile_adapter._as_id_set element-for-element, or the two tools
        # split the runtime-active set on malformed supersedes values
        for val in (["r.real", None], 1024, "r.x", ["a", "", "b"], None, []):
            self.assertEqual(cr._id_set(val), comp._as_id_set(val), f"diverged on {val!r}")

    def test_merge_rate_uses_provenance_not_just_counter(self):
        # merge_history recording 3 merges with no bumped counter must NOT report 0 merges
        import json as _json
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "mh.json")
            with open(p, "w") as fh:
                _json.dump({"user.tacit_heuristics": [
                    {"id": "a", "statement": "x", "scope": "s", "merge_history": ["m1", "m2", "m3"]},
                    {"id": "b", "statement": "y", "scope": "s"}]}, fh)
            out = run_cli([sys.executable, os.path.join(TOOLS, "dedup_check.py"), p])
        # 3 merges in the trail / (3 + 2 records) = 0.6; pre-fix (counter only) would be 0.0
        merge_line = [ln for ln in out.stdout.splitlines() if "merge_rate" in ln][0]
        self.assertIn("0.6", merge_line)

    def test_merge_rate_example_locked_unchanged(self):
        # the provenance-aware count must still reproduce the locked 0.095 on the clean example
        out = run_cli([sys.executable, os.path.join(TOOLS, "dedup_check.py"), EXAMPLE])
        self.assertIn("0.095", out.stdout)

    def test_compile_adapter_dup_id_statement_diff_scope_is_total_order(self):
        recs = {"user.identity_roles": [
            {"id": "x", "statement": "s", "scope": "beta", "review_status": "confirmed"},
            {"id": "x", "statement": "s", "scope": "alpha", "review_status": "confirmed"}]}
        rev = {"user.identity_roles": list(reversed(recs["user.identity_roles"]))}
        a = [r.get("scope") for r in comp.compile_adapter(recs, {})["sections"][comp.SECTION_NAMES[1]]]
        b = [r.get("scope") for r in comp.compile_adapter(rev, {})["sections"][comp.SECTION_NAMES[1]]]
        self.assertEqual(a, b)
        self.assertEqual(a, ["alpha", "beta"])

    def test_context_select_dup_id_statement_diff_tokens_is_total_order(self):
        big = {"id": "x", "statement": "s", "scope": "a", "confidence": 0.9, "label": "L" * 60}
        small = {"id": "x", "statement": "s", "scope": "a", "confidence": 0.9}
        sel1, _ = cs.select_context([big, small], token_budget=18)
        sel2, _ = cs.select_context([small, big], token_budget=18)
        self.assertEqual([r.get("label", "") for r in sel1], [r.get("label", "") for r in sel2])


class TestSchemaBoundParityIt17(unittest.TestCase):
    """it.17: schema-declared numeric bounds ([0,1] score/edit_fraction/weight, (0,1] pass_threshold)
    must be enforced by the standalone validator, and a finite out-of-range edit_fraction must not
    poison the averaged correction_cost (the negative direction is an L3/L4 gaming vector)."""

    def _ev(self, **result):
        r = _good_eval()
        r["scoring_rubric"] = {"criteria": [{"check": "a", "weight": 1.0}], "pass_threshold": 0.7}
        r["result"] = result
        return r

    def test_score_out_of_range_fails(self):
        self.assertFalse(vp.validate_record(self._ev(status="pass", score=5.0), "t").ok)
        self.assertFalse(vp.validate_record(self._ev(status="fail", score=-3.0), "t").ok)
        self.assertTrue(vp.validate_record(self._ev(status="pass", score=0.9), "t").ok)

    def test_edit_fraction_out_of_range_fails(self):
        self.assertFalse(vp.validate_record(self._ev(status="pass", score=0.9, edit_fraction=50.0), "t").ok)
        self.assertFalse(vp.validate_record(self._ev(status="pass", score=0.9, edit_fraction=-5.0), "t").ok)
        self.assertTrue(vp.validate_record(self._ev(status="pass", score=0.9, edit_fraction=0.08), "t").ok)

    def test_out_of_range_edit_fraction_does_not_poison_correction_cost(self):
        for bad in (50.0, -5.0, 1.5):
            ev = [{"record_type": "EvaluationCaseRecord", "id": "e", "review_status": "confirmed",
                   "result": {"status": "pass", "edit_fraction": bad}}]
            cc = cr.compute_indices({}, ev, [])["correction_cost"]
            self.assertIsNone(cc, f"out-of-range {bad} leaked into correction_cost: {cc}")
        # a valid in-range value still counts
        ev = [{"record_type": "EvaluationCaseRecord", "id": "e", "review_status": "confirmed",
               "result": {"status": "pass", "edit_fraction": 0.08}}]
        self.assertAlmostEqual(cr.compute_indices({}, ev, [])["correction_cost"], 0.08)

    def test_criteria_weight_out_of_range_fails_even_if_sum_is_one(self):
        r = self._ev(status="pass", score=0.9)
        r["scoring_rubric"]["criteria"] = [{"check": "a", "weight": 2.0}, {"check": "b", "weight": -1.0}]
        self.assertFalse(vp.validate_record(r, "t").ok)   # sums to 1.0 but weights out of [0,1]

    def test_pass_threshold_above_one_fails(self):
        r = self._ev(status="pass", score=0.9)
        r["scoring_rubric"]["pass_threshold"] = 1.5
        self.assertFalse(vp.validate_record(r, "t").ok)
        r2 = self._ev(status="pass", score=1.0)
        r2["scoring_rubric"]["pass_threshold"] = 1.0   # inclusive upper bound stays valid
        self.assertTrue(vp.validate_record(r2, "t").ok)


class TestLifecycleAndCheckersIt19(unittest.TestCase):
    """it.19: a base-shaped record carrying candidate provenance keys must NOT skip the base gates,
    and the honesty-checkers must not false-negative (gh_slug must drop No/Nl like github-slugger;
    check_commands must capture a shell-prompt-prefixed invocation)."""

    def test_base_record_with_candidate_fields_is_not_skipped(self):
        contaminated = {"id": "r", "record_type": "IdentityRole", "review_status": "confirmed",
                        "sensitivity": "restricted", "evidence_refs": [], "scope": "",
                        "confidence": 0.0, "created_at": "2026-01-01T00:00:00Z",
                        "updated_at": "2026-01-01T00:00:00Z",
                        "candidate_id": "c", "validation_status": "confirmed"}
        self.assertFalse(vp._is_candidate(contaminated))            # base shape wins
        self.assertFalse(vp.validate_record(contaminated, "t").ok)  # G1/G2/G5 fire, not skipped

    def test_legit_candidate_still_recognized(self):
        cand = {"candidate_id": "c", "candidate_type": "PreferenceCandidate",
                "validation_status": "pending", "concise_claim": "x", "evidence_refs": ["e"],
                "confidence": 0.8, "scope": "s", "sensitivity": "internal",
                "proposed_target_pack": "user.persona_core", "extraction_method": "session"}
        self.assertTrue(vp._is_candidate(cand))   # no base markers -> still a candidate (skipped)

    def test_gh_slug_drops_number_other_and_letter_like_github(self):
        self.assertEqual(ca.gh_slug("½ test"), "-test")        # No stripped
        self.assertEqual(ca.gh_slug("S10½ x"), "s10-x")        # No stripped, digits kept
        self.assertEqual(ca.gh_slug("stage 2 intro"), "stage-2-intro")  # Nd digits preserved
        self.assertEqual(ca.gh_slug("한국어 규칙"), "한국어-규칙")        # Korean (Lo) preserved

    def test_check_commands_captures_prompt_prefixed_invocation(self):
        import check_commands as cc  # noqa: E402
        self.assertEqual(cc.commands_in(["$ python3 tools/validate_packs.py examples/x"]),
                         ["python3 tools/validate_packs.py examples/x"])
        self.assertEqual(cc.commands_in(["> python tools/convergence_report.py d"]),
                         ["python tools/convergence_report.py d"])
        # a plain (unprefixed) invocation still captured
        self.assertEqual(cc.commands_in(["python3 tools/dedup_check.py d"]),
                         ["python3 tools/dedup_check.py d"])


class TestMaturityLadderGatesIt20(unittest.TestCase):
    """it.20: the maturity-gate clauses (the whole de-averaging ladder) had NO boundary tests — a
    regression weakening any L2/L3/L4 clause left all tests green. Lock each clause at its boundary
    by driving maturity_tier(ix) directly across the threshold."""

    def _l4_ix(self):
        # a fully L4-Convergent index dict; each test knocks ONE clause below its threshold
        return {"coverage": 1.0, "confirmation_ratio": 1.0, "human_confirmation_ratio": 1.0,
                "decision_fidelity": 1.0, "correction_cost": 0.0, "drift_stability": 1.0,
                "traceability": 1.0, "_seeded_packs": 14, "_content_packs_with_3": 12, "_n_eval": 5}

    def _tier(self, **override):
        ix = self._l4_ix(); ix.update(override)
        return cr.maturity_tier(ix)[0]

    def test_full_l4(self):
        self.assertEqual(self._tier(), "L4")

    def test_l3_drift_stability_boundary(self):                      # it.18 clause
        self.assertEqual(self._tier(drift_stability=0.70, **{}), "L3")   # passes L3, fails L4 drift>=0.85
        self.assertEqual(self._tier(drift_stability=0.69), "L2")        # fails L3 drift>=0.7

    def test_l3_decision_fidelity_boundary(self):
        self.assertEqual(self._tier(decision_fidelity=0.80), "L3")     # passes L3, fails L4 df>=0.9
        self.assertEqual(self._tier(decision_fidelity=0.79), "L2")

    def test_l3_correction_cost_boundary(self):
        self.assertEqual(self._tier(correction_cost=0.30), "L3")       # passes L3, fails L4 cost<=0.15
        self.assertEqual(self._tier(correction_cost=0.31), "L2")

    def test_l3_coverage_boundary(self):
        self.assertEqual(self._tier(coverage=0.80), "L3")              # passes L3, fails L4 coverage==1.0
        self.assertEqual(self._tier(coverage=0.79), "L2")

    def test_l4_drift_stability_boundary(self):
        self.assertEqual(self._tier(drift_stability=0.85), "L4")
        self.assertEqual(self._tier(drift_stability=0.84), "L3")

    def test_l4_correction_cost_boundary(self):
        self.assertEqual(self._tier(correction_cost=0.15), "L4")
        self.assertEqual(self._tier(correction_cost=0.16), "L3")

    def test_l2_coverage_and_df_boundaries(self):
        self.assertEqual(self._tier(coverage=0.50, decision_fidelity=0.6,
                                    correction_cost=0.9, drift_stability=0.0), "L2")
        self.assertEqual(self._tier(coverage=0.49, decision_fidelity=0.6,
                                    correction_cost=0.9, drift_stability=0.0), "L1")
        self.assertEqual(self._tier(coverage=0.5, decision_fidelity=0.59,
                                    correction_cost=0.9, drift_stability=0.0), "L1")

    def test_l1_vertical_required(self):
        self.assertEqual(self._tier(_content_packs_with_3=0, coverage=0.49,
                                    decision_fidelity=0.0), "L0")   # no content depth -> cannot reach L1


class TestPabMergeYamlRoundTripIt20(unittest.TestCase):
    """it.20: pab_merge --out YAML must be readable by the SAME bundled mini-parser convergence and
    compile use, or the documented merge->compile->converge pipeline silently zeroes the merged set."""

    def test_apply_yaml_roundtrips_through_mini_parser(self):
        inst = os.path.join(EXAMPLE, "instance-records.yaml")
        if not os.path.exists(inst):
            self.skipTest("example instance file absent")
        with tempfile.TemporaryDirectory() as tmp:
            empty = os.path.join(tmp, "incoming.json")
            with open(empty, "w") as fh:
                fh.write("[]")
            out = os.path.join(tmp, "instance-records.yaml")
            rc = run_cli([sys.executable, os.path.join(TOOLS, "pab_merge.py"),
                          inst, empty, "--apply", "--out", out])
            self.assertEqual(rc.returncode, 0, rc.stderr)
            parsed = cr.load_structured(out)   # the bundled mini-parser, NOT PyYAML
            self.assertIsNotNone(parsed, "pab_merge YAML output was unreadable by the mini-parser")
            nrec = sum(len(v) for v in parsed.values() if isinstance(v, list))
            self.assertGreater(nrec, 0, "round-trip produced zero records")


class TestUnicodeAndOperationalIt21(unittest.TestCase):
    """it.21: cross-tool NFC normalization (an NFD supersedes ref / scope tag must match its NFC
    counterpart, or a retired record stays LIVE / an in-scope record is dropped), dedup determinism,
    and the new schemas/ integrity gate."""

    def _nfc_nfd(self):
        import unicodedata as ud
        return ud.normalize("NFC", "한국어 규칙"), ud.normalize("NFD", "한국어 규칙")

    def test_nfd_supersedes_retires_nfc_target_in_both_tools(self):
        nfc, nfd = self._nfc_nfd()
        self.assertNotEqual(nfc, nfd)   # genuinely different byte sequences
        pack = "user.persona_core"
        recs = {pack: [
            {"id": nfc, "pack": pack, "record_type": "PreferenceRecord", "statement": "old",
             "review_status": "confirmed", "scope": "g"},
            {"id": "new", "pack": pack, "record_type": "PreferenceRecord", "statement": "new",
             "review_status": "confirmed", "scope": "g", "supersedes": [nfd]}]}
        sup_cr = cr._collect_superseded(recs, [])
        sup_ca = comp.collect_superseded(recs, [])
        self.assertEqual(sup_cr, sup_ca)                       # tools agree
        self.assertIn(cr._norm_id(nfc), sup_cr)                # NFD ref matched NFC target
        self.assertFalse(comp.is_runtime_active(recs[pack][0], sup_ca))  # old record retired, not LIVE

    def test_scope_overlap_matches_across_nfc_nfd(self):
        nfc, nfd = self._nfc_nfd()
        self.assertTrue(cs.scope_overlap([nfd], [nfc]))        # visually-identical tags overlap
        self.assertEqual(cs.normalize_tags([nfd]), cs.normalize_tags([nfc]))

    def test_dedup_check_output_is_deterministic(self):
        import json as _json
        with tempfile.TemporaryDirectory() as tmp:
            for nm in ("z.json", "a.json", "m.json"):
                with open(os.path.join(tmp, nm), "w") as fh:
                    _json.dump({"user.tacit_heuristics": [
                        {"id": nm[0], "statement": "always run the tests before committing code",
                         "scope": "s"}]}, fh)
            r1 = run_cli([sys.executable, os.path.join(TOOLS, "dedup_check.py"), tmp]).stdout
            r2 = run_cli([sys.executable, os.path.join(TOOLS, "dedup_check.py"), tmp]).stdout
            self.assertEqual(r1, r2)   # files are sorted before aggregation -> stable output

    def test_check_schemas_passes_clean_and_catches_defects(self):
        import json as _json
        rc = run_cli([sys.executable, os.path.join(TOOLS, "check_schemas.py"),
                      os.path.join(REPO, "schemas")])
        self.assertEqual(rc.returncode, 0, rc.stdout)          # the shipped schemas are clean
        with tempfile.TemporaryDirectory() as tmp:
            # a well-formed base + a per-pack schema with a broken $ref -> must FAIL
            with open(os.path.join(tmp, "record.base.schema.json"), "w") as fh:
                _json.dump({"$schema": "https://json-schema.org/draft/2020-12/schema",
                            "$id": "x", "title": "t", "description": "d", "type": "object"}, fh)
            with open(os.path.join(tmp, "user.broken.schema.json"), "w") as fh:
                _json.dump({"$schema": "https://json-schema.org/draft/2020-12/schema",
                            "$id": "y", "title": "t", "description": "d",
                            "allOf": [{"$ref": "./DELETED.schema.json"}]}, fh)
            rc2 = run_cli([sys.executable, os.path.join(TOOLS, "check_schemas.py"), tmp])
            self.assertEqual(rc2.returncode, 1, rc2.stdout)


class TestPropertyDeterminismIt23(unittest.TestCase):
    """it.23 (property-based fuzzing follow-up): correction_cost must be order-independent. Plain
    float sum is non-associative, so the same set of edit_fractions in a different order produced a
    last-ULP-different value, breaking byte-identity of the serialized indices. math.fsum fixes it.
    (The fuzzer's other finding — a merge non-fixpoint — did not reproduce against this tree's
    plan_batch intra-batch dedup, so no change was warranted there.)"""

    def _evcase(self, i, ef):
        return {"id": f"x.evalcase.{i}", "record_type": "EvaluationCaseRecord",
                "review_status": "confirmed", "result": {"status": "pass", "edit_fraction": ef}}

    def _cc(self, order):
        evs = [self._evcase(i, v) for i, v in enumerate(order)]
        return cr.compute_indices({}, evs, [])["correction_cost"]

    def test_correction_cost_is_order_independent(self):
        a = self._cc([0.1, 0.1, 0.4])
        b = self._cc([0.1, 0.4, 0.1])
        c = self._cc([0.4, 0.1, 0.1])
        self.assertEqual(a, b)
        self.assertEqual(b, c)
        self.assertAlmostEqual(a, 0.2, places=9)


class TestTriggerContractCluster5(unittest.TestCase):
    """open-design-decisions Cluster 5 (resolved): trigger.schema.json host_hook accepts a single
    token OR a list of tokens (multi-hook binding), so the 7 skill blocks that shipped a composite
    value now validate. check_triggers.py locks the embedded blocks against the schema's own enums."""

    def _run(self, *args):
        return run_cli([sys.executable, os.path.join(TOOLS, "check_triggers.py"), *args])

    def test_all_embedded_triggers_validate(self):
        r = self._run(os.path.join(REPO, "skills"), os.path.join(REPO, "schemas", "trigger.schema.json"))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("0 problem(s)", r.stdout)

    def test_check_triggers_catches_bad_host_hook_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            sk = os.path.join(tmp, "skills"); os.makedirs(sk)
            with open(os.path.join(sk, "x.md"), "w") as fh:
                fh.write("```yaml\ntrigger:\n  trigger_id: pab.evidence_capture.on_x\n"
                         "  skill: evidence_capture\n  signal: turn\n  cadence: continuous\n"
                         "  host_hook: [UserPromptSubmit, BogusHook]\n  produces: evidence_staged\n"
                         "  requires_confirmation: false\n  default_state: enabled\n```\n")
            r = self._run(sk, os.path.join(REPO, "schemas", "trigger.schema.json"))
            self.assertEqual(r.returncode, 1)
            self.assertIn("host_hook", r.stdout)

    def test_schema_host_hook_accepts_string_or_list(self):
        import json as _json
        schema = _json.load(open(os.path.join(REPO, "schemas", "trigger.schema.json"), encoding="utf-8"))
        hh = schema["properties"]["host_hook"]
        self.assertIn("oneOf", hh)                      # no longer a bare single-token enum
        self.assertIn("host_hook_token", schema.get("$defs", {}))


class TestCliExitContractCluster3(unittest.TestCase):
    """open-design-decisions Cluster 3 (resolved): CLI exit-code / loader-signal contract.
    Missing path -> 2 (sibling-tool consistency); multi-doc YAML merges its pack mappings instead of
    fabricating an 'unknown' pack; and a file that reads+parses to None (comment-only) is counted as
    read, so convergence does not conflate 'empty content' with 'no readable files' (exit 2)."""

    def _run(self, tool, *args):
        return run_cli([sys.executable, os.path.join(TOOLS, tool), *args])

    def test_dedup_missing_path_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = self._run("dedup_check.py", os.path.join(tmp, "nope"))
            self.assertEqual(r.returncode, 2)

    def test_dedup_multidoc_yaml_merges_not_phantom_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "multi.yaml")
            with open(p, "w") as fh:
                fh.write("user.tacit_heuristics:\n- {id: h1, statement: aa bb cc, scope: s}\n"
                         "---\nuser.persona_core:\n- {id: t1, statement: dd ee ff, scope: s}\n")
            out = self._run("dedup_check.py", p).stdout
            self.assertIn("across 2 pack(s)", out)   # merged, not one 'unknown' pack
            self.assertNotIn("unknown", out)

    def test_convergence_comment_only_file_not_exit_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "placeholder.yaml"), "w") as fh:
                fh.write("# only a comment, no records yet\n")
            r = self._run("convergence_report.py", tmp)
            self.assertEqual(r.returncode, 0)        # read-but-empty != 'no readable files'

    def test_convergence_truly_empty_dir_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = self._run("convergence_report.py", tmp)
            self.assertEqual(r.returncode, 2)        # genuinely no structured files


class TestMergeSurvivorDeterminismCluster1(unittest.TestCase):
    """open-design-decisions Cluster 1 (resolved): the intra-batch survivor is chosen by a canonical
    (canonical_key, id) tie-break, so plan_batch+apply_plan over ANY permutation of a batch yields
    the same final record set — not a first-arrival-dependent one (it.24 finding)."""

    import itertools as _it

    def _final(self, cands, order):
        batch = [cands[i] for i in order]
        plans = pab_merge.plan_batch({}, batch)
        merged, _ = pab_merge.apply_plan({}, batch, plans, "2026-01-01T00:00:00Z")
        canon = {}
        for pack, recs in merged.items():
            canon[pack] = sorted(
                (r.get("id"), tuple(sorted(r.get("merge_history", []))),
                 r.get("repetition_count"), tuple(sorted(r.get("supersedes", []))))
                for r in recs)
        return canon

    def test_duplicate_group_survivor_is_permutation_invariant(self):
        pack = "user.tacit_heuristics"
        cands = [_cand(id=i) for i in ("x.h.30", "x.h.10", "x.h.20")]   # same ck, distinct ids
        results = {repr(self._final(cands, list(p)))
                   for p in self._it.permutations(range(len(cands)))}
        self.assertEqual(len(results), 1, "duplicate-group final set varied with batch order")
        final = self._final(cands, [0, 1, 2])[pack]
        self.assertEqual(len(final), 1)
        self.assertEqual(final[0][0], "x.h.10")                # min id survives (canonical)
        self.assertEqual(final[0][1], ("x.h.20", "x.h.30"))    # others land in merge_history

    def test_refinement_cluster_is_permutation_invariant(self):
        cands = [_cand(id="x.h.51", scope="email"),
                 _cand(id="x.h.52", scope="chat"),
                 _cand(id="x.h.53", scope="external_email")]    # same identity, different scopes
        results = {repr(self._final(cands, list(p)))
                   for p in self._it.permutations(range(len(cands)))}
        self.assertEqual(len(results), 1, "refinement cluster final set varied with batch order")


class TestPropertyRegressionsIt24(unittest.TestCase):
    """it.24 (property-fuzz follow-up): lock the order-invariance properties that ~113k fuzzer cases
    upheld, so a future change cannot silently break determinism. Each uses a small FIXED record set
    and exhaustive permutations (no randomness) so the test itself is deterministic and fast."""

    import itertools as _it

    def _recs(self):
        # a small mixed set across packs/sections with varied review_status + a superseded record
        return {
            "user.identity_roles": [
                {"id": "role.1", "record_type": "IdentityRole", "statement": "founder",
                 "review_status": "confirmed", "scope": "context.global"},
                {"id": "role.2", "record_type": "IdentityRole", "statement": "maintainer",
                 "review_status": "confirmed", "scope": "context.global"}],
            "user.persona_core": [
                {"id": "trait.1", "record_type": "PreferenceRecord", "statement": "concise",
                 "review_status": "confirmed", "scope": "context.global"},
                {"id": "trait.old", "record_type": "PreferenceRecord", "statement": "verbose",
                 "review_status": "narrowed", "scope": "context.global"}],
            "user.tacit_heuristics": [
                {"id": "heur.1", "record_type": "HeuristicRecord", "statement": "test first",
                 "review_status": "confirmed", "scope": "context.task.code",
                 "supersedes": ["trait.old"]}],
        }

    def _permutations_of(self, recs, limit=6):
        # yield reorderings: permute pack-key order, and reverse within-pack record order
        import json
        keys = list(recs.keys())
        seen = []
        for i, kperm in enumerate(self._it.permutations(keys)):
            if i >= limit:
                break
            d = {}
            for k in kperm:
                rows = list(recs[k])
                d[k] = list(reversed(rows)) if (i % 2) else rows
            seen.append(d)
        return seen

    def test_compile_adapter_is_reorder_deterministic(self):
        import json
        base = self._recs()
        outs = set()
        for perm in self._permutations_of(base):
            adapter = comp.compile_adapter(perm, {})
            outs.add(json.dumps(adapter, sort_keys=True, ensure_ascii=False))
        self.assertEqual(len(outs), 1, "compile_adapter output varied under input reordering")

    def test_convergence_indices_are_reorder_deterministic(self):
        import json
        base = self._recs()
        outs = set()
        for perm in self._permutations_of(base):
            ix = cr.compute_indices(perm, [], [])
            pub = {k: v for k, v in ix.items() if not k.startswith("_")}
            outs.add(json.dumps(pub, sort_keys=True, ensure_ascii=False))
        self.assertEqual(len(outs), 1, "convergence indices varied under input reordering")

    def test_context_select_budget_is_monotone_nested(self):
        recs = [
            {"id": "a", "statement": "alpha rule", "scope": "context.task.code",
             "confidence": 0.95, "repetition_count": 3},
            {"id": "b", "statement": "beta rule here", "scope": "context.task.code",
             "confidence": 0.8, "repetition_count": 2},
            {"id": "c", "statement": "gamma rule longer text", "scope": "context.task.code",
             "confidence": 0.6, "repetition_count": 1},
        ]
        prev = set()
        for budget in range(0, 120, 4):
            selected, _ = cs.select_context(recs, token_budget=budget,
                                            task_tags=["context.task.code"])
            ids = {r["id"] for r in selected}
            # nesting: nothing selected at a smaller budget may be dropped at a larger one
            self.assertTrue(prev <= ids, f"budget {budget}: previously-selected dropped ({prev} -> {ids})")
            prev = ids

    def test_dedup_pairs_are_reorder_stable(self):
        import json
        recs = {"user.tacit_heuristics": [
            {"id": f"h{i}", "statement": s, "scope": "s"} for i, s in enumerate([
                "always run the tests before committing the code",
                "always run the tests prior to committing the code",
                "prefer subprocess over os system for shell calls"])]}
        with tempfile.TemporaryDirectory() as tmp:
            outs = set()
            for i in range(3):
                rows = list(recs["user.tacit_heuristics"])
                rows = rows[i:] + rows[:i]   # rotate input order
                p = os.path.join(tmp, "r.json")
                with open(p, "w") as fh:
                    json.dump({"user.tacit_heuristics": rows}, fh)
                out = run_cli([sys.executable, os.path.join(TOOLS, "dedup_check.py"), p]).stdout
                # the redundancy_ratio line must be invariant under input rotation
                ratio = [ln for ln in out.splitlines() if "redundancy_ratio" in ln]
                outs.add(ratio[0] if ratio else "")
            self.assertEqual(len(outs), 1, "dedup redundancy_ratio varied under input rotation")


class TestGamingDefensesCluster2(unittest.TestCase):
    """open-design-decisions Cluster 2 (partially resolved): the two concrete maturity-gaming
    vectors are closed while every locked example number is preserved. V1 = cross-pack id
    double-count (global id de-dup); V4 = drift_stability asymmetry (union of supersedes-target ids
    across ALL packs + bare drift events)."""

    CONTENT = ["user.persona_core", "user.communication_style", "user.decision_policy",
               "user.tacit_heuristics", "user.red_flags", "user.workflow_playbooks",
               "user.domain_overlays", "user.tool_stack", "user.artifact_policy",
               "user.boundary_authority", "user.identity_roles", "user.memory_project_graph"]

    def _rec(self, rid, stmt, scope="g", **kw):
        r = {"id": rid, "record_type": "PreferenceRecord", "statement": stmt, "scope": scope,
             "review_status": "confirmed", "evidence_refs": ["e"], "confidence": 1.0,
             "reliability": "behavioral"}
        r.update(kw)
        return r

    def test_v1_cross_pack_id_reuse_cannot_inflate_coverage(self):
        shared = [self._rec(f"a.{i}", f"claim {i}") for i in range(3)]
        atk = {p: [dict(r) for r in shared] for p in self.CONTENT}   # SAME 3 ids under 12 packs
        ix = cr.compute_indices(atk, [], [])
        # deduped: the 3 ids count toward exactly ONE content pack, not twelve
        self.assertEqual(ix["_content_packs_with_3"], 1)
        self.assertEqual(ix["_n_confirmed"], 3)                      # 3 distinct records, not 36
        self.assertEqual(cr.maturity_tier(ix)[0], "L0")             # honest, not L3

    def test_v4_content_pack_supersedes_counts_toward_drift(self):
        base = {"user.persona_core": [self._rec(f"r{i}", f"s{i}") for i in range(20)]}
        for i in range(6):   # retire 6 via content-pack supersedes edges, NO DriftRecords
            base["user.persona_core"].append(
                self._rec(f"n{i}", f"s{i} v2", scope="g2", supersedes=[f"r{i}"]))
        ix = cr.compute_indices(base, [], [])
        self.assertLess(ix["drift_stability"], 1.0)                 # was a vacuous 1.0
        self.assertEqual(ix["_supersessions"], 6)                   # the 6 hidden reversals count

    def test_example_numbers_preserved_under_new_counting(self):
        res = cr.collect(EXAMPLE)
        ix = cr.compute_indices(res[0], res[1], res[2])
        self.assertEqual(ix["_n_confirmed"], 19)
        self.assertEqual(ix["_supersessions"], 2)                  # 2 bare DriftRecords, unchanged
        self.assertAlmostEqual(ix["drift_stability"], 0.8947, places=4)
        self.assertAlmostEqual(ix["coverage"], 0.0714, places=4)
        self.assertEqual(ix["_content_packs_with_3"], 0)
        self.assertEqual(cr.maturity_tier(ix)[0], "L0")


# ───────────────────── bootstrap plan (skill 17, it.28) ─────────────────────
class TestBootstrapPlanIt28(unittest.TestCase):
    """skills/17-bootstrap.md Stage-2 mapping contract: the deterministic plan tool must
    reproduce the exact pack inventory the bootstrap adapter promises — 17 skill packs +
    12 spec packs + 14 template packs + 1 shared-schema pack = 44 builder packs and 14
    EMPTY personal shells — and follow the sibling CLI contract (missing root -> exit 2)."""

    def _run(self, *args):
        return run_cli([sys.executable, os.path.join(TOOLS, "bootstrap_plan.py"), *args])

    def test_plan_counts_locked_to_repo_inventory(self):
        r = self._run(REPO, "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        plan = json.loads(r.stdout)
        self.assertEqual(plan["counts"], {"skills": 17, "specs": 12, "templates": 14,
                                          "builder_packs": 44, "personal_shells": 14})
        self.assertEqual(len(plan["projects"]), 3)

    def test_plan_is_deterministic_and_names_follow_the_contract(self):
        a, b = self._run(REPO, "--json").stdout, self._run(REPO, "--json").stdout
        self.assertEqual(a, b)
        plan = json.loads(a)
        packs = [p["pack"] for p in plan["builder_packs"]]
        self.assertIn("skill.pab.bootstrap.v0.1", packs)            # 17-bootstrap.md -> snake name
        self.assertIn("skill.pab.tacit_knowledge_mining.v0.1", packs)
        self.assertIn("pa.kernel_schema.v0.1", packs)               # spec/01 -> pa.*
        self.assertIn("personal.persona_core.template.v0.1", packs)
        self.assertEqual(packs[-1], "pa.shared_schemas.v0.1")       # the 3 shared schemas, one pack
        # template packs carry BOTH the yaml template and its paired json schema as sources
        tmpl = next(p for p in plan["builder_packs"] if p["pack"] == "personal.persona_core.template.v0.1")
        self.assertEqual(len(tmpl["source"]), 2)
        self.assertEqual(tmpl["source"], ["templates/user.persona_core.template.yaml",
                                          "schemas/user.persona_core.schema.json"])
        for item in plan["builder_packs"]:
            self.assertTrue(all("\\" not in src for src in item["source"]), item)

    def test_subject_names_the_shells_and_missing_root_exits_2(self):
        plan = json.loads(self._run(REPO, "--subject", "logotekton", "--json").stdout)
        self.assertTrue(all(s.startswith("personal.logotekton.") for s in plan["personal_shells"]))
        with tempfile.TemporaryDirectory() as tmp:
            r = self._run(os.path.join(tmp, "nope"))
            self.assertEqual(r.returncode, 2)

    def test_subject_grammar_enforced_with_normalization_hint(self):
        # skill 17 Stage 0: the owner-chosen handle must fit the record-id grammar; the tool
        # rejects (never silently rewrites) and proposes the normalized form.
        r = self._run(REPO, "--subject", "Logo Tekton!", "--json")
        self.assertEqual(r.returncode, 2)
        self.assertIn("logo_tekton", r.stderr)
        for ok in ("logo_tekton", "logotekton2", "a_b_c"):
            self.assertEqual(self._run(REPO, "--subject", ok, "--json").returncode, 0, ok)


if __name__ == "__main__":
    unittest.main(verbosity=2)
