# Review record: framework-iterations-2026-10-13.md + benchmark-validation-selfqa-2026-10-13.md

Date: 2026-10-13. Reviewers: adversarial (boss/partner lens) + mistake-hunt/executability
(independent subagents, parallel). All findings below were applied in rev.2 unless marked
otherwise.

## Adversarial findings — applied

- **[BLOCKER] B1 (§1.7 pass@4 "free")**: +33% on the costliest line item, contradicts the
  minimum-3-runs rule. → DEMOTED from Tier 1 to Tier 2.1; now requires Sakura's budget
  sign-off, with the MLPerf variance finding cited as supporting (not dispositive) evidence.
- **[BLOCKER] B2 (§1.1 token logging "already exists")**: false — `--json-out` captures only
  a judge-side chars/4 cost estimate; no candidate token capture exists anywhere. →
  Rewrote §1.1 as "populate, don't pretend": add `--model` to json-out, populate existing
  `cost_usd`/`wall_time_s` scorecard columns manually, candidate-side automation moved to
  Tier 2.5.
- **[BLOCKER] B3 (§1.5 circular senior gate)**: agreement is measured BY senior grades, so the
  rule deadlocked the first calibration. → Added bootstrap clause (first 6 senior grades
  exempt; gate applies thereafter).
- **[MAJOR] M1 (rigged comparison set)**: all three benchmarks chosen for cost methodology;
  code-workflow neighbors never compared. → Reframed the whole doc: "cost-methodology gap
  analysis," with the scope limitation stated up front, not buried.
- **[MAJOR] M2 ("Validated" overstates desk research)**: per Sakura's 2026-10-08 audit,
  subagent sweeps are not evidence. → Title and verdict downgraded; all external claims
  labeled [SECONDARY].
- **[MAJOR] M3 (§1.3 wall-clock in --json-out incoherent)**: --json-out is the judge tool;
  candidate latency is manual. → Rewrote as manual population of the existing column.
- **[MAJOR] M4 (quality-per-dollar had no decision rule)**: reproduced the "ranking without a
  decision rule" flaw the doc accused the current goal of. → Added explicit rule: ratio governs
  only when budget binds or raw scores tie; otherwise raw ranking stands.
- **[MAJOR] M5 (pass@4 transfer asserted)**: folded into the B1 demotion.
- **[MAJOR] M6 (routing question buried)**: → self-Q&A Q1 and iterations §2.4 now keep the
  routing question explicitly open if crossovers appear.
- **[MAJOR] M7 (contamination superiority unmeasured)**: → softened; rotation [OPEN] stated.
- **Minors applied**: "owner: agent, tonight" × 7 rebalanced to what's actually executable;
  10% reliability threshold marked as proposed heuristic (unsourced); tie-band claim corrected
  to "within-tie ordering missing" (rule exists); Jev-key hearsay flagged; harness-weighting
  hand-wave removed; post_training "unknown" hit rate stated.

## Mistake-hunt findings — applied

- **[BLOCKER] B1/B2**: same token-logging/model-identifier falsehoods as adversarial B2 —
  fixed together (see above).
- **[MAJOR] M1 ($25 in neither GOAL.md nor methodology.md)**: → attribution corrected to
  "standing chat decision (Sakura 2026-10-03)"; writing it into the runbook is now an
  explicit Tier 1 action.
- **[MAJOR] M2 ("1004 trajectories")**: → corrected to "1024 GB300-hours" with the
  mischaracterization (cap vs staging policy) fixed.
- **[MAJOR] M3 (promised URLs absent)**: → sources section added to self-Q&A with all three URLs.
- **[MAJOR] M4 (tie-band "no decision rule" false)**: → corrected (see adversarial M-minor).
- **[MAJOR] M5 (pass@4 = docs-only change false)**: → folded into Tier 2.1 demotion.
- **[MAJOR] M6 ("calibration threshold" undefined)**: → gate rewritten around the bootstrap +
  existing 70%-agreement diagnostic instead of an invented threshold.
- **[MAJOR] M7 ("run log" doesn't exist)**: → §1.2 now defines `results/run-log.jsonl` as new.
- **Minors applied**: "Baidu" attribution hedged; scorecard columns described as
  "populate existing" not greenfield; negative-weight clip-at-zero caveat added to §2.2.

## What survived review unchanged

The central gap (cost as metric vs guardrail), the tier structure, Tier 3 items, and the
"explicitly NOT adopted" section (with the §2.4 routing caveat added).
