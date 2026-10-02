#!/usr/bin/env python3
"""Leakage audit: does the fixture itself spell out the hidden answer key?

For each `### Dn `+"`file:line`"+` section in fixture/DEBT-INVENTORY.md, take
the section title (the prose after the anchor) and check whether any run of
4+ consecutive title words appears verbatim in the corresponding fixture
file. A hit means the candidate could read the answer in the code's
comments/docstrings instead of discovering the debt itself.

This is a narrow, verbatim-only check (v1). It does not catch paraphrased
leakage — keeping the inventory's prose distinct from the fixture's prose
remains the reviewer's job. Run it whenever the fixture or the inventory
changes.

Usage:
    python src/llm_workflow_eval/judge/leakage_audit.py [--inventory fixture/DEBT-INVENTORY.md]
                                  [--workdir fixture/legacy-billing]
Exit 0: all clear. Exit 1: one or more verbatim leaks found.
"""
import argparse
import os
import re
import sys

SECTION_RE = re.compile(r"^### D\d+ `([^`]+)`\s*[-\u2013\u2014]\s*(.+)$")
NGRAM = 4  # consecutive title words that must not appear verbatim


def eprint(*args):
    print(*args, file=sys.stderr)


def normalize(text):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9_ ]", " ", text.lower()))


def title_phrases(title):
    words = normalize(title).split()
    if len(words) < NGRAM:
        return [" ".join(words)] if words else []
    return [" ".join(words[i:i + NGRAM]) for i in range(len(words) - NGRAM + 1)]


def parse_inventory(path):
    sections = []  # (anchor_file, title)
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = SECTION_RE.match(line.rstrip("\n"))
            if m:
                anchor, title = m.group(1), m.group(2)
                anchor_file = anchor.split(":")[0]
                sections.append((anchor_file, title))
    return sections


def main():
    ap = argparse.ArgumentParser(
        description="Check the hidden debt inventory isn't spelled out "
                    "verbatim in the fixture.")
    ap.add_argument("--inventory", default="fixture/DEBT-INVENTORY.md")
    ap.add_argument("--workdir", default="fixture/legacy-billing")
    args = ap.parse_args()

    if not os.path.isfile(args.inventory):
        eprint(f"inventory not found: {args.inventory}")
        sys.exit(2)

    sections = parse_inventory(args.inventory)
    if not sections:
        eprint("no Dn sections parsed from the inventory — check the format.")
        sys.exit(2)

    leaks = []
    for anchor_file, title in sections:
        fpath = os.path.join(args.workdir, anchor_file)
        if not os.path.isfile(fpath):
            eprint(f"warning: anchor target missing: {fpath}")
            continue
        with open(fpath, encoding="utf-8", errors="replace") as f:
            body = normalize(f.read())
        for phrase in title_phrases(title):
            if phrase and phrase in body:
                leaks.append((anchor_file, title, phrase))

    if leaks:
        print(f"LEAKS FOUND: {len(leaks)}")
        for anchor_file, title, phrase in leaks:
            print(f"  [LEAK] {anchor_file}: title {title!r} contains "
                  f"verbatim phrase {phrase!r} present in the fixture file")
        sys.exit(1)

    print(f"ALL CLEAR: {len(sections)} inventory sections, no verbatim "
          f"title phrases found in fixture files.")
    sys.exit(0)


if __name__ == "__main__":
    main()
