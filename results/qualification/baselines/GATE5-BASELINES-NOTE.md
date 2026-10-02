# Gate 5 — baseline protocols aggregate note (2026-10-01)

**Model:** qwen2.5-1.5b-local · **Seed:** 7 (T2) · **Driver:**
`tools/qualification/baseline_driver.py`

Protocol amendments (recorded in the driver docstring): A1 (prompt
concatenation simulates the single chat context), A2 (T3 sandbox replaces
harness config), A3 (2500-token generation cap after the uncapped T1 attempt
rambled past 6300 tokens / 900s without terminating).

## Results

| Baseline | Result |
|----------|--------|
| T1 (one-shot, no tools) | COMPLETED: T0 pass, deterministic recall **0/22**. The output is a near-verbatim echo of the prompt + fixture files — no review was written. (T0-pass here means almost nothing about quality: T0 checks document structure, not content. Do not misread "T0 pass" as "the baseline did okay.") |
| T2 (single context, 3 turns) | ABORTED: turn-2 implementer emitted no `<<<FILE>>>` blocks (same format failure as the harnessed runs). |
| T3 (human install) | t3_time = **41s** [REAL] (operator-executed Gate 3 rehearsal; the number to beat). |

## Baseline-vs-harness delta

Unmeasurable with this model: the harnessed Gate-2 runs (0/3 completed) and
the T2 baseline (aborted) both fail at the implementer format step, and the
T1 baseline scores 0/22. The model is the bottleneck in both conditions —
the delta the baselines are designed to isolate (harness contribution) cannot
be estimated until a model that clears the format bar is tested.

**What the baselines DO establish [REAL]:** the failure is not an artifact
of multi-agent orchestration. The single-context T2 baseline fails the same
way, and the no-tools T1 baseline cannot produce a review at all. A stronger
candidate model is the prerequisite for both the harnessed runs and the
baselines to yield signal.
