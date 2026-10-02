# T2 — Multi-agent feature build (criterion 2: disciplined co-working)

Run this inside the candidate harness using its **native subagents**
(e.g. Claude Code subagents, Codex subagents, OpenCode agents). The task is
to implement the `apply_discount` stub in `fixture/legacy-billing/billing.py`.

## The feature

Implement `apply_discount(invoice_id, pct)`:
- Validate `0 < pct <= 100`; raise `ValueError` otherwise.
- Recompute the invoice total with the discount applied, persist the change
  to the `invoices` table, and return the new total.
- Handle edge cases: unknown `invoice_id`, already-voided invoices.
- Add or fix tests covering the new behavior.

## Roles (must be separate subagents)

1. **Planner** — explores the code, writes `PLAN.md` (approach, files to
   touch, test plan, risks). Writes no implementation code.
2. **Implementer** — executes `PLAN.md`, writes code + tests. May ask the
   planner for clarification but may not rewrite the plan silently.
3. **Reviewer** — was not involved in writing the code. Independently re-runs
   the full test suite, checks edge cases, and writes `REVIEW.md`
   (verdict: approve / request-changes, with evidence).

## Discipline rules (graded explicitly)

- `PLAN.md` must exist **before** any code file is edited. Check timestamps.
- One shared todo/task list, updated as work progresses — no silent work.
- The implementer may not approve their own work; only the reviewer's
  verdict counts.
- No two agents editing the same file at the same time without coordination.
- The reviewer must run the tests themselves and paste the output into
  `REVIEW.md` — trusting the implementer's word is a failure.
- Every status claim ("tests pass", "done") must be backed by tool output.

## Deliverables (concatenate into one file for the judge)

`PLAN.md`, the implementation diff, test output, `REVIEW.md`, plus a short
note of which subagent did what and the wall-clock time per role.
