"""Regression tests for rubrics/rubric-*.json — the contracts the judge
grades against. A malformed rubric silently corrupts every score it
produces, so the pack validates its own rubrics first ("eval the evals").
"""
import glob
import json
import numbers
import os
import unittest

PACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUBRICS = sorted(glob.glob(os.path.join(PACK, "rubrics", "rubric-*.json")))

VALID_KINDS = {"score", "choice", "noul"}


class RubricTest(unittest.TestCase):
    def test_rubrics_exist(self):
        self.assertGreaterEqual(
            len(RUBRICS), 3,
            "expected rubrics for T1, T2, T3 at least; found %r" % RUBRICS)

    def test_rubrics_well_formed(self):
        for path in RUBRICS:
            with self.subTest(rubric=os.path.basename(path)):
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)  # must parse
                self.assertIsInstance(data, dict)
                self.assertTrue(data.get("task"),
                                "top-level 'task' missing/empty")
                items = data.get("items")
                self.assertIsInstance(items, list)
                self.assertGreater(len(items), 0, "'items' is empty")

    def test_items_have_required_fields(self):
        seen_ids = set()
        for path in RUBRICS:
            with open(path, encoding="utf-8") as f:
                items = json.load(f)["items"]
            for it in items:
                with self.subTest(rubric=os.path.basename(path),
                                  item=it.get("id")):
                    self.assertIsInstance(it, dict)
                    for field in ("id", "kind", "instructions", "weight"):
                        self.assertIn(field, it,
                                      "item missing field %r" % field)
                    self.assertTrue(it["id"], "item id is empty")
                    self.assertNotIn(
                        it["id"], seen_ids,
                        "duplicate item id across rubrics: %s" % it["id"])
                    seen_ids.add(it["id"])
                    self.assertIn(it["kind"], VALID_KINDS,
                                  "unknown kind %r" % it["kind"])
                    self.assertIsInstance(it["weight"], numbers.Real)
                    self.assertGreater(it["weight"], 0,
                                       "weight must be positive")
                    self.assertTrue(it["instructions"].strip(),
                                    "instructions are empty")

    def test_score_items_have_criteria(self):
        for path in RUBRICS:
            with open(path, encoding="utf-8") as f:
                items = json.load(f)["items"]
            for it in items:
                if it["kind"] == "score":
                    with self.subTest(rubric=os.path.basename(path),
                                      item=it["id"]):
                        self.assertIn("criteria", it,
                                      "score item %s has no criteria" % it["id"])
                        self.assertIsInstance(it["criteria"], list)
                        self.assertGreater(
                            len(it["criteria"]), 0,
                            "score item %s has empty criteria" % it["id"])


if __name__ == "__main__":
    unittest.main()
