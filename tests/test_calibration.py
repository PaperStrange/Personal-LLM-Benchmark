"""Regression test for judge/calibration.py — the Jev-vs-senior
agreement ritual.

Exercises both the happy path (high agreement) and the RECALIBRATE flag
path (a judge that disagrees with the senior on one item), using temp CSVs
passed as explicit paths.
"""
import csv
import os
import subprocess
import sys
import tempfile
import unittest

PACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CALIBRATION = os.path.join(PACK, "judge", "calibration.py")

HEADER = ["date", "run_id", "item_id", "jev_norm", "senior_norm",
          "jev_choice", "senior_choice", "notes"]


def write_csv(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        w.writerows(rows)


def numeric_row(date, run_id, item_id, jev, sen, notes=""):
    return [date, run_id, item_id, jev, sen, "", "", notes]


def choice_row(date, run_id, item_id, jev_c, sen_c, notes=""):
    return [date, run_id, item_id, "", "", jev_c, sen_c, notes]


def kappa_line(stdout, item_id):
    """Return the kappa-table line for item_id, or None."""
    in_cat = False
    for line in stdout.splitlines():
        if line.startswith("categorical agreement"):
            in_cat = True
            continue
        if in_cat and line.startswith(item_id):
            return line
    return None


def run_calibration(csv_path):
    return subprocess.run(
        [sys.executable, CALIBRATION, csv_path],
        capture_output=True, text=True, cwd=PACK)


class CalibrationTest(unittest.TestCase):
    def test_high_agreement(self):
        rows = [
            ["2026-09-22", "r1", "t1_arch", 0.83, 0.80, ""],
            ["2026-09-22", "r1", "t1_plan", 0.80, 0.80, ""],
            ["2026-09-22", "r1", "t1_trust", 0.77, 0.75, ""],
        ]
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = os.path.join(tmp, "cal.csv")
            write_csv(csv_path, rows)
            p = run_calibration(csv_path)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("100%", p.stdout)
        self.assertIn("no items below the recalibration threshold.", p.stdout)

    def test_recalibrate_flag(self):
        # One item where the judge disagrees with the senior twice
        # (|diff| = 0.5 > 0.15) must be flagged RECALIBRATE.
        rows = [
            ["2026-09-22", "r1", "t1_trust", 0.80, 0.30, "judge overrates"],
            ["2026-09-22", "r2", "t1_trust", 0.75, 0.25, "judge overrates"],
            ["2026-09-22", "r1", "t1_arch", 0.83, 0.80, ""],
        ]
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = os.path.join(tmp, "cal.csv")
            write_csv(csv_path, rows)
            p = run_calibration(csv_path)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("RECALIBRATE", p.stdout)
        self.assertIn("t1_trust", p.stdout)
        self.assertIn("recalibrate these items: t1_trust", p.stdout)

    def test_missing_file_exits_2(self):
        p = run_calibration(os.path.join("does-not-exist", "cal.csv"))
        self.assertEqual(p.returncode, 2)
        self.assertIn("No calibration data yet", p.stderr)

    def test_kappa_perfect_agreement(self):
        # Hand-verifiable: 4 identical (under_15_min, under_15_min) pairs.
        # p_o = 1, p_e = 1 -> kappa = 1.0 by the degenerate-case rule.
        rows = [choice_row("2026-09-30", "r1", "t3_time",
                           "under_15_min", "under_15_min")
                for _ in range(4)]
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = os.path.join(tmp, "cal.csv")
            write_csv(csv_path, rows)
            p = run_calibration(csv_path)
        self.assertEqual(p.returncode, 0, p.stderr)
        line = kappa_line(p.stdout, "t3_time")
        self.assertIsNotNone(line, "no kappa row for t3_time:\n" + p.stdout)
        self.assertIn("1.000", line)
        self.assertNotIn("skipped", p.stderr)

    def test_kappa_chance_agreement(self):
        # Hand-verifiable: (a,a),(a,b),(b,a),(b,b) with a=under_15_min,
        # b=under_1_hour. p_o = 2/4 = 0.5; marginals are 0.5/0.5 for both
        # judges, so p_e = 0.25 + 0.25 = 0.5 -> kappa = 0.0 exactly.
        a, b = "under_15_min", "under_1_hour"
        rows = [choice_row("2026-09-30", "r1", "t3_time", jc, sc)
                for jc, sc in [(a, a), (a, b), (b, a), (b, b)]]
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = os.path.join(tmp, "cal.csv")
            write_csv(csv_path, rows)
            p = run_calibration(csv_path)
        self.assertEqual(p.returncode, 0, p.stderr)
        line = kappa_line(p.stdout, "t3_time")
        self.assertIsNotNone(line, "no kappa row for t3_time:\n" + p.stdout)
        self.assertIn("0.000", line)

    def test_kappa_moderate_agreement_from_fixture(self):
        # The checked-in results/calibration.csv carries 6 t3_time verdict
        # pairs with hand-verified kappa = 0.500 (p_o = 4/6, p_e = 1/3).
        # Kappa must be computed from the rows, never hardcoded.
        p = run_calibration(os.path.join(PACK, "results", "calibration.csv"))
        self.assertEqual(p.returncode, 0, p.stderr)
        line = kappa_line(p.stdout, "t3_time")
        self.assertIsNotNone(line, "no kappa row for t3_time:\n" + p.stdout)
        self.assertIn("0.500", line)
        # The numeric table still reports on the score rows in the same file.
        self.assertIn("overall agreement", p.stdout)

    def test_mixed_numeric_and_categorical_rows(self):
        # One row carrying both a numeric score pair and a categorical
        # verdict pair must land in both tables, not be skipped.
        rows = [
            ["2026-09-30", "r1", "t3_time", 0.90, 0.90,
             "under_15_min", "under_15_min", "dual verdict row"],
        ]
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = os.path.join(tmp, "cal.csv")
            write_csv(csv_path, rows)
            p = run_calibration(csv_path)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("100%", p.stdout)  # numeric table
        line = kappa_line(p.stdout, "t3_time")
        self.assertIsNotNone(line, "no kappa row for t3_time:\n" + p.stdout)
        self.assertIn("1.000", line)
        self.assertNotIn("skipped", p.stderr)


if __name__ == "__main__":
    unittest.main()
