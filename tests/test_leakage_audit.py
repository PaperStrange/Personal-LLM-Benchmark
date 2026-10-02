"""Regression test for src/llm_workflow_eval/judge/leakage_audit.py.

The hidden answer key must not be spelled out verbatim in the fixture:
(a) the real inventory/fixture pair is clean, (b) a planted verbatim leak
is caught, (c) a missing inventory fails loudly instead of passing silent.
"""
import os
import subprocess
import sys
import tempfile
import unittest

PACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT = os.path.join(PACK, "src", "llm_workflow_eval", "judge", "leakage_audit.py")


class LeakageAuditTest(unittest.TestCase):
    def test_real_fixture_is_clean(self):
        p = subprocess.run(
            [sys.executable, AUDIT,
             "--inventory", os.path.join(PACK, "fixture", "DEBT-INVENTORY.md"),
             "--workdir", os.path.join(PACK, "fixture", "legacy-billing")],
            capture_output=True, text=True, cwd=PACK)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("ALL CLEAR", p.stdout)

    def test_planted_leak_is_caught(self):
        with tempfile.TemporaryDirectory() as tmp:
            inv = os.path.join(tmp, "inv.md")
            with open(inv, "w", encoding="utf-8") as f:
                f.write("### D1 `a.py:3` — Totally broken retry loop logic here\n")
            with open(os.path.join(tmp, "a.py"), "w", encoding="utf-8") as f:
                f.write("# totally broken retry loop logic here, fix later\n"
                        "x = 1\n"
                        "y = 2\n")
            p = subprocess.run(
                [sys.executable, AUDIT, "--inventory", inv,
                 "--workdir", tmp],
                capture_output=True, text=True, cwd=PACK)
        self.assertEqual(p.returncode, 1, p.stdout)
        self.assertIn("[LEAK]", p.stdout)
        self.assertIn("a.py", p.stdout)

    def test_missing_inventory_fails_loudly(self):
        p = subprocess.run(
            [sys.executable, AUDIT, "--inventory", "/nonexistent/inv.md",
             "--workdir", "/tmp"],
            capture_output=True, text=True, cwd=PACK)
        self.assertEqual(p.returncode, 2)


if __name__ == "__main__":
    unittest.main()
