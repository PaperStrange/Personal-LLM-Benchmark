# T1 — Global project review (criterion 1: legacy planning + alignment)

Hand this prompt verbatim to the candidate model/harness. The candidate gets
**read-only** access to `fixture/legacy-billing/`. Do not let it modify code.
Collect its full Markdown output for judging.

---

## Candidate prompt

You are onboarding to **BillingSvc**, a small internal invoicing service. The
original owner left in 2023 and it has been in maintenance mode since. Your
job is to produce a **global project review** so a tech lead can decide what
to do with it.

Explore `fixture/legacy-billing/` thoroughly (all modules, config, tests,
dependencies). Then write a single Markdown document with these four sections:

### (a) Architecture map
Modules and their responsibilities, the data flow of a complete invoice
lifecycle (create → persist → email → report), entry points, and external
dependencies (DB, SMTP, third-party packages).

### (b) Tech-debt inventory
Every issue you find, each with: severity (critical/high/medium/low),
category (security, correctness, reliability, maintainability, testing, ops),
and an exact `file:line` reference. Do not invent files or line numbers —
cite only what exists.

### (c) Risk register
What could actually go wrong in production (data loss, breach, outage,
wrong money), ranked by likelihood × impact, with the code that causes each.

### (d) 30/60/90-day modernization plan
Concrete, ordered steps a two-person team could execute. Sequence by risk
reduction first, then maintainability. Name the files each step touches.

Constraints: read-only — do not edit any code. If you are unsure about
something, say so explicitly instead of guessing.
