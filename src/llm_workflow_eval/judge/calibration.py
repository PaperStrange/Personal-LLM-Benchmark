#!/usr/bin/env python3
"""Judge calibration: how well does Jev agree with senior review?

Reads results/calibration.csv — one row per senior spot-check:

    date,run_id,item_id,jev_norm,senior_norm,jev_choice,senior_choice,notes

Numeric agreement: jev_norm and senior_norm are the 0-1 normalized scores
for the same rubric item on the same candidate output (see
src/llm_workflow_eval/judge/jev_judge.py --json-out for jev_norm; re-grade flagged/sampled items
with src/llm_workflow_eval/judge/senior_judge_prompt.md for senior_norm). Reported as mean
absolute |jev - senior| deviation and an agreement rate (|diff| <= 0.15).

Categorical agreement: jev_choice and senior_choice are the selected option
labels for choice-kind rubric items (e.g. t3_time's under_15_min /
under_1_hour / under_1_day / never_worked — see rubrics/rubric-T3.json).
Reported as Cohen's kappa, the chance-corrected agreement statistic the
literature supports over a flat threshold for categorical verdicts
(see docs/landscape.md, "Where the literature pressures
our current design", flag 1).
A row may carry both numeric and categorical verdicts; each is counted in
its own table independently.

Usage:
    python src/llm_workflow_eval/judge/calibration.py [results/calibration.csv]

Items with numeric agreement < 70% are flagged "recalibrate": reword the
rubric item or distrust the judge on it. Run quarterly, or whenever the
judge's answers start looking suspicious. Datasets and judges rot — this
ritual is the lie detector.
"""
import argparse
import csv
import os
import statistics
import sys
from collections import Counter

AGREE_TOLERANCE = 0.15  # v1 heuristic: |diff| <= 0.15 counts as agree.
# The flat 0.15 rule is an explicitly documented heuristic, not a principled
# constant; Cohen's kappa below is the principled categorical counterpart.
# A target-agreement-level escalation rule ("escalate until senior-agreement
# >= 0.80") is future work pending live calibration data — see README.
RECALIBRATE_BELOW = 0.70


def eprint(*args):
    print(*args, file=sys.stderr)


def cohens_kappa(pairs):
    """Cohen's kappa for categorical agreement.

    pairs: iterable of (jev_choice, senior_choice) label pairs.
    Returns None for no pairs. kappa = (p_o - p_e) / (1 - p_e) where p_o is
    observed agreement and p_e is the agreement expected by chance from the
    marginal label distributions. Perfect agreement on a single label gives
    1.0; chance-level agreement gives 0.0.
    """
    pairs = list(pairs)
    n = len(pairs)
    if n == 0:
        return None
    p_o = sum(1 for a, b in pairs if a == b) / n
    a_counts = Counter(a for a, _ in pairs)
    b_counts = Counter(b for _, b in pairs)
    p_e = sum((a_counts[c] / n) * (b_counts[c] / n)
              for c in set(a_counts) | set(b_counts))
    if 1.0 - p_e == 0.0:
        return 1.0 if p_o == 1.0 else 0.0
    return (p_o - p_e) / (1.0 - p_e)


def main():
    ap = argparse.ArgumentParser(
        description="Report Jev-vs-senior agreement from calibration.csv.")
    ap.add_argument("csv_path", nargs="?",
                    default="results/calibration.csv")
    args = ap.parse_args()

    if not os.path.isfile(args.csv_path):
        eprint(f"No calibration data yet: {args.csv_path} not found. "
              f"Log senior spot-checks there first (see header).")
        sys.exit(2)

    diffs_by_item = {}
    cats_by_item = {}
    skipped = 0
    with open(args.csv_path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            usable = False
            try:
                jev = float(row["jev_norm"])
                sen = float(row["senior_norm"])
            except (KeyError, TypeError, ValueError):
                pass
            else:
                diffs_by_item.setdefault(
                    row.get("item_id", "?"), []).append(abs(jev - sen))
                usable = True
            jev_c = (row.get("jev_choice") or "").strip()
            sen_c = (row.get("senior_choice") or "").strip()
            if jev_c and sen_c:
                cats_by_item.setdefault(
                    row.get("item_id", "?"), []).append((jev_c, sen_c))
                usable = True
            if not usable:
                skipped += 1

    if not diffs_by_item and not cats_by_item:
        eprint("No usable rows (need numeric jev_norm/senior_norm and/or "
               "categorical jev_choice/senior_choice).")
        sys.exit(2)
    if skipped:
        eprint(f"skipped {skipped} malformed row(s)")

    if diffs_by_item:
        print(f"{'item':<18}{'n':<5}{'mean_|diff|':<12}{'agree_rate':<11}"
              "status")
        print("-" * 62)
        all_diffs = []
        recalibrate = []
        for item_id in sorted(diffs_by_item):
            diffs = diffs_by_item[item_id]
            all_diffs.extend(diffs)
            agree = sum(1 for d in diffs if d <= AGREE_TOLERANCE) / len(diffs)
            status = ""
            if agree < RECALIBRATE_BELOW:
                status = "RECALIBRATE"
                recalibrate.append(item_id)
            print(f"{item_id:<18}{len(diffs):<5}"
                  f"{statistics.fmean(diffs):<12.3f}{agree:<11.0%}{status}")
        print("-" * 62)
        overall = (sum(1 for d in all_diffs if d <= AGREE_TOLERANCE)
                   / len(all_diffs))
        print(f"overall agreement (|diff| <= {AGREE_TOLERANCE}): "
              f"{overall:.0%} over {len(all_diffs)} comparisons")
        if recalibrate:
            print("recalibrate these items: " + ", ".join(recalibrate))
        else:
            print("no items below the recalibration threshold.")
        print()

    if cats_by_item:
        print("categorical agreement (Cohen's kappa on choice-item verdicts):")
        print(f"{'item':<18}{'n':<5}{'kappa':<8}{'observed':<10}")
        print("-" * 46)
        all_pairs = []
        for item_id in sorted(cats_by_item):
            pairs = cats_by_item[item_id]
            all_pairs.extend(pairs)
            kappa = cohens_kappa(pairs)
            observed = sum(1 for a, b in pairs if a == b) / len(pairs)
            print(f"{item_id:<18}{len(pairs):<5}{kappa:<8.3f}"
                  f"{observed:<10.0%}")
        print("-" * 46)
        print(f"overall kappa: {cohens_kappa(all_pairs):.3f} over "
              f"{len(all_pairs)} verdict pairs")
        print("kappa bands (Landis & Koch): <0 poor, 0-0.2 slight, "
              "0.2-0.4 fair, 0.4-0.6 moderate, 0.6-0.8 substantial, "
              "0.8-1.0 almost perfect")


if __name__ == "__main__":
    main()
