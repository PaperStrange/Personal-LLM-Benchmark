# Product Backlog — LLM Workflow Benchmark Pack

**Owner:** Harry. **GitHub issues:** parent #1 tracks all open stories (#2-#15). Pick up work by self-assigning an issue.

**Maintained:** every sprint planning moves items between
Backlog → Sprint → Done; nothing is planned from scratch twice. Statuses:
`TODO`, `SPRINT`, `BLOCKED`, `DONE`. Updated 2026-10-14.

**How to use this file.** Sprint planning = pick the top ready items off this
backlog, move them into that sprint's plan, and write acceptance criteria. When
Sakura asks for "the next iteration," the answer comes from here — not from a
fresh re-read of the world.

---

## Epic A — Cost as metric (not just guardrail)

| ID | Story | Priority | Status |
|---|---|---|---|
| A-1 | Populate `cost_usd`/`wall_time_s` per scorecard row (manual, honest); add `--model`/`--candidate` to `jev_judge.py` stamped into `--json-out` | P0 | DONE (Sprint 1, 2026-10-14) |
| A-2 | `results/run-log.jsonl`: one line per attempt (date, task, candidate, harness, status, failure_kind); failure rate reported next to pass@k; >10% unusable → not recommended | P0 | DONE (Sprint 1, 2026-10-14) |
| A-3 | Wall-clock discipline per attempt → median latency per (candidate × task) in the report | P0 | DONE (Sprint 1, 2026-10-14) |
| A-4 | Within-tie ordering rule: tie-band candidates ordered by measured `cost_usd`, then latency; quality-per-dollar governs ONLY when budget binds or scores tie in-band | P0 | DONE (Sprint 1, 2026-10-14) |
| A-5 | Persist the $25 campaign cap in methodology/runbook (currently a chat decision only) | P0 | DONE (Sprint 1, 2026-10-14) |
| A-6 | `post_training` lineage field per candidate; test correlation after 2+ campaigns, drop if null | P0 | DONE (Sprint 1, 2026-10-14) |
| A-7 (issue #2) | Per-task price proxies + value-weighted scores (re-run the ranked list under value weights, report flips) | P2 | TODO (Tier 3) |

## Epic B — Governance

| ID | Story | Priority | Status |
|---|---|---|---|
| B-1 | Senior gate with bootstrap clause: first 6 senior spot-checks exempt and establish the baseline; gate applies thereafter | P0 | DONE (Sprint 1, 2026-10-14) |
| B-2 (issue #3) | T2 negative-weight damage items (no pre-existing tests broken, no unrelated files modified) with clip-at-zero handling; hard gate: diff applies cleanly | P1 | TODO (Tier 2) |
| B-3 (issue #4) | Calibration as convergence loop: on disagreement, fix rubric/judge wording, re-run, bank the resolution | P1 | TODO (Tier 2) |

## Epic C — Judge path (the blocker)

| ID | Story | Priority | Status |
|---|---|---|---|
| C-1 (issue #5) | Resolve the cheap judge: (a) bind card for Jev, (b) senior-only minimal grading, or (c) new open judge — **Sakura's decision** | P0 | BLOCKED (on Sakura) |
| C-2 (issue #6) | If (c): candidate must pass the Gate 4b kill-test (grade 0/22 candidates, hit rubric floors) before any claim | P0 | TODO |
| C-3 (issue #7) | Close Gate 4: one live calibration call against the chosen judge | P0 | BLOCKED (on C-1) |

## Epic D — Campaign 1

| ID | Story | Priority | Status |
|---|---|---|---|
| D-1 (issue #8) | T1 on GPT-6 Luna and Sol via Codex, judged, with real cost_usd + latency populated | P0 | BLOCKED (on C-3) |
| D-2 (issue #9) | Campaign 1 report: ranked comparison, both rankings side by side (raw + value-aware), fuel-gauge accounting | P0 | BLOCKED (on D-1) |

## Epic E — Post-campaign improvements

| ID | Story | Priority | Status |
|---|---|---|---|
| E-1 (issue #10) | pass@4 as headline — needs Sakura's budget sign-off (+33% judge spend) | P1 | TODO (Tier 2) |
| E-2 (issue #11) | Input-scale stratification: T1 at two fixture sizes; watch for rank crossovers (if crossovers appear, single-ranked-list format is wrong) | P1 | TODO (Tier 2) |
| E-3 (issue #12) | Automated candidate-side cost/latency logging (instruments harness runners that don't exist as code yet) | P1 | TODO (Tier 2) |

## Epic F — Deferred (human time or judgment)

| ID | Story | Priority | Status |
|---|---|---|---|
| F-1 (issue #13) | Human labor-time baselines for the value-weighted comparison | P2 | TODO (Tier 3) |
| F-2 (issue #14) | Second cheap judge on a sample (cross-judge agreement) | P2 | TODO (Tier 3) |

## Epic G — Harness candidates

| ID | Story | Priority | Status |
|---|---|---|---|
| G-1 | Ruflo zero-spend dry run (see `docs/knowledge/ruflo-harness-brief.md`): verify tree + license + Mods docs, exercise CLI with no model calls, T2-shaped dry run on synthetic fixture, pass/fail + kill criteria | P1 | DONE (zero-spend scope only; substance criteria → G-2; report: `docs/knowledge/ruflo-dry-run-g1-report.md`, review: `docs/reviews/review-ruflo-g1-2026-10-28.md`) |
| G-2 (issue #15) | Ruflo live evaluation (pairs with candidate models; grading still needs C-1) | P1 | BLOCKED (on C-1 + fuel gauge + enforce-mode rules authored + T2 run design inside Claude Code/Codex) |

## Done (reference — the validated past)

- V1 dry run (2026-09-22), V2/V3 open loops (2026-09-30), V4 Gate 4a (2026-10-09),
  V5 gap analysis + 14 iterations (2026-10-13), V6 Gate 4b Decider kill (2026-10-13),
  validation knowledge base (2026-10-13). Details: `docs/knowledge/validation-knowledge-base.md`.
