# Gate 2 rehearsal — aggregate note (2026-10-01)

**Model:** qwen2.5-1.5b-local (ollama) · **Seed:** 7 (same planted bugs all runs:
`swapped_tax_rates`, `off_by_one_qty`) · **Harness:** `tools/qualification/gate2_driver.py`
(mock self-test ALL GREEN before the real runs).

## Outcomes

| Run | Result | Cause |
|-----|--------|-------|
| run1 | ABORTED | Valid attempt: implementer generated ~7000 tokens over 15 min without terminating → subprocess timeout. Genuine model non-termination. (Two earlier attempts aborted on harness parser bugs, preserved as `run1-aborted-parser-bug/` and `run1-aborted-badmarker/`; the parser was fixed and verified against the saved outputs.) |
| run2 | ABORTED | Implementer emitted 3.6KB of code with `# billing.py` comments and NO `<<<FILE>>>` markers. Genuine format non-compliance. |
| run3 | ABORTED | Implementer emitted code with NO markers at all. Genuine format non-compliance. |

**Completed runs: 0/3. Green runs: 0/3.**

## What this measures [REAL]

- The planners produced plan-formatted output in 4/5 attempts (runs 2, 3,
  run1-aborted-parser-bug, run1-aborted-badmarker). One attempt (run1 attempt
  3, the final valid run) violated the planner role entirely and wrote
  implementation code instead of a plan. "Plan-formatted," not "usable" — no
  plan was ever consumed by a working implementer, so usability is untested.
- The implementer step's format demands (exact `<<<FILE:path>>>` markers,
  complete file contents) exceed qwen2.5-1.5b's reliable instruction-following:
  2/3 valid attempts ignored the marker format entirely, 1/3 never terminated.
- Parser conditions were NOT identical across runs: runs 2 and 3 executed
  under the strict parser; run1 attempt 3 used the lenient parser (bare
  `<<<path>>>` accepted, ANSI stripped, constrained filename class). Runs
  2/3 outputs were verified to contain zero markers under either parser, so
  the comparison is fair — but the conditions differed.
- After fixing the driver bugs these real runs exposed (ollama path, ANSI
  stripping, bare-marker acceptance, filename-class runaway, duplicate
  capture_output kwarg), the remaining failures are model capability — not
  driver defects. The driver needed real fixes first; the model is the
  bottleneck that remains.

## Harness bugs found and fixed during the rehearsal (all verified)

1. Hardcoded ollama path → now searches PATH + both known locations.
2. Parser required `<<<FILE:path>>>`; model wrote `<<<path>>>` → now accepts both.
3. ANSI escape sequences in model output → stripped before parsing/writing.
4. Malformed marker (`<<<billing.py>>` with two `>`) made the lazy regex run
   away into a 500-char "filename" → filename class now excludes `<`, `>`,
   newlines; filenames sanity-checked as relative paths.
5. `subprocess.run()` duplicate `capture_output` kwarg (Gate 3 script).

## Implication for the real Gate 2

The real Gate 2 needs a more capable candidate model, or a more forgiving
implementer protocol (e.g. unified diffs, or fewer files). The rehearsal's
purpose — proving the machinery and measuring the floor — is served. The
floor is: this 1.5B local model cannot reliably execute the protocol.
