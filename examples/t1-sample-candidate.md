# SIMULATED CANDIDATE OUTPUT — for methodology dry-run only
# Produced by playing the T1 candidate prompt against fixture/legacy-billing.
# Written to exercise the grading pipeline realistically (strong but imperfect).

# BillingSvc — Global Project Review

## (a) Architecture map

**Modules and responsibilities**

- `config.py` — Central configuration: feature flags, secrets/credentials, SMTP settings, DB path, tax rates. Everything is hardcoded; there is no environment-specific config.
- `db.py` — Shared database helpers over SQLite: `get_conn()` (fresh connection per call), `run_query(sql)` (raw SQL, no parameterization), `find_customer(name)`, `init_schema()`.
- `billing.py` — God module: invoice math (`generate_invoice`, `calculate_tax`), persistence (`save_invoice`, `get_invoice`, `list_invoices`, `void_invoice`), email (`send_invoice_email`), plus the unimplemented `apply_discount` stub. Entry point for the service.
- `reports.py` — Monthly reporting: `monthly_report()` (CSV export), `customer_totals()`. Contains its own duplicated `_tax()` implementation.
- `tests/test_billing.py` — Stale test suite (2 tests, both broken).

**Invoice lifecycle data flow**

1. Create: `billing.generate_invoice(customer_id, items)` builds the invoice dict in memory (subtotal → `calculate_tax` → total).
2. Persist: `billing.save_invoice()` writes to the `invoices` table via `db.get_conn()` + string-formatted INSERT.
3. Email: `billing.send_invoice_email()` logs into SMTP with hardcoded credentials and sends the total.
4. Report: `reports.monthly_report()` queries `invoices` and writes a CSV; `reports.customer_totals()` aggregates per customer.

**External dependencies**: SQLite file at `/var/lib/billingsvc/billing.db`, SMTP at `smtp.internal.example.com:587`, third-party packages from `requirements.txt` (flask 1.1.4, requests 2.22.0, gunicorn 19.9.0 — though I am unsure whether flask/gunicorn are actually imported anywhere; nothing in the modules imports them).

**Entry points**: `billing.py` `__main__` block (generates and saves one invoice); `reports.monthly_report()` presumably run by cron (no cron config found — unsure).

## (b) Tech-debt inventory

1. **Critical, security** — `config.py:5`: `SECRET_KEY` hardcoded and committed to git. Every clone leaks it.
2. **Critical, security** — `config.py:6`: live-looking `API_TOKEN = "sk-live-..."` committed to git.
3. **Critical, security** — `config.py:11`: SMTP password hardcoded; used by `billing.py` to authenticate mail.
4. **Critical, security** — `db.py:24`: SQL injection in `find_customer` via `%` string formatting. Same pattern in `billing.py:55` (`list_invoices`) and `billing.py:42` (`save_invoice`).
5. **High, reliability** — `db.py:12`: `run_query` opens a connection per call and never closes it; neither do `save_invoice` (`billing.py:35`) nor `void_invoice` (`billing.py:75`). Connection leak under load.
6. **High, correctness** — `reports.py:9`: `_tax()` is a hand-copied duplicate of `billing.calculate_tax` with a drifted CA rate (0.075 vs 0.0725 in `config.py:15`). Finance reports and invoices disagree on CA tax.
7. **High, correctness** — `reports.py:16`: `monthly_report` filters on a `created` column that does not exist in the `invoices` schema (`db.py:27`). The report crashes on every run. (I am unsure whether the schema was migrated somewhere I cannot see; based on `init_schema` there is no `created` column.)
8. **High, maintainability** — `billing.py:1`: god module owns invoice math, tax, raw SQL, and SMTP. Every change risks every concern.
9. **Medium, correctness/security** — `reports.py:23`: CSV rows built with `%` formatting instead of the `csv` module; commas/quotes corrupt output, formula cells could inject.
10. **Medium, testing** — `tests/test_billing.py:10`: `test_invoice_total` calls `billing.create_invoice`, which no longer exists (renamed to `generate_invoice`). Suite cannot even be collected.
11. **Medium, testing** — `tests/test_billing.py:15`: asserts CA tax of 7.5 on $100, but the current rate (`config.py:15`) gives 7.25. Encodes pre-2023 behavior.
12. **Medium, security/ops** — `config.py:3`: `DEBUG=True` never turned off; verbose tracebacks plus committed secrets leak internals.
13. **Medium, security/ops** — `requirements.txt:2`: ancient pins (`flask==1.1.4`, `requests==2.22.0`, `gunicorn==19.9.0`) with known CVEs since 2021.

## (c) Risk register

1. **Breach via committed secrets (likelihood: high, impact: critical)** — `config.py:5`, `config.py:6`, `config.py:11`. Anyone with repo access owns prod credentials. Combined with `DEBUG=True` (`config.py:3`), an error page can leak them further.
2. **SQL injection → data theft/tampering (likelihood: medium, impact: critical)** — `db.py:24`, `billing.py:42`, `billing.py:55`. Customer names flow into raw SQL.
3. **Wrong money on CA invoices (likelihood: high, impact: high)** — `reports.py:9` vs `config.py:15`: finance and the service compute different CA tax. Silent, ongoing.
4. **Monthly reporting fully broken (likelihood: certain, impact: medium)** — `reports.py:16` references non-existent `created` column; every run crashes.
5. **Outage under load (likelihood: medium, impact: high)** — `db.py:12` connection leak; SQLite + leaked connections will eventually lock or exhaust file descriptors.
6. **Corrupt CSV exports (likelihood: medium, impact: medium)** — `reports.py:23` unescaped formatting.
7. **No safety net (likelihood: certain, impact: medium)** — both tests broken (`tests/test_billing.py:10`, `:15`); any change ships blind.

## (d) 30/60/90-day modernization plan (two-person team)

**Days 1–30 — stop the bleeding (risk reduction)**
1. Rotate all committed secrets and move to environment variables (`config.py`). Touches: `config.py`, deployment config.
2. Parameterize all SQL: convert `db.py` (`find_customer`, `run_query` call sites) and `billing.py:42`, `billing.py:55` to `?` placeholders. Touches: `db.py`, `billing.py`.
3. Set `DEBUG=False` and add a proper logging setup. Touches: `config.py`.
4. Fix or remove the `created` filter in `reports.py:16` (add the column via migration or drop the filter). Touches: `reports.py`, `db.py`.

**Days 31–60 — correctness and safety net**
5. Unify tax logic: single `calculate_tax` in a new `tax.py`, delete `reports._tax`; reconcile the CA rate with finance (0.0725 vs 0.075). Touches: `reports.py`, `billing.py`, new `tax.py`, `config.py`.
6. Rewrite the test suite: fix `tests/test_billing.py` (rename call, update rate), add tests for `save_invoice`/`void_invoice`/edge cases. Touches: `tests/`.
7. Close DB connections: context managers in `db.py`, or one connection per request. Touches: `db.py`, `billing.py`.

**Days 61–90 — maintainability**
8. Split the god module: `invoices.py` (math), `persistence.py` (SQL), `mailer.py` (SMTP) behind thin interfaces. Touches: `billing.py` → new modules.
9. CSV via the `csv` module with quoting; add output validation. Touches: `reports.py`.
10. Upgrade pinned dependencies (`requirements.txt`) and add Dependabot-style pinning policy. Touches: `requirements.txt`.
11. Make `DB_PATH` configurable via environment with a sane local default. Touches: `config.py`.
