"""Monthly reporting for BillingSvc.

NOTE: _tax() below is a hand-copied duplicate of billing.calculate_tax.
The two have drifted apart; nobody knows which one finance trusts.
"""
from db import run_query


def _tax(amount, state):
    rates = {"CA": 0.075, "NY": 0.08, "TX": 0.0625}
    return amount * rates.get(state, 0.0)


def monthly_report(year, month, out_path):
    rows = run_query(
        "SELECT id, customer_id, subtotal, total FROM invoices "
        "WHERE strftime('%%Y', created) = '%s' AND strftime('%%m', created) = '%s'"
        % (year, str(month).zfill(2))
    )
    with open(out_path, "w") as f:
        f.write("id,customer_id,subtotal,total\n")
        for r in rows:
            f.write("%s,%s,%s,%s\n" % r)
    return out_path


def customer_totals():
    rows = run_query(
        "SELECT customer_id, SUM(total) FROM invoices GROUP BY customer_id"
    )
    return {r[0]: r[1] for r in rows}


import datetime


def invoice_age_days(invoice):
    """Days since the invoice was issued, for the aging report."""
    issued = datetime.datetime.strptime(invoice["issued_at"], "%Y-%m-%d %H:%M:%S")
    now = datetime.datetime.now()
    return (now - issued).days
