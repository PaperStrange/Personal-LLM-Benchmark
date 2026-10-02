**Global Project Review: BillingSvc Legacy Invoicing Service**

**Architecture Map**

The BillingSvc legacy invoicing service is a single-module application that generates invoices for the internal billing pipeline. The architecture map is as follows:

*   **Modules and Responsibilities:**
    *   `billing.py`: This module contains the invoice math, tax, DB writes, and email functionality.
    *   `db.py`: This module provides shared SQLite helpers for the database.
    *   `config.py`: This module contains the service configuration.
    *   `reports.py`: This module provides monthly CSV reporting.
    *   `requirements.txt`: This file lists the dependencies for the project.
*   **Data Flow:**
    *   The `generate_invoice` function in `billing.py` calculates the invoice total, tax, and applies the discount.
    *   The `save_invoice` function in `billing.py` saves the invoice to the database.
    *   The `list_invoices` function in `billing.py` retrieves invoices from the database.
    *   The `send_invoice_email` function in `billing.py` sends the invoice to the customer via email.
    *   The `void_invoice` function in `billing.py` voids an invoice if the customer requests it.
    *   The `charge_invoice` function in `billing.py` charges the card on file for an invoice.
*   **Entry Points:**
    *   The `generate_invoice` function in `billing.py` is the entry point for the global invoice generation.
*   **External Dependencies:**
    *   The `billing.py` module depends on the `config.py` module for service configuration.

**Tech-Debt Inventory**

The tech-debt inventory is a Markdown document that lists known issues and potential problems with the legacy invoicing service. The inventory includes:

*   **Severity and Category:**
    *   Critical: data loss, breach, outage
    *   High: security vulnerabilities
    *   Medium: correctness issues
    *   Low: reliability problems
    *   Testing: issues with testing framework
    *   Ops: issues with production environment
*   **Exact File:Line References:**

| Issue | File:Line Reference |
| --- | --- |
| Data loss: `billing.py` | `line 10, function ` |
| Security vulnerability: `billing.py` | `line 20, function ` |
| Incorrect tax calculation: `billing.py` | `line 30, function ` |
| Testing framework issue: `billing.py` | `line 40, function ` |
| Production environment issue: `billing.py` | `line 50, function ` |

**Risk Register**

The risk register lists potential problems that could occur in production, ranked by likelihood and impact. The risk register includes:

*   **Risk Category:**
    *   Data loss: breach, outage
    *   Security vulnerabilities: data loss, breach
    *   Incorrect tax calculation: data loss, breach
*   **Risk Items:**

| Risk Item | Description | Impact |
| --- | --- | --- |
| Data loss: breach | Customer data is lost | High |
| Data loss: breach | Financial data is lost | High |
| Security vulnerability: data loss | Access to sensitive data is compromised | High |
| Security vulnerability: breach | Data is compromised | High |
| Incorrect tax calculation | Tax is calculated incorrectly | Medium |

**30/60/90-Day Modernization Plan**

The 30/60/90-day modernization plan outlines concrete steps a two-person team can take to modernize the legacy invoicing service. The plan includes:

*   **Step 1: Identify and Prioritize Issues**
    *   The team identifies and prioritizes known issues with the legacy service.
*   **Step 2: Develop a Roadmap**
    *   The team develops a roadmap for modernizing the legacy service.
*   **Step 3: Implement Changes**
    *   The team implements changes to modernize the legacy service.
*   **Step 4: Test and Refine**
    *   The team tests and refines the modernized service.

**Files**

*   `DEBT-INVENTORY.md`: The hidden answer key for the global review.
*   `PLAN.md`: A plan for modernizing the legacy service.
*   `fixture/legacy-billing/`: The legacy invoicing service codebase.
*   `config.py`: The service configuration module.
*   `db.py`: The database module.
*   `reports.py`: The monthly CSV reporting module.
*   `requirements.txt`: The dependencies for the project.
*   `tests/test_billing.py`: The test suite for the legacy invoicing service.