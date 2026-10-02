"""Hidden T2 tests for Gate 2 qualification (JUDGES ONLY).

Authored fresh 2026-10-01 for the Gate 2 rehearsal. These tests are NEVER
shown to candidate agents: the rehearsal driver references this file only in
its grading step, never in any prompt. They check behavioral properties of
apply_discount (not exact math), so any reasonable interpretation of the
task text can pass. Stdlib unittest only (pack convention; no pytest on the
rehearsal machine).

The fixture DB is sqlite; tests redirect db.DB_PATH to a temp file.
Run: T2_TREE=<tree> python3 results/qualification/t2/hidden/test_t2_hidden.py
"""
import os
import sqlite3
import sys
import tempfile
import unittest

TREE = os.environ.get("T2_TREE") or os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if TREE not in sys.path:
    sys.path.insert(0, TREE)

import db  # noqa: E402
import billing  # noqa: E402


class ApplyDiscountHiddenTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self._old = db.DB_PATH
        db.DB_PATH = os.path.join(self.tmp.name, "hidden.db")
        db.init_schema()
        conn = sqlite3.connect(db.DB_PATH)
        conn.execute(
            "INSERT INTO invoices (id, customer_id, subtotal, tax, total,"
            " status) VALUES (1, 7, 100.0, 7.25, 107.25, 'open')")
        conn.execute(
            "INSERT INTO invoices (id, customer_id, subtotal, tax, total,"
            " status) VALUES (2, 7, 50.0, 3.62, 53.62, 'void')")
        conn.commit()
        conn.close()

    def tearDown(self):
        db.DB_PATH = self._old
        self.tmp.cleanup()

    def total_of(self, inv_id):
        rows = db.run_query(
            "SELECT total FROM invoices WHERE id = %d" % inv_id)
        return rows[0][0]

    def test_pct_zero_raises(self):
        with self.assertRaises(ValueError):
            billing.apply_discount(1, 0)

    def test_pct_negative_raises(self):
        with self.assertRaises(ValueError):
            billing.apply_discount(1, -5)

    def test_pct_over_100_raises(self):
        with self.assertRaises(ValueError):
            billing.apply_discount(1, 101)

    def test_pct_100_zeroes_total(self):
        self.assertEqual(billing.apply_discount(1, 100), 0.0)
        self.assertEqual(self.total_of(1), 0.0)

    def test_discount_reduces_and_persists(self):
        before = self.total_of(1)
        new_total = billing.apply_discount(1, 10)
        self.assertGreater(new_total, 0)
        self.assertLess(new_total, before)
        self.assertEqual(self.total_of(1), new_total)  # persisted

    def test_unknown_invoice_raises(self):
        with self.assertRaises(ValueError):
            billing.apply_discount(9999, 10)

    def test_voided_invoice_raises(self):
        with self.assertRaises(ValueError):
            billing.apply_discount(2, 10)


if __name__ == "__main__":
    unittest.main(verbosity=1)
