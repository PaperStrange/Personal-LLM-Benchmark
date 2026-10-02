"""Regression test for the anchor-hygiene finding (dry run 2026-09-22, F1).

The deterministic T1 debt-recall check matches hidden-inventory anchors
(`### Dn \\`file:line\\``) by exact string. If a fixture edit shifts line
numbers, recall measurement silently corrupts. This test re-verifies every
anchor against the real fixture: 22 anchors, each pointing at a line that
exists AND exhibiting the expected flaw (the `Expect:` substring under each
inventory entry). Phase 1 review found the old test only checked the line
*exists* — a wrong-line anchor like the original D15 (billing.py:15 instead
of :19) passed silently. Human review was the only gate; now it isn't.
"""
import os
import re
import unittest

PACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INVENTORY = os.path.join(PACK, "fixture", "DEBT-INVENTORY.md")
FIXTURE = os.path.join(PACK, "fixture", "legacy-billing")

ANCHOR_RE = re.compile(r"^### D\d+ `([^`]+)`")
EXPECT_RE = re.compile(r"^Expect:\s*(.+)$")

# Candidate-visible citation name -> real path under the fixture.
PATH_MAP = {
    "billing.py": "billing.py",
    "db.py": "db.py",
    "config.py": "config.py",
    "reports.py": "reports.py",
    "test_billing.py": os.path.join("tests", "test_billing.py"),
    "requirements.txt": "requirements.txt",
}

EXPECTED_ANCHOR_COUNT = 22


def parse_inventory(path=INVENTORY):
    """Return [(anchor, expect_substring, expect_context)] per ### Dn entry.

    expect_context is the `~ in <enclosing-def>` qualifier (None when the
    anchored line is textually unique in its file).
    """
    entries = []
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            m = ANCHOR_RE.match(line)
            if m:
                entries.append([m.group(1), None, None])
                continue
            m = EXPECT_RE.match(line)
            if m and entries:
                expect = m.group(1).strip()
                if " ~ in " in expect:
                    sub, _, ctx = expect.partition(" ~ in ")
                    entries[-1][1:] = [sub.strip(), ctx.strip()]
                else:
                    entries[-1][1] = expect
    return [(a, s, c) for a, s, c in entries]


def parse_anchors(path=INVENTORY):
    return [a for a, _, _ in parse_inventory(path)]


def fixture_lines(anchor, fixture_dir=FIXTURE):
    base = os.path.basename(anchor).split(":")[0]
    if base not in PATH_MAP:
        raise AssertionError("anchor cites a file outside the fixture map")
    full = os.path.join(fixture_dir, PATH_MAP[base])
    if not os.path.isfile(full):
        raise AssertionError("fixture file missing: %s" % full)
    with open(full, encoding="utf-8") as f:
        return f.read().splitlines()


def anchored_line(anchor, fixture_dir=FIXTURE):
    lines = fixture_lines(anchor, fixture_dir)
    num = int(os.path.basename(anchor).split(":")[1])
    if not 1 <= num <= len(lines):
        raise AssertionError(
            "%s cites line %d but the file has %d lines (fixture drift!)"
            % (anchor, num, len(lines)))
    return lines[num - 1]


def assert_anchor_content(anchor, expect, context, fixture_dir=FIXTURE):
    """The anchor's line must exhibit the expected flaw (and, when the
    anchored line is textually duplicated in the file, belong to the
    expected enclosing function)."""
    if expect is None:
        raise AssertionError("%s has no Expect: line in the inventory"
                             % anchor)
    line = anchored_line(anchor, fixture_dir)
    if expect not in line:
        raise AssertionError(
            "%s: expected substring %r not found on anchored line %r"
            % (anchor, expect, line))
    if context is not None:
        lines = fixture_lines(anchor, fixture_dir)
        num = int(os.path.basename(anchor).split(":")[1])
        defs = [l for l in lines[:num] if l.startswith("def ")]
        if not defs or not defs[-1].startswith("def " + context):
            raise AssertionError(
                "%s: anchored line is inside %r, expected enclosing "
                "function %r (textually identical lines exist elsewhere)"
                % (anchor, defs[-1] if defs else None, context))


def line_count(path):
    with open(path, encoding="utf-8") as f:
        return sum(1 for _ in f)


def verify_pair(fixture_dir=FIXTURE, inventory_path=INVENTORY):
    """Full anchor verification for one (fixture_dir, inventory_path) pair.

    Used by the canonical suite (defaults) and by tests/test_rotation.py for
    generated vintages. Raises AssertionError describing the first problem.
    """
    entries = parse_inventory(inventory_path)
    if len(entries) != EXPECTED_ANCHOR_COUNT:
        raise AssertionError(
            "inventory anchor count changed: %d (expected %d)"
            % (len(entries), EXPECTED_ANCHOR_COUNT))
    anchors = [a for a, _, _ in entries]
    if len(set(anchors)) != len(anchors):
        raise AssertionError("duplicate anchors: %r" % anchors)
    for anchor, expect, context in entries:
        base = os.path.basename(anchor).split(":")[0]
        if base not in PATH_MAP:
            raise AssertionError(
                "anchor cites a file outside the fixture map: %s" % anchor)
        full = os.path.join(fixture_dir, PATH_MAP[base])
        if not os.path.isfile(full):
            raise AssertionError("fixture file missing: %s" % full)
        total = line_count(full)
        num = int(os.path.basename(anchor).split(":")[1])
        if not 1 <= num <= total:
            raise AssertionError(
                "%s cites line %d but the file has %d lines (fixture drift!)"
                % (anchor, num, total))
        assert_anchor_content(anchor, expect, context,
                              fixture_dir=fixture_dir)


class AnchorHygieneTest(unittest.TestCase):
    def test_anchor_count(self):
        anchors = parse_anchors()
        self.assertEqual(
            len(anchors), EXPECTED_ANCHOR_COUNT,
            "inventory anchor count changed: %d (expected %d). "
            "If you edited the fixture, update EXPECTED_ANCHOR_COUNT and "
            "re-verify every anchor." % (len(anchors), EXPECTED_ANCHOR_COUNT))
        self.assertEqual(len(set(anchors)), len(anchors),
                         "duplicate anchors: %r" % anchors)

    def test_anchor_shape(self):
        for anchor in parse_anchors():
            with self.subTest(anchor=anchor):
                m = re.match(r"^(?:[\w.\-]+/)*([\w\-]+\.\w+):(\d+)$", anchor)
                self.assertIsNotNone(m, "anchor not in file:line form")

    def test_anchors_point_at_real_lines(self):
        for anchor in parse_anchors():
            with self.subTest(anchor=anchor):
                base, num = os.path.basename(anchor).split(":")
                num = int(num)
                self.assertIn(base, PATH_MAP,
                              "anchor cites a file outside the fixture map")
                full = os.path.join(FIXTURE, PATH_MAP[base])
                self.assertTrue(os.path.isfile(full),
                                "fixture file missing: %s" % full)
                total = line_count(full)
                self.assertGreaterEqual(num, 1, "line number < 1")
                self.assertLessEqual(
                    num, total,
                    "%s has %d lines but anchor cites line %d "
                    "(fixture drift!)" % (base, total, num))

    def test_anchors_exhibit_expected_content(self):
        # The Phase 1 gap: existence alone let a wrong-line anchor through.
        for anchor, expect, context in parse_inventory():
            with self.subTest(anchor=anchor):
                try:
                    assert_anchor_content(anchor, expect, context)
                except AssertionError as e:
                    self.fail(str(e))

    def test_every_entry_has_expect_line(self):
        missing = [a for a, s, _ in parse_inventory() if not s]
        self.assertEqual(missing, [],
                         "inventory entries without an Expect: line: %r"
                         % missing)


if __name__ == "__main__":
    unittest.main()
