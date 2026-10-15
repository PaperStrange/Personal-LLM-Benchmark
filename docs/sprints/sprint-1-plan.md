# Sprint 1 — Tier 1 framework changes

**Sprint goal:** make cost a measured metric and close the governance holes, with
zero spend and no judge dependency. **Backlog items:** A-1…A-6, B-1.
**Started:** 2026-10-14. **Owner:** Harry.

## Stories and acceptance criteria

**S1.1 — Candidate identity in judge outputs (A-1, code)**
`jev_judge.py` gains a `--model` flag (the pre-existing required
`--candidate` file argument is kept); both values are stamped into every
`--json-out` payload. Existing tests updated; new test asserts the stamp is
present. AC: `python3 tests/run_all.py` (the pack's suite) green; `--json-out`
from a dry invocation contains `model` and `candidate` fields.

**S1.2 — `post_training` lineage field (A-6, schema)**
Scorecard schema gains a mandatory `post_training` field; empty/unknown allowed
with an explicit `unknown` value (never blank). AC: schema documented in
methodology.md; correction (review, 2026-10-14): no code in the pack reads or
writes `results/scorecard.csv` — rows are hand-written by design — so the
schema change is the CSV header plus documented semantics, and no code path
can read or drop the column.

**S1.3 — Reliability log (A-2, code + docs)**
`results/run-log.jsonl` schema defined: `date, task, candidate, harness, status
(ok/fail), failure_kind`. Runbook rule: failure rate reported per
(candidate × task) next to pass@k; >10% unusable output → not recommended
regardless of score. AC: schema doc + one example line; runbook section written.

**S1.4 — Latency discipline (A-3, docs)**
Runbook: record wall-clock per attempt at run time (stopwatch discipline);
populate the existing `wall_time_s` scorecard column; report median per
(candidate × task). AC: runbook section written; column semantics documented.

**S1.5 — Within-tie ordering + quality-per-dollar rule (A-4, docs)**
Runbook: candidates inside the tie band (|Δcomposite| < max run-spread) are
ordered by measured `cost_usd`, then latency. Decision rule: the ratio governs
ONLY when (a) the budget binds or (b) raw scores tie inside the band; otherwise
the raw ranking stands. Both rankings shown side by side. AC: runbook section
written; example worked through.

**S1.6 — $25 cap persistence (A-5, docs)**
The $25 hard campaign cap (standing chat decision, 2026-10-03) written into
methodology.md and runbook.md with its semantics: guardrail, aborts are [INFRA]
not model failures. AC: cap stated in both docs; runbook states abort handling.

**S1.7 — Senior gate with bootstrap (B-1, docs)**
Runbook: first 6 senior spot-checks (one per T1 item or equivalent) are exempt
and establish the baseline; the gate applies thereafter — no *further* senior
spend until cheap-tier agreement meets the calibration bar. AC: runbook section
written; the circularity is named and the bootstrap resolves it.

## Definition of Done

1. Suite green (no regressions).
2. Docs changes reviewed for consistency (no contradictions between
   methodology.md, runbook.md, and the framework-iterations doc).
3. Plural independent review (adversarial + mistake-hunt) with written records;
   findings applied.
4. Pushed to remote `main`; verified present on remote.
5. Backlog updated: A-1…A-6, B-1 → DONE.

## Out of scope

Tier 2/3 items, any judge-path work (BLOCKED on Sakura's C-1 decision), any
spend. Suite scope: the pack's existing test suite — no new harness code for
candidate-side logging (that's E-3, Tier 2).
