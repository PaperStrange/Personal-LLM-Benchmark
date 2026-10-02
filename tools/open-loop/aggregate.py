#!/usr/bin/env python3
"""Aggregate open-loop repeats from one output dir into aggregate.json.

Discovers complete runs (runN-meta.json + judge-runN.json both present) in
the output dir, aggregates the judge payloads through the ONE guarded path
(judge/aggregate.py: independence + vintage guards, pass@k/pass^k), then
adds the open-loop layer T0 guards can't see: per-run T0 status, wall time,
mean confidence, deterministic recall. Writes aggregate.json.

Usage:
    python3 tools/open-loop/aggregate.py [--out results/open-loop]
                                         [--threshold 60]

Defaults to $OPEN_LOOP_OUT, then results/open-loop under the pack.
The scorecard row stays handwritten; this script only crunches numbers.
"""
import argparse
import datetime
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.abspath(os.path.join(HERE, "..", ".."))


def load_judge_aggregate():
    spec = importlib.util.spec_from_file_location(
        "judge_aggregate", os.path.join(PACK, "judge", "aggregate.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_runs(outdir):
    """Return [(n, meta, judge_path)] for complete runs only.

    Scans the directory for every runN-meta.json (sorted by N) so a skipped
    run number can never silently hide later runs. A repeat counts as
    complete when the candidate passed T0 AND the judge produced a payload;
    incomplete repeats are listed separately, never dropped.
    """
    complete, incomplete = [], []
    for name in sorted(os.listdir(outdir)):
        m = re.fullmatch(r"run(\d+)-meta\.json", name)
        if not m:
            continue
        n = int(m.group(1))
        meta_p = os.path.join(outdir, name)
        judge_p = os.path.join(outdir, "judge-run%d.json" % n)
        with open(meta_p, encoding="utf-8") as f:
            meta = json.load(f)
        if os.path.exists(judge_p):
            complete.append((n, meta, judge_p))
        else:
            incomplete.append((n, meta))
    return complete, incomplete


def seconds_between(started, finished):
    try:
        a = datetime.datetime.fromisoformat(started)
        b = datetime.datetime.fromisoformat(finished)
        return max(0.0, (b - a).total_seconds())
    except (ValueError, TypeError):
        return None


def run_note(outdir, n, meta):
    """Honest one-line reason a repeat has no judge payload."""
    if meta.get("t0") != "PASS":
        return {"run": n, "t0": meta.get("t0"),
                "note": "T0 gate failed, no judge spend"}
    elog = "judge-run%d.error.log" % n
    if os.path.exists(os.path.join(outdir, elog)):
        note = "judge failed; raw output retained in " + elog
    else:
        note = ("judge failed; raw emission was not retained "
                "(error logging was added to the driver after this run)")
    return {"run": n, "t0": meta.get("t0"), "note": note}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--threshold", type=float, default=60.0)
    args = ap.parse_args()
    outdir = args.out or os.environ.get(
        "OPEN_LOOP_OUT", os.path.join(PACK, "results", "open-loop"))
    ja = load_judge_aggregate()
    complete, incomplete = load_runs(outdir)
    if not complete:
        raise SystemExit("no complete runs found in %s" % outdir)

    stats = ja.aggregate_files([jp for _, _, jp in complete],
                               threshold=args.threshold)

    def load_json(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    confs = [load_json(jp).get("mean_confidence") for _, _, jp in complete]
    recalls = [load_json(jp).get("deterministic_recall")
               for _, _, jp in complete]
    t0 = [(n, m.get("t0")) for n, m, _ in complete]
    t0_pass = sum(1 for _, s in t0 if s == "PASS")
    wall = [seconds_between(m.get("started"), m.get("finished"))
            for _, m, _ in complete]
    wall_total = round(sum(w for w in wall if w is not None))
    first_meta = complete[0][1]

    agg = {
        "outdir": outdir,
        "attempts": len(complete) + len(incomplete),
        "n_complete_runs": len(complete),
        "incomplete_runs": [run_note(outdir, n, m)
                            for n, m in incomplete],
        "model": first_meta.get("candidate"),
        "judge": first_meta.get("judge"),
        "threshold": args.threshold,
        "t0_pass_complete_runs": "%d/%d" % (t0_pass, len(complete)),
        "composites": [round(c, 1) for c in stats["composites"]],
        "composite_mean": round(stats["composite_mean"], 1),
        "composite_population_std": round(stats["composite_std"], 1),
        "composite_min": round(stats["composite_min"], 1),
        "composite_max": round(stats["composite_max"], 1),
        "pass_at_k": stats["pass_at_k"],
        "pass_cubed_k": stats["pass_cubed_k"],
        "vintage": stats["vintage"],
        "per_item": {k: {"mean": round(v["mean"], 2),
                         "min": round(v["min"], 2),
                         "max": round(v["max"], 2), "n": v["n"]}
                     for k, v in stats["items"].items()},
        "mean_confidence_per_run": confs,
        "deterministic_recall_per_run": [
            {"found": r.get("found"), "total": r.get("total")}
            if isinstance(r, dict) else r for r in recalls],
        "wall_time_s_complete_runs": wall_total,
        "note": ("Judge is the same open-weight model as the candidate, so "
                 "NOT independent and NOT Jev. Metrics characterize the "
                 "stand-in judge, not credible candidate capability. "
                 "pass@k/pass^k are computed over COMPLETE runs only "
                 "(n_complete_runs); incomplete repeats are listed, never "
                 "silently dropped. t0_pass_complete_runs and "
                 "wall_time_s_complete_runs also cover complete runs only; "
                 "the scorecard's t0_pass/wall_time_s sum ALL attempts."),
    }
    with open(os.path.join(outdir, "aggregate.json"), "w") as f:
        json.dump(agg, f, indent=2)

    print("attempts=%d complete=%d t0(complete)=%s" % (
        agg["attempts"], agg["n_complete_runs"],
        agg["t0_pass_complete_runs"]))
    for inc in agg["incomplete_runs"]:
        print("  incomplete run %d: t0=%s — %s" % (
            inc["run"], inc["t0"], inc["note"]))
    print("composite: %s  mean=%.1f  pstd=%.1f  min=%.1f  max=%.1f" % (
        agg["composites"], agg["composite_mean"],
        agg["composite_population_std"], agg["composite_min"],
        agg["composite_max"]))
    print("pass@k=%d pass^%d=%d (threshold %g, complete runs only)" % (
        agg["pass_at_k"], agg["n_complete_runs"], agg["pass_cubed_k"],
        args.threshold))
    print("wall_time_s_complete_runs=%d" % agg["wall_time_s_complete_runs"])
    print("wrote %s" % os.path.join(outdir, "aggregate.json"))


if __name__ == "__main__":
    main()
