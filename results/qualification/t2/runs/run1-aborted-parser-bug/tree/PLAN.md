```
### PLAN.md

approach: Validate and recompute invoice total with discount applied

files to touch:
- `billing.py`: implement `apply_discount(invoice_id, pct)`
- `config.py`: no changes needed
- `db.py`: add `apply_discount` to `get_conn`
- `reports.py`: add function to generate reports with updated invoice info
- `requirements.txt`: no changes needed

test plan:
- Write unit tests for `apply_discount`
- Add a test for `apply_discount` using a known good invoice and discount
- Ensure the new function works with both valid and invalid input

risks:
- If the `apply_discount` function fails due to unexpected errors, it could[5D[K
could cause data loss
- Handling edge cases like unknown invoice_id or voided invoices might intr[4D[K
introduce new bugs
- The tax calculation logic might need adjustment if the discount is applie[6D[K
applied to the taxable amount

```
