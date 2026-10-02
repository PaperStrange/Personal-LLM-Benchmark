"""Regression test for judge/aggregate.py — pass@k / pass^k reporting.

Builds three --json-out payloads (composites 72.5 / 58.0 / 65.0, threshold
60) so exactly one run is below bar: expects pass@k=1 ("capable") but
pass^3=0 ("flaky"), the path that single-run scoring would hide.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

PACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGGREGATE = os.path.join(PACK, "judge", "aggregate.py")


def make_run(composite, value, run_id=None):
    payload = {
        "task": "T1",
        "composite": composite,
        "mean_confidence": 0.75,
        "flagged": [],
        "items": [
            {"id": "t1_arch", "kind": "score", "result": "x",
             "conf": 0.8, "weight": 2, "value": value},
            {"id": "t1_trust", "kind": "score", "result": "x",
             "conf": 0.7, "weight": 3, "value": value},
        ],
        "deterministic_recall": None,
        "est_cost_usd": 0.0001,
    }
    if run_id is not None:
        payload["run_id"] = run_id
    return payload


def write_run(tmp, name, payload):
    p = os.path.join(tmp, name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(payload, f)
    return p


class AggregateTest(unittest.TestCase):
    def test_pass_at_k_and_pass_cubed(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for i, (comp, val) in enumerate(
                    [(72.5, 0.80), (58.0, 0.55), (65.0, 0.70)]):
                p = os.path.join(tmp, "run%d.json" % i)
                with open(p, "w", encoding="utf-8") as f:
                    json.dump(make_run(comp, val), f)
                paths.append(p)
            p = subprocess.run(
                [sys.executable, AGGREGATE, *paths, "--threshold", "60"],
                capture_output=True, text=True, cwd=PACK)
        self.assertEqual(p.returncode, 0, p.stderr)
        out = p.stdout
        self.assertIn("runs: 3", out)
        self.assertIn("succeeded runs: 2/3", out)
        self.assertIn("pass@k (>=1 of 3 runs succeeded): 1", out)
        self.assertIn("pass^3 (all 3 runs succeeded):   0", out)
        self.assertIn("capable but flaky", out)

    def test_all_pass_reliable(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for i, comp in enumerate([72.5, 70.0, 65.0]):
                p = os.path.join(tmp, "run%d.json" % i)
                with open(p, "w", encoding="utf-8") as f:
                    json.dump(make_run(comp, 0.75), f)
                paths.append(p)
            p = subprocess.run(
                [sys.executable, AGGREGATE, *paths, "--threshold", "60"],
                capture_output=True, text=True, cwd=PACK)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("pass@k (>=1 of 3 runs succeeded): 1", p.stdout)
        self.assertIn("pass^3 (all 3 runs succeeded):   1", p.stdout)
        self.assertIn("reliable", p.stdout)

    def test_per_item_means(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for i, (comp, val) in enumerate(
                    [(72.5, 0.80), (58.0, 0.55), (65.0, 0.70)]):
                p = os.path.join(tmp, "run%d.json" % i)
                with open(p, "w", encoding="utf-8") as f:
                    json.dump(make_run(comp, val), f)
                paths.append(p)
            p = subprocess.run(
                [sys.executable, AGGREGATE, *paths, "--threshold", "60"],
                capture_output=True, text=True, cwd=PACK)
        self.assertEqual(p.returncode, 0, p.stderr)
        # mean of 0.80/0.55/0.70 = 0.683...; min..max 0.55..0.80
        self.assertIn("t1_arch", p.stdout)
        self.assertIn("0.55..0.80", p.stdout)
        self.assertIn("composite: mean 65.2", p.stdout)

    # Independence guard: pass@k/pass^k count independent rollouts, never
    # the same rollout twice. Duplicates must fail loudly (exit 2).

    def test_same_file_twice_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p0 = write_run(tmp, "run0.json", make_run(72.5, 0.80))
            p = subprocess.run(
                [sys.executable, AGGREGATE, p0, p0, "--threshold", "60"],
                capture_output=True, text=True, cwd=PACK)
        self.assertEqual(p.returncode, 2, p.stdout)
        self.assertIn("byte-identical", p.stderr)

    def test_copied_file_rejected(self):
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            p0 = write_run(tmp, "run0.json", make_run(72.5, 0.80))
            p1 = os.path.join(tmp, "run0-copy.json")
            shutil.copy(p0, p1)  # different path, same bytes
            p = subprocess.run(
                [sys.executable, AGGREGATE, p0, p1, "--threshold", "60"],
                capture_output=True, text=True, cwd=PACK)
        self.assertEqual(p.returncode, 2, p.stdout)
        self.assertIn("byte-identical", p.stderr)

    def test_duplicate_run_id_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Same run_id, different content: the copy-a-rollout fabrication.
            p0 = write_run(tmp, "run0.json",
                           make_run(72.5, 0.80, run_id="abc123"))
            p1 = write_run(tmp, "run1.json",
                           make_run(65.0, 0.70, run_id="abc123"))
            p = subprocess.run(
                [sys.executable, AGGREGATE, p0, p1, "--threshold", "60"],
                capture_output=True, text=True, cwd=PACK)
        self.assertEqual(p.returncode, 2, p.stdout)
        self.assertIn("duplicate run_id", p.stderr)

    def test_distinct_run_ids_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            p0 = write_run(tmp, "run0.json",
                           make_run(72.5, 0.80, run_id="aaa"))
            p1 = write_run(tmp, "run1.json",
                           make_run(65.0, 0.70, run_id="bbb"))
            p = subprocess.run(
                [sys.executable, AGGREGATE, p0, p1, "--threshold", "60"],
                capture_output=True, text=True, cwd=PACK)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("pass^2 (all 2 runs succeeded):   1", p.stdout)


    # Composite spread: the per-candidate summary reports mean/std/min/max
    # of the composite across rollouts (population std, so a single rollout
    # has std 0.0 rather than undefined). The README's tie-band policy reads
    # this number.

    def _aggregate(self, composites):
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for i, comp in enumerate(composites):
                p = os.path.join(tmp, "run%d.json" % i)
                with open(p, "w", encoding="utf-8") as f:
                    json.dump(make_run(comp, 0.7), f)
                paths.append(p)
            p = subprocess.run(
                [sys.executable, AGGREGATE, *paths, "--threshold", "60"],
                capture_output=True, text=True, cwd=PACK)
        return p

    def _std_of(self, composites):
        p = self._aggregate(composites)
        self.assertEqual(p.returncode, 0, p.stderr)
        m = re.search(r"composite: mean [\d.]+ / std ([\d.]+) /", p.stdout)
        self.assertIsNotNone(m, "std missing from scorecard: %s" % p.stdout)
        return float(m.group(1))

    def test_composite_std_reported(self):
        p = self._aggregate([72.5, 58.0, 65.0])
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("composite: mean 65.2 / std", p.stdout)

    def test_composite_std_correct(self):
        # pstdev([72.5, 58.0, 65.0]) = 5.92... (population std, not n-1)
        self.assertAlmostEqual(self._std_of([72.5, 58.0, 65.0]), 5.92, places=1)

    def test_composite_std_single_run_zero(self):
        self.assertEqual(self._std_of([72.5]), 0.0)

    def test_composite_std_reflects_spread(self):
        narrow = self._std_of([60.0, 61.0, 62.0])
        wide = self._std_of([40.0, 60.0, 80.0])
        self.assertLess(narrow, wide)


if __name__ == "__main__":
    unittest.main()
