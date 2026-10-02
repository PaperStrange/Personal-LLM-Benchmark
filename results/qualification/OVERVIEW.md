# Qualification overview (2026-10-01)

Zero-spend local qualification of the benchmark pack's own machinery, before
any live candidate runs. All claims carry [REAL]/[SIM]/[OPEN] labels.

## Gate 1, step 1 — deterministic instrument validation [REAL]: PASS

Strong control (authored from DEBT-INVENTORY.md, 22 anchors): **22/22** recall.
Weak control (dry-run synthetic): **12/22** recall.
Proves the parsing/anchor machinery works. Live Jev discrimination [OPEN].

## Gate 2 — role-separation rehearsal [REAL]: 0/3 completed

Model qwen2.5-1.5b-local, seed 7, mock self-test ALL GREEN before real runs.
- run1: implementer non-termination (15-min timeout, ~7000 tokens).
- run2, run3: implementer ignored `<<<FILE>>>` markers (format non-compliance).
- 3 driver bugs fixed during the runs (ollama path, ANSI stripping,
  bare-marker acceptance, filename-class runaway); originals preserved.
- Planners produced plan-formatted output in 4/5 attempts; one role violation
  (planner wrote code).
- Honest floor: this 1.5B model cannot execute the protocol. Real Gate 2
  needs a stronger model or a simpler implementer protocol.

## Gate 3 — sandboxed install rehearsal [REAL]: ALL GREEN

@t3_time 41s [REAL]; tarball SHA-512 matched; 4775 files sandboxed; MCP
session functional; temp HOME removed; operator `~/.npm` untouched.
Allowlist status: PROPOSED (awaiting nod). Harness absorption [OPEN].

## Gate 5 — baselines [REAL]

- T1 baseline: T0 pass, **0/22** recall (pure prompt echo — no review written).
- T2 baseline: ABORTED (same implementer format failure as harnessed runs).
- T3 baseline: 41s operator time-to-working.
- Baseline-vs-harness delta: unmeasurable with this model; the failure is
  not an orchestration artifact (single-context baseline fails the same way).

## Reviews

Plural independent review completed 2026-10-01: adversarial methodology
(APPROVE WITH FIXES, 12 findings F1–F12) + mistake-hunt/executability
(APPROVE WITH FIXES, 5 bugs). All required fixes applied and verified:
mock self-test ALL GREEN, full suite 100/100.

## T0 zero-reference proposal

Awaiting Sakura's concrete nod. Regenerated at
`~/workspace/goals/llm-workflow-benchmark-pack/hidden_files/t0-proposal/`.
Not applied; v1 classifications preserved.

## What remains [OPEN]

Gate 4 (live Jev calibration), Gate 1 steps 2–3 (live judging), Gate 6
(policy demo), Gate 7 (final review), first ranked comparison — all need
Sakura's Jev API key, candidate shortlist, and cost-abort threshold.
