"""Regression test for judge/jev_judge.py — the Jev scoring pipeline.

Runs the real script against the canned mock typesafe_sdk (self-contained
copy in tests/helpers/mock_typesafe): validates stdout shape, the
low-confidence flag path, the --json-out schema, and the deterministic
debt-recall hook. Does NOT validate real Jev output — that needs a live
calibration call (see methodology report, finding F3).
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

PACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JUDGE = os.path.join(PACK, "judge", "jev_judge.py")
MOCK_SDK = os.path.join(PACK, "tests", "helpers", "mock_typesafe")
RUBRIC = os.path.join(PACK, "rubrics", "rubric-T1.json")
INVENTORY = os.path.join(PACK, "fixture", "DEBT-INVENTORY.md")

# A candidate that cites a few known anchors, so deterministic recall is
# non-trivial but not perfect.
CANDIDATE = """# Review
config.py:5 hardcodes SECRET_KEY. db.py:24 has SQL injection.
db.py:12 leaks connections. reports.py:9 duplicates tax logic.
The architecture is a god module in billing.py.
"""

REQUIRED_JSON_KEYS = {"task", "composite", "mean_confidence", "flagged",
                      "items", "deterministic_recall", "est_cost_usd",
                      "fixture_vintage"}
REQUIRED_ITEM_KEYS = {"id", "kind", "result", "conf", "weight", "value"}


def run_judge(candidate, json_out, mock_run="1", extra_args=()):
    env = dict(os.environ)
    env["PYTHONPATH"] = MOCK_SDK + os.pathsep + env.get("PYTHONPATH", "")
    env["TYPESAFE_API_KEY"] = "dryrun-test"
    env["MOCK_RUN"] = mock_run
    return subprocess.run(
        [sys.executable, JUDGE, "--rubric", RUBRIC, "--candidate", candidate,
         "--inventory", INVENTORY, "--json-out", json_out, *extra_args],
        capture_output=True, text=True, cwd=PACK, env=env)


class JudgePipelineTest(unittest.TestCase):
    def test_exit_and_stdout_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            cand = os.path.join(tmp, "cand.md")
            with open(cand, "w", encoding="utf-8") as f:
                f.write(CANDIDATE)
            p = run_judge(cand, os.path.join(tmp, "out.json"))
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("composite:", p.stdout)
        self.assertIn("mean confidence:", p.stdout)
        self.assertIn("deterministic debt recall:", p.stdout)

    def test_low_confidence_flag_path(self):
        # Mock run 1 gives t1_precision confidence 0.52 (< 0.55 threshold),
        # which must be routed to senior review.
        with tempfile.TemporaryDirectory() as tmp:
            cand = os.path.join(tmp, "cand.md")
            with open(cand, "w", encoding="utf-8") as f:
                f.write(CANDIDATE)
            out = os.path.join(tmp, "out.json")
            p = run_judge(cand, out, mock_run="1")
            with open(out, encoding="utf-8") as f:
                data = json.load(f)
        self.assertIn("LOW CONFIDENCE", p.stdout)
        self.assertIn("t1_precision", p.stdout)
        self.assertIn("t1_precision", data["flagged"])

    def test_low_conf_threshold_flag_is_honored(self):
        # --low-conf-threshold must change flagging in both directions.
        # MOCK_RUN=1 gives t1_precision confidence 0.52; MOCK_RUN=2 gives
        # t1_precision confidence 0.60 (all other confs are higher).
        with tempfile.TemporaryDirectory() as tmp:
            cand = os.path.join(tmp, "cand.md")
            with open(cand, "w", encoding="utf-8") as f:
                f.write(CANDIDATE)
            # Lower the bar: 0.52 is no longer below the threshold.
            out = os.path.join(tmp, "low.json")
            p = run_judge(cand, out, mock_run="1",
                          extra_args=["--low-conf-threshold", "0.50"])
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            with open(out, encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data["flagged"], [])
            self.assertNotIn("LOW CONFIDENCE", p.stdout)
            # Raise the bar: 0.60 is now below the threshold.
            out = os.path.join(tmp, "high.json")
            p = run_judge(cand, out, mock_run="2",
                          extra_args=["--low-conf-threshold", "0.61"])
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            with open(out, encoding="utf-8") as f:
                data = json.load(f)
            self.assertIn("t1_precision", data["flagged"])
            self.assertIn("LOW CONFIDENCE (< 0.61)", p.stdout)

    def test_json_out_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            cand = os.path.join(tmp, "cand.md")
            with open(cand, "w", encoding="utf-8") as f:
                f.write(CANDIDATE)
            out = os.path.join(tmp, "out.json")
            p = run_judge(cand, out)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            with open(out, encoding="utf-8") as f:
                data = json.load(f)
        self.assertTrue(REQUIRED_JSON_KEYS <= set(data),
                        "missing keys: %s" % (REQUIRED_JSON_KEYS - set(data)))
        self.assertGreaterEqual(data["composite"], 0)
        self.assertLessEqual(data["composite"], 100)
        self.assertIsInstance(data["items"], list)
        self.assertGreater(len(data["items"]), 0)
        for it in data["items"]:
            with self.subTest(item=it.get("id")):
                self.assertTrue(REQUIRED_ITEM_KEYS <= set(it),
                                "item missing keys: %s"
                                % (REQUIRED_ITEM_KEYS - set(it)))
                self.assertIsNotNone(it["id"])
                self.assertIn(it["kind"], {"score", "choice", "noul"})

    def test_deterministic_recall_hook(self):
        with tempfile.TemporaryDirectory() as tmp:
            cand = os.path.join(tmp, "cand.md")
            with open(cand, "w", encoding="utf-8") as f:
                f.write(CANDIDATE)
            out = os.path.join(tmp, "out.json")
            p = run_judge(cand, out)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            with open(out, encoding="utf-8") as f:
                data = json.load(f)
        # Candidate cites config.py:5, db.py:24, db.py:12, reports.py:9 —
        # exactly 4 of the 22 inventory anchors.
        self.assertEqual(data["deterministic_recall"]["found"], 4)
        self.assertEqual(data["deterministic_recall"]["total"], 22)


if __name__ == "__main__":
    unittest.main()
