"""Regression tests for judge/trace_check.py (Phase 3c).

Hand-verifiable inputs: a looping trace must be flagged, a healthy varied
trace must not be, an alternating A/B trace must be flagged as thrashing,
and the reported entropy must match a hand computation. No named metrics —
plain consecutive-repetition and low-variety-window detection, per
research/LLM-BENCHMARK-LANDSCAPE.md item 16.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

PACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECKER = os.path.join(PACK, "judge", "trace_check.py")

sys.path.insert(0, PACK)
from judge.trace_check import analyze_trace, load_trace  # noqa: E402


def ev(step, role, action, target, outcome="ok", note=None):
    d = {"step": step, "role": role, "action": action, "target": target,
         "outcome": outcome}
    if note is not None:
        d["note"] = note
    return d


def write_trace(tmp, events):
    path = os.path.join(tmp, "trace.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")
    return path


class TraceCheckTest(unittest.TestCase):
    def test_looping_trace_is_flagged(self):
        # Hand-verifiable: steps 3-8 are the same (read_file, billing.py)
        # six times in a row -> one looping flag, run_length 6.
        events = [
            ev(1, "planner", "read_file", "config.py"),
            ev(2, "planner", "read_file", "db.py"),
        ] + [ev(i, "implementer", "read_file", "billing.py")
             for i in range(3, 9)]
        summary = analyze_trace(events)
        loops = [f for f in summary["flags"] if f["type"] == "looping"]
        self.assertEqual(len(loops), 1)
        self.assertEqual(loops[0]["run_length"], 6)
        self.assertEqual(loops[0]["action"], "read_file")
        self.assertEqual(loops[0]["target"], "billing.py")
        self.assertEqual(summary["max_consecutive_repeat"], 6)

    def test_healthy_varied_trace_is_not_flagged(self):
        # Hand-verifiable: 12 steps cycling 4 distinct pairs; longest
        # consecutive run is 1, every 8-window has 4 distinct pairs.
        cycle = [("read_file", "billing.py"), ("read_file", "config.py"),
                 ("edit_file", "billing.py"), ("run_tests", "pytest")]
        roles = ["planner", "planner", "implementer", "reviewer"]
        events = [ev(i + 1, roles[i % 4], a, t)
                  for i, (a, t) in enumerate(cycle * 3)]
        summary = analyze_trace(events)
        self.assertEqual(summary["flags"], [])
        self.assertEqual(summary["steps"], 12)
        self.assertEqual(summary["distinct_pairs"], 4)

    def test_alternation_is_flagged_as_thrashing(self):
        # Hand-verifiable: edit billing.py / edit config.py alternating for
        # 8 steps, no consecutive repeat, no progress -> thrashing flag.
        events = [ev(i + 1, "implementer", "edit_file",
                     "billing.py" if i % 2 == 0 else "config.py")
                  for i in range(8)]
        summary = analyze_trace(events)
        thrash = [f for f in summary["flags"] if f["type"] == "thrashing"]
        self.assertTrue(thrash, "alternating A/B trace must be flagged")
        loops = [f for f in summary["flags"] if f["type"] == "looping"]
        self.assertEqual(loops, [],
                         "no consecutive repeat here, so no looping flag")
        self.assertEqual(summary["max_consecutive_repeat"], 1)

    def test_entropy_matches_hand_computation(self):
        # Hand-verifiable: two pairs at 50/50 -> exactly 1.0 bit.
        events = [ev(1, "planner", "read_file", "a.py"),
                  ev(2, "planner", "read_file", "b.py"),
                  ev(3, "planner", "read_file", "a.py"),
                  ev(4, "planner", "read_file", "b.py")]
        summary = analyze_trace(events)
        self.assertAlmostEqual(summary["entropy_bits"], 1.0, places=3)

    def test_repeat_threshold_is_configurable(self):
        events = [ev(i + 1, "implementer", "read_file", "billing.py")
                  for i in range(4)]
        self.assertEqual(analyze_trace(events, max_repeat=5)["flags"], [])
        flagged = analyze_trace(events, max_repeat=4)["flags"]
        self.assertTrue(any(f["type"] == "looping" for f in flagged))

    def test_malformed_lines_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "trace.jsonl")
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n")
                f.write("{not valid json}\n")
                f.write(json.dumps(ev(1, "planner", "read_file", "a.py"))
                        + "\n")
            events, malformed = load_trace(path)
            self.assertEqual(len(events), 1)
            self.assertEqual(malformed, 1)
            summary = analyze_trace(events, malformed_lines=malformed)
            self.assertEqual(summary["steps"], 1)
            self.assertEqual(summary["malformed_lines"], 1)

    def test_all_garbage_trace_reports_malformed_not_clean(self):
        # A 100% corrupt trace must not report as a clean empty one: the
        # malformed count is part of the JSON summary, not just stderr.
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "trace.jsonl")
            with open(path, "w", encoding="utf-8") as f:
                for i in range(3):
                    f.write("{bad line %d}\n" % i)
            events, malformed = load_trace(path)
            summary = analyze_trace(events, malformed_lines=malformed)
            self.assertEqual(summary["steps"], 0)
            self.assertEqual(summary["malformed_lines"], 3)
            self.assertEqual(summary["flags"], [])

    def test_cli_reports_json_and_exits_zero(self):
        events = [ev(i + 1, "implementer", "read_file", "billing.py")
                  for i in range(6)]
        with tempfile.TemporaryDirectory() as tmp:
            path = write_trace(tmp, events)
            p = subprocess.run([sys.executable, CHECKER, path],
                               capture_output=True, text=True, cwd=PACK)
            self.assertEqual(p.returncode, 0, p.stderr)
            summary = json.loads(p.stdout)
        self.assertTrue(any(f["type"] == "looping"
                            for f in summary["flags"]))


if __name__ == "__main__":
    unittest.main()
