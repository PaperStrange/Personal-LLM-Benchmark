#!/usr/bin/env python3
"""Flag looping / thrashing in a T2 action trace (JSONL).

Reads the trace format documented in tasks/t2-discount-fix/TRACE-FORMAT.md
(one JSON object per line: step, role, action, target, outcome) and reports:

- the (action, target) distribution and its Shannon entropy in bits
  (diagnostic only — plain descriptive statistic, not a named metric);
- **looping**: the same (action, target) repeated >= N consecutive steps;
- **thrashing**: a window of W consecutive steps using <= 2 distinct
  (action, target) pairs, each appearing >= 2 times.

Deliberately no fancy metric names: research/LLM-BENCHMARK-LANDSCAPE.md
(item 16) notes the concrete metric proposals in this space lack a citable
source, so the pack describes these plainly as repetition/loop detection.
Flag thresholds are uncalibrated against real T2 traces ([OPEN]) — flags
mean "send to senior review", not "deduct points".

Usage:
    python judge/trace_check.py trace.jsonl [--max-repeat 5] [--window 8]
Exit 0 always (this is a reporter, not a gate); the JSON summary goes to
stdout, problems to stderr.
"""
import argparse
import json
import math
import sys
from collections import Counter


def load_trace(path):
    """Return (events, malformed_lines).

    Malformed lines are skipped with a stderr warning; the count is
    returned (not just warned) so a corrupt trace can't report as a
    clean empty one.
    """
    events = []
    malformed = 0
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as exc:
                malformed += 1
                print("warning: skipping malformed line %d: %s"
                      % (lineno, exc), file=sys.stderr)
    return events, malformed


def pair(event):
    return (event.get("action"), event.get("target"))


def shannon_entropy(counts):
    total = sum(counts.values())
    if total == 0:
        return 0.0
    return -sum((c / total) * math.log2(c / total)
                for c in counts.values() if c > 0)


def find_loops(events, max_repeat):
    """Runs of >= max_repeat consecutive identical (action, target) pairs."""
    flags = []
    if not events:
        return flags
    run_pair = pair(events[0])
    run_start = 0
    run_len = 1
    for i in range(1, len(events)):
        if pair(events[i]) == run_pair:
            run_len += 1
        else:
            if run_len >= max_repeat:
                flags.append({
                    "type": "looping",
                    "action": run_pair[0],
                    "target": run_pair[1],
                    "steps": [run_start + 1, run_start + run_len],
                    "run_length": run_len,
                    "detail": ("same action+target %r on %r repeated %d "
                               "consecutive steps (steps %d-%d)"
                               % (run_pair[0], run_pair[1], run_len,
                                  run_start + 1, run_start + run_len)),
                })
            run_pair = pair(events[i])
            run_start = i
            run_len = 1
    if run_len >= max_repeat:
        flags.append({
            "type": "looping",
            "action": run_pair[0],
            "target": run_pair[1],
            "steps": [run_start + 1, run_start + run_len],
            "run_length": run_len,
            "detail": ("same action+target %r on %r repeated %d consecutive "
                       "steps (steps %d-%d)"
                       % (run_pair[0], run_pair[1], run_len,
                          run_start + 1, run_start + run_len)),
        })
    return flags


def find_thrash(events, window):
    """Windows of `window` steps using <= 2 distinct pairs, each >= 2x."""
    flags = []
    n = len(events)
    if n < window:
        return flags
    pairs = [pair(e) for e in events]
    for start in range(n - window + 1):
        win = pairs[start:start + window]
        counts = Counter(win)
        if len(counts) <= 2 and all(c >= 2 for c in counts.values()):
            flags.append({
                "type": "thrashing",
                "steps": [start + 1, start + window],
                "pairs": [{"action": a, "target": t, "count": c}
                          for (a, t), c in sorted(counts.items())],
                "detail": ("steps %d-%d use only %d distinct action+target "
                           "pairs with no progress signal"
                           % (start + 1, start + window, len(counts))),
            })
    return flags


def analyze_trace(events, malformed_lines=0, max_repeat=5, window=8):
    counts = Counter(pair(e) for e in events)
    return {
        "steps": len(events),
        "malformed_lines": malformed_lines,
        "distinct_pairs": len(counts),
        "action_counts": dict(
            sorted(Counter(e.get("action") for e in events).items(),
                   key=lambda kv: (-kv[1], str(kv[0])))),
        "entropy_bits": round(shannon_entropy(counts), 3),
        "max_consecutive_repeat": max(
            (len(list(g)) for _, g in _runs(pair(e) for e in events)),
            default=0),
        "flags": find_loops(events, max_repeat)
                 + find_thrash(events, window),
    }


def _runs(seq):
    """Yield (value, run_list) groups of consecutive equal values."""
    seq = list(seq)
    if not seq:
        return
    cur, run = seq[0], [seq[0]]
    for v in seq[1:]:
        if v == cur:
            run.append(v)
        else:
            yield cur, run
            cur, run = v, [v]
    yield cur, run


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("trace")
    ap.add_argument("--max-repeat", type=int, default=5)
    ap.add_argument("--window", type=int, default=8)
    args = ap.parse_args(argv)
    events, malformed = load_trace(args.trace)
    summary = analyze_trace(events, malformed_lines=malformed,
                            max_repeat=args.max_repeat,
                            window=args.window)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
