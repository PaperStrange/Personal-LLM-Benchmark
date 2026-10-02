#!/usr/bin/env python3
"""Aggregate repeated Jev-judge runs: pass@k / pass^k reporting.

Each input JSON is one `--json-out` file from src/llm_workflow_eval/judge/jev_judge.py (one repeat
of the same (task, candidate)). Success for a run is defined as
composite >= --threshold.

Usage:
    python src/llm_workflow_eval/judge/jev_judge.py --rubric rubrics/rubric-T1.json \
        --candidate results/t1-r1.md --json-out results/t1-r1.json
    # ... repeat k times, one --json-out per repeat ...
    python src/llm_workflow_eval/judge/aggregate.py results/t1-r1.json results/t1-r2.json \
        results/t1-r3.json [--threshold 60]

Reports:
  - per-item mean normalized value across runs (with min..max spread)
  - composite mean / std / min / max
  - pass@k  = 1 if at least one of the k runs succeeded, else 0
  - pass^k  = 1 if all k runs succeeded, else 0
  - one-line reliability interpretation
  - fixture vintage the inputs were graded against (--vintage; mixed
    vintages are refused, like non-independent rollouts)

pass@k measures capability ("can it do this at all?"); pass^k measures
reliability ("can you trust it to do this consistently?").

Independence rule (Jiang et al., "Beyond Pass@k", arXiv 2608.14711): k
counts INDEPENDENT rollouts — one --json-out file per rollout. A widespread
operationalization error sets n to the number of unit tests inside a single
submission, which inflates scores by 0.85-0.97 absolute. This script enforces
the rule: input files that are byte-identical (same file twice, copies, hard
links) or carry duplicate run_ids are rejected with exit 2 instead of
silently double-counted.
"""
import argparse
import hashlib
import json
import os
import statistics
import sys


def eprint(*args):
    print(*args, file=sys.stderr)


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def aggregate_files(paths, threshold=60.0, vintage=None):
    """Guard and aggregate judge --json-out files; return a result dict.

    Applies the independence guards (byte-identical inputs, duplicate
    run_ids) and the vintage guard, then computes per-item means and the
    composite mean / population-std / min / max plus pass@k / pass^k.
    Raises SystemExit(2) on guard violations, exactly as the CLI does.

    Extracted so src/llm_workflow_eval/drivers/open-loop/aggregate.py reuses the one guarded
    aggregation path instead of reimplementing it.
    """
    # Independence guard: each input must be one independent rollout's
    # --json-out. Byte-identical inputs (same file twice, copies, hard links)
    # or duplicate run_ids would silently inflate pass@k — reject loudly.
    seen_hashes = {}
    for p in paths:
        with open(p, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest()
        if h in seen_hashes:
            eprint(f"ERROR: {p!r} is byte-identical to {seen_hashes[h]!r}: "
                   "pass@k/pass^k require independent rollouts, "
                   "one --json-out per run.")
            sys.exit(2)
        seen_hashes[h] = p

    payloads = [load(p) for p in paths]
    run_ids = [p.get("run_id") for p in payloads if p.get("run_id")]
    if run_ids and len(set(run_ids)) != len(run_ids):
        eprint("ERROR: duplicate run_id values across inputs: pass@k/pass^k "
               "require independent rollouts.")
        sys.exit(2)

    # Vintage guard: a composite averaged across the canonical fixture and a
    # rotated variant (or two different variants) would be meaningless, so
    # mixed vintages are refused like mixed rollouts. Inputs that predate
    # vintage stamping report "unknown" and may only aggregate with each other.
    stamped = {p.get("fixture_vintage", "unknown") for p in payloads}
    if len(stamped) > 1:
        eprint(f"ERROR: mixed fixture vintages across inputs: "
               f"{sorted(stamped)} — aggregate one vintage at a time.")
        sys.exit(2)
    resolved_vintage = vintage or next(iter(stamped))
    if vintage and next(iter(stamped)) != "unknown" \
            and vintage != next(iter(stamped)):
        eprint(f"ERROR: --vintage {vintage!r} contradicts the stamped "
               f"vintage {next(iter(stamped))!r} in the inputs.")
        sys.exit(2)

    k = len(payloads)
    composites = [p["composite"] for p in payloads]
    successes = [c >= threshold for c in composites]

    # Per-item means across runs (skip items with no normalized value).
    by_item = {}
    for p in payloads:
        for it in p.get("items", []):
            if it.get("value") is not None:
                by_item.setdefault(it["id"], []).append(it["value"])
    items = {item_id: {"mean": statistics.fmean(vals),
                       "min": min(vals), "max": max(vals), "n": len(vals)}
             for item_id, vals in sorted(by_item.items())}

    pass_at_k = 1 if any(successes) else 0
    pass_cubed_k = 1 if all(successes) else 0
    if pass_cubed_k:
        interp = "reliable: every run cleared the threshold."
    elif pass_at_k:
        interp = ("capable but flaky: at least one run succeeded, not all — "
                  "investigate variance before trusting this candidate.")
    else:
        interp = "below bar: no run reached the threshold."

    return {
        "k": k,
        "threshold": threshold,
        "vintage": resolved_vintage,
        "items": items,
        "composites": composites,
        "composite_mean": statistics.fmean(composites),
        "composite_std": statistics.pstdev(composites),
        "composite_min": min(composites),
        "composite_max": max(composites),
        "succeeded": sum(successes),
        "pass_at_k": pass_at_k,
        "pass_cubed_k": pass_cubed_k,
        "interpretation": interp,
    }


def main():
    ap = argparse.ArgumentParser(
        description="Aggregate repeated judge runs into pass@k / pass^k.")
    ap.add_argument("runs", nargs="+", help="--json-out files from jev_judge.py")
    ap.add_argument("--threshold", type=float, default=60.0,
                    help="composite >= threshold counts as success (default 60)")
    ap.add_argument("--vintage", default=None,
                    help="fixture vintage label for this report (default: the "
                         "vintage stamped in the inputs, or 'unknown' when "
                         "the inputs predate vintage stamping). Must agree "
                         "with the stamped vintage or aggregation is refused.")
    args = ap.parse_args()

    r = aggregate_files(args.runs, threshold=args.threshold,
                        vintage=args.vintage)

    print(f"runs: {r['k']}  threshold: {r['threshold']:g}  "
          f"vintage: {r['vintage']}")
    print(f"{'item':<18}{'mean':<8}{'min..max':<16}{'n'}")
    print("-" * 52)
    for item_id, s in r["items"].items():
        print(f"{item_id:<18}{s['mean']:<8.2f}"
              f"{s['min']:.2f}..{s['max']:.2f}{'':<9}{s['n']}")
    print("-" * 52)
    # Spread of the observed composites. Population std (pstdev), not the
    # sample form: a single rollout has no observed spread, so std is 0.0
    # rather than undefined. This is the number the README's tie-band policy
    # uses to decide whether a |delta composite| is a ranking or a tie.
    print(f"composite: mean {r['composite_mean']:.1f} / "
          f"std {r['composite_std']:.1f} / "
          f"min {r['composite_min']:.1f} / max {r['composite_max']:.1f}")
    print(f"succeeded runs: {r['succeeded']}/{r['k']} "
          f"(composite >= {r['threshold']:g})")

    print(f"pass@k (>=1 of {r['k']} runs succeeded): {r['pass_at_k']}")
    print(f"pass^{r['k']} (all {r['k']} runs succeeded):   "
          f"{r['pass_cubed_k']}")

    print(f"interpretation: {r['interpretation']}")


if __name__ == "__main__":
    main()
