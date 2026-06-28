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


# ───────────────────────── convergence: locked example numbers ─────────────
class TestConvergenceExample(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pack_records, eval_cases, drift_records, n = cr.collect(EXAMPLE)
        cls.ix = cr.compute_indices(pack_records, eval_cases, drift_records)
        cls.tier, cls.tname, _ = cr.maturity_tier(cls.ix)
        cls.n_files = n

    def test_maturity_is_L2(self):
        self.assertEqual(self.tier, "L2")

    def test_six_indices_locked(self):
        ix = self.ix
        self.assertTrue(almost(ix["coverage"], 0.714285, 3), ix["coverage"])
        self.assertTrue(almost(ix["coverage_strict"], 0.071428, 3), ix["coverage_strict"])
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

    def test_only_L3_blocker_is_coverage(self):
        # with correction_cost measured, the sole remaining L3 gap is coverage (#7)
        _, _, reasons = cr.maturity_tier(self.ix)
        unmet = [k for k, ok in reasons.items() if k.startswith("L3_") and not ok]
        self.assertEqual(unmet, ["L3_coverage>=0.8"])


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
            "traceability": 1.0, "_seeded_packs": 8, "_n_eval": 3,
        }
        tier, _, reasons = cr.maturity_tier(base)
        self.assertFalse(reasons["L2_human_confirmation_ratio>=0.6"])
        self.assertNotEqual(tier, "L2")  # blocked despite confirmation_ratio 0.75
        # had the same confirms been human-gated (hcr 0.75), L2 legitimately opens
        tier2, _, _ = cr.maturity_tier({**base, "human_confirmation_ratio": 0.75})
        self.assertEqual(tier2, "L2")


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
        self.assertIn("L2 Working", r.stdout)
        self.assertIn("0.71", r.stdout)

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
