#!/usr/bin/env python3
"""T0 deterministic hard gate for the LLM workflow eval pack.

Cheap, necessary-condition checks on a candidate's task output. This is the
first tier of the methodology:

    T0 (free, deterministic, hard gate) -> Jev (cheap, judged) -> senior (sampled)

If T0 fails, the output does not deserve any Jev spend: fix the candidate run
and re-check. These checks are necessary conditions, NOT quality judgments —
a PASS here says "worth grading", not "good".

Usage:
    python judge/t0_checks.py --task T1 --candidate results/t1-a.md \
        --inventory fixture/DEBT-INVENTORY.md --workdir fixture/legacy-billing
    python judge/t0_checks.py --task T2 --candidate results/t2-a.md \
        --workdir /tmp/t2-run
    python judge/t0_checks.py --task T3 --candidate results/t3-report.md

Prints one [PASS]/[FAIL] line per check with a detail; [INFO] lines are
diagnostic only (never pass/fail). Exit code 0 iff every check passes.
"""
import argparse
import os
import re
import sys


# Maps a `xxx.py` name as cited by candidates to its real path under --workdir.
T1_REF_FILES = {
    "billing.py": "billing.py",
    "db.py": "db.py",
    "config.py": "config.py",
    "reports.py": "reports.py",
    "test_billing.py": os.path.join("tests", "test_billing.py"),
}

# The four sections the T1 prompt demands, as case-insensitive patterns.
T1_SECTIONS = {
    "architecture map": r"architect",
    "debt inventory": r"\bdebt\b",
    "risk register": r"\brisk\b",
    "30/60/90-day plan": r"30\s*/\s*60\s*/\s*90|30-60-90|moderniz",
}


def eprint(*args):
    print(*args, file=sys.stderr)


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def line_count(path):
    with open(path, encoding="utf-8") as f:
        return sum(1 for _ in f)


def check_candidate_file(path):
    """T0-a (all tasks): the candidate output exists and is non-empty."""
    if not os.path.isfile(path):
        return ("candidate_file", False, f"not found: {path}")
    size = os.path.getsize(path)
    if size == 0:
        return ("candidate_file", False, f"empty: {path}")
    return ("candidate_file", True, f"exists, {size} bytes")


def t1_checks(text, workdir):
    """Necessary conditions for a global project review."""
    out = []

    # (b) all four required sections present
    missing = [name for name, pat in T1_SECTIONS.items()
               if not re.search(pat, text, re.IGNORECASE)]
    if missing:
        out.append(("t1_sections", False,
                    "missing sections: " + ", ".join(missing)))
    else:
        out.append(("t1_sections", True,
                    "all four sections present (architecture, debt, risk, plan)"))

    # (c) no hallucinated file:line refs — cited line must exist in the file
    bounds = {}
    for name, rel in T1_REF_FILES.items():
        full = os.path.join(workdir, rel)
        if os.path.isfile(full):
            bounds[name] = line_count(full)
    bad = []
    for m in re.finditer(
            r"\b(billing|db|config|reports|test_billing)\.py:(\d+)", text):
        name, num = m.group(1) + ".py", int(m.group(2))
        if name not in bounds:
            bad.append(f"{name}:{num} (file not found under workdir)")
        elif num < 1 or num > bounds[name]:
            bad.append(f"{name}:{num} (file has {bounds[name]} lines)")
    if bad:
        out.append(("t1_refs_valid", False,
                    "out-of-range refs: " + "; ".join(bad[:5])))
    else:
        n = len(re.findall(
            r"\b(billing|db|config|reports|test_billing)\.py:\d+", text))
        out.append(("t1_refs_valid", True,
                    f"{n} file:line refs, all within file bounds"))
    return out


def t1_inventory_info(text, inventory_path):
    """(d) INFO only: raw anchor-hit count against the hidden inventory."""
    anchors = []
    for line in read_text(inventory_path).splitlines():
        m = re.match(r"### D\d+ `([^`]+)`", line.strip())
        if m:
            anchors.append(m.group(1))
    found = [a for a in anchors if a in text]
    return f"[INFO] inventory anchors cited: {len(found)}/{len(anchors)}"


def t2_checks(workdir):
    """Necessary conditions for the disciplined multi-agent build."""
    out = []

    # (a) PLAN.md exists in the workdir
    plan = os.path.join(workdir, "PLAN.md")
    if os.path.isfile(plan) and os.path.getsize(plan) > 0:
        out.append(("t2_plan_exists", True, f"PLAN.md present ({plan})"))
    else:
        out.append(("t2_plan_exists", False, f"PLAN.md missing/empty: {plan}"))

    # (b) REVIEW.md exists and carries a verdict
    review = os.path.join(workdir, "REVIEW.md")
    review_text = ""
    if os.path.isfile(review):
        review_text = read_text(review)
    if review_text and re.search(r"approve|request-changes", review_text,
                                 re.IGNORECASE):
        out.append(("t2_review_verdict", True,
                    "REVIEW.md contains a verdict (approve/request-changes)"))
    else:
        out.append(("t2_review_verdict", False,
                    f"REVIEW.md missing or has no verdict: {review}"))

    # (c) REVIEW.md contains test-run evidence (not just the implementer's word)
    if re.search(r"passed|failed|pytest|unittest|assert|\bok\b", review_text,
                 re.IGNORECASE):
        out.append(("t2_test_evidence", True,
                    "REVIEW.md shows test-run evidence"))
    else:
        out.append(("t2_test_evidence", False,
                    "REVIEW.md shows no test-run evidence"))

    # (d) apply_discount is actually implemented (stub removed)
    billing = os.path.join(workdir, "billing.py")
    if not os.path.isfile(billing):
        out.append(("t2_implemented", False, f"billing.py not found: {billing}"))
        return out
    src = read_text(billing)
    idx = src.find("def apply_discount")
    if idx == -1:
        out.append(("t2_implemented", False,
                    "apply_discount not defined in billing.py"))
    else:
        body = src[idx:]
        nxt = body.find("\ndef ", 1)
        if nxt != -1:
            body = body[:nxt]
        if "NotImplementedError" in body:
            out.append(("t2_implemented", False,
                        "apply_discount still raises NotImplementedError"))
        else:
            out.append(("t2_implemented", True,
                        "apply_discount body no longer a stub"))

    # (e) plan-before-code ordering: PLAN.md must predate the billing.py edit.
    # Catches the failure mode where a candidate writes the "plan" after the
    # fact in a single context (dry-run finding, 2026-09-22).
    plan_p = os.path.join(workdir, "PLAN.md")
    billing_p = os.path.join(workdir, "billing.py")
    if os.path.isfile(plan_p) and os.path.isfile(billing_p):
        if os.path.getmtime(plan_p) <= os.path.getmtime(billing_p):
            out.append(("t2_plan_before_code", True,
                        "PLAN.md predates the billing.py edit"))
        else:
            out.append(("t2_plan_before_code", False,
                        "PLAN.md is NEWER than billing.py: plan written after code"))
    return out


def t3_checks(text):
    """Necessary conditions for the expandability report."""
    out = []

    # (b) names a plugin AND a repo URL/host
    has_url = re.search(r"github\.com/|gitlab\.com/|https?://\S+", text)
    has_kind = re.search(r"plugin|skill|\bmcp\b", text, re.IGNORECASE)
    if has_url and has_kind:
        out.append(("t3_plugin_named", True,
                    f"names a plugin/skill/MCP and a repo host ({has_url.group(0)[:40]})"))
    else:
        out.append(("t3_plugin_named", False,
                    "must name a plugin/skill/MCP AND a repo URL/host"))

    # (c) states time-to-working
    if re.search(r"minute|hour", text, re.IGNORECASE):
        out.append(("t3_time_to_working", True, "states time-to-working"))
    else:
        out.append(("t3_time_to_working", False,
                    "no time-to-working stated (minutes/hours)"))

    # (d) states an outcome
    if re.search(r"worked|failed|success", text, re.IGNORECASE):
        out.append(("t3_outcome", True, "states an outcome"))
    else:
        out.append(("t3_outcome", False,
                    "no outcome stated (worked/failed/success)"))
    return out


def main():
    ap = argparse.ArgumentParser(
        description="T0 deterministic hard gate: exit 0 iff all checks pass.")
    ap.add_argument("--task", required=True, choices=["T1", "T2", "T3"])
    ap.add_argument("--candidate", required=True,
                    help="candidate output/report file")
    ap.add_argument("--inventory", default=None,
                    help="T1 only: hidden debt inventory (INFO count only)")
    ap.add_argument("--workdir", default="fixture/legacy-billing",
                    help="fixture or run working directory")
    args = ap.parse_args()

    results = [check_candidate_file(args.candidate)]
    text = read_text(args.candidate) if results[0][1] else ""

    if args.task == "T1":
        if results[0][1]:
            results.extend(t1_checks(text, args.workdir))
            if args.inventory:
                print(t1_inventory_info(text, args.inventory))
    elif args.task == "T2":
        results.extend(t2_checks(args.workdir))
    elif args.task == "T3":
        if results[0][1]:
            results.extend(t3_checks(text))

    all_pass = True
    for name, ok, detail in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
        all_pass = all_pass and ok

    print(f"T0 {args.task}: {'ALL CHECKS PASSED' if all_pass else 'GATE FAILED'} "
          f"({sum(1 for _, ok, _ in results if ok)}/{len(results)} checks)")
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
