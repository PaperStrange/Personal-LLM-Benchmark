# Iteration plan — benchmark pack v2 → v3

The organized path. Each phase is a closed loop: implement → suite green →
docs truthful → commit. The standing workflow below is never broken by any
phase.

## Standing workflow (the thing in mind, always)

```
tasks ──▶ T0 gate (free, deterministic) ──▶ Jev judge (cheap) ──▶ senior spot-check
   │                                                              │
   └────────────── baselines (harness=none) ◀─────────────────────┘
                                    ▼
                    aggregate (pass@k / pass^k) ──▶ calibration ──▶ scorecard
                                    ▲
                    eval-the-evals suite: python3 tests/run_all.py (must stay green)
```

Every phase ends with: full suite green, README/methodology docs match
reality (no aspirational controls stated as fact), evidence labels ([REAL] /
[SIM] / [OPEN]) correct, then commit. Fixture edits must never shift
existing anchor line numbers — new fixture code is appended, never inserted.

## Phase 1 — Harden measurement (IN PROGRESS)

Goal: the pack can separate close candidates on evidence, not noise.

- **1a. Debt inventory 14 → 22 anchors.** Append ~8 new synthetic debts to
  fixture files (real flaws in code, appended at end of files so D1–D14 line
  numbers never shift). New inventory entries D15–D22 with accurate
  `file:line` anchors. Update `test_anchors` (count 14→22),
  `test_judge_pipeline` recall denominator, leakage audit titles, and every
  "14 anchors" reference in README / KB / methodology report.
- **1b. Reliability reporting.** `aggregate.py` gains composite std alongside
  mean/min/max (+ regression test). README documents the tie-band policy:
  |Δcomposite| smaller than the max observed run-spread is a tie until
  repeat data says otherwise (addresses "small gaps are noise").
- Acceptance: suite green (35 tests), `leakage_audit.py` ALL CLEAR,
  `test_anchors` 22/22.

## Phase 2 — Judge tiering (DISPATCHED 2026-09-30)

- **2a.** `calibration.py`: Cohen's κ on choice-item verdicts alongside the
  |diff| heuristic (κ needs categorical verdicts — choice items have them).
- **2b.** Parameterize the 0.55 escalation threshold; document the migration
  path to a target-agreement-level rule ("escalate until senior-agreement ≥
  0.80") once calibration data accumulates.
- **2c.** Strengthen `test_anchors.py`: each inventory entry gains an
  `Expect:` line with a short distinctive substring of its anchored fixture
  line; the test asserts the substring is present. (Phase 1 review found the
  current test only checks the line *exists* — a wrong-line anchor like the
  original D15 passed silently. Human review was the only gate.)
- Acceptance: suite green; calibration output shows both metrics on the
  checked-in rows (numeric rows are [REAL] ritual mechanics, categorical
  rows are [SIM] illustration until live T3 calibration exists);
  a deliberately wrong-lined anchor fails the suite.

## Phase 3 — T2/T3 depth (DISPATCHED 2026-09-30)

- **3a. T2 coordination quality.** Script plants 2 subtle bugs per run into
  the fixture copy; `rubric-T2.json` gains items: did the reviewer catch the
  planted issues? did the plan match the implementation?
- **3b. T3 claim-level rubric.** Rewrite `rubric-T3.json` on the MCP-Atlas
  template: discovered / installed / configured / functional /
  recovered-from-error, plus a private holdout split of extension tasks.
- **3c. T2 thrash check.** Define a JSONL action-trace format for T2 runs;
  checker computes tool-call entropy and flags looping/thrashing as a
  discipline signal (source a proper citation before naming any metric).
- Acceptance: suite green; planted issues caught by the pack's own checks.

## Phase 4 — Rotation & vintage (queued)

- **4a.** Fixture variant generator (identifier rotation procedure);
  `fixture_vintage` stamped into `jev_judge --json-out` and printed by
  `judge/aggregate.py` (which refuses mixed vintages); the `scorecard.csv`
  schema reserves a `fixture_vintage` column but no writer appends rows yet —
  aggregate reports are the stamped record today. Anchors re-verified per
  vintage by the suite.
- Acceptance: two vintages generated; `test_anchors` passes on both.

## Backlog (blocked on real data, not on us)

- Live Jev calibration call (needs TypeSafe API key + spend approval).
- Target-agreement escalation rule (needs calibration rows).
- First real candidate runs (needs candidate shortlist).

## Status log

- 2026-09-30: Plan written. Phase 1 dispatched.
- 2026-09-30: Phase 1 complete + committed (e0043ca). Two independent
  reviewers (adversarial + mistake-hunt) found 5 fixes, all applied:
  D15 re-anchored billing.py:15→:19, D18 consequence corrected
  (sqlite3 default timeout, not indefinite), README D1–D22, tie-band
  wording corrected (max−min band can't narrow), 4/22 recall disclosure
  added. 35 tests green, leakage ALL CLEAR (22).
- 2026-09-30: Phase 2 dispatched.
- 2026-09-30: Phase 2 complete + committed (326dabf). Two independent
  reviewers (adversarial + mistake-hunt) hand-verified the κ math
  (κ=0.500 on the 6 checked-in [SIM] rows), traced the threshold flag
  through the real code path, and attacked the D18 def-context check.
  One required fix applied: false citation in calibration.py docstring
  (claimed Gu et al. 2024 / "B10-B13" — neither exists; now points to
  the landscape doc's design flag 1). 42 tests green, leakage ALL CLEAR.
- 2026-09-30: Phase 3 dispatched.
- 2026-09-30: Phase 3 complete + committed. Two independent reviewers
  (adversarial + mistake-hunt) verified: planted bugs are real behavioral
  defects, canonical fixture untouched, rubric/report labels honest
  ([REAL plumbing / OPEN validation]). 4 fixes applied from review:
  loud warning when --bugs count != 2, T3 holdout wording aligned to
  "no holdout task exists yet", _inside() guard hardened to realpath
  (reviewer demonstrated an abspath symlink bypass — old code let it
  through, new code refuses, negative-proofed), trace_check reports
  malformed_lines in JSON (an all-garbage trace no longer "passes clean").
  59 tests green, leakage ALL CLEAR (22).
- 2026-09-30: Phase 4 dispatched.
- 2026-09-30: Phase 4 complete (uncommitted). `tasks/t1-legacy-review/
  rotate_fixture.py`: deterministic AST-based identifier rotation
  (~50 identifiers, seeded pools), emits variant pair (renamed tree +
  remapped inventory, anchors unchanged, Expect lines re-verified against
  renamed code), refuses the canonical tree, freezes the T2
  `apply_discount(invoice_id, pct)` contract. `jev_judge.py
  --fixture-vintage` stamps `--json-out`; `judge/aggregate.py --vintage`
  prints it and refuses mixed vintages (exit 2); legacy unstamped inputs
  aggregate as "unknown". 17 new tests in `tests/test_rotation.py`
  (two vintages differ from each other + canonical, anchors pass per
  vintage, leakage ALL CLEAR per vintage, behavioral equivalence,
  canonical untouched). Suite: 76 tests green, leakage ALL CLEAR (22).
- 2026-09-30: Phase 4 plural review (adversarial + mistake-hunt) BLOCKED
  the first tree on two integrity findings, both fixed before commit:
  (1) the word-boundary prose remapper corrupted the judge's answer key
  (rewrote English words and API refs — e.g. `datetime.datetime.now()`
  became the false `datetime.datetime.current_time()`); prose remapping is
  now restricted to bare-identifier backtick spans whose new name provably
  occurs in the variant code, with a regression test pinning the observed
  corruption classes plus a span invariant (no invented names, no missed
  remaps). (2) `--fixture-vintage` silently defaulted to canonical, which
  would mislabel a variant run with no error; it now auto-detects from the
  VINTAGE file next to `--inventory`, falling back to `v1-2026-09` only for
  the canonical tree (regression-tested both ways). Should-fix applied too:
  collision check 3 no longer compares against Attribute names
  (`conn.cursor()` falsely rejected 103/200 seeds; verified 0/200 rejected
  now) and now covers import aliases as bare-namespace identifiers.
  Mistake-hunt also required a README wording fix (scorecard.csv has the
  `fixture_vintage` column in schema but no writer appends rows yet).
  Final: 78 tests green, leakage ALL CLEAR (22), canonical fixture
  byte-identical.

- 2026-10-01: LEAK FINDING (banked for later iterations, per Sakura): the
  qwen2.5-1.5b and llama3.2-1b T1 open-loop runs passed T0 under gate v1 while
  citing zero `file:line` references — a vacuous pass, since `t1_refs_valid`
  only checked cited refs for range validity and never required presence.
  Gate v2 (applied 2026-10-01, Sakura-approved) now FAILS zero-ref candidates.
  The v1 passes are NOT reclassified; they stand as documented artifacts of
  the hole. Lesson for future gates: every "validates X" check must also
  assert "X is present" — a validity check without a presence requirement
  passes vacuously. Audit all T0/T1/T2/T3 checks for this pattern next
  iteration.
