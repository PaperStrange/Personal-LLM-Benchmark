#!/usr/bin/env python3
"""Jev-powered judge for the LLM workflow eval pack.

Scores a candidate's task output against a rubric JSON using TypeSafe's Jev
(System One) model: one parallel system_one call, all rubric items as
questions at once.

Usage:
    export TYPESAFE_API_KEY=...
    pip install typesafe-sdk
    python src/llm_workflow_eval/judge/jev_judge.py --rubric rubrics/rubric-T1.json \
        --candidate results/t1-candidate-a.md [--inventory fixture/DEBT-INVENTORY.md]

For T2/T3, concatenate the deliverables into a single --candidate file first.

Scoring:
  - score items: normalized as score / (n_levels - 1)  (levels are ordered)
  - noul items: the 0-1 probability (inverted if the item sets "invert": true)
  - choice items: probability mass on the item's "target" option (skipped from
    the composite if the item has no "target")
  - composite = weighted mean of normalized values, scaled to 0-100
  - any item with confidence below the low-confidence threshold (default
    0.55; override with --low-conf-threshold) is flagged for senior-judge
    review

With --inventory, a deterministic debt-recall check runs alongside the Jev
scores: each `### Dn `+"`file:line`"+` anchor in the inventory is counted as
found if that exact file:line string appears in the candidate output.

Tier order (see README.md "Methodology"): run src/llm_workflow_eval/judge/t0_checks.py FIRST — it is
the free deterministic hard gate, and a T0 failure means no Jev spend. This
script is the second tier (cheap, one parallel call grades the whole rubric).
The third tier is the senior judge (src/llm_workflow_eval/judge/senior_judge_prompt.md), applied to
sampled runs plus every item flagged below the low-confidence threshold
(default 0.55; see --low-conf-threshold).

--json-out writes a machine-readable result for src/llm_workflow_eval/judge/aggregate.py
(pass@k / pass^k over repeated runs):
    {"task", "composite", "mean_confidence", "flagged", "items",
     "deterministic_recall", "est_cost_usd"}
"""
import argparse
import json
import os
import re
import sys
import uuid

STATE_CHAR_BUDGET = 50000
LOW_CONF_THRESHOLD = 0.55
JEV_INPUT_USD_PER_MTOK = 0.042
# Canonical fixture vintage; variant generators stamp v2-seed<N> instead.
CANON_VINTAGE = "v1-2026-09"


def eprint(*args):
    print(*args, file=sys.stderr)


def load_rubric(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["items"] if isinstance(data, dict) else data


def load_rubric_task(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("task") if isinstance(data, dict) else None


def parse_inventory(path):
    """Extract `file:line` anchors from ### Dn `file:line` headers."""
    anchors = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"### D\d+ `([^`]+)`", line.strip())
            if m:
                anchors.append(m.group(1))
    return anchors


def build_questions(items):
    from typesafe_sdk import Choice, Noul, Score

    questions = {}
    for it in items:
        kind = it["kind"]
        if kind == "score":
            questions[it["id"]] = Score(
                instructions=it["instructions"], criteria=it["criteria"]
            )
        elif kind == "choice":
            questions[it["id"]] = Choice(
                instructions=it["instructions"], criteria=it["criteria"]
            )
        elif kind == "noul":
            questions[it["id"]] = Noul(instructions=it["instructions"])
        else:
            raise ValueError(f"unknown rubric kind: {kind}")
    return questions


def normalize(item, answer):
    """Return (normalized 0-1 value or None, display string)."""
    kind = item["kind"]
    if kind == "score":
        n = len(item["criteria"])
        return answer.score / (n - 1), f"{answer.score:.2f}/{n - 1}"
    if kind == "noul":
        v = answer.noul
        if item.get("invert"):
            v = 1.0 - v
        return v, f"{answer.noul:.2f}"
    if kind == "choice":
        target = item.get("target")
        if not target:
            return None, f"{answer.choice}"
        probs = answer.probabilities or {}
        return float(probs.get(target, 0.0)), f"{answer.choice}"
    raise ValueError(f"unknown rubric kind: {kind}")


def main():
    ap = argparse.ArgumentParser(description="Jev judge for the eval pack")
    ap.add_argument("--rubric", required=True, help="rubric JSON file")
    ap.add_argument("--candidate", required=True, help="candidate output file")
    ap.add_argument(
        "--inventory",
        default=None,
        help="hidden debt inventory (enables deterministic recall check)",
    )
    ap.add_argument(
        "--json-out",
        default=None,
        help="write machine-readable result JSON for src/llm_workflow_eval/judge/aggregate.py",
    )
    ap.add_argument(
        "--low-conf-threshold",
        type=float,
        default=LOW_CONF_THRESHOLD,
        help="flag items with confidence below this value for senior review "
             f"(default {LOW_CONF_THRESHOLD}; uncalibrated heuristic — see "
             "README for the migration path to a target-agreement rule)",
    )
    ap.add_argument(
        "--fixture-vintage",
        default=None,
        help="fixture vintage this run was graded against. If omitted, it "
             "is auto-detected: a VINTAGE file next to --inventory stamps "
             "the variant (e.g. v2-seed7 — see "
             "tasks/t1-legacy-review/rotate_fixture.py); otherwise the "
             "canonical fixture vintage v1-2026-09 is assumed. Pass it "
             "explicitly whenever the inventory directory cannot speak for "
             "the fixture. Stamped into --json-out so src/llm_workflow_eval/judge/aggregate.py "
             "can refuse to mix vintages.",
    )
    args = ap.parse_args()

    if args.fixture_vintage is None:
        # Auto-detect from the inventory's directory: variant inventories
        # ship with a VINTAGE stamp file. A silent canonical default here
        # once let a variant run be mislabeled v1-2026-09 with no error —
        # the exact failure the vintage system exists to prevent.
        detected = CANON_VINTAGE
        if args.inventory:
            stamp = os.path.join(os.path.dirname(
                os.path.abspath(args.inventory)), "VINTAGE")
            if os.path.isfile(stamp):
                with open(stamp, encoding="utf-8") as f:
                    detected = f.read().strip()
        args.fixture_vintage = detected

    if not os.environ.get("TYPESAFE_API_KEY"):
        eprint("ERROR: TYPESAFE_API_KEY is not set.")
        sys.exit(2)
    try:
        from typesafe_sdk import TypeSafeClient
    except ImportError:
        eprint("ERROR: typesafe_sdk is not installed. Run: pip install typesafe-sdk")
        sys.exit(2)

    items = load_rubric(args.rubric)
    with open(args.candidate, encoding="utf-8") as f:
        candidate_output = f.read()

    inventory_text = ""
    if args.inventory:
        with open(args.inventory, encoding="utf-8") as f:
            inventory_text = f.read()

    # Truncate the candidate output (not the inventory) to fit the state budget.
    if len(candidate_output) + len(inventory_text) > STATE_CHAR_BUDGET:
        room = STATE_CHAR_BUDGET - len(inventory_text)
        eprint(
            f"WARNING: state exceeds ~{STATE_CHAR_BUDGET} chars; "
            f"truncating candidate output to {room} chars."
        )
        candidate_output = candidate_output[:room]

    state = {"candidate_output": candidate_output}
    if inventory_text:
        state["debt_inventory"] = inventory_text

    questions = build_questions(items)
    client = TypeSafeClient()
    response = client.system_one(state=state, questions=questions)

    rows = []
    wsum = 0.0
    wtotal = 0.0
    for it in items:
        ans = response.answers[it["id"]]
        conf = getattr(ans, "confidence", None)
        value, disp = normalize(it, ans)
        weight = float(it.get("weight", 1))
        if value is not None:
            wsum += value * weight
            wtotal += weight
        rows.append(
            {
                "id": it["id"],
                "kind": it["kind"],
                "result": disp,
                "conf": conf,
                "weight": weight,
                "value": value,
            }
        )

    print(f"{'id':<16}{'kind':<8}{'result':<16}{'conf':<8}{'wt':<4}{'norm'}")
    print("-" * 64)
    for r in rows:
        conf_s = f"{r['conf']:.2f}" if r["conf"] is not None else "n/a"
        norm_s = f"{r['value']:.2f}" if r["value"] is not None else "skip"
        print(
            f"{r['id']:<16}{r['kind']:<8}{r['result']:<16}"
            f"{conf_s:<8}{r['weight']:<4g}{norm_s}"
        )

    composite = (wsum / wtotal * 100.0) if wtotal else 0.0
    print("-" * 64)
    print(f"composite: {composite:.1f} / 100")

    confs = [r["conf"] for r in rows if r["conf"] is not None]
    if confs:
        print(f"mean confidence: {sum(confs) / len(confs):.2f}")

    threshold = args.low_conf_threshold
    flagged = [r["id"] for r in rows
               if r["conf"] is not None and r["conf"] < threshold]
    if flagged:
        print(f"LOW CONFIDENCE (< {threshold}) - send to senior judge: "
              + ", ".join(flagged))
    else:
        print("no low-confidence items.")

    recall = None
    if args.inventory:
        anchors = parse_inventory(args.inventory)
        found = [a for a in anchors if a in candidate_output]
        missing = [a for a in anchors if a not in candidate_output]
        pct = 100.0 * len(found) / len(anchors) if anchors else 0.0
        recall = {"found": len(found), "total": len(anchors),
                  "pct": round(pct, 1), "missed": missing}
        print(f"deterministic debt recall: {len(found)}/{len(anchors)} "
              f"({pct:.0f}%)")
        if missing:
            print("missed: " + ", ".join(missing))

    total_chars = len(candidate_output) + len(inventory_text)
    est_cost = total_chars / 4 / 1e6 * JEV_INPUT_USD_PER_MTOK
    print(f"est. judge cost: ~${est_cost:.4f} (output tokens are free)")

    if args.json_out:
        mean_conf = (sum(confs) / len(confs)) if confs else None
        payload = {
            "task": load_rubric_task(args.rubric),
            # Unique per invocation: lets src/llm_workflow_eval/judge/aggregate.py detect the same
            # rollout file being counted twice (copies share content but keep
            # the original run_id; independent rollouts never collide).
            "run_id": uuid.uuid4().hex,
            # Fixture vintage this run was graded against. aggregate.py
            # refuses to mix vintages: a composite averaged across the
            # canonical fixture and a rotated variant would be meaningless.
            "fixture_vintage": args.fixture_vintage,
            "composite": round(composite, 1),
            "mean_confidence": round(mean_conf, 2) if mean_conf is not None else None,
            "flagged": flagged,
            "items": [
                {"id": r["id"], "kind": r["kind"], "result": r["result"],
                 "conf": round(r["conf"], 3) if r["conf"] is not None else None,
                 "weight": r["weight"],
                 "value": round(r["value"], 4) if r["value"] is not None else None}
                for r in rows
            ],
            "deterministic_recall": recall,
            "est_cost_usd": round(est_cost, 4),
        }
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        print(f"wrote {args.json_out}")


if __name__ == "__main__":
    main()
