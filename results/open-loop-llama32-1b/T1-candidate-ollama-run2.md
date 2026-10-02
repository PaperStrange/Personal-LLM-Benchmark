**Global Project Review**
========================

**Overview**
------------

This review assesses the current state of the `BillingSvc` project, specifically its legacy codebase, and provides recommendations for improvement.

**Architecture Map**
-------------------

The project's architecture is as follows:

*   **Modules and Responsibilities**:
    *   The `billing.py` module contains the invoice math, tax, and DB writes logic.
    *   The `db.py` module provides shared SQLite helpers.
    *   The `config.py` module configures the service.
    *   The `reports.py` module generates monthly CSV reports.
    *   The `requirements.txt` file lists dependencies.
    *   The `tests/test_billing.py` module tests the billing logic.
*   **Entry Points**:
    *   The `billing.py` module serves as the entry point for the billing logic.
    *   The `db.py` module provides a stub for the `apply_discount()` method.
    *   The `config.py` module configures the service.
*   **External Dependencies**:
    *   The `requests` library is used for HTTP requests.
    *   The `gunicorn` server is used for running the Flask app.

**Tech-Debt Inventory**
------------------------

A tech-debt inventory was created to track known issues in the codebase. The inventory includes:

*   **Severity**:
    *   Critical (1)
    *   High (2)
    *   Medium (3)
    *   Low (4)
*   **Category**:
    *   Security (1)
    *   Correctness (2)
    *   Reliability (3)
    *   Maintainability (4)
    *   Testing (5)
    *   Ops (6)
*   **File:Line Reference**:
    *   For example, a file containing a known issue might look like this:
    ```
# bug#123: Fix the issue in billing.py
```