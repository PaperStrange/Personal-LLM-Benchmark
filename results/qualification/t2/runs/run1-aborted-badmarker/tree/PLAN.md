```markdown
PLAN.md

- **approach**: Implement `apply_discount(invoice_id, pct)` in `billing.py`
`billing.py` to recompute the invoice total with the discount applied, pers
persist the change to the invoices table, and return the new total. Ensure 
it handles edge cases such as unknown invoice_id and already-voided invoice
invoices.

- **files to touch**:
  - `billing.py`: Implement `apply_discount()` to validate 0 < pct <= 100, 
recompute the invoice total, persist the change, and return the new total.

- **test plan**:
  - Add or fix tests covering the new behavior. For example, test the disco
discount applied to an invoice and ensure it correctly recompiles the total
total and persists the change.

- **risks**:
  - Edge cases like unknown invoice_id or already-voided invoices require c
careful handling to ensure the behavior is as expected.
  - Ensuring the new behavior is correctly recompiled and persisted is cruc
crucial to maintain functionality.
  - Implementing and testing the `apply_discount()` function carefully to a
avoid bugs.
```
