# Methodology (full)

> Compressed summary in the [README](../README.md). Research survey: [landscape.md](landscape.md). Runbook: [runbook.md](runbook.md).

## Methodology

**Tier order: T0 → Jev → senior.** `src/llm_workflow_eval/judge/t0_checks.py` is the free,
deterministic hard gate: section presence, `file:line` refs within file
bounds, PLAN.md/REVIEW.md existence, real test evidence in the review, and
the implementation actually done. If T0 fails, **no Jev spend happens** — fix
the run and re-check. A T0 pass buys one Jev call (`src/llm_workflow_eval/judge/jev_judge.py`),
which grades the whole rubric in a single parallel call. The expensive senior
judge (`src/llm_workflow_eval/judge/senior_judge_prompt.md`) only sees sampled runs plus every item
Jev flagged below the low-confidence threshold (default 0.55 — override with
`jev_judge.py --low-conf-threshold`).

**Baselines.** See `tasks/BASELINES.md`: run each task once with a raw model
and no harness. The baseline-vs-harness delta is the harness's measured
contribution — which is the whole point of separating criterion 1 (model)
from criteria 2–3 (harness).

**Repeats.** Minimum 3 runs per (task, candidate). `src/llm_workflow_eval/judge/jev_judge.py
--json-out` writes one machine-readable result per repeat;
`src/llm_workflow_eval/judge/aggregate.py` rolls k repeats into **pass@k** (≥1 of k runs succeeded)
and **pass^k** (all k runs succeeded) at a composite threshold (default 60).
Report both: pass@k is capability ("can it do this at all?"), pass^k is
reliability ("can you trust it consistently?"). Single runs mean nothing on
non-deterministic systems.

**Calibration ritual.** Log every senior spot-check to
`results/calibration.csv` (Jev normalized score vs senior normalized score,
per item). Run `src/llm_workflow_eval/judge/calibration.py` quarterly — items with < 70% agreement
(|diff| ≤ 0.15 counts as agree) get recalibrated: reword the rubric item or
distrust the judge on it. Refresh tasks as models saturate them; a benchmark
everyone aces measures nothing.

**Stage 0 is a filter, not a ranking.** Public leaderboards pre-screen
candidates; never compare cross-harness numbers naively — a score is always a
(harness, model, config) tuple.

**Eval the evals.** The pack has its own regression suite: run
`python3 tests/run_all.py` from the pack root and it validates the evaluator
itself — T0 gate pass/fail paths, rubric schemas, debt-anchor hygiene (all 22
anchors must point at real fixture lines), the Jev pipeline against a canned
mock, pass@k aggregation, and the calibration math — then writes a single
overview report to `results/pack-test-overview.md`. Stdlib `unittest` only,
no real API spend. If the suite is red, the methodology is broken: fix the
evaluator before grading any candidate.

### Why this design (threats to validity)

Each choice below is a defense against a documented failure mode in the
benchmark literature. Full survey with citations:
`docs/landscape.md`.

- **Synthetic, private fixture.** Public code benchmarks rot: OpenAI
  withdrew from SWE-bench Verified, citing contamination and
  shortcut-rewarding tests,
  and models locate bugs from memorized text at 76% vs 53% off-benchmark
  ("The SWE-Bench Illusion"). Our fixture has no public repo and no training
  footprint — contamination resistance by construction.
- **Fixture rotation & vintage.** Identifier rotation is implemented
  ([REAL]): `python tasks/t1-legacy-review/rotate_fixture.py --seed 7`
  deterministically renames ~50 function/config/local identifiers via
  AST-based renaming (strings, SQL, comments untouched), emitting a variant
  pair — renamed code tree plus remapped `DEBT-INVENTORY.md` — with every
  `file:line` anchor preserved and every `Expect:` line re-verified against
  the renamed code. Inventory prose remapping is deliberately conservative:
  only bare identifiers inside backtick code spans are remapped, and only
  when the new name provably occurs in the variant code — English words and
  API references (e.g. `datetime.datetime.now()`) are never rewritten, after
  review caught a word-boundary regex emitting false statements into the
  judge's answer key. The T2 contract surface (`apply_discount(invoice_id,
  pct)`) is frozen so the task spec stays valid. Variants land in
  `fixture/variants/` (gitignored, never committed) stamped `v2-seed<seed>`;
  the canonical fixture is vintage `v1-2026-09`. **When to rotate:** fresh
  seed per candidate campaign; never compare scores across vintages.
  `jev_judge.py --fixture-vintage` stamps every `--json-out` (auto-detected
  from the VINTAGE file next to `--inventory` when the flag is omitted —
  there is no silent canonical default), and
  `src/llm_workflow_eval/judge/aggregate.py` prints the vintage and refuses mixed-vintage inputs
  (exit 2) — the same discipline as the independent-rollout guard. The
  `scorecard.csv` schema reserves a `fixture_vintage` column (no writer
  appends rows yet — aggregate reports are the stamped record today).
  **Effectiveness [OPEN]:** we have not measured a memorized model scoring
  lower on a variant; rotation is a precaution, not a proven defense.
- **Hidden answer key.** SWE-bench+ showed 32.67% of "successful" patches won
  via solution leakage (the fix visible in the issue text). The candidate
  sees code; only the judge sees `DEBT-INVENTORY.md`. `src/llm_workflow_eval/judge/leakage_audit.py`
  verifies no inventory title appears verbatim in the fixture (v1:
  verbatim-only; paraphrase stays the reviewer's job).
- **Judge tiering T0 → Jev → senior.** Cheap-first escalation in the spirit
  of "Trust or Escalate" — though our 0.55 cutoff is an uncalibrated
  heuristic, not the paper's provable guarantee. **Migration path** (explicit
  future work, blocked on live calibration data): replace the fixed cutoff
  with a target-agreement-level rule — "escalate until senior-agreement ≥
  0.80". Concretely: from `results/calibration.csv` rows, find the Jev
  confidence level at which Jev-vs-senior agreement (numeric |diff| ≤ 0.15
  rate, or Cohen's κ on choice items) reaches 0.80, and set
  `--low-conf-threshold` to that level. The rule is auditable
  ("0.80 agreement" is a property of measured data); "conf < 0.55" is not.
  LLM confidence is systematically overconfident, so the calibration ritual
  exists — never trust Jev's raw confidence numbers.
- **pass@k *and* pass^k.** τ-bench's framing: pass@k is capability, pass^k
  is reliability. `aggregate.py` enforces that k counts independent
  rollouts, never tests-within-a-run (the most common silent inflation bug
  in the literature).
- **Don't over-interpret small composite gaps.** Autorubric diagnostics:
  ~55% of judge variance is unexplained by rubric criteria. Report T0,
  pass@k/pass^k, and calibration next to every composite; treat close scores
  as ties until repeats say otherwise.
- **Tie band.** `aggregate.py` reports the composite's mean/std/min/max
  across repeats (population std, so a single run shows std 0.0). When
  comparing two candidates, a |Δcomposite| smaller than the max observed
  run-spread (max−min composite across the repeat runs) is reported as a
  **tie**, not a ranking — the difference sits inside the measurement
  noise. More repeats stabilize the spread estimate (the max−min band is
  conservative by construction — it can only widen or hold as samples are
  added, never narrow); only gaps outside it are claimed as
  real differences between candidates.
- **Harness disclosure is required.** Swapping only the harness moves
  Pass@1 by up to 27.4pp (Claw-SWE-Bench) — nearly the full model-to-model
  spread. Every `scorecard.csv` row must name its harness (the `harness`
  column); treat scores without a named harness as unattributable and do not
  compare them against harnessed runs.

## Budget math (why this is cheap)

- Candidate run, GPT-6 Luna ($0.10 in / $0.50 out per MTok): a T1 review of
  ~100k input + 20k output tokens ≈ **$0.02**.
- Jev judge call: ~50k chars of state ≈ 12.5k tokens ≈ **$0.0005**.
- Full pack × 3 repeats × 5 candidates ≈ **$1–2 total**, most of it the
  candidate runs. Screening on Luna instead of a flagship is a ~20–100× saving.

## Running the tasks

**T1.** Hand `tasks/T1-global-review.md` verbatim to the candidate with
read-only access to `fixture/legacy-billing/`. Save its Markdown output, then
run the T0 gate **before** any Jev spend:

```bash
python src/llm_workflow_eval/judge/t0_checks.py --task T1 --candidate results/t1-candidate-a.md \
    --inventory fixture/DEBT-INVENTORY.md --workdir fixture/legacy-billing
# exit 0 required; fix the run and re-check if it fails
export TYPESAFE_API_KEY=...
pip install typesafe-sdk
python src/llm_workflow_eval/judge/jev_judge.py --rubric rubrics/rubric-T1.json \
    --candidate results/t1-candidate-a.md \
    --inventory fixture/DEBT-INVENTORY.md \
    --json-out results/t1-candidate-a-r1.json
```

`--inventory` adds a deterministic debt-recall check (D1–D22 anchors) next to
Jev's judged scores, and `--json-out` feeds `src/llm_workflow_eval/judge/aggregate.py` for pass@k /
pass^k over repeats. **Never show `fixture/DEBT-INVENTORY.md` to a candidate.**

**T2.** Run `tasks/T2-multi-agent.md` in the harness with its native
subagents, in a **copy** of the fixture (never the original). Seed that copy
with 2 subtle reviewer-catchable bugs first:

```bash
python tasks/t2-discount-fix/plant_bugs.py --src fixture/legacy-billing \
    --dest /tmp/t2-run-copy --seed 7
# writes the judges-only manifest to tasks/t2-discount-fix/plant_manifest.json
# (gitignored) — never show it to the candidate
```

Concatenate `PLAN.md` + diff + test output + `REVIEW.md` + role notes into
one file, then:

```bash
python src/llm_workflow_eval/judge/t0_checks.py --task T2 --candidate results/t2-a.md \
    --workdir /tmp/t2-run-copy
# then judge with rubrics/rubric-T2.json (no inventory), --json-out per repeat
```

`rubrics/rubric-T2.json` grades coordination quality explicitly:
`t2_coord_1`/`t2_coord_2` (did the reviewer catch the 2 planted bugs?) and
`t2_plan_match` (did the implementation follow `PLAN.md`?). Optionally log
the run's action trace in the JSONL format of
`tasks/t2-discount-fix/TRACE-FORMAT.md` and run
`src/llm_workflow_eval/judge/trace_check.py` on it — it flags looping / thrashing as a discipline
signal (uncalibrated thresholds; flags mean "send to senior review").

**T3.** Follow `tasks/T3-expandability.md`, write the install report, then
`python src/llm_workflow_eval/judge/t0_checks.py --task T3 --candidate results/t3-report.md` before
judging with `rubrics/rubric-T3.json`. The T3 rubric is claim-level
(MCP-Atlas template): `t3_discovered` / `t3_installed` / `t3_configured` /
`t3_functional` / `t3_recovered` plus the `t3_time` choice item, so valid
alternative trajectories get full credit. A second set of extension tasks is
held out of this repo for contamination resistance ([OPEN] — documented in
the rubric, no holdout task run yet).

**Baselines.** Before harnessed runs, do one raw-model-no-harness baseline
per task — see `tasks/BASELINES.md`. Label it `harness=none` in the scorecard.

**Senior review.** Any rubric item with Jev confidence below the
low-confidence threshold (default 0.55, override with `jev_judge.py
--low-conf-threshold`) is flagged.
Re-grade those — and spot-check T1 overall — with `src/llm_workflow_eval/judge/senior_judge_prompt.md`
in a frontier model. Log each (jev_norm, senior_norm) pair to
`results/calibration.csv` — and for choice-kind items also log the selected
options as (jev_choice, senior_choice), which `src/llm_workflow_eval/judge/calibration.py` turns
into Cohen's κ — and append one row per (harness, model, task)
aggregate to `results/scorecard.csv`.

**promptfoo (optional).** Copy `examples/promptfoo.example.yaml` to
`promptfoo.yaml`, fill in providers, run `promptfoo eval --repeat 3`. The
example matrix covers Codex SDK (GPT-6 Luna/Sol), Claude Agent SDK, and
OpenCode SDK, with cost ($2) and latency (10 min) gates. For one-off grading,
`jev_judge.py` is cheaper and simpler.

## Swapping in your own repo

1. Snapshot your repo into `fixture/` (or point the task prompts at it).
2. Write your own `DEBT-INVENTORY.md`: 10–15 known issues as
   `### Dn \`file:line\`` entries (the judge regex-matches these).
3. Reuse the rubrics unchanged — only T1's recall item needs the inventory.

## File map

```
README.md                    this file
tasks/                       verbatim prompts to hand candidates
  T1-global-review.md        legacy onboarding + review prompt
  T2-multi-agent.md          3-role subagent feature build
  T3-expandability.md        third-party plugin/skill/MCP install test
  BASELINES.md               raw-model-no-harness baseline protocols
  t2-discount-fix/
    plant_bugs.py            plants 2 seeded subtle bugs into a fixture COPY
                             (judges-only manifest; never show candidates)
    TRACE-FORMAT.md          JSONL action-trace format for T2 runs
fixture/
  legacy-billing/            the fixture codebase (BillingSvc)
    billing.py               god module (~110 lines) + apply_discount stub
    db.py                    string-concatenated SQL, unclosed connections
    config.py                hardcoded secrets, DEBUG=True
    reports.py               drifted duplicate tax logic, unescaped CSV
    requirements.txt         ancient pins
    tests/test_billing.py    stale, broken test suite
    README.md                fixture guide + swap instructions
  DEBT-INVENTORY.md          HIDDEN answer key (D1-D22) - judges only
rubrics/                     Jev-ready rubric JSON (score/choice/noul items)
src/llm_workflow_eval/judge/
  t0_checks.py               T0 deterministic hard gate (free, runs first)
  jev_judge.py               CLI: one Jev call grades a whole rubric (--json-out)
  aggregate.py               pass@k / pass^k over repeated --json-out runs
  leakage_audit.py           hidden-key leakage check (inventory vs fixture)
  calibration.py             Jev-vs-senior agreement report (quarterly ritual)
  trace_check.py             looping/thrashing flags on T2 action traces
  senior_judge_prompt.md     frontier-model spot-check template
src/llm_workflow_eval/harness/
  promptfoo.example.yaml     EXAMPLE multi-harness matrix (copy to use)
docs/
  methodology.md             this file (full methodology)
  runbook.md                 Stage -1 runbook
  landscape.md               surveyed benchmark literature + implications
  iteration-log.md           dated iteration log
results/
  scorecard.csv              one row per (harness, model, task) aggregate
  calibration.csv            senior spot-check log for the calibration ritual
  pack-test-overview.md      single overview report from tests/run_all.py
tests/                       the pack's OWN regression suite ("eval the evals")
  run_all.py                 single entry point: runs the suite, writes the overview
  test_t0_gate.py            T0 gate pass/fail paths incl. plan-before-code
  test_rubrics.py            rubric JSON schemas and required fields
  test_anchors.py            debt-anchor hygiene (F1 regression)
  test_judge_pipeline.py     jev_judge.py vs canned mock typesafe_sdk
  test_aggregate.py          pass@k / pass^k math + independence guard + composite std
  test_leakage_audit.py      hidden-key leakage audit (clean/planted/missing)
  test_calibration.py        calibration agreement + RECALIBRATE flag
  test_plant_bugs.py         bug planter: 2 seeded bugs, manifest, fixture untouched
  test_trace_check.py        trace checker: looping/thrashing flags, entropy
  helpers/mock_typesafe/     self-contained canned typesafe_sdk mock
```

## Requirements

- Python 3.10+, `pip install typesafe-sdk`, `TYPESAFE_API_KEY` set
  (get a key at console.typesafe.ai — access starts at $5 in credits).
- promptfoo only if you want the Stage 3 matrix: `npm install -g promptfoo`.
- The fixture is stdlib-only Python; no install needed to read or run it.
