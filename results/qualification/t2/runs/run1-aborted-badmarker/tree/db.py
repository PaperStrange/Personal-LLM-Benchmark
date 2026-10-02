"""Shared DB helpers for BillingSvc (legacy payments database)."""
import sqlite3

from config import DB_PATH


def get_conn():
    # Fresh connection per call. Callers are expected to close it; most don't.
    return sqlite3.connect(DB_PATH)


def run_query(sql):
    """Run raw SQL and return all rows. No parameterization anywhere."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    conn.commit()
    return rows


def find_customer(name):
    return run_query(
        "SELECT id, name, email FROM customers WHERE name = '%s'" % name
    )


def init_schema():
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY, name TEXT, email TEXT
        );
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            subtotal REAL, tax REAL, total REAL,
            status TEXT DEFAULT 'open'
        );
        """
    )
    conn.commit()


def export_invoices(out_path):
    """Dump the invoices table for the month-end close."""
    rows = run_query("SELECT * FROM invoices")
    with open(out_path, "w") as f:
        for r in rows:
            f.write(",".join(str(v) for v in r) + "\n")
    return out_path


def get_analytics_conn():
    # Dedicated connection for the reporting dashboards.
    return sqlite3.connect(DB_PATH)
