"""PROPOSAL regression tests: T0 must require >=1 file:line ref (T1).

These tests assert the DESIRED behavior (gate v2). They FAIL against the
current src/llm_workflow_eval/judge/t0_checks.py (gate v1, zero refs pass vacuously) and PASS
after applying ./t0_ref_requirement.patch. Awaiting Sakura's nod before
anything moves. No retroactive reclassification of completed runs.
"""
import os
import subprocess
import sys
import tempfile
import unittest

PACK = os.path.expanduser(
    "~/workspace/your_files/llm-workflow-eval-pack")
T0 = os.path.join(PACK, "src", "llm_workflow_eval", "judge", "t0_checks.py")
FIXTURE = os.path.join(PACK, "fixture", "legacy-billing")
INVENTORY = os.path.join(PACK, "fixture", "DEBT-INVENTORY.md")


def run_t0(*args):
    return subprocess.run(
        [sys.executable, T0, *args],
        capture_output=True, text=True, cwd=PACK,
    )


# All four T1 sections present, but ZERO file:line references --
# the observed qwen/llama run-1 failure mode.
T1_ZERO_REFS = """# Review

## Architecture
The architecture centers on billing.py with db.py helpers.

## Debt inventory
The config file hardcodes secrets. The database layer has SQL injection.
No line numbers are cited anywhere in this review.

## Risk register
risk of credential leak is high.

## 30/60/90 plan
30/60/90-day modernization plan: rotate secrets, parameterize SQL.
"""

T1_ONE_REF = T1_ZERO_REFS.replace(
    "No line numbers are cited anywhere in this review.",
    "config.py:5 hardcodes the SECRET_KEY.")


class T0RefRequirementTest(unittest.TestCase):
    def test_zero_refs_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            cand = os.path.join(tmp, "cand.md")
            with open(cand, "w", encoding="utf-8") as f:
                f.write(T1_ZERO_REFS)
            p = run_t0("--task", "T1", "--candidate", cand,
                       "--inventory", INVENTORY, "--workdir", FIXTURE)
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        self.assertIn("[FAIL] t1_refs_valid", p.stdout)
        self.assertIn("GATE FAILED", p.stdout)

    def test_one_valid_ref_passes_refs_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            cand = os.path.join(tmp, "cand.md")
            with open(cand, "w", encoding="utf-8") as f:
                f.write(T1_ONE_REF)
            p = run_t0("--task", "T1", "--candidate", cand,
                       "--inventory", INVENTORY, "--workdir", FIXTURE)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("[PASS] t1_refs_valid", p.stdout)

    def test_out_of_range_still_fails(self):
        bad = T1_ONE_REF + "\nSee billing.py:9999 for details.\n"
        with tempfile.TemporaryDirectory() as tmp:
            cand = os.path.join(tmp, "cand.md")
            with open(cand, "w", encoding="utf-8") as f:
                f.write(bad)
            p = run_t0("--task", "T1", "--candidate", cand,
                       "--inventory", INVENTORY, "--workdir", FIXTURE)
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        self.assertIn("[FAIL] t1_refs_valid", p.stdout)
        self.assertIn("billing.py:9999", p.stdout)


if __name__ == "__main__":
    unittest.main()
