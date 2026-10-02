#!/usr/bin/env python3
"""Gate 5: baseline protocols (tasks/BASELINES.md) with the local model.

- T1 baseline: ONE generation, task prompt + full fixture text, no tools.
- T2 baseline: ONE concatenated context playing planner -> implementer ->
  self-reviewer sequentially (no subagents, no separation). Discipline items
  requiring true role separation are marked N/A BY CONSTRUCTION.
- T3 baseline: the operator-executed Gate 3 rehearsal doubles as the human
  baseline; its t3_time (42s) is the number to beat.

Amendments to the documented protocol (recorded, not silent):
  A1. "Plain chat session" is simulated by prompt concatenation: `ollama run`
      is stateless, so the T2 single context is built by concatenating each
      turn's prompt+output. Information content is identical to one context.
  A2. T3 baseline: no candidate harness exists in the rehearsal, so the human
      installs into a temp-HOME sandbox (not "the harness's config"),
      scripted rather than by-hand for repeatability. Time-to-working still
      measured.
  A3. Generation is capped at 2500 tokens per turn (T1) via num_predict.
      The uncapped T1 attempt rambled past 6300 tokens / 900s without
      terminating; a real harness sets max tokens, so the cap is the honest
      backstop, not output selection.

Usage:
    python3 tools/qualification/baseline_driver.py --out results/qualification/baselines
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

PACK = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(PACK, "tools", "qualification"))
from gate2_driver import (Run, snapshot, extract, ollama_generate, clean,  # noqa: E402
                          unified_diff, PLANNER_PROMPT, IMPLEMENTER_PROMPT)

MODEL = "qwen2.5-1.5b-local"
SEED = 7  # same planted bugs as the harnessed runs: paired comparison

T1_BASELINE_PROMPT = """{task}

You have no tools and no code execution. Below is the full text of every
file in fixture/legacy-billing/. Write the review document now.

{tree}
"""


def t1_baseline(out):
    task = open(os.path.join(PACK, "tasks", "T1-global-review.md")).read()
    tree = snapshot(os.path.join(PACK, "fixture", "legacy-billing"))
    prompt = T1_BASELINE_PROMPT.format(task=task, tree=tree)
    with open(os.path.join(out, "t1-prompt.txt"), "w") as f:
        f.write(prompt)
    t0 = time.time()
    # Capped: the uncapped attempt rambled past 6300 tokens / 900s without
    # terminating. A real harness sets max tokens; the cap is the honest
    # backstop. Recorded as amendment A3.
    text = ollama_generate(prompt, timeout=600, num_predict=2500)
    dt = time.time() - t0
    cand = os.path.join(out, "T1-baseline-qwen.md")
    with open(cand, "w") as f:
        f.write(clean(text))
    p0 = subprocess.run(
        [sys.executable, os.path.join(PACK, "judge", "t0_checks.py"),
         "--task", "T1", "--candidate", cand,
         "--inventory", os.path.join(PACK, "fixture", "DEBT-INVENTORY.md"),
         "--workdir", os.path.join(PACK, "fixture", "legacy-billing")],
        capture_output=True, text=True, cwd=PACK)
    p1 = subprocess.run(
        [sys.executable, os.path.join(PACK, "judge", "jev_judge.py"),
         "--rubric", os.path.join(PACK, "rubrics", "rubric-T1.json"),
         "--candidate", cand,
         "--inventory", os.path.join(PACK, "fixture", "DEBT-INVENTORY.md"),
         "--json-out", os.path.join(out, "t1-baseline-payload.json")],
        capture_output=True, text=True, cwd=PACK,
        env={**os.environ,
             "PYTHONPATH": os.path.join(PACK, "tests", "helpers",
                                        "mock_typesafe"),
             "MOCK_RUN": "1", "TYPESAFE_API_KEY": "dryrun"})
    m = re.search(r"deterministic debt recall:\s*(\S+)", p1.stdout)
    note = {"model": MODEL, "wall_s": round(dt, 1),
            "t0_pass": p0.returncode == 0,
            "deterministic_recall": m.group(1) if m else None,
            "chars": len(text)}
    with open(os.path.join(out, "t1-baseline-note.json"), "w") as f:
        json.dump(note, f, indent=2)
    print("T1 baseline: t0=%s recall=%s (%.0fs)"
          % (note["t0_pass"], note["deterministic_recall"], dt))
    return note


def t2_baseline(out):
    """One context, three turns. The reviewer IS the implementer (self-review)."""
    bdir = os.path.join(out, "t2")
    os.makedirs(os.path.join(bdir, "prompts"), exist_ok=True)
    run = Run(bdir, seed=SEED)
    run.trace_fh = open(os.path.join(bdir, "trace.jsonl"), "w",
                        encoding="utf-8")
    try:
        run.plant()
        snap = snapshot(run.tree)
        originals = {}
        for root, _d, files in os.walk(run.tree):
            _d[:] = [d for d in _d if d != "__pycache__"]
            for fn in files:
                fp = os.path.join(root, fn)
                try:
                    with open(fp, encoding="utf-8") as f:
                        originals[os.path.relpath(fp, run.tree)] = f.read()
                except (UnicodeDecodeError, OSError):
                    continue

        # Turn 1 — plan (same prompt as the harnessed planner).
        p1 = PLANNER_PROMPT.format(tree=snap)
        o1 = clean(ollama_generate(p1, timeout=600, num_predict=2500))
        plan = extract(o1, "<<<PLAN>>>", "<<<END>>>")
        with open(os.path.join(run.tree, "PLAN.md"), "w") as f:
            f.write(plan + "\n")
        with open(os.path.join(bdir, "prompts", "t2-prompt-t1.txt"), "w") as f:
            f.write(p1)
        run.log("baseline", "turn", "plan", "ok",
                note="single context, chars=%d" % len(o1))

        # Turn 2 — implement, WITH the plan turn in context (no separation).
        impl_core = IMPLEMENTER_PROMPT.format(plan=plan, tree=snap)
        impl_core = impl_core.split("You are the IMPLEMENTER", 1)[1]
        p2 = (p1 + "\n\nYOUR PLAN OUTPUT:\n" + o1
              + "\n\nNow implement your plan.\nYou are the IMPLEMENTER"
              + impl_core)
        o2 = clean(ollama_generate(p2, timeout=600, num_predict=2500))
        blocks = re.findall(r"<<<(?:FILE:)?([^<>\n]+?)>>>\s*\n(.*?)<<<END>>>",
                            o2, re.DOTALL)
        good = [(r.strip(), c) for r, c in blocks
                if r.strip() and ".." not in r and not r.strip().startswith("/")
                and re.fullmatch(r"[A-Za-z0-9_./-]+", r.strip())]
        if not good:
            raise RuntimeError("baseline implementer emitted no file blocks")
        for rel, content in good:
            dest = os.path.join(run.tree, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "w") as f:
                f.write(content.strip() + "\n")
        with open(os.path.join(bdir, "prompts", "t2-prompt-t2.txt"), "w") as f:
            f.write(p2)
        run.log("baseline", "turn", "implement", "ok",
                note="files=%d" % len(good))

        # Turn 3 — self-review: the SAME context reviews its own work.
        diff = unified_diff(run.tree, originals)
        p3 = (p2 + "\n\nYOUR IMPLEMENTATION OUTPUT (file blocks):\n" + o2
              + "\n\nNow write REVIEW.md reviewing YOUR OWN work above. "
                "You saw the code being written (no independent reviewer). "
                "Output ONLY the REVIEW.md content between <<<REVIEW>>> and "
                "<<<END>>> markers, starting with a line "
                "`VERDICT: APPROVE` or `VERDICT: REQUEST-CHANGES`.")
        o3 = clean(ollama_generate(p3, timeout=600, num_predict=2500))
        review = extract(o3, "<<<REVIEW>>>", "<<<END>>>")
        with open(os.path.join(run.tree, "REVIEW.md"), "w") as f:
            f.write(review + "\n")
        with open(os.path.join(bdir, "prompts", "t2-prompt-t3.txt"), "w") as f:
            f.write(p3)
        run.log("baseline", "turn", "self-review", "ok",
                note="BY CONSTRUCTION: reviewer==implementer")

        candidate = run.write_deliverable(plan, diff,
                                          "(no separate test run)", review)
        grading = run.grade(review, candidate)
        note = {
            "model": MODEL, "seed": SEED,
            "by_construction": [
                "t2_roles: FAIL/N/A — planner, implementer, reviewer are one context",
                "reviewer saw the code being written; self-approval unavoidable",
            ],
            "grading": grading,
        }
        with open(os.path.join(bdir, "t2-baseline-note.json"), "w") as f:
            json.dump(note, f, indent=2, default=str)
        print("T2 baseline: green=%s t0=%s hidden=%s coord=%s" % (
            grading["green"], grading["t0_pass"], grading["hidden_pass"],
            {k: v["identified"] for k, v in grading["coord"].items()}))
        return note
    finally:
        run.trace_fh.close()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", choices=["t1", "t2"], default=None)
    args = ap.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)
    if args.only in (None, "t1"):
        t1_baseline(args.out)
    if args.only in (None, "t2"):
        t2_baseline(args.out)
    print("BASELINES DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
