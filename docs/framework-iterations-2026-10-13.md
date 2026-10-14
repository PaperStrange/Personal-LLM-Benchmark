# Framework iterations from cost-methodology gap analysis (2026-10-13, rev.2)

What this is: a gap analysis of our pack's *cost treatment* against three benchmarks chosen
for their cost methodology — OmegaUse-OfficeVal (per-task price proxies, value-weighted scores),
AssemblyAI Voice Standard Bench (quality+speed+cost tables, no composite), MLPerf Training v6.1
(budget-as-benchmark). Deep-read reports from all three informed this; solo self-Q&A in
`docs/benchmark-validation-selfqa-2026-10-13.md`.

**Scope limitation (stated, not buried)**: the comparison set was selected for cost methodology,
not for code-workflow coverage. Actual benchmark neighbors (SWE-bench, τ-bench, Terminal-Bench)
were not compared. Nothing below validates our *goal* against rival code benchmarks — it
validates our *budget treatment* against benchmarks that do it well. All external claims are
[SECONDARY] (researcher-read, not first-hand). Per the solution-validity law, every iteration
is a hypothesis until a candidate campaign measures it.

**Validation verdict (downgraded honestly)**: our goal — LLM+harness selection for code workflow
under startup budget — remains distinct among the three compared. But all three operationalize
cost as a *metric* while we use budget only as a *guardrail* (the $25 cap is a standing chat
decision, not yet written into GOAL.md/methodology.md). That is the central gap, and it survives
review. What did NOT survive review: the original draft's claims that candidate token/cost
logging "already exists" (it doesn't), that pass@4 is "free" (+33% judge spend), and that the
senior-gate was implementable as written (circular). Those are corrected below.

## Tier 1 — docs + small code, before the next candidate run

### 1.1 Cost-per-task: populate, don't pretend
**Status correction**: `jev_judge.py --json-out` captures only a judge-side `est_cost_usd`
(chars/4 estimate). There is NO candidate token/cost capture — candidate runs are manual
harness executions producing markdown. `results/scorecard.csv` already has `cost_usd` and
`wall_time_s` columns in its schema (zero data rows; rows are hand-written per the runbook).
**Action**:
1. Add `--model`/`--candidate` to `jev_judge.py`, stamped into `--json-out` (small code +
   test update) — without a candidate identifier no per-model price table can ever apply.
2. Populate `cost_usd` per scorecard row from provider dashboards/billing after each run
   (manual, honest about it — same as rows today).
3. Candidate-side automated token logging requires instrumenting harness runners that don't
   exist as code — Tier 2, not tonight.
**Decision rule for quality-per-dollar** (new, required): the ratio governs ONLY when (a) the
budget binds, or (b) raw scores tie inside the band. Otherwise the raw ranking stands — a
non-binding $25 cap should buy the 90 @ $0.50/task over the 85 @ $0.05/task, and the doc must
say so. Both rankings shown side by side; the rule above picks.

### 1.2 Reliability log (new file, then gate)
**Status correction**: no run log exists; failed attempts produce no `--json-out`.
**Action**: (1) define `results/run-log.jsonl` — one line per attempt: `date, task, candidate,
harness, status (ok/fail), failure_kind`; (2) report failure rate per (candidate × task) next
to pass@k; (3) runbook rule: >10% unusable output → not recommended regardless of score
(the 10% is a proposed heuristic, not sourced — AssemblyAI excluded unreliable models but
published no threshold). Owner: agent.

### 1.3 Latency: manual population, not --json-out
**Status correction**: wall-clock can't go in `--json-out` — that's the judge tool; candidate
latency happens in manual harness runs. **Action**: record wall-clock per attempt alongside
the run (stopwatch discipline in the runbook); populate the existing `wall_time_s` scorecard
column; report median per (candidate × task). Docs-only.

### 1.4 Within-tie ordering by cost (the actual gap)
**Status correction**: methodology.md already defines the tie rule (|Δcomposite| < max
run-spread → tie). What's missing is only *ordering within* the band. **Action**: runbook
rule — candidates inside the tie band are ordered by measured `cost_usd` (then latency); a
candidate outside the quality band cannot win on price. Docs-only.

### 1.5 Senior gate with bootstrap clause (was circular)
**Status correction**: "no senior grades until Jev agreement meets threshold" deadlocks —
agreement is *measured by* senior grades. **Action**: runbook rule with bootstrap — the first
N senior spot-checks (N=6, one per T1 item or equivalent) are exempt and establish the
baseline; the gate applies thereafter: no *further* senior spend until cheap-tier agreement
meets the calibration bar. (Also corrected: MLPerf's figure is "1024 GB300-hours," a workload
cap — not "1004 trajectories" and not a staging policy.) Docs-only.

### 1.6 `post_training` lineage field
Unchanged from rev.1: mandatory scorecard field per candidate from vendor release notes;
honest caveat — vendors rarely disclose recipes, expect mostly "unknown"; test correlation
after 2+ campaigns, drop if null. Small schema edit.

## Tier 2 — after campaign 1 (needs real work or spend)

### 2.1 pass@4 as headline — DEMOTED from Tier 1
**Status correction**: not free. Methodology mandates minimum 3 repeats; k=4 is +33% on the
costliest line item and contradicts the published budget math. **Action**: needs Sakura's
budget sign-off, not an agent tonight-action. Kept as a proposal with MLPerf's variance
finding cited as supporting (not dispositive) evidence — a training-systems variance result
doesn't by itself retire our pass@k/pass^k semantics, which answer the buy question directly.

### 2.2 Negative-weight damage items + usability gate (T2)
Unchanged: add "no pre-existing tests broken" / "no unrelated files modified" with negative
weights; hard gate that the diff applies cleanly. Note (new): `normalize()`/aggregate math
assumes 0–100 composites — negative weights need OmegaUse's clip-at-zero handling or the
60-threshold semantics break. Rubric + test update.

### 2.3 Calibration as convergence loop
Unchanged: on disagreement, fix rubric/judge wording, re-run, bank the resolution. Process
change starting with tonight's Gate 4 calibration.

### 2.4 Input-scale stratification
Unchanged (T1 at two fixture sizes; watch for rank crossovers). **Honest caveat** (new): if
crossovers appear, the single-ranked-list output format is wrong — the routing question from
the self-Q&A ("Luna for T1, Astra for T2?") reopens. Not pre-decided.

### 2.5 Candidate-side automated cost/latency logging
The real version of old §1.1/§1.3: instrument harness runners. New engineering + tests. After
campaign 1 proves the manual columns are worth automating.

## Tier 3 — deferred (human time or judgment)

### 3.1 Per-task price proxies + value-weighted scores
Unchanged: freelance quotes or expert estimates with OmegaUse's consistency rule; report raw
AND weighted side by side. Owner: Sakura (quotes) + agent (wiring). After campaign 1.

### 3.2 Human labor-time baselines
Unchanged. Owner: Sakura (people/time).

### 3.3 Second cheap judge on a sample
Unchanged (~20% of items; judge–judge offset). Reprice after the Jev key lands.

## Explicitly NOT adopted (with reasons)

- **AssemblyAI's "no composite score"**: their audience routes workloads; ours makes one buy
  decision — with the §2.4 caveat above kept open rather than buried.
- **OmegaUse's pure-verifier grading**: T1/T2 need judgment; execution-only can't score them.
- **MLPerf's fixed-quality design**: fits training systems, not model selection.
- **OmegaUse's contamination posture**: they never discuss it. Ours (synthetic fixture +
  rotation) is arguably stronger, but rotation effectiveness is [OPEN] — unmeasured — so no
  superiority is claimed.

## Evidence labels

External claims [SECONDARY] throughout (researcher-read 2026-10-13; arXiv 2607.27155,
assemblyai.com/blog/voice-standard-bench, mlcommons.org/2026/09/mlperf-training-llm-post-training/).
The $25 cap is a standing chat decision (Sakura, 2026-10-03), not yet in GOAL.md/methodology.md —
writing it into the runbook is part of Tier 1. Iterations are hypotheses until campaign 1.
