# DEBT-INVENTORY.md — HIDDEN ANSWER KEY

> **DO NOT show this file to any candidate model or agent. For judges only.**
> Used by `judge/jev_judge.py --inventory` to score T1 debt recall deterministically.
> Format: each `### Dn` entry anchors on `file:line` so the judge can regex-match
> candidate citations. Keep the anchor on the most representative line.
> The `Expect:` line under each header is a short substring of the true
> anchored fixture line (regression-checked by `tests/test_anchors.py`:
> a wrong-line anchor fails the suite). If the anchored line is textually
> identical to another line in the same file, disambiguate with
> `~ in <enclosing-def>` naming the function the anchor belongs to.

### D1 `config.py:5` — Hardcoded SECRET_KEY committed to git
Expect: SECRET_KEY = "dev-secret-key-do-not-use"
Severity: critical · Category: security
A placeholder secret committed to source control; every clone leaks it.

### D2 `config.py:6` — Live API token committed to git
Expect: API_TOKEN
Severity: critical · Category: security
`API_TOKEN = "sk-live-..."` looks like a production credential in source.

### D3 `config.py:11` — Hardcoded SMTP password
Expect: SMTP_PASS
Severity: critical · Category: security
Mail credentials in config; `billing.py` logs into SMTP with them.

### D4 `db.py:24` — SQL injection in find_customer
Expect: WHERE name = '%s'
Severity: critical · Category: security
Customer name interpolated directly into SQL via `%` formatting. Same pattern
in `billing.py:55` (list_invoices) and `billing.py:42` (save_invoice).

### D5 `db.py:12` — Unclosed DB connections (connection leak)
Expect: def run_query(sql):
Severity: high · Category: reliability
`run_query` opens a connection per call and never closes it; neither do
`save_invoice` (`billing.py:35`) or `void_invoice` (`billing.py:75`).
Leaks connections under load.

### D6 `reports.py:9` — Duplicated, drifted tax logic
Expect: def _tax(amount, state):
Severity: high · Category: correctness
`_tax()` is a hand-copied duplicate of `billing.calculate_tax` with a
different CA rate (0.075 vs 0.0725 in `config.py:15`). Finance trusts one of
them; nobody knows which.

### D7 `reports.py:17` — Query references non-existent `created` column
Expect: strftime('%%Y', created)
Severity: high · Category: correctness
The monthly report filters on `created`, but the `invoices` schema in
`db.py:27` has no such column. The report crashes on every run.

### D8 `billing.py:1` — God module: one file owns invoicing, tax, persistence, and mail
Expect: BillingSvc - invoice generation
Severity: high · Category: maintainability
`billing.py` owns invoice generation, tax calculation, raw SQL writes, and
SMTP email. No separation; every change risks every concern.

### D9 `reports.py:23` — Unescaped CSV output (format corruption / CSV injection)
Expect: f.write("%s,%s,%s,%s
Severity: medium · Category: correctness/security
Rows are written with `%` string formatting instead of the `csv` module, so
commas/quotes in data corrupt the file and formulas could inject.

### D10 `tests/test_billing.py:10` — Stale test calls a removed function
Expect: billing.create_invoice
Severity: medium · Category: testing
`test_invoice_total` calls `billing.create_invoice`, which no longer exists
(renamed to `generate_invoice`). The suite cannot even be collected cleanly.

### D11 `tests/test_billing.py:15` — Test asserts an outdated tax rate
Expect: calculate_tax(100.0, "CA") == 7.5
Severity: medium · Category: testing
Asserts CA tax of 7.5 on $100, but the current rate (`config.py:15`) yields
7.25. The test encodes pre-2023 behavior and fails.

### D12 `config.py:3` — DEBUG=True never turned off
Expect: DEBUG = True
Severity: medium · Category: security/ops
Verbose tracebacks enabled; combined with D1–D3 this leaks internals.

### D13 `requirements.txt:2` — Ancient pinned dependencies
Expect: flask==1.1.4
Severity: medium · Category: security/ops
`flask==1.1.4`, `requests==2.22.0`, `gunicorn==19.9.0` — pinned in 2021,
multiple known CVEs since, never revisited.

### D14 `config.py:13` — Absolute production DB path breaks local dev
Expect: /var/lib/billingsvc/billing.db
Severity: low · Category: ops
`DB_PATH = "/var/lib/billingsvc/billing.db"` only exists on the prod host;
the service cannot start anywhere else without editing source.

### D15 `billing.py:19` — Money amounts computed in binary floats
Expect: subtotal += it["price"] * it["qty"]
Severity: high · Category: correctness
Item prices are floats; `subtotal += it["price"] * it["qty"]` accumulates
binary-float rounding error on every invoice. Penny-off totals at scale.

### D16 `billing.py:94` — Charge posted with no idempotency key
Expect: def charge_invoice(invoice_id, card_token):
Severity: critical · Category: reliability
`charge_invoice` posts a charge on every call with nothing the gateway can
dedupe on. Callers retry on network timeouts, so one invoice can be charged
twice and nothing detects it.

### D17 `db.py:49` — Unbounded fetchall in invoice export
Expect: SELECT * FROM invoices
Severity: high · Category: reliability
`export_invoices` selects the entire invoices table and `fetchall`s it into
memory before writing. Memory grows with the table; a big month-end kills
the process.

### D18 `db.py:58` — Reporting connection configured with no timeout
Expect: return sqlite3.connect(DB_PATH) ~ in get_analytics_conn
Severity: medium · Category: reliability
`get_analytics_conn` opens a connection with no timeout configured, so a
locked or slow database stalls the reporting dashboards on the driver's
default instead of a deliberate setting.

### D19 `config.py:18` — Wildcard ALLOWED_HOSTS accepts every host
Expect: ALLOWED_HOSTS = ["*"]
Severity: critical · Category: security
`ALLOWED_HOSTS = ["*"]` disables host-header validation; cache poisoning and
host-header attacks are one request away.

### D20 `config.py:20` — Session cookie not marked Secure
Expect: SESSION_COOKIE_SECURE = False
Severity: high · Category: security
`SESSION_COOKIE_SECURE = False` lets the session cookie travel over plain
HTTP; anyone on the network path can steal a session.

### D21 `reports.py:40` — Invoice age computed from timezone-naive datetimes
Expect: datetime.datetime.now()
Severity: medium · Category: correctness
`invoice_age_days` compares `datetime.datetime.now()` against parsed local
timestamps. DST changes and server moves silently shift aging buckets.

### D22 `tests/test_billing.py:18` — Test writes to the production database
Expect: def test_db_roundtrip():
Severity: high · Category: testing/ops
`test_db_roundtrip` calls `init_schema()` against the real `DB_PATH`
(`/var/lib/billingsvc/billing.db`) and inserts rows. Running the suite
mutates production data.
