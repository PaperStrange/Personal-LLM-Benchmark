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


def charge_invoice(invoice_id, card_token):
    """Charge the card on file for an invoice. Called by the nightly job."""
    inv = get_invoice(invoice_id)
    cents = int(inv["total"] * 100)
    return _post_charge(card_token, cents)


def _post_charge(card_token, amount_cents):
    payload = {"token": card_token, "amount_cents": amount_cents}
    return _gateway_call("https://pay.internal.example.com/charge", payload)


def _gateway_call(url, payload):
    import json
    import urllib.request

    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())
