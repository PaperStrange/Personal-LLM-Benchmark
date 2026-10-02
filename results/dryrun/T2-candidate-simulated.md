===== PLAN.md =====
# PLAN.md — T2 dry-run: implement `apply_discount(invoice_id, pct)`

**Roles**: planner (this doc) → implementer → reviewer, played sequentially in one
dry-run session (deviation from true multi-agent setup noted in the report).

## Contract (from the stub docstring)
- Validate `0 < pct <= 100`; raise `ValueError` otherwise.
- Recompute the invoice total with the percent discount applied.
- Persist the change; return the new total.

## Design decisions
1. Discount applies to the **subtotal**; tax is recomputed from the discounted
   subtotal via the existing `calculate_tax(subtotal, state)` and stored back on
   the invoice dict, mirroring `generate_invoice`'s math. Rationale: tax must
   follow the discounted price, and reusing `calculate_tax` avoids a third copy
   of tax logic (there are already two: `billing.calculate_tax` and
   `reports._tax`).
2. Persist via the existing row update in `save_invoice`'s style — but
   `save_invoice` does INSERT. A discount is an UPDATE on the stored row.
   Implementation: read invoice with `get_invoice(invoice_id)` (raises
   `LookupError`-style failure if missing → use `ValueError("unknown invoice")`
   to keep the error contract simple and documented).
3. Round money to 2 decimals at the boundary (`round(..., 2)`), consistent with
   how `generate_invoice` produces totals.

## Edge cases
- `pct` = 0, negative, > 100, non-numeric → `ValueError`.
- `pct` = 100 → total becomes 0.0 tax 0.0; allowed (boundary of `<= 100`).
- Unknown `invoice_id` → `ValueError`.
- Invoice without a `state` key → fall back to `"CA"` default used by
  `calculate_tax`.

## Test plan
- New file `tests/test_discount.py` (plain asserts, runnable with `python` —
  no pytest in this environment): valid discount math, boundary 100,
  invalid pct values, unknown invoice, persistence round-trip (re-read from DB
  shows discounted total).
- DB isolation: tests point `config.DB_PATH` at a temp file, then restore.
  The repo's existing `tests/test_billing.py` is stale (calls removed
  `create_invoice`) and is NOT part of this run — noted as a finding, not fixed
  here.

## Files touched
- `billing.py`: implement `apply_discount` only. No refactor of neighbors.
- `tests/test_discount.py`: new.

===== REVIEW.md =====
# REVIEW.md — T2 dry-run: `apply_discount` implementation

**Reviewer role**: independent pass over the implementer's diff (played
sequentially in this dry run; in the real benchmark these are separate
subagents).

## Verdict: approve

The implementation matches PLAN.md and the stub contract:
- `0 < pct <= 100` validated, `ValueError` on bad input (including bools,
  strings, None) and on unknown invoice ids.
- Discount applies to subtotal; tax recomputed via the shared
  `calculate_tax(..., "CA")` — no third copy of tax logic.
- Persisted with UPDATE; returned total matches the re-read DB row
  (test_persists_to_db).
- Boundary `pct=100` → 0.0 works; no changes outside `billing.py`
  (plus the new test file), per plan.

## Test evidence
`python tests/test_discount.py` → **passed 5/5**
(ok test_boundary_100_percent, ok test_invalid_pct_rejected,
ok test_persists_to_db, ok test_unknown_invoice_rejected,
ok test_valid_discount_math). DB was isolated to a temp file.

## Findings (follow-ups, not blockers)
1. The new code reuses the module's `%`-formatting SQL style. The values are
   all computed numbers and `invoice_id` is `int()`-cast, so there is no
   injection vector here — but the pattern is a smell worth fixing
   module-wide (see T1 finding D4).
2. `tests/test_billing.py` remains stale (calls removed `create_invoice`);
   deliberately untouched as out of scope. Recommend a cleanup task.
3. `get_invoice` returns a positional tuple; the implementation indexes
   `row[2]` for subtotal. Correct per the schema, but fragile — a future
   schema change would silently misread. Noted, not blocking.

===== TESTLOG.txt =====
ok test_boundary_100_percent
ok test_invalid_pct_rejected
ok test_persists_to_db
ok test_unknown_invoice_rejected
ok test_valid_discount_math
passed 5/5
