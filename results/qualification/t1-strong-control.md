# T1 reference review — BillingSvc (strong control, authored 2026-10-01)

Authored directly from `fixture/DEBT-INVENTORY.md` for Gate 1 instrument
validation. Cites all 22 anchors with exact `file:line`. [SIM] — synthetic
control for calibration, not a candidate output.

## Architecture

BillingSvc (`billing.py:1` — "BillingSvc - invoice generation") is a god
module: one file owns invoice math, tax calculation, raw SQL persistence,
and SMTP email, with no separation between concerns. Configuration lives in
`config.py`, shared DB helpers in `db.py`, reporting in `reports.py`, and a
stale test suite in `tests/test_billing.py`. Dependencies are pinned ancient
(`requirements.txt:2` — `flask==1.1.4`).

## Debt inventory

**Security (critical first).** `config.py:5` hardcodes `SECRET_KEY =
"dev-secret-key-do-not-use"`; `config.py:6` commits a live-looking
`API_TOKEN`; `config.py:11` hardcodes `SMTP_PASS` — every clone leaks all
three. `db.py:24` interpolates the customer name straight into SQL
(`WHERE name = '%s'`), a textbook SQL injection, with the same pattern in
`billing.py:55` (`list_invoices`) and `billing.py:42` (`save_invoice`).
`config.py:18` sets `ALLOWED_HOSTS = ["*"]`, disabling host-header
validation entirely. `config.py:20` leaves `SESSION_COOKIE_SECURE = False`,
so session cookies travel over plain HTTP. `config.py:3` leaves `DEBUG =
True` on, leaking verbose tracebacks on top of all of the above.

**Correctness.** `billing.py:19` accumulates money in binary floats
(`subtotal += it["price"] * it["qty"]`) — penny-off totals at scale.
`reports.py:9` hand-duplicates the tax logic (`def _tax(amount, state):`)
with a drifted CA rate (0.075 vs 0.0725 in `config.py:15`); finance trusts
one of them, nobody knows which. `reports.py:17` filters on a `created`
column (`strftime('%%Y', created)`) that the `invoices` schema (`db.py:27`)
does not have — the monthly report crashes on every run. `reports.py:23`
writes CSV rows with `%` formatting (`f.write("%s,%s,%s,%s`) instead of the
`csv` module, so commas/quotes corrupt output and formulas can inject.
`reports.py:40` computes invoice age from `datetime.datetime.now()`,
timezone-naive, so DST shifts silently move aging buckets.

**Reliability.** `db.py:12` (`def run_query(sql):`) opens a connection per
call and never closes it — same leak in `billing.py:35` (`save_invoice`)
and `billing.py:75` (`void_invoice`). `billing.py:94` (`def
charge_invoice(invoice_id, card_token):`) posts a charge with no idempotency
key, so a retried invoice can be charged twice undetected. `db.py:49`
(`SELECT * FROM invoices`) `fetchall`s the whole table into memory for
export — a big month-end kills the process. `db.py:58`
(`return sqlite3.connect(DB_PATH) ~ in get_analytics_conn`) configures no
timeout, so a locked DB stalls dashboards on the driver's default.

**Testing / ops.** `tests/test_billing.py:10` calls `billing.create_invoice`,
which no longer exists. `tests/test_billing.py:15` asserts
`calculate_tax(100.0, "CA") == 7.5`, encoding the pre-2023 rate (now 7.25).
`tests/test_billing.py:18` (`def test_db_roundtrip():`) runs `init_schema()`
against the real `DB_PATH` — the suite mutates production data.
`config.py:13` pins `DB_PATH = "/var/lib/billingsvc/billing.db"`, so the
service cannot start off the prod host without editing source.

## Risk register

| # | Location | Risk |
|---|----------|------|
| 1 | `config.py:5`, `config.py:6`, `config.py:11` | Credential leak — secrets in git |
| 2 | `db.py:24`, `billing.py:55`, `billing.py:42` | SQL injection — data breach |
| 3 | `billing.py:94` | Double charging — direct revenue loss |
| 4 | `config.py:18` | Host-header attacks |
| 5 | `billing.py:19` | Penny-off totals at scale |
| 6 | `reports.py:17` | Monthly report always crashes |
| 7 | `db.py:49` | Month-end OOM |
| 8 | `tests/test_billing.py:18` | Tests mutate production |

## 30/60/90 plan

- **30 days:** rotate all secrets out of `config.py:5`, `config.py:6`,
  `config.py:11` into a vault; parameterize SQL at `db.py:24`,
  `billing.py:55`, `billing.py:42`; set `DEBUG = False` (`config.py:3`).
- **60 days:** add idempotency keys (`billing.py:94`); replace float money
  math (`billing.py:19`) with Decimal; fix or quarantine the stale tests
  (`tests/test_billing.py:10`, `tests/test_billing.py:15`,
  `tests/test_billing.py:18`); make `DB_PATH` (`config.py:13`)
  environment-driven.
- **90 days:** split the god module (`billing.py:1`); unify tax logic
  (`reports.py:9` vs `config.py:15`); fix the `created` column crash
  (`reports.py:17`); close connection leaks (`db.py:12`,
  `billing.py:35`, `billing.py:75`); bound the export (`db.py:49`).
