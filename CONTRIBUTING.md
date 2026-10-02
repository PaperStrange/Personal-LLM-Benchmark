# Contributing

## Ground rules

1. **Every claim carries an evidence label.** `[REAL]` = genuinely executed,
   `[SIM]` = fabricated input through real plumbing, `[OPEN]` = unvalidated
   gap. Never present a mock as a real result.
2. **Zero-spend first.** Validate methodology on synthetic fixtures before
   any live or costly run.
3. **Suite stays green.** `python3 tests/run_all.py` must pass before any
   commit. Add a regression test for every bug you fix.
4. **Plural independent review.** No methodology change lands without
   adversarial + executability review.

## Adding a task

1. Add the task definition under `tasks/` (see `tasks/T1-global-review.md`
   for the format).
2. Add the rubric under `rubrics/` (see `rubrics/rubric-T1.json`).
3. Add T0 checks in `src/llm_workflow_eval/judge/t0_checks.py`.
4. Add regression tests under `tests/`.
5. Document the methodology in `docs/`.

## Layout

- `src/llm_workflow_eval/` — the machinery (judge, drivers, harness)
- `tasks/`, `rubrics/`, `fixture/` — the benchmark definition
- `docs/` — methodology and runbooks
- `tests/` — the pack's own regression suite ("eval the evals")
- `results/` — curated qualification evidence (not run noise)
- `examples/` — runnable examples
