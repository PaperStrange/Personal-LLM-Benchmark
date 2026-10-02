# BillingSvc (fixture)

Fictional internal invoicing service. The original owner left in 2023 and
the codebase has been in maintenance mode ever since. It is small on purpose:
a few hundred lines is enough to tell whether a candidate model can map a
codebase, find the debt, and plan realistically — without burning your
context window or your budget.

## Layout

| File | What it does |
|---|---|
| `billing.py` | Invoice math, tax, DB writes, email — all in one module. Contains a stub `apply_discount()` used by task T2. |
| `db.py` | Shared SQLite helpers. |
| `config.py` | Service configuration. |
| `reports.py` | Monthly CSV reporting. |
| `requirements.txt` | Dependency pins. |
| `tests/test_billing.py` | The test suite. Take its claims with a grain of salt. |

## Rules for candidates

- Read-only for task T1 (global review). Do not modify any code.
- Task T2 may edit code, but only after writing `PLAN.md`.
- `fixture/DEBT-INVENTORY.md` (one level up) is the hidden answer key.
  **Never show it to a candidate.** It exists so judges can score recall.

## Swapping in your own repo

To evaluate against your real legacy codebase instead of this fixture:
1. Copy a snapshot of your repo into `fixture/` (or point the task prompts at it).
2. Write your own `DEBT-INVENTORY.md` with 10–15 known issues in the same
   format (`### Dn \`file:line\`` entries).
3. Reuse the rubrics in `rubrics/` unchanged — only T1's recall item needs
   the inventory, and `judge/jev_judge.py --inventory` handles it.
