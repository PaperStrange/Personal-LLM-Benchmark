# T2 action-trace format (JSONL)

One JSON object per line, UTF-8, describing a single agent action during a
T2 multi-agent run. Produced by the harness wrapper (or a manual scribe for
now — no harness emits these yet, [OPEN]); consumed by
`src/llm_workflow_eval/judge/trace_check.py`, which flags looping / thrashing as a discipline
signal on top of the artifact grading in `rubrics/rubric-T2.json`.

## Fields

| field   | type             | meaning                                                        |
|---------|------------------|----------------------------------------------------------------|
| step    | int (1-based)    | sequence number within the run                                 |
| role    | string           | `planner` \| `implementer` \| `reviewer` \| `harness`            |
| action  | string           | tool/verb name, e.g. `read_file`, `edit_file`, `run_tests`, `web_search`, `ask_clarify` |
| target  | string \| null   | what the action touched: file path, command, or URL; null when none |
| outcome | string           | `ok` \| `error` \| `noop`                                       |
| note    | string (opt)     | free text, e.g. the error message on `error`                   |

Keep `action` names stable within a run — the checker groups by the exact
`(action, target)` pair, so `read_file` vs `read` on the same file would
count as two different pairs.

## Example

```jsonl
{"step": 1, "role": "planner", "action": "read_file", "target": "billing.py", "outcome": "ok"}
{"step": 2, "role": "planner", "action": "read_file", "target": "config.py", "outcome": "ok"}
{"step": 3, "role": "implementer", "action": "edit_file", "target": "billing.py", "outcome": "ok"}
{"step": 4, "role": "implementer", "action": "run_tests", "target": "pytest tests/", "outcome": "error", "note": "2 failed: test_discount_bounds"}
{"step": 5, "role": "reviewer", "action": "run_tests", "target": "pytest tests/", "outcome": "ok"}
```

## What the checker does with it

`src/llm_workflow_eval/judge/trace_check.py` reports the `(action, target)` distribution and a
plain Shannon entropy (bits) as a diagnostic, then flags two plain-language
patterns — no named metrics, per the literature guidance in
`docs/landscape.md` (item 16: concrete metric names in this
space lack a citable source, so the pack does not invent one):

- **looping** — the same `(action, target)` repeated ≥ N consecutive steps
  (default N=5).
- **thrashing** — a window of W consecutive steps (default W=8) using ≤ 2
  distinct `(action, target)` pairs, each appearing ≥ 2 times (e.g.
  edit-A / edit-B / edit-A / edit-B without progress).

Flag thresholds are uncalibrated against real T2 traces ([OPEN]); treat
flags as "send to senior review", not as scores.
