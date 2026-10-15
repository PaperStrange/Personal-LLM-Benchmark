# LLM Workflow Benchmark — Validation Knowledge Base

**Purpose.** One managed record of every validation this benchmark pack has been put
through — what was tested, what the evidence showed, what survived, what died, and
what is still open. Written 2026-10-13. New validations append as dated entries;
nothing here is rewritten to make the past look better.

**Reading rule.** Every claim carries an evidence label: **[REAL]** genuinely
executed, **[SIM]** fabricated input through real plumbing, **[OPEN]** unvalidated.
A validation that fails is recorded with the same weight as one that passes —
failed validations are the knowledge base's most valuable entries.

**Maintenance.** Append-only. When a later validation overturns an earlier conclusion,
add a dated correction naming what it replaces; do not edit the original entry.

---

## Master timeline

| Date | Validation | Verdict |
|---|---|---|
| 2026-09-22 | V1 — Methodology dry run | Plumbing works; mock-Jev scores [SIM]; senior re-grade [REAL] |
| 2026-09-30 | V2 — Open loop, Qwen2.5-1.5B | Loop closes [REAL]; candidate fails 0/22; stand-in judge lenient |
| 2026-09-30 | V3 — Open loop, Llama-3.2-1B | 1B rung below stability floor; judge leniency worse (85.7 on 0/22) |
| 2026-10-05/09 | V4 — Gate 4a, Decider 2B int8 | Pipeline validated [REAL]; calibration 0% agreement; offset ~0.33 |
| 2026-10-13 | V5 — Cost-methodology gap analysis | Cost is guardrail, not metric — central gap; 14 iterations |
| 2026-10-13 | V6 — Gate 4b, Decider discriminative test | **FAIL** — Decider cannot discriminate; judge path killed |
| 2026-09-22 → 10-13 | V7 — Jev API key thread | Console works; key needs credit-card binding; parked as Todo |

## The design under test

**Goal (GOAL.md, refreshed 2026-09-30):** close all seven Stage −1 qualification
gates so the first ranked candidate comparison — T1 on GPT-6 Luna and Sol via
Codex, judged by a calibrated Jev — is a measurement, not theater. Then run the
comparison and deliver a ranked model list, gating each stage on the fuel gauge
(GPT credit, Codex reset status).

**Seven Stage −1 gates (docs/runbook.md):**
1. T1 strong/weak controls order correctly.
2. T2 genuine role separation.
3. T3 sandboxed install rehearsal.
4. One live Jev calibration call (before Gate 1 step 2).
5. Baseline protocols exercised.
6. Policy gates enforced by a run.
7. Plural independent review.

**Judge pipeline (the thing most validations test):** deterministic T0 gate (free)
→ cheap judge (Jev, designed) → senior review (expensive spot-checks). Calibration
ritual: track judge-vs-senior agreement per rubric item; recalibrate on disagreement.
Metrics: pass@k, pass^k, composite distribution, tie band. Hard campaign cap **$25**
(standing chat decision, Sakura 2026-10-03 — not yet written into GOAL.md /
methodology.md). Approved candidate shortlist (2026-10-03): `gpt-6-luna`,
`gpt-6.1-sol`, `gpt-6-astra` — do not silently replace.

**Fixture.** Synthetic private legacy billing codebase with a hidden debt inventory:
**14 items at dry-run (2026-09-22) → 22 items from the open loop onward
(2026-09-30).** The "14-item" figure in older summaries is stale; current T0 checks
against 22 anchors.

**"Senior" grades.** All banked senior grades are operator-as-senior re-grades
(non-independent). No independent human expert has graded to date — a standing
limitation on every calibration number in this document. **Sample size of the
anchor: n=1** — one simulated candidate, re-graded once, in one sitting. Every
calibration number downstream (V4's 0% agreement, V6's comparison column) rests
on those six numbers.

---

## V1 — Methodology dry run (2026-09-22)

**What ran.** T0 gate, mock-Jev judge, aggregate, scorecard — all local, synthetic
fixture, `/tmp` copies only. No real repos, no real services.

**Evidence.**
- T0 hard gate: [REAL]. Passed the simulated candidate.
- Judge scores (`results/dryrun/jev-run1/2/3.json`): **[SIM]** — canned mock values.
  Never quote these as Jev measurements.
- Senior re-grade (`results/calibration.csv`, 6 T1 rows): [REAL] operator re-grade
  of the simulated review. Deterministic recall on that candidate: **12/14 = 0.857**.
  Senior: arch 0.80, recall 0.85, precision 0.88, risks 0.85, plan 0.80, trust 0.75.
  These six numbers are the banked anchor for every later calibration comparison.
- T3 time rows in calibration.csv: [SIM] illustrative categorical pairs for kappa
  computation; no live T3 calibration run exists.

**Verdict.** Plumbing works. Nothing about any real judge or candidate was measured.
The senior re-grade became the calibration anchor — its non-independence is the
standing caveat on Gates 4a/4b.

## V2 — Open loop, Qwen2.5-1.5B (2026-09-30)

**What ran.** One genuine loop, zero spend: real local candidate call → T0 → real
local judge call → aggregate → scorecard. Candidate and judge both
`ollama/qwen2.5-1.5b-local` (Qwen2.5-1.5B-Instruct Q4_K_M, Apache-2.0, SHA-256
recorded). 3 counted repeats at temperature 0.7, plus 1 earlier failed attempt
(4 attempts total — see below).

**Evidence.**
- Candidate: deterministic debt recall **0/22 in all 3 repeats** [REAL]. Plausible
  prose, zero exact `file:line` anchors.
- Stand-in judge: composites 63.6 / 70.7 / 70.7 (mean 68.3), all above the 60
  "success" threshold [REAL]. Recall item scored 1/3, 2/3, 2/3 against identical
  0/22 ground truth, confidences 0.85–0.95, zero low-confidence flags.
- Senior read (non-independent): recall should be 0/3; risks/plan/trust 1/3 not 2/3;
  precision noul 0.95 vacuous (zero cited references = trivially "only real refs").
  The semantic-credit objection was considered and answered in the report: the T1
  contract demands exact references, and run 1 names no files at all.
- One earlier attempt at a 2500-token generation budget failed T0 (truncated
  before risk register/plan); budget raised to 4500 (per the open-loop report, a
  harness parameter, not a prompt change). **Loss disclosed:** the failed
  attempt's raw artifacts were overwritten by the rerun — only the outcome
  survives. The 3 counted runs are the post-budget-raise ones.

**Verdict.** The loop closes; the measurement does not. pass@k=1 / pass^3=1 here
measure the judge's leniency, not candidate capability. **First strong evidence
that this weak judge inflates composites past the success threshold** (one judge,
three repeats, one fixture — evidence for this judge, not proof in general).
Thresholds must be set per judge after calibration, not carried over from the
Jev design point.

**Open questions raised:** T0 vacuous pass (`t1_refs_valid` passed on zero
references under the v1 gate) — **CLOSED prospectively by gate v2 (2026-09-30)**,
which FAILS zero-ref candidates; earlier runs are NOT reclassified. Success
thresholds for uncalibrated judges — still open.

## V3 — Open loop, Llama-3.2-1B (2026-09-30)

**What ran.** Same T1 loop, second model (`ollama/llama3.2-1b-local`, Q4_K_M,
Llama 3.2 Community License [SECONDARY]). 3 attempts.

**Evidence.**
- Run 1: T0 PASS, judge complete, composite **85.7** — on deterministic recall 0/22,
  with the judge awarding t1_recall **3/3 at confidence 1.00** [REAL].
- Run 2: T0 FAIL (truncated candidate, no risk register / plan) — gate behaved.
- Run 3: T0 PASS, **judge failed** to emit a parseable score within the 3-attempt
  retry budget. **Harness gap:** raw emission not retained. Fixed afterward —
  driver now persists `judge-runN.error.log`.
- No reruns (failures stand as evidence; rerunning would be cherry-picking). No
  senior review (`senior_reviewed=no`).

**Verdict.** The 1B rung is below the stability floor for this loop (1 T0 fail, 1
judge fail). Worse: on n=1, the weaker model was a *more* lenient judge (85.7 >
68.3), not a stricter one. Sample too small for a measurement. The failures were
informative (T0 gate behaved; the judge failure exposed a harness gap) — but the
loop is not yet stable. Nothing about Llama as a candidate beyond "too small for
this T1 harness at this budget."

## V4 — Gate 4a, Decider 2B int8 (2026-10-05 / 2026-10-09)

**What ran.** Amazon's open-source Jev clone (Strands Decider 2B v21, Apache-2.0) as
the cheap-judge stand-in, run through the Gate 4 pipeline end to end against the
same simulated T1 candidate and banked senior grades as V1.

**Evidence.**
- **Blocked → solved [REAL].** Stock bf16 server OOM-killed (exit 137, 2026-10-05);
  no swap (`swapon` blocked); bitsandbytes incompatible with Qwen3.5 linear
  attention on CPU (8-bit silent no-op, 4-bit kernel crash `N must be divisible by
  block_n`). Solution: torch-native per-tensor int8, LoRA merged before
  quantization, vocab pruned 248,044 → **963 tokens** for the actual fixture,
  pointer head fp32, ~1.8GB steady-state. Builder:
  `~/workspace/gate4a/build_quantized.py`.
- **Pipeline validated [REAL].** Decider's `/v1/systemone` endpoint is Jev-shaped;
  `typesafe_sdk` client redirects via `base_url`; score answers require a `legend`
  field (discovered empirically). `run_gate4a.py` reuses `jev_judge.py`'s
  `build_questions`/`normalize` verbatim → `calibration-gate4a.csv` → `calibration.py`
  exits 0.
- **Calibration: 0% agreement** (|diff| ≤ 0.15) over 6 comparisons [REAL]:
  Decider 0.470–0.545 vs senior 0.75–0.88. Gaps: 0.330, 0.331, 0.335, 0.320,
  0.328, 0.245 — four of six within ±0.008 of ~0.33, five within ±0.010. A flat
  +0.33 correction would bring all six inside the band **in-sample** (n=6 — a
  hypothesis, not a result).
- Environment lessons (durable): `TMPDIR` under /home/hatch (`/tmp` is 512MB
  tmpfs); sanitize `NO_PROXY` (httpx crashes on bracketed IPv6 entries).

**Verdict.** Pipeline: VALIDATED. Model-as-judge: UNPROVEN. The stable-looking offset
was recorded as a hypothesis for out-of-sample testing (→ V6). Whether the gap
reflected the model, int8 quantization, or the synthetic fixture was [OPEN].

## V5 — Cost-methodology gap analysis (2026-10-13)

**What ran.** Not a model run — a framework validation. Our pack's goal and budget
treatment compared against three external benchmarks (researcher deep-reads,
[SECONDARY]): OmegaUse-OfficeVal (100 long-horizon office tasks, per-task price
proxies, value-weighted scores that *flip* the ranking), AssemblyAI Voice Standard
Bench (quality+speed+cost tables, reliability-gated picks, tie-break rules), MLPerf
Training v6.1 post-training (budget-as-benchmark, pass@4 lowest variance).

**Finding.** Our goal (code-workflow model+harness selection under startup budget)
is distinct among the three — but all three operationalize cost as a *metric*
while we use the $25 cap only as a *guardrail*. Central gap.

**Output.** 14 framework iterations in 3 tiers
(`docs/iterations/framework-iterations-2026-10-13.md`, rev.2). Tier 1 (docs + small code):
populate `cost_usd`/`wall_time_s` scorecard columns, reliability log, within-tie
ordering by cost, senior gate with bootstrap clause, `post_training` lineage field.
Tier 2: pass@4 (demoted — needs Sakura's budget sign-off, +33% judge spend),
negative-weight damage items, calibration-as-convergence-loop, input-scale
stratification, automated cost/latency logging. Tier 3 (human time): price proxies,
human labor baselines, second cheap judge.

**Review history.** Plural review caught 3+2 blockers in rev.1 (false
"token logs already exist" premise, circular senior gate, pass@4 labeled "free") —
all fixed in rev.2. **Honest scope:** comparison set chosen for cost methodology,
not code-workflow neighbors; external claims [SECONDARY].

## V6 — Gate 4b, Decider discriminative test (2026-10-13)

**What ran.** The out-of-candidate test V4's offset hypothesis needed: the same
int8 Decider graded the three REAL Qwen open-loop candidates (V2, all 0/22 anchors)
on all 6 T1 dimensions. Same fixture, same rubric, same pipeline — only the
candidates differ. No senior labor — ground truth was already banked.

**Evidence** (`results/gate4b-decider-discriminative.csv`, 18 rows, exit 0) [REAL]:

| item | run1 (0/22) | run2 (0/22) | run3 (0/22) | gate4a good cand |
|---|---|---|---|---|
| t1_arch | 0.527 | 0.487 | 0.502 | 0.470 |
| t1_recall | 0.526 | 0.571 | 0.528 | 0.519 |
| t1_precision | 0.469 | 0.479 | 0.436 | 0.545 |
| t1_risks | 0.507 | 0.500 | 0.453 | 0.530 |
| t1_plan | 0.514 | 0.488 | 0.507 | 0.472 |
| t1_trust | 0.556 | 0.528 | 0.557 | 0.505 |

**Analysis.**
- **Recall violates the rubric floor.** Bottom level: "Found almost none of the
  known debts" (floor 0.0). Decider gave 0.526–0.571 ≈ level 1.58/3 for zero
  anchors. Self-contained kill — no cross-candidate comparison needed.
- **Structural omissions invisible.** run2 (no risk register, no 30/60/90 plan)
  scored risks 0.500 vs 0.507 (run1), plan 0.488 vs 0.514.
- **No dynamic range.** All 24 scores across V4+V6: 0.436–0.571. The model emits
  ~0.5 ± 0.06 across these four candidates on one fixture. The V4 "+0.33 stable
  offset" was a compression artifact, not a calibration — stable because the model
  barely varies.
- **Truncation disclosure.** Engine caps state at 3072 tokens (right-truncation;
  inventory renders last). run1 ≈ 2559 tokens (clean), run2 ≈ 3001, run3 ≈ 3106
  — run2/run3 lost some inventory tail. Verdict stands: run1 is a clean run
  (different candidate and build from Gate 4a, not a replication of it) and
  0 anchors is a floor score at any visible inventory length.
- **Scope.** Discrimination failure *proven* on recall/risks/plan (ground truth
  exists); *suggestive* on arch/precision/trust. Hypothesis B "strongly supported"
  (n=3 × 1 fixture — solid for a gate kill, not general confirmation). Cause
  (model vs int8 vs rubric out-of-distribution) remains [OPEN] and not worth
  chasing without a new reason.

**Verdict. FAIL — Decider 2B v21 (int8, this box) disqualified as cheap judge.**
Do not revisit without new evidence (different precision, different model, or
retrained head). Full report: `hidden_files/gate4a/GATE4B-REPORT.md` (bookkeeping;
plural-reviewed, review record alongside).

## V7 — Jev API key thread (2026-09-22 → 2026-10-13)

| Date | Event |
|---|---|
| 2026-09-22 | Key outstanding before live candidate runs; live-Jev gate explicit. |
| 2026-10-05 | Gmail search: no TypeSafe/Jev key email. Zero-spend Gate 4a proposed. |
| 2026-10-09 | Watch run: still nothing. Gate 4a no longer depends on the key; Jev-vs-Decider comparison still does. |
| 2026-10-13 | Sakura logged into the Jev/TypeSafe console. Key usage requires **binding a credit card**. He does not want to spend on Jev testing yet. **Marked as Todo.** Daily key-watch cron disabled (premise obsolete — the key will not arrive on its own). |

---

## The judge problem (central thread)

Every *judge* validation since V1 has hit the same wall: the cheap judge. (V5
never tested the judge — it was a framework analysis, not a model run.)

| Judge candidate | Evidence | Status |
|---|---|---|
| Jev (TypeSafe API) | Designed choice; never executed — key needs credit-card binding | PARKED (Todo) |
| Mock Jev (V1) | Canned values [SIM] | Not a judge — plumbing only |
| Qwen2.5-1.5B same-model stand-in (V2) | Lenient: 68.3 composite on 0/22; recall 1–2/3 vs 0/22 | DISQUALIFIED (leniency proven) |
| Llama-3.2-1B same-model stand-in (V3) | Worse leniency: 85.7, recall 3/3 at conf 1.00 on 0/22; 1 judge parse failure | DISQUALIFIED |
| Decider 2B v21 int8 (V4/V6) | 0% calibration agreement; no discrimination; no dynamic range | DISQUALIFIED (V6) |
| Senior (operator re-grade) | Only judge that has ever tracked ground truth | Works, non-independent, expensive (human time) |

**Standing consequence.** The cheap-judge tier is empty. Stage −1 Gate 4 ("one live
Jev calibration call") cannot close zero-spend. Any future judge candidate must
pass the V6 discriminative test (grade 0/22 candidates + structurally broken
candidates; must hit rubric floors) before any claim is made about it.

## What survives (validated components)

- **T0 deterministic gate** [REAL]: failed genuinely truncated candidates (V2 2500-token
  attempt, V3 run2), passed structurally complete ones. Caveat: under the v1 gate,
  `t1_refs_valid` passed zero-reference reviews (vacuous pass) — closed
  prospectively by gate v2 (2026-09-30), which FAILS zero refs; v1 runs not
  reclassified.
- **Pipeline/plumbing** [REAL]: prompt → generation → T0 → judge → aggregate →
  scorecard, vintage stamping, pass@k/pass^k math (suite green). The independence
  guards exist in code and pass hermetic tests but have never been exercised by a
  real run — every real run so far was non-independent by design.
- **Deterministic recall check** [REAL]: agreed with the senior read on both
  occasions it was checked (V1 simulated candidate, V2 Qwen) and disagreed with
  every weak judge.
- **Failure accounting**: failed attempts stand as evidence (V3 no-rerun rule),
  with one disclosed exception — the V2 2500-token attempt's raw artifacts were
  overwritten; only its outcome survives.

## Proposals (not yet validated — NOT survivors)

- **Framework iterations (V5):** 14 proposals, Tier 1 unimplemented. They are
  hypotheses until a candidate campaign measures them (per the solution-validity
  law). Listed here so they are tracked, not banked.

## What is dead (killed paths + revival conditions)

| Path | Killed by | Revival requires |
|---|---|---|
| Same-model stand-in judge (Qwen) | V2 leniency | Nothing — non-independent by construction |
| Same-model stand-in judge (Llama) | V3 leniency + instability | Nothing — same reason |
| Decider 2B v21 int8 as judge | V6 no-discrimination | New evidence: different precision, model, or retrained head |
| Mock-Jev scores as measurements | V1 labeling | Nothing — [SIM] by definition |
| "+0.33 Decider offset" calibration | V6 compression artifact | Nothing — the offset was never a calibration |
| $25 cap as the only budget treatment | V5 gap analysis | Tier 1 iterations (cost-as-metric columns) |

## Current state + critical path (2026-10-13)

- **Stage −1: NO-GO.** Gate 4 (live Jev calibration) is the blocker; Gates 1–3, 5–6
  untested on live candidates. Gate 7 (plural review) is a process gate applied
  to every deliverable; it is never at risk of failing a run.
- **Critical path:** resolve the cheap judge → close Gate 4 → run T1 on Luna/Sol
  via Codex → ranked comparison. Note: the V7 Jev-vs-Decider comparison is moot —
  V6 killed the Decider, so there is nothing left to compare Jev against on that
  axis.
- **Judge options (Sakura's call):** (a) bind card for Jev (parked Todo);
  (b) senior-only grading on a minimal set (human time, no card);
  (c) another open judge model — must pass the V6 kill-test first.
- **Judge-agnostic work that can proceed now:** V5 Tier 1 iterations (cost columns,
  reliability log, tie ordering, senior-gate bootstrap, lineage field).
- **Standing constraints:** zero-spend until Sakura authorizes spend; no test no
  fact no result; every deliverable plural-reviewed with written records; the
  deliverable isn't delivered until it's on the remote.

## Decision log (Sakura's calls that shaped this work)

- 2026-09-30: "Why not search for open-source LLM to achieve your task and close
  one true calling loop?" → open-loop path (V2/V3), zero-spend judge exploration.
- 2026-10-03: candidate shortlist locked (Luna, Sol, Astra); $25 cap set.
- 2026-10-13: "validate the goal of our benchmark against existed one to iterate
  the whole framework" → V5 gap analysis + iterations.
- 2026-10-13: Jev key deferred — "don't want to throw out the cash for testing
  Jev yet, mark it as Todo."
- 2026-10-13: "go on" → V6 discriminative test executed.
- 2026-10-13: "Document the failed validation in details, as well as the past
  one for managing a whole, substantial knowledge base" → this document.

## Evidence ledger (where every claim lives)

| Claim | File |
|---|---|
| V1 dry run | `results/dryrun/METHODOLOGY-REPORT.md`, `results/calibration.csv` |
| V2 open loop Qwen | `results/open-loop/OPEN-LOOP-REPORT.md`, `results/open-loop/*` |
| V3 open loop Llama | `results/open-loop/OPEN-LOOP-REPORT.md` (second loop), `results/open-loop-llama32-1b/` |
| V4 Gate 4a | `~/workspace/goals/llm-workflow-benchmark-pack/hidden_files/gate4a/GATE4A-REPORT.md` (goal root, not pack root), `results/calibration-gate4a.csv`, `~/workspace/gate4a/build_quantized.py` |
| V5 gap analysis | `docs/iterations/framework-iterations-2026-10-13.md`, `docs/iterations/benchmark-validation-selfqa-2026-10-13.md`, `docs/reviews/review-framework-iterations-2026-10-13.md` |
| V6 Gate 4b | `~/workspace/goals/llm-workflow-benchmark-pack/hidden_files/gate4a/GATE4B-REPORT.md` + `GATE4B-REVIEW.md` (goal root, not pack root), `results/gate4b-decider-discriminative.csv`, `~/workspace/gate4a/run_gate4b_discriminative.py` |
| V7 Jev thread | Goal timeline (2026-10-13 entry), this document |
| Gates + runbook | `docs/runbook.md`, `docs/methodology.md` |
