"""Stale test suite for BillingSvc. Last touched 2022.

Both tests are broken: one calls a function that no longer exists,
the other asserts a tax rate from before the 2023 rate change.
"""
import billing


def test_invoice_total():
    inv = billing.create_invoice(1, [{"sku": "X", "price": 5.0, "qty": 2}])
    assert inv["total"] == 10.0


def test_tax():
    assert billing.calculate_tax(100.0, "CA") == 7.5


def test_db_roundtrip():
    from db import init_schema, run_query

    init_schema()
    run_query("INSERT INTO customers (name, email) VALUES ('probe', 'p@x.com')")
    assert run_query("SELECT COUNT(*) FROM customers")[0][0] >= 1
