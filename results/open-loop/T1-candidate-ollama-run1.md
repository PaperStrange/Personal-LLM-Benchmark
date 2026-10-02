### Architecture map

**BillingSvc**

- **Billing** module owns invoice math, tax, DB writes, and email.
- **GenerateInvoice** function creates an invoice dict.
- **calculate_tax** function calculates tax based on state.
- **save_invoice** function saves the invoice to the database.
- **get_invoice** function retrieves an invoice from the database.
- **list_invoices** function lists invoices for a customer.
- **send_invoice_email** function sends an email with the invoice details.
- **void_invoice** function voids an invoice and sets its status to 'void'.
- **apply_discount** function applies a discount to an invoice, stubbed for the T2 multi-agent task.

**dependencies**

- **smtplib** for sending emails.
- **email.mime.text** for creating email messages.
- **config** for SMTP configuration.
- **db** for database operations.
- **tax_rates** for tax rates.
- **get_conn** and **run_query** for database connections and queries.

### Tech-debt inventory

1. **calculate_tax** function has drifted from the 2023 rate change, causing incorrect tax calculations.
2. **send_invoice_email** function relies on an email address that no longer exists.
3. **get_analytics_conn** function has been unused for a long time.
4. **run_query** function is used in both generating invoices and listing invoices, but it is read-only.
5. **create_invoice** function creates an invoice without tax calculation, causing incorrect invoice totals.
6. **void_invoice** function sets the status to 'void' without validating the invoice ID.
7. **apply_discount** function is stubbed for the T2 multi-agent task and has no implementation.

### Risk register

1. **calculate_tax** function has drifted from the 2023 rate change, causing incorrect tax calculations.
2. **send_invoice_email** function relies on an email address that no longer exists.
3. **get_analytics_conn** function has been unused for a long time.
4. **run_query** function is used in both generating invoices and listing invoices, but it is read-only.
5. **create_invoice** function creates an invoice without tax calculation, causing incorrect invoice totals.
6. **void_invoice** function sets the status to 'void' without validating the invoice ID.
7. **apply_discount** function is stubbed for the T2 multi-agent task and has no implementation.

### 30/60/90-day modernization plan

1. **calculate_tax** function drifts from the 2023 rate change. Implement a new function for tax calculation based on the 2023 rate.
2. **send_invoice_email** function relies on an email address that no longer exists. Create a new email address and update the configuration.
3. **get_analytics_conn** function has been unused for a long time. Create a new database connection for analytics purposes.
4. **run_query** function is used in both generating invoices and listing invoices, but it is read-only. Implement a new function for read-only operations.
5. **create_invoice** function creates an invoice without tax calculation, causing incorrect invoice totals. Implement a function for tax calculation and apply it to the invoices.
6. **void_invoice** function sets the status to 'void' without validating the invoice ID. Implement a function for validating the invoice ID and set the status.
7. **apply_discount** function is stubbed for the T2 multi-agent task and has no implementation. Implement a new function for applying discounts and test it.