# Gate 1, step 1 — deterministic-axis instrument validation (2026-10-01)

**Method:** mock SDK (`tests/helpers/mock_typesafe`), zero cost, zero network.
Read only the `deterministic debt recall:` line; canned Jev scores ignored.

| Control | Source | Deterministic recall |
|---|---|---|
| Strong | `results/qualification/t1-strong-control.md` (authored fresh 2026-10-01 directly from `fixture/DEBT-INVENTORY.md`, all 22 anchors with file:line) | **22/22 (100%)** [REAL] |
| Weak | `results/dryrun/T1-candidate-simulated.md` (dry-run synthetic) | **12/22 (55%)** [REAL] |

**Verdict:** PASS [REAL] — strong > weak on the deterministic axis (22/22 vs 12/22).

**What this proves:** `parse_inventory` and the anchor format work end to end
(the strong control is 22/22 by construction; the machinery reports it
correctly). **What it does NOT prove:** that the judge discriminates real
candidate quality — the discrimination burden sits on live Jev (Gate 1 step 2,
needs Sakura's API key) and the senior judge (Gate 1 step 3). Both [OPEN].
