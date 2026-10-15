# Review record: validation-knowledge-base.md (2026-10-13)

Reviewers: adversarial (boss/partner lens) + mistake-hunt/executability (independent
subagents, parallel). All findings applied below; reviewer claims verified by
parent before applying (runbook gate-v2 text and framework-iteration count
re-checked against the files).

## Adversarial — 7 MAJORs, all applied

- **M1 (V5 iterations listed as survivors):** moved to a new "Proposals (not yet
  validated)" section; Tier 1 explicitly unimplemented hypotheses.
- **M2 (survives contradicts V2):** T0 bullet now carries the vacuous-pass caveat
  + gate-v2 fix; failure-accounting bullet carries the V2 overwritten-artifacts
  exception.
- **M3 ("every validation hit the wall"):** → "every *judge* validation" (V5 never
  tested the judge).
- **M4 ("validated by failing"):** → "failures were informative; the loop is not
  yet stable."
- **M5 (n=1 anchor unstated):** Senior-grades paragraph now states n=1 explicitly.
- **M6 ("has never lied / every time"):** → "agreed on both occasions checked
  (V1, V2)."
- **M7 (ledger paths don't resolve):** hidden_files rows now give goal-root paths
  with the base difference stated.
- Minors m1–m10 applied: "first proof" → "first strong evidence"; "out-of-sample"
  → "out-of-candidate"; "regardless of input" scoped; "clean replication" →
  "clean run"; V7/V6 mootness noted in Current State; budget-raise attributed to
  the open-loop report; Gate 7 "holds" clarified; independence guards noted as
  code-only, never exercised by a real run; V2 attempt denominator stated (4 total,
  3 counted); narrative language ("failed honestly", "lied") removed.

## Mistake-hunt — 3 MINORs, all applied

- **M1:** "13 iterations" → 14 (verified: 1.1–1.6 + 2.1–2.5 + 3.1–3.3).
- **M2:** "five of six within ±0.008" → four within ±0.008, five within ±0.010
  (recomputed: deviations 0.000/0.001/0.005/0.010/0.002).
- **M3:** T0 vacuous pass "still open" was stale — runbook gate v2 (2026-09-30)
  FAILS zero refs; earlier runs NOT reclassified. V2 entry updated to CLOSED
  prospectively.

## Standing

No verdict changed. The V6 FAIL verdict, the decision log, and all loss
disclosures survived both reviews.
