"""Regression test for the Phase 4a fixture variant generator.

Generates two vintages (seeds 7 and 8) in tmp and asserts:
  (a) the two variant trees differ from each other and from canonical
      (rotation actually happened — not byte-identical);
  (b) the full anchor verification (existence + Expect: content) passes on
      EACH variant pair, via the refactored tests/test_anchors.py logic;
  (c) canonical pair still passes (covered by test_anchors; asserted here
      too for the pair);
  (d) src/llm_workflow_eval/judge/leakage_audit.py is ALL CLEAR on each variant pair;
  (e) scorecard/aggregate output carries the stamped vintage, and mixed
      vintages are refused;
plus guards: the generator refuses the canonical tree, leaves canonical
bytes untouched, keeps line counts (anchors don't shift), keeps anchors
textually identical, and the rotated code still runs (behavioral
equivalence with canonical + the T2 apply_discount contract frozen).
Review follow-ups: variant-inventory prose is span-safe (no English-word or
API-reference corruption in the judge's answer key), --fixture-vintage
auto-detects from the inventory's VINTAGE file instead of silently
defaulting to canonical, and collision check 3 accepts all seeds 0..199.
"""
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

PACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TESTS)
import test_anchors

ROTATE = os.path.join(PACK, "tasks", "t1-legacy-review", "rotate_fixture.py")
AGGREGATE = os.path.join(PACK, "src", "llm_workflow_eval", "judge", "aggregate.py")
JUDGE = os.path.join(PACK, "src", "llm_workflow_eval", "judge", "jev_judge.py")
LEAKAGE = os.path.join(PACK, "src", "llm_workflow_eval", "judge", "leakage_audit.py")
MOCK_SDK = os.path.join(PACK, "tests", "helpers", "mock_typesafe")
RUBRIC = os.path.join(PACK, "rubrics", "rubric-T1.json")
CANON_CODE = os.path.join(PACK, "fixture", "legacy-billing")
CANON_INV = os.path.join(PACK, "fixture", "DEBT-INVENTORY.md")


def _load_rotate():
    spec = importlib.util.spec_from_file_location("rotate_fixture", ROTATE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


rotate_fixture = _load_rotate()

SEEDS = (7, 8)


def tree_hash(root):
    h = hashlib.sha256()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
        for fn in sorted(filenames):
            if fn.endswith((".pyc", ".pyo")):
                continue
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, root)
            h.update(rel.encode("utf-8") + b"\x00")
            with open(p, "rb") as f:
                h.update(f.read() + b"\x00")
    return h.hexdigest()


def gen_variant(seed, tmp):
    out = os.path.join(tmp, "v2-seed%d" % seed)
    info = rotate_fixture.generate(seed, out)
    return out, info


def run_module_variant(code_dir, args_tuple_src, expr):
    """Run `expr` in a subprocess with code_dir first on sys.path.

    args_tuple_src is Python source for the positional args to go(), e.g.
    "('generate_invoice', 'invoice_age_days')" for canonical or the renamed
    alternatives for a variant.
    """
    script = (
        "import json, sys; sys.path.insert(0, %r); "
        "ns = {}; exec(%r, ns); "
        "print(json.dumps(ns['go'](*%s)))"
        % (code_dir, expr, args_tuple_src))
    p = subprocess.run([sys.executable, "-c", script],
                       capture_output=True, text=True, cwd=PACK)
    if p.returncode != 0:
        raise AssertionError("variant smoke failed: %s%s" % (p.stdout,
                                                             p.stderr))
    return json.loads(p.stdout)


class RotationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.variants = {}
        for seed in SEEDS:
            out, info = gen_variant(seed, cls.tmp.name)
            cls.variants[seed] = (out, info)
        cls.canon_hash = tree_hash(CANON_CODE)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    # (a) rotation actually happened -------------------------------------
    def test_vintages_differ_from_canonical(self):
        for seed, (out, _) in self.variants.items():
            with self.subTest(seed=seed):
                self.assertNotEqual(
                    tree_hash(os.path.join(out, "legacy-billing")),
                    self.canon_hash,
                    "variant is byte-identical to canonical: no rotation")

    def test_vintages_differ_from_each_other(self):
        outs = [o for o, _ in self.variants.values()]
        self.assertNotEqual(
            tree_hash(os.path.join(outs[0], "legacy-billing")),
            tree_hash(os.path.join(outs[1], "legacy-billing")),
            "two seeds produced identical trees: seed has no effect")

    def test_identifiers_actually_renamed(self):
        for seed, (out, _) in self.variants.items():
            with self.subTest(seed=seed):
                rmap = rotate_fixture.build_rename_map(seed)
                with open(os.path.join(out, "legacy-billing",
                                       "billing.py"), encoding="utf-8") as f:
                    body = f.read()
                self.assertNotIn("def generate_invoice", body)
                self.assertIn("def " + rmap["generate_invoice"], body)
                # frozen T2 contract surface survives
                self.assertIn("def apply_discount(invoice_id, pct):", body)

    # (b) anchors pass on each variant ------------------------------------
    def test_anchors_pass_on_each_variant(self):
        for seed, (out, _) in self.variants.items():
            with self.subTest(seed=seed):
                try:
                    test_anchors.verify_pair(
                        os.path.join(out, "legacy-billing"),
                        os.path.join(out, "DEBT-INVENTORY.md"))
                except AssertionError as e:
                    self.fail("variant v2-seed%d: %s" % (seed, e))

    def test_variant_anchors_textually_identical(self):
        canon = test_anchors.parse_anchors(CANON_INV)
        for seed, (out, _) in self.variants.items():
            with self.subTest(seed=seed):
                variant = test_anchors.parse_anchors(
                    os.path.join(out, "DEBT-INVENTORY.md"))
                self.assertEqual(variant, canon,
                                 "variant anchors shifted or changed")

    # (c) canonical pair still passes --------------------------------------
    def test_canonical_pair_still_passes(self):
        try:
            test_anchors.verify_pair()
        except AssertionError as e:
            self.fail("canonical pair: %s" % e)

    # (d) leakage audit on each variant -------------------------------------
    def test_leakage_audit_all_clear_on_variants(self):
        for seed, (out, _) in self.variants.items():
            with self.subTest(seed=seed):
                p = subprocess.run(
                    [sys.executable, LEAKAGE,
                     "--inventory", os.path.join(out, "DEBT-INVENTORY.md"),
                     "--workdir", os.path.join(out, "legacy-billing")],
                    capture_output=True, text=True, cwd=PACK)
                self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
                self.assertIn("ALL CLEAR", p.stdout)

    # guards -----------------------------------------------------------------
    def test_canonical_tree_untouched_by_generation(self):
        self.assertEqual(tree_hash(CANON_CODE), self.canon_hash,
                         "canonical fixture changed during variant generation")

    def test_generator_refuses_canonical_tree(self):
        bad = os.path.join(CANON_CODE, "variants")
        with self.assertRaises(ValueError):
            rotate_fixture.generate(99, bad)
        p = subprocess.run(
            [sys.executable, ROTATE, "--seed", "99", "--out", bad],
            capture_output=True, text=True, cwd=PACK)
        self.assertEqual(p.returncode, 2, p.stdout + p.stderr)

    def test_line_counts_unchanged(self):
        # Renaming is within-line: every file keeps its line count, so no
        # file:line anchor can shift.
        for seed, (out, _) in self.variants.items():
            with self.subTest(seed=seed):
                for dirpath, _, filenames in os.walk(CANON_CODE):
                    for fn in filenames:
                        if not fn.endswith(".py"):
                            continue
                        rel = os.path.relpath(os.path.join(dirpath, fn),
                                              CANON_CODE)
                        with open(os.path.join(CANON_CODE, rel),
                                  encoding="utf-8") as f:
                            canon_n = sum(1 for _ in f)
                        with open(os.path.join(out, "legacy-billing", rel),
                                  encoding="utf-8") as f:
                            var_n = sum(1 for _ in f)
                        self.assertEqual(var_n, canon_n,
                                         "%s line count changed" % rel)

    def test_variant_code_runs_with_same_behavior(self):
        expr = (
            "def go(gen_name, age_name):\n"
            "    import billing, inspect\n"
            "    gen = getattr(billing, gen_name)\n"
            "    inv = gen(1, [{'sku': 'X', 'price': 5.0, 'qty': 2}])\n"
            "    sig = list(inspect.signature(billing.apply_discount).parameters)\n"
            "    try:\n"
            "        billing.apply_discount(1, 10)\n"
            "        stub = 'no-raise'\n"
            "    except NotImplementedError:\n"
            "        stub = 'stub'\n"
            "    import reports\n"
            "    age_fn = getattr(reports, age_name)\n"
            "    age = age_fn({'issued_at': '2020-01-01 00:00:00'})\n"
            "    return {'total': inv['total'], 'sig': sig, 'stub': stub,\n"
            "            'age': age}\n"
        )
        canon = run_module_variant(CANON_CODE, "('generate_invoice', 'invoice_age_days')", expr)
        self.assertEqual(canon["sig"], ["invoice_id", "pct"])
        self.assertIsInstance(canon["age"], int)
        for seed, (out, _) in self.variants.items():
            with self.subTest(seed=seed):
                rmap = rotate_fixture.build_rename_map(seed)
                names = "('%s', '%s')" % (rmap["generate_invoice"],
                                          rmap["invoice_age_days"])
                var = run_module_variant(os.path.join(out, "legacy-billing"),
                                         names, expr)
                self.assertEqual(var["total"], canon["total"],
                                 "renamed code behaves differently")
                self.assertEqual(var["sig"], ["invoice_id", "pct"],
                                 "T2 contract signature changed")
                self.assertEqual(var["stub"], "stub",
                                 "apply_discount stub contract broken")

    # (e) vintage stamping ----------------------------------------------------
    def test_vintage_file_stamped(self):
        for seed, (out, _) in self.variants.items():
            with self.subTest(seed=seed):
                with open(os.path.join(out, "VINTAGE"),
                          encoding="utf-8") as f:
                    self.assertEqual(f.read().strip(), "v2-seed%d" % seed)

    def _write_run(self, tmp, name, vintage):
        payload = {"task": "T1", "composite": 72.5, "run_id": name,
                   "items": [], "fixture_vintage": vintage}
        p = os.path.join(tmp, name + ".json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        return p

    def test_aggregate_reports_stamped_vintage(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = [self._write_run(tmp, "r%d" % i, "v2-seed7")
                     for i in range(2)]
            p = subprocess.run([sys.executable, AGGREGATE, *paths],
                               capture_output=True, text=True, cwd=PACK)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("vintage: v2-seed7", p.stdout)

    def test_aggregate_refuses_mixed_vintages(self):
        with tempfile.TemporaryDirectory() as tmp:
            p0 = self._write_run(tmp, "r0", "v1-2026-09")
            p1 = self._write_run(tmp, "r1", "v2-seed7")
            p = subprocess.run([sys.executable, AGGREGATE, p0, p1],
                               capture_output=True, text=True, cwd=PACK)
        self.assertEqual(p.returncode, 2, p.stdout)
        self.assertIn("mixed fixture vintages", p.stderr)

    def test_aggregate_vintage_flag_must_agree(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = [self._write_run(tmp, "r%d" % i, "v2-seed7")
                     for i in range(2)]
            p = subprocess.run(
                [sys.executable, AGGREGATE, *paths,
                 "--vintage", "v2-seed8"],
                capture_output=True, text=True, cwd=PACK)
        self.assertEqual(p.returncode, 2, p.stdout)
        self.assertIn("contradicts the stamped", p.stderr)

    def test_aggregate_accepts_unstamped_legacy_inputs(self):
        # results/dryrun/jev-run*.json predate vintage stamping: they must
        # still aggregate (as "unknown"), not break the old path.
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for i in range(2):
                payload = {"task": "T1", "composite": 70.0,
                           "run_id": "legacy%d" % i, "items": []}
                q = os.path.join(tmp, "old%d.json" % i)
                with open(q, "w", encoding="utf-8") as f:
                    json.dump(payload, f)
                paths.append(q)
            p = subprocess.run([sys.executable, AGGREGATE, *paths],
                               capture_output=True, text=True, cwd=PACK)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("vintage: unknown", p.stdout)

    def test_build_rename_map_accepts_many_seeds(self):
        # Review finding: the old collision check 3 compared alternatives
        # against Attribute names too (`conn.cursor()`), loudly rejecting
        # 103/200 seeds on the benign `cur` -> `cursor` pattern. The check
        # now covers the bare-name namespace (+ import aliases, + fixture
        # module attrs); no seed in 0..199 may be rejected.
        for seed in range(200):
            try:
                rotate_fixture.build_rename_map(seed)
            except ValueError as e:
                self.fail("seed %d rejected: %s" % (seed, e))

    def test_variant_inventory_prose_not_corrupted(self):
        # Review finding: the old word-boundary prose remapper rewrote
        # English words and API references, emitting FALSE statements into
        # the judge's answer key — e.g. `datetime.datetime.current_time()`
        # (code still calls .now()), "`fetchall`server", "mo-end".
        # Prose remapping is now restricted to bare-identifier backtick
        # spans whose new name provably occurs in the variant code.
        import ast as _ast
        with tempfile.TemporaryDirectory() as tmp:
            out, _ = gen_variant(7, tmp)
            with open(os.path.join(out, "DEBT-INVENTORY.md"),
                      encoding="utf-8") as f:
                inv = f.read()
            for bad in ("datetime.datetime.current_time()",
                        "`fetchall`server", "mo-end", "driver'server",
                        "tax_amount logic", "inserts results",
                        "Customer full_name", "outdated tax_amount"):
                self.assertNotIn(bad, inv,
                                 "prose corruption present: %r" % bad)
            rmap = rotate_fixture.build_rename_map(7)
            new_names = set(rmap.values())
            code_names = set()
            for root, _, files in os.walk(
                    os.path.join(out, "legacy-billing")):
                for fn in files:
                    if not fn.endswith(".py"):
                        continue
                    with open(os.path.join(root, fn),
                              encoding="utf-8") as f:
                        tree = _ast.parse(f.read())
                    # Same collection as
                    # rotate_fixture._variant_code_names: bare NAMEs, args,
                    # and def names (renames land in all three).
                    for node in _ast.walk(tree):
                        if isinstance(node, _ast.Name):
                            code_names.add(node.id)
                        elif isinstance(node, _ast.arg):
                            code_names.add(node.arg)
                        elif isinstance(
                                node, (_ast.FunctionDef,
                                       _ast.AsyncFunctionDef)):
                            code_names.add(node.name)
            span_re = re.compile(r"`([^`]+)`")
            # Every backtick span naming a rename alternative must name a
            # rename that really happened in code (no invented names).
            for m in span_re.finditer(inv):
                inner = m.group(1).strip()
                if inner.isidentifier() and inner in new_names:
                    self.assertIn(
                        inner, code_names,
                        "prose names %r, never renamed in code" % inner)
            # No missed remaps: a bare span in canonical prose whose rename
            # really happened must appear remapped in the variant.
            with open(CANON_INV, encoding="utf-8") as f:
                canon = f.read()
            for m in span_re.finditer(canon):
                inner = m.group(1).strip()
                if inner.isidentifier() and inner in rmap \
                        and rmap[inner] in code_names:
                    self.assertIn("`%s`" % rmap[inner], inv,
                                  "prose span `%s` not remapped" % inner)

    def test_jev_judge_stamps_fixture_vintage(self):
        env = dict(os.environ)
        env["PYTHONPATH"] = MOCK_SDK + os.pathsep + env.get("PYTHONPATH", "")
        env["TYPESAFE_API_KEY"] = "dryrun-test"
        env["MOCK_RUN"] = "1"
        with tempfile.TemporaryDirectory() as tmp:
            cand = os.path.join(tmp, "cand.md")
            with open(cand, "w", encoding="utf-8") as f:
                f.write("config.py:5 hardcodes SECRET_KEY.\n")
            out = os.path.join(tmp, "stamped.json")
            p = subprocess.run(
                [sys.executable, JUDGE, "--rubric", RUBRIC,
                 "--candidate", cand, "--json-out", out,
                 "--fixture-vintage", "v2-seed7"],
                capture_output=True, text=True, cwd=PACK, env=env)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            with open(out, encoding="utf-8") as f:
                payload = json.load(f)
            self.assertEqual(payload["fixture_vintage"], "v2-seed7")

            out2 = os.path.join(tmp, "default.json")
            p = subprocess.run(
                [sys.executable, JUDGE, "--rubric", RUBRIC,
                 "--candidate", cand, "--json-out", out2],
                capture_output=True, text=True, cwd=PACK, env=env)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            with open(out2, encoding="utf-8") as f:
                payload2 = json.load(f)
            self.assertEqual(payload2["fixture_vintage"], "v1-2026-09")

            # Auto-detect (review finding): with no --fixture-vintage, a
            # VINTAGE file next to --inventory stamps the variant; the old
            # silent canonical default mislabeled variant runs with no
            # error. Canonical inventory (no VINTAGE file) falls back to
            # v1-2026-09.
            var_out, _ = gen_variant(7, tmp)
            var_inv = os.path.join(var_out, "DEBT-INVENTORY.md")
            out3 = os.path.join(tmp, "autodetect-variant.json")
            p = subprocess.run(
                [sys.executable, JUDGE, "--rubric", RUBRIC,
                 "--candidate", cand, "--inventory", var_inv,
                 "--json-out", out3],
                capture_output=True, text=True, cwd=PACK, env=env)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            with open(out3, encoding="utf-8") as f:
                payload3 = json.load(f)
            self.assertEqual(payload3["fixture_vintage"], "v2-seed7")

            out4 = os.path.join(tmp, "autodetect-canonical.json")
            p = subprocess.run(
                [sys.executable, JUDGE, "--rubric", RUBRIC,
                 "--candidate", cand, "--inventory", CANON_INV,
                 "--json-out", out4],
                capture_output=True, text=True, cwd=PACK, env=env)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            with open(out4, encoding="utf-8") as f:
                payload4 = json.load(f)
            self.assertEqual(payload4["fixture_vintage"], "v1-2026-09")


if __name__ == "__main__":
    unittest.main()
