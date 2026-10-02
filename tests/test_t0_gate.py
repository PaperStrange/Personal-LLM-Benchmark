"""Regression tests for src/llm_workflow_eval/judge/t0_checks.py — the T0 deterministic gate.

Runs the real script in subprocesses against synthetic candidates and
workdirs, asserting exit codes and [PASS]/[FAIL] markers. The T1 good-path
test points --workdir at the real fixture/legacy-billing (read-only; the
script never writes).
"""
import os
import subprocess
import sys
import tempfile
import unittest

PACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T0 = os.path.join(PACK, "src", "llm_workflow_eval", "judge", "t0_checks.py")
FIXTURE = os.path.join(PACK, "fixture", "legacy-billing")
INVENTORY = os.path.join(PACK, "fixture", "DEBT-INVENTORY.md")


def run_t0(*args):
    return subprocess.run(
        [sys.executable, T0, *args],
        capture_output=True, text=True, cwd=PACK,
    )


T1_GOOD = """# Review

## Architecture
The architecture centers on billing.py with db.py helpers.

## Debt inventory
config.py:5 hardcodes SECRET_KEY. db.py:24 has SQL injection.

## Risk register
risk of credential leak is high.

## 30/60/90 plan
30/60/90-day modernization plan: rotate secrets, parameterize SQL.
"""

T1_BAD = """# Review

## Architecture
Some architecture text. config.py:5 is cited.

## Debt inventory
db.py:24 is a problem.

## Risk register
risk noted.
Ref billing.py:9999 which does not exist.
"""  # missing plan section + out-of-range ref

T2_BILLING_GOOD = '''"""Billing module."""


def apply_discount(invoice_id, pct):
    """Apply a percent discount."""
    if not 0 < pct <= 100:
        raise ValueError("pct must satisfy 0 < pct <= 100")
    return 90.0
'''

T2_BILLING_STUB = '''"""Billing module."""


def apply_discount(invoice_id, pct):
    """STUB."""
    raise NotImplementedError("apply_discount not implemented yet")
'''

T3_GOOD = """# Expandability report
Installed the acme-formatter plugin from github.com/acme/acme-formatter.
Time-to-working: about 30 minutes. The install worked and the demo ran.
"""

T3_BAD = """# Expandability report
Installed some plugin. Time-to-working: about 30 minutes. It worked.
"""  # names a plugin but no repo URL/host


def write(path, content, mtime=None):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    if mtime is not None:
        os.utime(path, (mtime, mtime))


class T0GateTest(unittest.TestCase):
    # ---- T1 ----
    def test_t1_good_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            cand = os.path.join(tmp, "cand.md")
            write(cand, T1_GOOD)
            p = run_t0("--task", "T1", "--candidate", cand,
                       "--inventory", INVENTORY, "--workdir", FIXTURE)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("ALL CHECKS PASSED", p.stdout)
        self.assertIn("[PASS] t1_sections", p.stdout)
        self.assertIn("[PASS] t1_refs_valid", p.stdout)

    def test_t1_bad_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            cand = os.path.join(tmp, "cand.md")
            write(cand, T1_BAD)
            p = run_t0("--task", "T1", "--candidate", cand,
                       "--inventory", INVENTORY, "--workdir", FIXTURE)
        self.assertEqual(p.returncode, 1)
        self.assertIn("GATE FAILED", p.stdout)
        self.assertIn("[FAIL] t1_sections", p.stdout)
        self.assertIn("[FAIL] t1_refs_valid", p.stdout)
        self.assertIn("billing.py:9999", p.stdout)

    # ---- T2 ----
    def _t2_workdir(self, tmp, plan_first=True, stub=False):
        t0 = 1_700_000_000.0
        billing = T2_BILLING_STUB if stub else T2_BILLING_GOOD
        if plan_first:
            write(os.path.join(tmp, "PLAN.md"), "# Plan\nDo it right.", t0)
            write(os.path.join(tmp, "billing.py"), billing, t0 + 10)
        else:  # plan written AFTER the code edit: the dry-run failure mode
            write(os.path.join(tmp, "billing.py"), billing, t0)
            write(os.path.join(tmp, "PLAN.md"), "# Plan\nDo it right.", t0 + 10)
        write(os.path.join(tmp, "REVIEW.md"),
              "# Review\nVerdict: approve.\nTest evidence: passed 5/5.")
        cand = os.path.join(tmp, "cand.md")
        write(cand, "# T2 deliverable\nplan + review + test log")
        return tmp, cand

    def test_t2_good_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            wd, cand = self._t2_workdir(tmp)
            p = run_t0("--task", "T2", "--candidate", cand, "--workdir", wd)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("ALL CHECKS PASSED", p.stdout)
        self.assertIn("[PASS] t2_plan_before_code", p.stdout)

    def test_t2_bad_ordering_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            wd, cand = self._t2_workdir(tmp, plan_first=False)
            p = run_t0("--task", "T2", "--candidate", cand, "--workdir", wd)
        self.assertEqual(p.returncode, 1)
        self.assertIn("[FAIL] t2_plan_before_code", p.stdout)

    def test_t2_bad_stub_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            wd, cand = self._t2_workdir(tmp, stub=True)
            p = run_t0("--task", "T2", "--candidate", cand, "--workdir", wd)
        self.assertEqual(p.returncode, 1)
        self.assertIn("[FAIL] t2_implemented", p.stdout)

    # ---- T3 ----
    def test_t3_good_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            cand = os.path.join(tmp, "cand.md")
            write(cand, T3_GOOD)
            p = run_t0("--task", "T3", "--candidate", cand)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("ALL CHECKS PASSED", p.stdout)

    def test_t3_bad_missing_url_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            cand = os.path.join(tmp, "cand.md")
            write(cand, T3_BAD)
            p = run_t0("--task", "T3", "--candidate", cand)
        self.assertEqual(p.returncode, 1)
        self.assertIn("[FAIL] t3_plugin_named", p.stdout)


if __name__ == "__main__":
    unittest.main()
