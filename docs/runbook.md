# Stage −1 Qualification Runbook

**Status: NOT STARTED (2026-09-30).** This runbook turns the seven
qualification gates in `results/dryrun/METHODOLOGY-REPORT.md` (§Go / no-go)
into exact procedures. No gate may be marked pass on a claim — each needs
the artifact named below. **No ranked candidate comparison or subscription
spend until all seven pass.** The live-Jev calls inside Gates 1 and 4 are
the exception: they proceed only after the fuel gauge reads sufficient AND
Sakura's handover items are complete (fuel gauge first, every time).

## Fuel gauge (before ANY costly step)

| Source | Check | 2026-09-30 reading |
|---|---|---|
| GPT credit | `platform.openai.com` billing — credit balance covers the planned calls | **UNKNOWN** [OPEN] — key presence indicated in env but not usable from this machine (read attempt returned empty key); Sakura must verify or re-issue via Secure Vault |
| Codex reset | `codex --version` runs; CLI authenticated; usage/reset visible | [REAL] CLI v0.149.0 installed, NOT logged in (`~/.codex` absent) — reset status UNKNOWN [OPEN] until Sakura signs in |
| TypeSafe/Jev | `TYPESAFE_API_KEY` validates against the real `system_one` endpoint | **UNKNOWN** [OPEN] — key presence indicated, validity unconfirmed; no live call made (gated by this runbook) |

If any gauge reads UNKNOWN or insufficient: stop. Do not start gate work
that needs it.

## Gate 1 — T1 strong/weak controls order correctly

- **Strong control:** reference review authored directly from
  `fixture/DEBT-INVENTORY.md` — cites all 22 anchors with file:line.
  (Author it fresh; do not reuse the dry-run synthetic candidate.)
- **Weak control:** review citing ~12 anchors (the dry-run synthetic
  candidate — deterministic recall 12/22 against the current inventory,
  12/14 at dry-run time — may serve if its text is on file).
- Grade each control three ways:
  1. Deterministic: `PYTHONPATH=tests/helpers/mock_typesafe MOCK_RUN=1 TYPESAFE_API_KEY=dryrun python3 src/llm_workflow_eval/judge/jev_judge.py --rubric rubrics/rubric-T1.json --candidate <control>.md --inventory fixture/DEBT-INVENTORY.md --json-out <payload>.json` — mock SDK, zero cost and zero network; read only the `deterministic debt recall:` line and ignore the canned Jev scores. (Instrument validation, not discrimination: the strong control is authored from the inventory, so 22/22 is guaranteed by construction — this step validates `parse_inventory` and the anchor format. The discrimination burden sits on live Jev + senior.)
  2. Live Jev: same command with `TYPESAFE_API_KEY` set and the real `typesafe_sdk` importable (mock `tests/helpers/mock_typesafe` NOT on `PYTHONPATH`; `MOCK_RUN` is irrelevant to SDK selection), `--json-out`. **Run only after Gate 4 passes** — the live-call path must be verified before any graded spend.
  3. Senior judge: human read by a designee who did not author the controls (not Sakura — the operator is not independent of the project), blind to which control is which. The senior judge grades against the inventory as ground truth (per `src/llm_workflow_eval/judge/senior_judge_prompt.md`) — independent of Jev and of control authorship, not blind to the answer key.
- Note: since gate v2 (2026-09-30), `t1_refs_valid` in `src/llm_workflow_eval/judge/t0_checks.py` FAILS with zero `file:line` refs — the T1 task text requires an exact file:line reference per debt issue, so zero refs means the task contract was not followed. Earlier runs (qwen/llama open loops) were graded under the v1 gate and are NOT reclassified. Grade controls by exact-anchor recall (step 1), live Jev (step 2), and senior (step 3); never pass a control through T0 alone.
- **Pass:** strong > weak on all three gradings; Jev confidences across items: sample stdev > 0.05 AND max−min > 0.10 (predeclared — a flat line means the judge is not discriminating); deterministic recall ≈ 22/22 vs ≈ 12/22.
- **Artifacts:** both control texts, both `--json-out` payloads, senior
  verdict note, all committed under `results/qualification/`.

## Gate 2 — T2 genuine role separation

- Run `tasks/t2-discount-fix/` with **two genuinely separate agents**:
  planner (writes plan, never touches code) and reviewer (reviews diff
  against the plan only — never the planted-bug manifest, which is JUDGES
  ONLY per `plant_bugs.py:29-30` and goes exclusively to the grader scoring
  `t2_coord_1/2`; the reviewer never saw the plan written).
  Separate contexts; handoff only through the plan file + diff.
- Plant bugs via `tasks/t2-discount-fix/plant_bugs.py` into a disposable
  copy (never the canonical tree). Predeclare the plant seed(s) before the
  runs: `plant_bugs.py` selects via `random.Random(seed).sample(CATALOG, 2)` —
  same seed across the 3 runs tests agent variance, different seeds test
  robustness; unspecified means post-hoc adjustable.
- **Pass:** 3 repeat runs all green; reviewer catches both planted bugs
  each run (rubric items); trace logs saved per run; a role-separation
  note records exactly what each role could and could not see.
- **Artifacts:** per-run traces, `src/llm_workflow_eval/judge/trace_check.py` summaries, hidden
  test results (hidden tests are authored fresh at qualification time and
  never shown to candidate agents — no hidden-test suite exists in-repo yet),
  all under `results/qualification/t2/`.

## Gate 3 — T3 sandboxed install rehearsal

- Create the allowlist first (it does not exist yet): ONE pinned extension
  version (record name + version + source URL + hash); get it approved
  before Gate 3 runs. Then install/configure that version inside a
  **temporary HOME** (or container): 
  `HOME=$(mktemp -d)` so no real config is touched.
- Take before/after manifests (`find $HOME -type f | sort` diff).
- **Pass:** all six claim items (`t3_discovered` … `t3_recovered`) evidenced;
  after-manifest minus before-manifest is exactly the extension's files;
  cleanup (`rm -rf` temp HOME) leaves zero residue — the temp dir is gone
  (`test ! -e $TMPHOME`), or a fresh `mktemp -d` manifests empty.
- **Artifacts:** manifests, diff, cleanup proof, under
  `results/qualification/t3/`.

## Gate 4 — one live Jev calibration call (**run before Gate 1 step 2**)

- With the real `typesafe_sdk` importable and `TYPESAFE_API_KEY` set,
  run `TYPESAFE_API_KEY=<key> python3 src/llm_workflow_eval/judge/jev_judge.py --rubric rubrics/rubric-T1.json --candidate <strong-control>.md --inventory fixture/DEBT-INVENTORY.md --json-out <payload>.json` (real `typesafe_sdk` importable, mock `tests/helpers/mock_typesafe` not on `PYTHONPATH`; `MOCK_RUN` is irrelevant to SDK selection) on **both controls** from Gate 1 (strong + weak): response shape and confidence behavior on the strong control, discrimination as strong > weak on the same items — a single strong-control call verifies shape but cannot demonstrate discrimination.
- **Pass:** the `system_one` call completes without an error envelope; `--json-out` parses with scores + confidences per item (not an error envelope);
  confidence values across items: sample stdev > 0.05 AND max−min > 0.10 (predeclared — a flat line means the judge is not discriminating — investigate, do not proceed).
- Record cost (`est_cost_usd` in `--json-out`; input/output token counts come
  from the raw SDK response or provider dashboard — `jev_judge.py` does not
  print them); append to `results/qualification/scorecard.csv` (create it;
  `cost_usd` column as in `results/scorecard.csv`). Scorecard rows in this repo
  are hand-written — label the row as such per the honesty convention, or
  generate it.
- **Artifact:** the payload + a one-paragraph shape/behavior note under
  `results/qualification/`.

## Gate 5 — baseline protocols exercised

- Run each documented baseline protocol end to end (the T1/T2/T3 baseline
  procedures in `tasks/BASELINES.md`).
- **Pass:** every protocol produces its specified output artifact. A protocol
  that cannot be run as written is amended, not silently rewritten: record
  what changed and why, re-review the amendment, and record which protocol
  version passed. Never report an amended protocol as "the documented
  protocol passed" — a protocol that exists only on paper does not count.

## Gate 6 — policy gates enforced by a run

For one full Gate 1–3 pass, demonstrate each: **validity** (controls in
Gate 1), **isolation** (disposable copies, temp HOME — Gate 2/3), **repeatability**
(3× runs, Gate 2), **agreement** (Jev vs senior on the calibration rows, κ
reported via `src/llm_workflow_eval/judge/calibration.py:cohens_kappa`; predeclare a minimum pair
count first — six items from one calibration call is a noisy point estimate,
report per L2 not as a point estimate), **cleanup** (manifests, Gate 3), **maximum-cost** (per-run USD logged in
scorecard; the standing campaign cap is **$25** — declared before every run,
written into the run-log, honored on hit; cap aborts are [INFRA], never model
failures — see "Campaign reporting rules").

## Gate 7 — plural independent review

- The qualification report (gates 1–6 evidence, one document) goes through
  **two independent reviewers** (adversarial + mistake-hunt), fixes applied,
  re-verified — the same law as the build phases.
- Only then does `METHODOLOGY-REPORT.md` §Go / no-go get re-dated and
  re-signed. Not before.

## Campaign reporting rules (Sprint 1)

Zero-spend, judge-agnostic governance. These rules apply from the first
candidate campaign onward.

### Reliability log (`results/run-log.jsonl`)

Every attempt — successful or not — gets one JSON line, appended at run time:

```json
{"date": "2026-10-14", "task": "T1", "candidate": "gpt-6-luna",
 "harness": "none", "status": "fail", "failure_kind": "t0_gate"}
```

- `status`: `ok` or `fail` only. `fail` means the attempt produced no usable
  graded output (T0 fail, judge parse failure, harness crash, cap abort).
- `failure_kind`: free-text cause — `t0_gate`, `judge_parse`,
  `harness_crash`, `cap_abort`, `operator_abort`. New kinds are added as they
  occur; do not invent kinds prospectively.
- `note` (optional): free-text annotation — e.g. the template marker on the
  example line. Never required; parsers must tolerate its absence.
- Append-only: never edit or delete a line. An invalid run is a `fail` line,
  not a deletion.
- Reporting: failure rate per (candidate × task) is printed next to pass@k
  in every campaign report. **`cap_abort` lines are excluded from the
  failure-rate computation** — a cap abort is [INFRA], logged so the
  campaign's spend story is complete, but it says nothing about the
  candidate and must never push one over the 10% bar.
- **Rule:** >10% unusable output → the candidate is **not recommended**,
  regardless of its score. (10% is a proposed heuristic — AssemblyAI excluded
  unreliable models but published no threshold.) Reliability is a gate, not a
  footnote.

### Wall-clock discipline

Candidate latency is measured by the operator at run time — a stopwatch,
not an estimate:

- Start the clock when the candidate run starts; stop when its output file is
  written. One number per attempt, seconds.
- Populate the scorecard's `wall_time_s` column with the **median** per
  (candidate × task) — latency distributions are skewed, the mean lies.
- Record attempts that failed too: they count for the reliability log even
  when they contribute no score.
- Judge-side latency is not tracked here — the judge's `est_cost_usd` is a
  cost estimate, not a latency measure; do not conflate the two.

### Within-tie ordering + quality-per-dollar

The tie rule is already in methodology.md: |Δcomposite| < max observed
run-spread (max−min across repeats) = **tie**, not a ranking.

- Candidates inside the tie band are ordered by measured `cost_usd` (then
  `wall_time_s`). A candidate outside the quality band can never win on
  price — cost is an ordering tiebreaker, not a substitute for capability.
- **Quality-per-dollar decision rule:** the ratio governs ONLY when
  (a) the budget binds — the raw-quality winner cannot be graded within the
  $25 cap, so the choice is among affordable candidates, ranked by
  quality-per-dollar — or (b) raw scores tie inside the band. Otherwise
  the raw quality ranking stands. Note what (a) is NOT: it is not a ratio
  against an unmeasured score — if A was never graded, its composite is
  [OPEN], not an input to the ratio.
- Both rankings are shown side by side in every report: raw (quality) and
  value-aware (quality-per-dollar). The rule above picks which one decides.

Worked example. A: composite 90, $0.50/task. B: composite 85, $0.05/task.
Run-spread is 1.2, so 90 vs 85 is NOT a tie.

- Budget non-binding (the $25 cap covers both at planned repeats): **raw
  ranking decides — A first.** The report shows B's 10× cost advantage
  alongside, and the operator notes that a binding budget would flip it.
- Budget binding (grading A's repeats × $0.50/task would blow the $25 cap):
  A drops out of the affordable set — its 90 is [OPEN] at this budget, not a
  measured fact to ratio against. Among affordable candidates,
  quality-per-dollar governs: **B is the recommendation**, with the binding
  constraint named explicitly ("A ungradable at this budget").
- If A scored 89.5 and B 90 with spread 1.2, they tie in-band: **B first**,
  ordered by cost_usd ($0.05 < $0.50).

### $25 campaign cap (guardrail)

Standing decision (Sakura, 2026-10-03): the campaign stops when cumulative
spend across candidate runs + judge calls + senior grading reaches **$25**.

- Track spend as the campaign runs (provider dashboards/billing after each
  batch — manual, honest). Reaffirm Gate 6's $25 maximum-cost line before
  each run (the line is standing, not per-run mutable).
- On cap hit: **stop immediately.** The abort is logged in run-log.jsonl with
  `failure_kind: cap_abort` and status `fail` for the unstarted attempts.
  A cap abort is [INFRA] — the run plan was too expensive; it is never a
  model failure and never counted against a candidate's score.
- Report the partial results with the cap hit named: which runs completed,
  which were aborted, and what the completed portion cost. Never silently
  drop the aborted half of a campaign.

### Senior gate (bootstrap clause)

The naive gate — "no senior grades until cheap-tier agreement meets the
bar" — deadlocks: agreement is *measured by* senior grades.

- **Bootstrap:** the first 6 senior spot-checks (one per T1 item, or the
  equivalent for T2/T3) are exempt from the gate. They establish the
  agreement baseline (`results/calibration.csv`).
- **Gate applies thereafter:** no *further* senior spend until cheap-tier
  agreement meets the calibration bar (|diff| ≤ 0.15 rate, per
  `src/llm_workflow_eval/judge/calibration.py` — noting that 0.15 is itself a
  v1 heuristic from `calibration.py`'s `AGREE_TOLERANCE`, derived from an n=6
  in-sample analysis, not a principled threshold). If agreement holds, senior
  spend stays at the spot-check sampling rate; if it drops, senior grading
  pauses with the cheap tier until the rubric/judge wording is fixed and
  re-run (the convergence loop, B-3).
- Senior grading is the expensive tier by design — this gate exists to keep
  it that way.

## Handover checklist (Sakura)

- [ ] Jev API key (Secure Vault link — never paste in chat)
- [ ] Candidate shortlist confirmed (pilot plan: `examples/promptfoo.example.yaml` — T1 on GPT-6 Luna + Sol via Codex first)
- [ ] Codex CLI signed in on this machine (or wherever the runs will execute)
- [ ] GPT credit verified sufficient at platform.openai.com
- [ ] Max-cost abort threshold declared — **$25** (standing campaign cap, Sakura 2026-10-03; Gate 6 honors it before any run)
