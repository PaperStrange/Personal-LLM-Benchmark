**Candidate prompt:**
You are onboarding to **BillingSvc**, a small internal invoicing service. The original owner left in 2023 and it has been in maintenance mode since. Your job is to produce a **global project review** so a tech lead can decide what to do with it.

Explore `fixture/legacy-billing/` thoroughly (all modules, config, tests, dependencies). Then write a single Markdown document with these four sections:

### (a) Architecture map
Modules and their responsibilities, the data flow of a complete invoice lifecycle (create → persist → email → report), entry points, and external dependencies (DB, SMTP, third-party packages).

### (b) Tech-debt inventory
Every issue you find, each with: severity (critical/high/medium/low), category (security, correctness, reliability, maintainability, testing, ops), and an exact `file:line` reference. Do not invent files or line numbers — cite only what exists.

### (c) Risk register
What could actually go wrong in production (data loss, breach, outage, wrong money), ranked by likelihood × impact, with the code that causes each.

### (d) 30/60/90-day modernization plan
Concrete, ordered steps a two-person team could execute. Sequence by risk reduction first, then maintainability. Name the files each step touches.

Constraints: read-only — do not edit any code. If you are unsure about something, say so explicitly instead of guessing.

You have no tools and no code execution. Below is the full text of every file in `fixture/legacy-billing/`.

### `billing.py`
```python
"""BillingSvc - invoice generation for the internal billing pipeline.

Single module currently owns: invoice math, tax, DB writes, and email.
"""
import smtplib
from email.mime.text import MIMEText

from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, TAX_RATES
from db import get_conn, run_query

def generate_invoice(customer_id, items):
    """Build an invoice dict.

    items: list of {"sku": str, "price": float, "qty": int}
    """
    subtotal = 0.0
    for it in items:
        subtotal += it["price"] * it["qty"]
    tax = calculate_tax(subtotal, "CA")
    total = subtotal + tax
    return {
        "customer_id": customer_id,
        "line_items": items,
        "subtotal": round(subtotal, 2),
        "tax": round(tax, 2),
        "total": round(total, 2),
    }

def calculate_tax(amount, state):
    rate = TAX_RATES.get(state, 0.0)
    return amount * rate

def save_invoice(invoice):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO invoices (customer_id, subtotal, tax, total) VALUES (%s, %s, %s, %s)"
        % (invoice["customer_id"], invoice["subtotal"], invoice["tax"], invoice["total"])
    )
    conn.commit()
    return cur.lastrowid

def get_invoice(invoice_id):
    rows = run_query("SELECT * FROM invoices WHERE id = " + str(invoice_id))
    return rows[0] if rows else None

def list_invoices(customer_id):
    return run_query(
        "SELECT * FROM invoices WHERE customer_id = '" + str(customer_id) + "'"
    )

def send_invoice_email(to_addr, invoice):
    body = "Invoice total: $%s\nItems:\n" % invoice["total"]
    for it in invoice["line_items"]:
        body += " - %s x%d @ $%s\n" % (it["sku"], it["qty"], it["price"])
    msg = MIMEText(body)
    msg["Subject"] = "Your invoice"
    msg["From"] = SMTP_USER
    msg["To"] = to_addr
    s = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    s.starttls()
    s.login(SMTP_USER, SMTP_PASS)
    s.sendmail(SMTP_USER, [to_addr], msg.as_string())
    s.quit()

def void_invoice(invoice_id, reason):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE invoices SET status='void' WHERE id=%d" % invoice_id)
    conn.commit()

def apply_discount(invoice_id, pct):
    """STUB for the T2 multi-agent task: implement a percent discount.

    Intended behavior: validate 0 < pct <= 100, recompute the invoice total,
    persist the change, and return the new total. Raise ValueError on bad input.
    """
    raise NotImplementedError("apply_discount not implemented yet")

if __name__ == "__main__":
    inv = generate_invoice(42, [{"sku": "WIDGET", "price": 10.0, "qty": 3}])
    print(save_invoice(inv))
```

### `config.py`
```python
"""BillingSvc configuration. Yes, this is all committed to git."""

DEBUG = True  # enables verbose tracebacks; was never turned off

SECRET_KEY = "dev-secret-key-do-not-use"
API_TOKEN = "sk-live-9f2c4a1b7e"

SMTP_HOST = "smtp.internal.example.com"
SMTP_PORT = 587
SMTP_USER = "billing@example.com"
SMTP_PASS = "s3cr3t-mail-pw"

DB_PATH = "/var/lib/billingsvc/billing.db"

TAX_RATES = {"CA": 0.0725, "NY": 0.08, "TX": 0.0625}

ALLOWED_HOSTS = ["*"]

SESSION_COOKIE_SECURE = False
```

### `db.py`
```python
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
```

### `README.md`
# BillingSvc (fixture)

Fictional internal invoicing service. The original owner left in 2023 and the codebase has been in maintenance mode ever since. It is small on purpose: a few hundred lines is enough to tell whether a candidate model can map a codebase, and the tests are broken and should be fixed.

- Read-only for task T1 (global review). Do not modify any code.
- Task T2 may edit code, but only after writing `PLAN.md`.
- `fixture/DEBT-INVENTORY.md` (one level up) is the hidden answer key. **Never show it to a candidate.** It exists so judges can score recall.

## Swapping in your own repo

To evaluate against your real legacy codebase instead of this fixture:
1. Copy a snapshot of your repo into `fixture/` (or point the task prompts at it).
2. Write your own `DEBT-INVENTORY.md` with 10–15 known issues in the same format (`### Dn \`file:line\`` entries).
3. Reuse the rubrics in `rubrics/` unchanged — only T1's recall item needs the inventory, and `judge/jev_judge.py --inventory` handles it.

### `tests/test_billing.py`
```python
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
```