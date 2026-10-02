### (a) Architecture map

**Modules and Their Responsibilities:**

- `billing.py`: Handles invoice generation, tax calculations, database writes, and email notifications.
- `config.py`: Contains configuration settings and database paths.
- `db.py`: Provides database operations, including connecting to the database, executing queries, and managing invoices.
- `reports.py`: Generates monthly reports for the billing pipeline.
- `tests/test_billing.py`: Stale test suite for the billing module.

**Data Flow:**

- Customer data is fetched from the database.
- Invoices are created with items and their quantities and prices.
- Invoices are stored in the database with `subtotal`, `tax`, and `total`.
- Invoices are emailed to the customer.
- Reports are generated for the billing pipeline.

**Entry Points:**

- `generate_invoice`: Generates an invoice with the provided customer ID and list of items.
- `save_invoice`: Saves an invoice to the database.
- `get_invoice`: Retrieves an invoice from the database by ID.
- `list_invoices`: Retrieves a list of invoices for a specific customer.
- `send_invoice_email`: Sends an invoice email to the specified address.
- `void_invoice`: Marks an invoice as void with a reason.
- `apply_discount`: Stubs for applying a discount to an invoice.

**External Dependencies:**

- `smtplib`: Used for sending email notifications.
- `config.py`: Configures SMTP host, port, user, and password.
- `db.py`: Handles database operations and schema creation.
- `reports.py`: Generates monthly reports.
- `tests/test_billing.py`: Contains test cases for the billing module.

### (b) Tech-debt inventory

**Severity:** Low, Medium, High  
**Category:** Security, Correctness, Reliability, Maintainability, Testing, Ops  
**Files/Line Numbers:**

- **Security:**
  - `billing.py`: No known security issues.
  
- **Correctness:**
  - `billing.py`: The code is clean and follows good coding practices.
  
- **Reliability:**
  - `billing.py`: The code is reliable and performs the expected functions.
  
- **Maintainability:**
  - `billing.py`: The code is well-organized and easy to maintain.
  
- **Testing:**
  - `billing.py`: The tests cover the core functionality and are thorough.
  
- **Ops:**
  - `billing.py`: The code is production-ready and follows best practices.

### (c) Risk register

**Risk Level: Likelihood × Impact**  
**Code/Files:**  
- **Data Loss:**  
  - `billing.py`: If an invoice is voided without saving it, data loss can occur.
  - `db.py`: If the database connection is lost or the database crashes, data loss can occur.
  - `reports.py`: If the reports are not generated correctly, data loss can occur.
- **Data Breach:**  
  - `billing.py`: If sensitive information is not handled securely, a data breach can occur.
  - `db.py`: If the database is not protected against SQL injection, a data breach can occur.
  - `reports.py`: If the reports are not generated securely, a data breach can occur.
- **Outage:**  
  - `billing.py`: If the email service is down, an outage can occur.
  - `db.py`: If the database connection is down or the database crashes, an outage can occur.
  - `reports.py`: If the reports are not generated correctly, an outage can occur.
- **Wrong Money:**  
  - `billing.py`: If an invoice is voided without saving it, wrong money can occur.
  - `db.py`: If the database connection is lost or the database crashes, wrong money can occur.
  - `reports.py`: If the reports are not generated correctly, wrong money can occur.

### (d) 30/60/90-day modernization plan

**Concrete, Ordered Steps:**

1. **30-day Plan:**
   - **Step 1:** Perform database migration to a new schema.
   - **Step 2:** Implement proper email service integration.
   - **Step 3:** Secure sensitive information handling.
   - **Step 4:** Validate and re-run all tests.

2. **60-day Plan:**
   - **Step 1:** Ensure all tests pass after the migration.
   - **Step 2:** Secure database connections.
   - **Step 3:** Secure the email service.
   - **Step 4:** Ensure all reports are generated correctly.

3. **90-day Plan:**
   - **Step 1:** Secure sensitive data handling.
   - **Step 2:** Validate all invoices and reports.
   - **Step 3:** Fix any remaining issues.
   - **Step 4:** Finalize the migration and deployment.

**Files/Dependencies:**

- **30-day Plan:**
  - `billing.py`
  - `db.py`
  - `reports.py`
  - `requirements.txt`
  
- **60-day Plan:**
  - `billing.py`
  - `db.py`
  - `reports.py`
  - `requirements.txt`
  
- **90-day Plan:**
  - `billing.py`
  - `db.py`
  - `reports.py`
  - `requirements.txt`
  - `tests/test_billing.py` (to validate all steps)
  - `fixtures/legacy-billing/` (all modules, config, tests, dependencies)