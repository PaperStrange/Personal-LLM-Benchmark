### Architecture Map

**Modules and Responsibilities:**

- **billing.py:**
  - **generate_invoice**: Builds an invoice dictionary with subtotal, tax, and total.
  - **calculate_tax**: Calculates tax for a subtotal based on the state.
  - **save_invoice**: Inserts an invoice into the database.
  - **get_invoice**: Retrieves an invoice from the database.
  - **list_invoices**: Retrieves all invoices for a specific customer.
  - **send_invoice_email**: Sends an email to a customer with their invoice details.
  - **void_invoice**: Marks an invoice as void and provides a reason.
  - **charge_invoice**: Charges a credit card for an invoice.
  - **apply_discount**: Applies a discount to an invoice (stub).

- **config.py:**
  - **TAX_RATES**: Mapping of tax rates by state.
  - **DEBUG**: Debug mode flag.
  - **SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS**: SMTP server details.
  - **DB_PATH**: Path to the database file.
  - **ALLOWED_HOSTS**: List of allowed hosts.
  - **SESSION_COOKIE_SECURE**: False for development.

- **db.py:**
  - **get_conn**: Returns a connection to the database.
  - **run_query**: Executes raw SQL queries.
  - **find_customer**: Finds a customer by name.
  - **init_schema**: Initializes the database schema.
  - **export_invoices**: Dumps all invoices for the month-end close.
  - **get_analytics_conn**: Returns a dedicated connection for reporting.

- **reports.py:**
  - **_tax**: Helper function for calculating tax.
  - **monthly_report**: Generates a monthly report of invoices.
  - **customer_totals**: Calculates the total for each customer.
  - **invoice_age_days**: Calculates the days since an invoice was issued.

- **requirements.txt**: List of dependencies for the project.

**Data Flow:**

1. **Create an invoice** (billing.py):
   - Generates an invoice with subtotal, tax, and total.
   
2. **Persist an invoice** (billing.py):
   - Inserts the invoice into the database.

3. **Email an invoice** (billing.py):
   - Sends an email to a customer with their invoice details.

4. **Report an invoice** (reports.py):
   - Generates a monthly report of invoices.

**Entry Points:**

- **billing.py**: Entry point for invoice generation and management.
- **config.py**: Configures the application and database.
- **db.py**: Handles database operations.
- **reports.py**: Generates monthly reports.
- **requirements.txt**: List of dependencies.

**External Dependencies:**

- **DB**: Database connection.
- **SMTP**: SMTP server for email sending.
- **TAX_RATES**: Tax rates.
- **DEBUG**: Debug mode.
- **ALLOWED_HOSTS**: List of allowed hosts.
- **SESSION_COOKIE_SECURE**: False for development.

### Tech-Debt Inventory

- **calculate_tax**: Tax calculation stub (billing.py).
- **send_invoice_email**: Email sending stub (billing.py).
- **apply_discount**: Discount application stub (billing.py).
- **void_invoice**: Invoice voiding stub (billing.py).
- **charge_invoice**: Credit card charging stub (billing.py).
- **monthly_report**: Monthly report generator (reports.py).
- **customer_totals**: Customer total calculation (reports.py).

**Severity:**
- High: **calculate_tax**
- Medium: **send_invoice_email**
- Low: All other tech-debt

**Category:**
- Correctness
- Reliability
- Maintainability
- Testing
- Ops
- Security

### Risk Register

- **Data Loss**:
  - **Risk**: Risk of data loss.
  - **Code**: `send_invoice_email` and `void_invoice`.
  - **Impact**: Data loss.
  - **File**: `billing.py`, `config.py`.

- **Security Breach**:
  - **Risk**: Risk of a security breach.
  - **Code**: `charge_invoice`.
  - **Impact**: Data breach.
  - **File**: `billing.py`, `config.py`.

- **Outage**:
  - **Risk**: Risk of a service outage.
  - **Code**: `charge_invoice`.
  - **Impact**: Service outage.
  - **File**: `billing.py`, `config.py`.

- **Wrong Money**:
  - **Risk**: Risk of incorrect money being charged.
  - **Code**: `charge_invoice`.
  - **Impact**: Incorrect money.
  - **File**: `billing.py`, `config.py`.

### 30/60/90-Day Modernization Plan

#### 30-Day Plan:

1. **Debug and Fix**:
   - Identify and fix all tech-debt issues in `billing.py`.
   - Implement `calculate_tax`, `send_invoice_email`, `apply_discount`, `void_invoice`, `charge_invoice`, `monthly_report`, and `customer_totals` as needed.

#### 60-Day Plan:

1. **Refactor**:
   - Refactor `billing.py` to use SQLAlchemy for ORM operations.
   - Refactor `billing.py` to handle database transactions more robustly.
   - Refactor `billing.py` to use a more secure approach for email sending.
   - Refactor `billing.py` to handle more complex invoice generation logic.

#### 90-Day Plan:

1. **Redesign**:
   - Design a new system for invoice generation and management.
   - Implement a new database schema and ORM.
   - Implement a new email sending system.
   - Implement a new reporting system.
   - Implement a new system for managing customer discounts.
   - Implement a new system for managing credit card charges.

**Sequence by Risk Reduction First, then Maintainability:**

1. **Debug and Fix**: 30 days.
2. **Refactor**: 60 days.
3. **Redesign**: 90 days.