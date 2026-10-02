"""Regression tests for tasks/t2-discount-fix/plant_bugs.py.

Covers the Phase 3a acceptance: the planter puts exactly 2 seeded subtle
bugs into a disposable fixture COPY, the judges-only manifest matches the
planted locations, the canonical fixture/ tree is byte-identical
afterwards, and every catalog bug is genuinely detectable (behavioral
check per bug), not cosmetic.
"""
import contextlib
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

PACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLANTER = os.path.join(PACK, "tasks", "t2-discount-fix", "plant_bugs.py")
SRC = os.path.join(PACK, "fixture", "legacy-billing")

CATALOG_IDS = {"off_by_one_qty", "swapped_tax_rates", "dropped_none_guard"}


def run_planter(*args):
    return subprocess.run([sys.executable, PLANTER, *args],
                          capture_output=True, text=True, cwd=PACK)


def fixture_hashes():
    out = {}
    for root, _, files in os.walk(os.path.join(PACK, "fixture")):
        for fn in sorted(files):
            p = os.path.join(root, fn)
            with open(p, "rb") as f:
                out[os.path.relpath(p, PACK)] = hashlib.sha256(f.read()).hexdigest()
    return out


@contextlib.contextmanager
def copy_modules(copy_dir):
    """Import the COPY's billing/config/db under their plain module names.

    copy_dir goes first on sys.path so `from config import ...` inside the
    copied billing.py resolves to the copy's config.py, not anything else.
    Restores sys state afterwards.
    """
    saved = {m: sys.modules.pop(m)
             for m in ("billing", "config", "db") if m in sys.modules}
    sys.path.insert(0, copy_dir)
    try:
        import billing  # noqa: F401
        import config  # noqa: F401
        yield sys.modules["billing"], sys.modules["config"]
    finally:
        sys.path.remove(copy_dir)
        for m in ("billing", "config", "db"):
            sys.modules.pop(m, None)
        sys.modules.update(saved)


class PlantBugsTest(unittest.TestCase):
    def test_seed_selects_exactly_two_distinct_bugs(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = os.path.join(tmp, "copy")
            manifest = os.path.join(tmp, "manifest.json")
            p = run_planter("--src", SRC, "--dest", dest, "--seed", "42",
                            "--manifest", manifest)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            with open(manifest, encoding="utf-8") as f:
                data = json.load(f)
        self.assertEqual(len(data["bugs"]), 2)
        ids = [b["id"] for b in data["bugs"]]
        self.assertEqual(len(set(ids)), 2, "planted bugs must be distinct")
        self.assertTrue(set(ids) <= CATALOG_IDS)
        self.assertIn("_judges_only", data)

    def test_manifest_matches_planted_locations(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = os.path.join(tmp, "copy")
            manifest = os.path.join(tmp, "manifest.json")
            p = run_planter("--src", SRC, "--dest", dest, "--seed", "7",
                            "--manifest", manifest)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            with open(manifest, encoding="utf-8") as f:
                data = json.load(f)
            # The pack's own --verify check must pass on a fresh planting.
            v = run_planter("--src", SRC, "--dest", dest, "--verify",
                            "--manifest", manifest)
            self.assertEqual(v.returncode, 0, v.stdout + v.stderr)
            for bug in data["bugs"]:
                path = os.path.join(dest, bug["file"])
                with open(path, encoding="utf-8") as f:
                    lines = f.readlines()
                # 1-based manifest line, matching DEBT-INVENTORY.md convention.
                self.assertIn(bug["signature"], lines[bug["line"] - 1])
                with open(path, encoding="utf-8") as f:
                    whole = f.read()
                self.assertNotIn(bug["original"], whole,
                                 "original string must be gone")

    def test_canonical_fixture_untouched(self):
        before = fixture_hashes()
        with tempfile.TemporaryDirectory() as tmp:
            dest = os.path.join(tmp, "copy")
            manifest = os.path.join(tmp, "manifest.json")
            p = run_planter("--src", SRC, "--dest", dest, "--seed", "1",
                            "--manifest", manifest)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        after = fixture_hashes()
        self.assertEqual(before, after,
                         "canonical fixture/ tree must be byte-identical")

    def test_refuses_dest_inside_src(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = os.path.join(tmp, "manifest.json")
            p = run_planter("--src", SRC,
                            "--dest", os.path.join(SRC, "evil-copy"),
                            "--seed", "1", "--manifest", manifest)
            self.assertNotEqual(p.returncode, 0)
            self.assertFalse(os.path.exists(os.path.join(SRC, "evil-copy")))

    def test_refuses_dest_inside_src_through_symlink(self):
        # The guard must see through symlinks: src via an unresolved alias
        # and dest via the resolved real path defeated the old
        # abspath-based check (commonpath compared two different spellings
        # of the same tree). realpath must refuse it.
        with tempfile.TemporaryDirectory() as tmp:
            real_src = os.path.join(tmp, "real-src")
            os.makedirs(real_src)
            alias = os.path.join(tmp, "alias-src")
            os.symlink(real_src, alias)
            manifest = os.path.join(tmp, "manifest.json")
            p = run_planter("--src", alias,
                            "--dest", os.path.join(real_src, "evil-copy"),
                            "--seed", "1", "--manifest", manifest)
            self.assertNotEqual(p.returncode, 0)
            self.assertFalse(os.path.exists(os.path.join(real_src, "evil-copy")))

    def test_verify_catches_tampered_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = os.path.join(tmp, "copy")
            manifest = os.path.join(tmp, "manifest.json")
            p = run_planter("--src", SRC, "--dest", dest, "--seed", "3",
                            "--manifest", manifest)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            with open(manifest, encoding="utf-8") as f:
                data = json.load(f)
            bug = data["bugs"][0]
            # Tamper: restore the original line in the copy.
            path = os.path.join(dest, bug["file"])
            with open(path, encoding="utf-8") as f:
                text = f.read()
            with open(path, "w", encoding="utf-8") as f:
                f.write(text.replace(bug["planted"], bug["original"], 1))
            v = run_planter("--src", SRC, "--dest", dest, "--verify",
                            "--manifest", manifest)
            self.assertNotEqual(v.returncode, 0,
                                "--verify must fail on a tampered copy")

    def _plant_one(self, tmp, bug_id):
        dest = os.path.join(tmp, "copy-" + bug_id)
        manifest = os.path.join(tmp, "manifest-%s.json" % bug_id)
        p = run_planter("--src", SRC, "--dest", dest, "--bugs", bug_id,
                        "--manifest", manifest)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        return dest

    def test_off_by_one_qty_is_detectable(self):
        # Hand-verifiable: 2 units @ $10 must subtotal $20; the bug makes $30.
        with tempfile.TemporaryDirectory() as tmp:
            dest = self._plant_one(tmp, "off_by_one_qty")
            with copy_modules(dest) as (billing, _):
                inv = billing.generate_invoice(
                    7, [{"sku": "W", "price": 10.0, "qty": 2}])
                self.assertEqual(inv["subtotal"], 30.0)
            clean = os.path.join(tmp, "clean")
            shutil.copytree(SRC, clean)
            with copy_modules(clean) as (billing, _):
                inv = billing.generate_invoice(
                    7, [{"sku": "W", "price": 10.0, "qty": 2}])
                self.assertEqual(inv["subtotal"], 20.0)

    def test_swapped_tax_rates_is_detectable(self):
        # Hand-verifiable: 7.25% of $100 is $7.25; the bug gives $6.25.
        with tempfile.TemporaryDirectory() as tmp:
            dest = self._plant_one(tmp, "swapped_tax_rates")
            with copy_modules(dest) as (billing, _):
                self.assertEqual(billing.calculate_tax(100.0, "CA"), 6.25)
            clean = os.path.join(tmp, "clean")
            shutil.copytree(SRC, clean)
            with copy_modules(clean) as (billing, _):
                # 0.0725 is not exact in binary floating point.
                self.assertAlmostEqual(billing.calculate_tax(100.0, "CA"),
                                       7.25, places=9)

    def test_dropped_none_guard_is_detectable(self):
        # Hand-verifiable: unknown invoice -> None on clean tree,
        # IndexError on the planted tree (run_query stubbed to []).
        with tempfile.TemporaryDirectory() as tmp:
            dest = self._plant_one(tmp, "dropped_none_guard")
            with copy_modules(dest) as (billing, _):
                billing.run_query = lambda sql: []
                with self.assertRaises(IndexError):
                    billing.get_invoice(999)
            clean = os.path.join(tmp, "clean")
            shutil.copytree(SRC, clean)
            with copy_modules(clean) as (billing, _):
                billing.run_query = lambda sql: []
                self.assertIsNone(billing.get_invoice(999))


if __name__ == "__main__":
    unittest.main()
