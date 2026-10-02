#!/usr/bin/env python3
"""Plant subtle, reviewer-catchable bugs into a disposable COPY of the T2 fixture.

Operational use: each T2 multi-agent run gets a fresh fixture copy with 2
seeded subtle bugs, so rubric-T2.json's coordination items (t2_coord_1,
t2_coord_2) can grade whether the reviewer's REVIEW.md actually caught them.
This is the MARBLE-style coordination-quality upgrade described in
docs/landscape.md item 19: grade coordination, not just
artifacts.

SAFETY: this script copies src -> dest itself and never modifies the source
tree. It refuses a dest inside src. The canonical fixture/ tree (and therefore
every DEBT-INVENTORY.md anchor) is never touched — a regression test
(tests/test_plant_bugs.py) asserts byte-identical fixture files after planting.

Usage:
    python tasks/t2-discount-fix/plant_bugs.py \
        --src fixture/legacy-billing --dest /tmp/t2-run-copy \
        --seed 7 [--manifest tasks/t2-discount-fix/plant_manifest.json]

    Selection: random.Random(seed).sample(CATALOG, 2). --bugs id1,id2
    overrides the seed with an explicit selection (used by the regression
    suite to exercise each catalog entry).

    --verify --dest X --manifest M re-checks that every manifest bug's
    signature is present at its recorded file:line in the copy (the pack's
    own "did the planting actually land" check).

The manifest is JUDGES ONLY (gitignored): it maps bug id -> file:line ->
description. Never show it to a candidate, never ship it with the task.
"""
import argparse
import json
import os
import random
import shutil
import sys

# Each entry: a precise, unique original substring and its buggy replacement.
# "signature" is the planted string a checker asserts on; "detect" names the
# behavioral check the regression suite runs for that bug.
CATALOG = [
    {
        "id": "off_by_one_qty",
        "file": "billing.py",
        "original": '        subtotal += it["price"] * it["qty"]',
        "planted": '        subtotal += it["price"] * (it["qty"] + 1)',
        "signature": 'it["price"] * (it["qty"] + 1)',
        "description": (
            "Off-by-one in generate_invoice: each line item is billed for "
            "qty+1 units, inflating every subtotal. A reviewer re-running "
            "the numbers (or the fixture's own tests) catches it; skimming "
            "the diff does not."
        ),
        "detect": "generate_invoice(7, [{'sku':'W','price':10.0,'qty':2}])"
                  "['subtotal'] == 30.0 (clean tree gives 20.0)",
    },
    {
        "id": "swapped_tax_rates",
        "file": "config.py",
        "original": 'TAX_RATES = {"CA": 0.0725, "NY": 0.08, "TX": 0.0625}',
        "planted": 'TAX_RATES = {"CA": 0.0625, "NY": 0.08, "TX": 0.0725}',
        "signature": '"CA": 0.0625',
        "description": (
            "Swapped CA/TX tax rates in config.py: California invoices are "
            "under-taxed, Texas invoices over-taxed. Only a reviewer who "
            "checks config values against a known-good reference catches it."
        ),
        "detect": "calculate_tax(100.0, 'CA') == 6.25 (clean tree gives 7.25)",
    },
    {
        "id": "dropped_none_guard",
        "file": "billing.py",
        "original": "    return rows[0] if rows else None",
        "planted": "    return rows[0]",
        "signature": "return rows[0]",
        "description": (
            "Dropped None-guard in get_invoice: unknown invoice ids now "
            "raise IndexError instead of returning None. The T2 task "
            "explicitly requires handling unknown invoice_id, so a reviewer "
            "exercising that edge case catches it."
        ),
        "detect": "get_invoice(<unknown>) raises IndexError with run_query "
                  "stubbed to []; clean tree returns None",
    },
]

DEFAULT_MANIFEST = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "plant_manifest.json")


def eprint(*args):
    print(*args, file=sys.stderr)


def _inside(child, parent):
    # realpath (not abspath): the guard must see through symlinks, or src
    # passed via an unresolved alias defeats the dest-inside-src check.
    try:
        return os.path.commonpath(
            [os.path.realpath(child), os.path.realpath(parent)]
        ) == os.path.realpath(parent)
    except ValueError:
        return False


def plant(src, dest, seed=0, bug_ids=None, manifest_path=None):
    """Copy src -> dest, plant 2 (or bug_ids) bugs, write the manifest.

    Returns the manifest dict.
    """
    src = os.path.realpath(src)
    dest = os.path.realpath(dest)
    if _inside(dest, src):
        raise ValueError(
            "refusing: dest %r is inside src %r (would endanger the "
            "canonical fixture)" % (dest, src))
    if os.path.exists(dest):
        raise ValueError("refusing: dest %r already exists" % dest)
    if manifest_path is None:
        manifest_path = DEFAULT_MANIFEST

    if bug_ids is not None:
        wanted = [b.strip() for b in bug_ids.split(",") if b.strip()]
        selected = [b for b in CATALOG if b["id"] in wanted]
        unknown = set(wanted) - {b["id"] for b in selected}
        if unknown:
            raise ValueError("unknown bug ids: %s" % sorted(unknown))
    else:
        selected = random.Random(seed).sample(CATALOG, 2)

    shutil.copytree(src, dest)

    # Apply in catalog order so overlapping targets (none today) stay
    # deterministic regardless of selection order.
    planted = []
    for bug in CATALOG:
        if bug["id"] not in {b["id"] for b in selected}:
            continue
        path = os.path.join(dest, bug["file"])
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
        hits = [i for i, ln in enumerate(lines) if bug["original"] in ln]
        if len(hits) != 1:
            raise RuntimeError(
                "bug %r: expected exactly 1 occurrence of the original "
                "string in %s, found %d — fixture drifted; refusing to "
                "plant blindly" % (bug["id"], bug["file"], len(hits)))
        lineno = hits[0] + 1  # 1-based, matches DEBT-INVENTORY.md convention
        lines[hits[0]] = lines[hits[0]].replace(bug["original"],
                                                bug["planted"], 1)
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        planted.append({
            "id": bug["id"],
            "file": bug["file"],
            "line": lineno,
            "original": bug["original"],
            "planted": bug["planted"],
            "signature": bug["signature"],
            "description": bug["description"],
        })

    manifest = {
        "_judges_only": ("JUDGES ONLY — never show to candidates or ship "
                         "with candidate-facing task materials."),
        "seed": seed,
        "bugs": planted,
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    return manifest


def verify(dest, manifest_path):
    """Re-check every manifest bug's signature at its recorded file:line."""
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    problems = []
    for bug in manifest["bugs"]:
        path = os.path.join(os.path.abspath(dest), bug["file"])
        try:
            with open(path, encoding="utf-8") as f:
                lines = f.readlines()
        except OSError as exc:
            problems.append("%s: cannot read %s: %s"
                            % (bug["id"], bug["file"], exc))
            continue
        lineno = bug["line"]
        if not (1 <= lineno <= len(lines)):
            problems.append("%s: line %d out of range in %s"
                            % (bug["id"], lineno, bug["file"]))
            continue
        if bug["signature"] not in lines[lineno - 1]:
            problems.append(
                "%s: signature %r not on %s:%d"
                % (bug["id"], bug["signature"], bug["file"], lineno))
        if bug["original"] in "".join(lines):
            problems.append("%s: original string still present in %s"
                            % (bug["id"], bug["file"]))
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--src", required=True)
    ap.add_argument("--dest", required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--bugs",
                    help="comma-separated catalog ids; overrides --seed")
    ap.add_argument("--manifest", default=None)
    ap.add_argument("--verify", action="store_true",
                    help="verify a previous planting instead of planting")
    args = ap.parse_args(argv)

    manifest_path = args.manifest or DEFAULT_MANIFEST
    if args.verify:
        problems = verify(args.dest, manifest_path)
        if problems:
            for p in problems:
                eprint("VERIFY FAIL:", p)
            return 1
        print("verify OK: %s" % manifest_path)
        return 0

    if args.bugs is not None:
        n = len([b for b in args.bugs.split(",") if b.strip()])
        if n != 2:
            eprint("WARNING: --bugs plants %d bug(s); the T2 rubric expects "
                   "exactly 2 planted bugs per run. This override is for the "
                   "regression suite only — do not use it in real runs." % n)

    manifest = plant(args.src, args.dest, seed=args.seed,
                     bug_ids=args.bugs, manifest_path=manifest_path)
    for bug in manifest["bugs"]:
        print("planted %-18s %s:%d" % (bug["id"], bug["file"], bug["line"]))
    print("manifest (JUDGES ONLY): %s" % manifest_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
