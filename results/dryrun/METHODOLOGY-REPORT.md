# Methodology dry-run report — 2026-09-22 (v2, with explicit evidence)

**Scope.** Validate the evaluation methodology itself before any candidate model
runs and before touching any real environment. Everything ran locally:
synthetic fixture + `/tmp` copies only. No real repos, no real services.

## Evidence legend

Every claim below carries one of three labels:

- **[REAL]** — genuinely executed. The code ran, the files were read/written,
  the numbers were computed from actual inputs.
- **[SIM]** — simulated input, real plumbing. The input was fabricated (by me
  or by a mock), but the code under test executed for real against it.
- **[OPEN]** — not validated. No evidence either way; a known gap.

## Validation results

### 1. T0 hard gate (`judge/t0_checks.py`) — [REAL]
- T1: `t0_checks.py --task T1 --candidate results/dryrun/T1-candidate-simulated.md
  --inventory fixture/DEBT-INVENTORY.md --workdir fixture/legacy-billing`
  → exit 0, `T0 T1: ALL CHECKS PASSED (3/3 checks)`.
- T2: `--task T2 --workdir /tmp/t2-dryrun --candidate results/dryrun/T2-candidate-simulated.md`
  → exit 0, `T0 T2: ALL CHECKS PASSED (6/6 checks)`, including the
  `t2_plan_before_code` timestamp check (PLAN.md 22:58:17 predates billing.py
  22:58:24, verified with `ls --time-style=full-iso`).
- Fail paths [REAL]: missing plan section, out-of-range `billing.py:9999` ref,
  unimplemented stub, unknown `--task` → exit 2. Re-covered as regression
  tests in `tests/test_t0_gate.py` (T1 good/bad, T2 good/bad-ordering via
  explicit `os.utime` mtimes/bad-stub, T3 good/bad-URL).

### 2. Jev judge pipeline (`judge/jev_judge.py`) — [SIM] input, [REAL] plumbing
- Ran 3× with `PYTHONPATH=tests/helpers/mock_typesafe` (canonical mock location;
  the original dry-run copy under `results/dryrun/` was removed as redundant),
  `TYPESAFE_API_KEY=dryrun-dummy`, `MOCK_RUN=1/2/3` → exit 0 each.
- [REAL] plumbing verified: argument parsing, state assembly, candidate
  truncation logic, stdout table rendering, composite arithmetic
  (weights 2,3,2,2,2,3 → run1 composite **80.0/100**, mean confidence 0.74),
  the low-confidence rule firing (**t1_precision** at conf 0.52 < 0.55 was
  flagged for senior review), `--json-out` schema
  (`results/dryrun/jev-run{1,2,3}.json` contain task/composite/mean_confidence/
  flagged/items/deterministic_recall/est_cost_usd), cost estimate line.
- [SIM] every score and confidence value is canned. No real model judged
  anything; the mock returns fixed numbers regardless of candidate content.

### 3. Deterministic debt recall — [REAL] matching on [SIM] candidate text
- Computed **12/14 (86%)** on the simulated review; correctly reported the
  misses: `reports.py:17` (I cited `:16` — a genuine citation error the check
  caught) and `config.py:13` (D14, never mentioned).
- The candidate text itself is [SIM] (I wrote it playing candidate), but the
  regex matching, anchor parsing, and miss reporting executed genuinely.

### 4. Anchor verification — [REAL]
- All 14 `file:line` anchors in `fixture/DEBT-INVENTORY.md` checked against
  actual fixture line counts; spot-verified by hand (D7 `reports.py:17` is the
  `created` WHERE clause, D10 `test_billing.py:10` is the stale call,
  D14 `config.py:13` is the absolute DB path). Now a regression test
  (`tests/test_anchors.py`) so any future fixture edit that shifts lines fails
  the suite loudly.

### 5. pass@k aggregation (`judge/aggregate.py`) — [REAL] math on [SIM] inputs
- 3 mock JSONs → composite mean 79.1 (min 73.3, max 84.0), pass@k=1,
  pass^3=1, "reliable" interpretation. The flaky path (pass@k=1, pass^3=0,
  "capable but flaky") was verified with synthetic inputs.
- The aggregation arithmetic is [REAL]; the run-to-run variance is [SIM].

### 6. Calibration ritual (`judge/calibration.py` + `calibration.csv`) — [REAL] math on [SIM] data
- 6 honest senior-vs-mock rows → 100% agreement, no false RECALIBRATE.
  Divergent synthetic data → `RECALIBRATE` flag fires correctly.
- Now also reports **Cohen's κ on choice-item verdicts** alongside the
  |diff| ≤ 0.15 heuristic: 6 illustrative `t3_time` verdict pairs (choice
  options from `rubrics/rubric-T3.json`) → κ = 0.500, hand-verified from the
  rows (p_o = 4/6, p_e = 1/3). Perfect-agreement (κ = 1.0) and
  chance-agreement (κ = 0.0) paths are regression-tested. The categorical
  rows are [SIM] illustration; real T3 calibration is [OPEN].
- The 0.55 escalation cutoff is now parameterized (`jev_judge.py
  --low-conf-threshold`, default unchanged); the migration path to a
  target-agreement-level rule ("escalate until senior-agreement ≥ 0.80") is
  documented in README and blocked on live calibration data.
- The agreement computation is [REAL]; whether real Jev confidences agree
  with real senior grades is [OPEN].

### 7. T2 discipline rehearsal — [REAL] artifacts, [SIM] role separation
- [REAL]: PLAN.md written before any code edit; `apply_discount` genuinely
  implemented in `/tmp/t2-dryrun/billing.py`; `tests/test_discount.py`
  genuinely executed → **passed 5/5** against a real temp SQLite database
  (DB isolated via temp file); REVIEW.md genuinely written with verdict
  "approve" plus test evidence; T0 T2 6/6 on the real artifacts.
- [SIM]: planner, implementer, and reviewer were played by me in one session,
  not isolated subagents. True multi-agent context separation is [OPEN]; the
  timestamp check is a partial mitigation, not a proof.

### 8. Unified regression suite (`tests/run_all.py`) — [REAL]
- `python3 tests/run_all.py` from the pack root → **24 tests, 0 failures,
  0 errors**, exit 0. Single overview written to
  `results/pack-test-overview.md`. This is the executable version of
  items 1–6 above.

### 9. Spend — [REAL]
- $0. No real API keys were used (only `dryrun-dummy`); no network calls to
  any model or service were made. The fuel-gauge discipline held.

## Findings

- **F1. Anchor hygiene [REAL] → fixed.** Anchors verified accurate today;
  regression test added. Evidence: `tests/test_anchors.py` passing.
- **F2. T2 single-context fakery [REAL observation] → mitigated.**
  My rehearsal proved T0 couldn't distinguish one session playing three roles
  from three agents. `t2_plan_before_code` added and validated (6/6).
  Residual risk (no per-agent tool logs) is [OPEN].
- **F3. Live Jev call path [OPEN].** Mock proved plumbing only. Real
  `system_one` response shape, confidence calibration, and failure modes are
  unknown until one real call succeeds. This is the remaining gate.
- **F4. T3 hands-on install [OPEN].** No plugin was installed in the dry run;
  side-effect risk unmeasured. First real T3 stays read-only/containerized.
- **F5. Baselines protocol [OPEN] in practice.** `tasks/BASELINES.md` written,
  never exercised.

## What this dry run proves — and what it does not

**Proves [REAL]:** the evaluation machine runs. Gates gate, recall is
measured correctly, anchors are sound, aggregation and calibration math are
correct, the T2 discipline loop is executable, the whole suite passes, and it
all costs $0 on disposable fixtures.

**Does not prove [OPEN]:** that the machine *measures correctly*. Whether Jev
discriminates strong from weak reviews, whether the rubric ranks real models
sensibly, and whether the T2 discipline artifacts reflect genuine multi-agent
behavior all require real candidate outputs and the live Jev call.

## Risk register for real candidate runs

| Risk | Mitigation | Evidence status |
|---|---|---|
| Runaway API/subscription cost | T0 gate before any judge spend; `--repeat 3` cap; per-candidate cost in scorecard.csv; fuel-gauge check per stage | [REAL] $0 dry run |
| Destructive edits to real code | T2 only on disposable fixture copies; T1 read-only by prompt; never point a candidate at a real repo in Stage 2 | [REAL] rehearsal in /tmp copy |
| Plugin/MCP side effects (T3) | First pass read-only or containerized; pinned, allowlisted extensions | [OPEN] never rehearsed |
| Judge miscalibration | Low-confidence → senior review; agreement tracked in calibration.csv | [SIM] math real, live behavior open |
| Single-run noise | pass@1 + pass^3 over ≥3 repeats | [REAL] math, [SIM] variance |

## Go / no-go

**Stage −1 verdict: NO-GO for candidate comparisons — evaluator plumbing
validated only** (corrected 2026-09-30; the earlier conditional "GO"
understated what qualification requires).

What the dry run genuinely proved [REAL]: the suite runs end to end
(78 deterministic tests green), gates refuse bad inputs loudly
(mixed rollouts, mixed vintages, malformed traces, canonical-tree writes),
anchors are content-checked, and total API spend was $0.

What it did NOT prove — the qualification gates that must pass before any
ranked candidate comparison:
1. **T1 controls**: a strong and a weak T1 control, graded by deterministic
   scoring + live Jev + an independent senior judge, ordering correctly
   (strong > weak) — never run.
2. **T2 role separation**: genuine separate agent roles (or a real
   multi-agent harness) with logs, hidden tests, repeatability, and
   role-separation proof — all T2 roles were played by one session [SIM].
3. **T3 sandboxing**: install/configure inside a temporary HOME/config or a
   container, pinned allowlisted extension, before/after manifests, cleanup
   proof — never rehearsed [OPEN].
4. **Live Jev calibration**: one authorized live call to verify the real
   response shape, confidence behavior, and discrimination on known
   strong/weak items — never made; all Jev scores to date are canned [SIM].
5. **Baseline protocols exercised**: the documented baselines have been
   specified but never run in practice.
6. **Validity/isolation/repeatability/agreement/cleanup/maximum-cost gates**:
   stated as policy, not yet enforced by a run.
7. **Plural independent review** of the final qualification report.

Until gates 1–7 pass, candidate scores may be collected for plumbing
exercise only and must never be presented as a ranking. When they pass,
this section gets re-dated and re-signed — not before.

## Known limitations / future work (from the 2026-09-30 literature survey)

Full survey: `research/LLM-BENCHMARK-LANDSCAPE.md`. Each item keeps the
pack's evidence-label convention.

- **L1. Agreement rule is ad hoc [OPEN].** `|diff| ≤ 0.15` is a v1
  heuristic; literature prefers Cohen's κ or TH-Score. Upgrade to κ once ≥ 2
  independent senior graders exist.
- **L2. 22 anchors is small for discrimination [OPEN].** Anthropic's 20–50
  task guidance implies close candidates won't separate on 22 anchors.
  Report confidence intervals, not point estimates; consider growing the
  inventory.
- **L3. Escalation cutoff should become a target agreement level [OPEN].**
  "Escalate until senior-agreement ≥ 0.80" is auditable; "conf < 0.55" is
  not. Redesign the tiering rule once calibration data accumulates.
- **L4. T2 coordination quality [REAL plumbing / OPEN validation].**
  Implemented 2026-09-30: `tasks/t2-discount-fix/plant_bugs.py` plants 2
  seeded subtle bugs (off-by-one qty, swapped CA/TX tax rates, dropped
  None-guard — catalog of 3, seeded sample of 2) into a disposable fixture
  copy, never the canonical tree; `rubric-T2.json` gains `t2_coord_1`,
  `t2_coord_2` (did the reviewer catch the planted bugs?) and
  `t2_plan_match` (did the implementation follow PLAN.md). The regression
  suite asserts each planted bug is behaviorally detectable and the fixture
  stays byte-identical. Still [OPEN]: no real multi-agent run has faced
  planted bugs yet, so reviewer catch rates are unknown.
- **L5. T3 claim-level rubric [REAL plumbing / OPEN validation].**
  Implemented 2026-09-30: `rubrics/rubric-T3.json` rewritten on the
  MCP-Atlas template — `t3_discovered` / `t3_installed` / `t3_configured` /
  `t3_functional` / `t3_recovered` (each with evidence requirements) plus
  the unchanged `t3_time` choice item (option keys untouched, so the
  calibration κ fixture still applies). A private holdout split of
  extension tasks is documented in the rubric as [OPEN] — no holdout task
  exists or has been run yet. Still [OPEN]: the claim items have never been
  graded by live Jev or a senior judge.
- **L6. T2 thrash detection [REAL plumbing / OPEN validation].**
  Implemented 2026-09-30: `tasks/t2-discount-fix/TRACE-FORMAT.md` defines
  the JSONL action-trace format; `judge/trace_check.py` reports the
  (action, target) distribution and a plain Shannon entropy diagnostic,
  flagging consecutive repetition (looping) and low-variety windows
  (thrashing) in plain language — no named metrics, per the literature
  guidance (item 16: citable metric names don't exist in this space).
  Still [OPEN]: flag thresholds are uncalibrated against real T2 traces,
  and no harness emits traces yet; flags mean "send to senior review".
- **L7. Small composite gaps are noise [OPEN].** ~55% of judge variance is
  unexplained by rubric criteria (autorubric diagnostics). Policy: report
  T0, pass@k/pass^k, and calibration next to every composite; treat close
  scores as ties.
- **L8. Fixture rotation: procedure [REAL], effectiveness [OPEN].**
  Implemented 2026-09-30 (`tasks/t1-legacy-review/rotate_fixture.py`):
  deterministic AST-based identifier rotation emits variant pairs
  (renamed tree + remapped inventory + VINTAGE stamp, gitignored), anchors
  preserved, Expect lines re-verified, vintage stamped through the judge
  pipeline with mixed-vintage aggregation refused. Still [OPEN]: we have
  not measured a memorized model scoring lower on a variant; rotation is
  a precaution, not a proven defense. Policy: fresh seed per candidate
  campaign; never compare scores across vintages.
