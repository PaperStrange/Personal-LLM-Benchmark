#!/usr/bin/env python3
"""Fixture variant generator: deterministic identifier rotation (Phase 4a).

Produces a fixture VARIANT from the canonical `fixture/` tree: every file
under `fixture/legacy-billing/*.py` is copied with a defined set of Python
identifiers renamed (function names, module constants, locals/params),
driven by `--seed`. The generator emits a variant PAIR:

    <out>/legacy-billing/      renamed code tree (same layout, same line numbers)
    <out>/DEBT-INVENTORY.md    remapped answer key (anchors unchanged)
    <out>/VINTAGE              vintage stamp, e.g. "v2-seed7"

Usage:
    python tasks/t1-legacy-review/rotate_fixture.py --seed 7
    python tasks/t1-legacy-review/rotate_fixture.py --seed 7 \\
        --out /tmp/v2-seed7

Why rotation exists: a candidate that has memorized the canonical fixture
verbatim (names like `generate_invoice`, `TAX_RATES`) should not get free
recall. Renaming breaks verbatim matching while preserving behavior, so the
T1 task still measures debt discovery, not memorization.

DESIGN DECISIONS (documented, not incidental)
--------------------------------------------
1. Which identifiers are renamed: ~50 function names, module-level config
   constants, and local/parameter names across the five fixture .py files —
   enough that verbatim-memorized code no longer matches, small enough to
   stay mechanically correct. String literals, dict keys, SQL text, comments
   and docstrings are NEVER renamed (they are data/prose, and SQL column
   names must keep working).
2. What is NOT renamed: `apply_discount`, `invoice_id`, `pct`. These are the
   T2 task's contract surface (`tasks/T2-multi-agent.md` pins
   `apply_discount(invoice_id, pct)`); renaming them would silently change
   the task spec. The variant's T2 task is identical to canonical.
3. Titles and body prose are remapped conservatively: ONLY bare identifiers
   inside backtick code spans, and ONLY when the new name provably occurs in
   the variant code. English words that happen to match a rename key ("tax",
   "name", "s"), possessives, and dotted/API references such as
   `datetime.datetime.now()` are left verbatim — an earlier word-boundary
   regex rewrote those and produced false statements in the judge's answer
   key (e.g. `datetime.datetime.current_time()`). Compound code expressions
   keep their original wording; the machine-verified `Expect:` lines carry
   the exact remapped substrings, so judges always have ground truth.
4. `Expect:` lines are remapped via Python tokenization of the anchored
   line's code tokens and VERIFIED against the renamed anchored line: the
   new Expect must be a substring of the renamed line. When the Expect
   refers to text the renamer deliberately left alone (e.g. D4's SQL string
   `WHERE name = '%s'`, D8's docstring prose), the original Expect is kept —
   but only if it still matches the renamed line. Anything else is a hard
   error, not a silent pass.
5. Renaming is within-line identifier substitution only: no lines are added,
   removed, or reordered, so every `file:line` anchor keeps pointing at the
   same logical line. The suite asserts identical line counts per file.
6. Vintage naming: the canonical fixture is `v1-2026-09`. Variants are
   `v2-seed<seed>`. Rotate per candidate campaign (fresh seed), never reuse
   a vintage across campaigns whose scores will be compared.
7. The generator REFUSES to write into the canonical tree (same realpath
   guard discipline as plant_bugs.py) and refuses an existing dest.

Evidence labels: the rotation PROCEDURE is [REAL] (this script, tested).
Its EFFECTIVENESS against memorization is [OPEN] — we have not measured a
memorized model scoring lower on a variant, and we state that plainly.

Method: AST-based edit collection (ast.Name / arg / FunctionDef /
Attribute / import alias nodes), edits applied right-to-left per line on
UTF-8 bytes using node column offsets (byte offsets in CPython), then the
renamed source is re-parsed AND compiled. Attribute renames use
value.end_col_offset (the dot position) because Attribute.col_offset points
at the value, not the attribute name.
"""
import argparse
import ast
import io
import keyword
import os
import random
import re
import shutil
import sys
import tokenize

PACK = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
FIXTURE_DIR = os.path.join(PACK, "fixture")
CODE_DIR = os.path.join(FIXTURE_DIR, "legacy-billing")
CANON_INVENTORY = os.path.join(FIXTURE_DIR, "DEBT-INVENTORY.md")

CANON_VINTAGE = "v1-2026-09"
DEFAULT_OUT = os.path.join(FIXTURE_DIR, "variants", "v2-seed{seed}")

# ---------------------------------------------------------------- pools
# canonical identifier -> plausible alternatives. The seeded choice below
# must never collide with an unrenamed identifier (checked programmatically).
POOLS = {
    # functions
    "generate_invoice": ["build_invoice", "make_invoice", "issue_invoice",
                         "draft_invoice", "new_invoice"],
    "calculate_tax": ["compute_tax", "calc_tax", "tax_for", "get_tax_amount",
                      "figure_tax"],
    "save_invoice": ["store_invoice", "persist_invoice", "write_invoice",
                     "insert_invoice"],
    "get_invoice": ["fetch_invoice", "load_invoice", "read_invoice",
                    "retrieve_invoice"],
    "list_invoices": ["find_invoices", "query_invoices", "search_invoices",
                      "all_invoices"],
    "send_invoice_email": ["email_invoice", "mail_invoice", "dispatch_invoice",
                           "notify_by_email"],
    "void_invoice": ["cancel_invoice", "invalidate_invoice", "retract_invoice"],
    "charge_invoice": ["bill_invoice", "collect_payment", "process_charge"],
    "_post_charge": ["_submit_charge", "_send_charge", "_push_charge"],
    "_gateway_call": ["_gateway_request", "_call_gateway", "_http_charge"],
    "get_conn": ["open_conn", "new_connection", "connect_db", "db_connect"],
    "run_query": ["exec_query", "execute_sql", "db_query", "raw_query"],
    "find_customer": ["lookup_customer", "get_customer_by_name",
                      "search_customer"],
    "init_schema": ["setup_schema", "create_tables", "ensure_schema",
                    "bootstrap_schema"],
    "export_invoices": ["dump_invoices", "write_invoice_export",
                        "backup_invoices"],
    "get_analytics_conn": ["open_analytics_conn", "reporting_conn",
                           "analytics_connect"],
    "monthly_report": ["month_report", "monthly_summary", "report_for_month"],
    "customer_totals": ["totals_by_customer", "customer_sums",
                        "per_customer_totals"],
    "invoice_age_days": ["days_since_issued", "invoice_age", "aging_days"],
    "_tax": ["_compute_tax", "_tax_for", "_rate_tax"],
    # config constants
    "SECRET_KEY": ["APP_SECRET", "MASTER_KEY", "SECRET_TOKEN"],
    "API_TOKEN": ["SERVICE_TOKEN", "ACCESS_TOKEN", "API_SECRET"],
    "SMTP_HOST": ["MAIL_HOST", "SMTP_SERVER", "EMAIL_HOST"],
    "SMTP_PORT": ["MAIL_PORT", "SMTP_SERVER_PORT", "EMAIL_PORT"],
    "SMTP_USER": ["MAIL_USER", "SMTP_LOGIN", "EMAIL_USER"],
    "SMTP_PASS": ["MAIL_PASS", "SMTP_PASSWORD", "EMAIL_PASS"],
    "DB_PATH": ["DATABASE_PATH", "DB_FILE", "SQLITE_PATH"],
    "TAX_RATES": ["TAX_TABLE", "STATE_TAX_RATES", "TAX_BY_STATE"],
    "DEBUG": ["DEBUG_MODE", "VERBOSE_DEBUG", "APP_DEBUG"],
    "ALLOWED_HOSTS": ["PERMITTED_HOSTS", "HOST_ALLOWLIST", "TRUSTED_HOSTS"],
    "SESSION_COOKIE_SECURE": ["SECURE_SESSION_COOKIE", "COOKIE_SECURE_FLAG"],
    # locals / params
    "subtotal": ["items_total", "sub_total", "net_amount"],
    "customer_id": ["cust_id", "customer_ref", "client_id"],
    "items": ["order_items", "cart_items", "products"],
    "invoice": ["inv_doc", "bill_doc", "invoice_obj"],
    "card_token": ["payment_token", "charge_token", "token"],
    "tax": ["tax_amount", "computed_tax"],
    "total": ["grand_total", "amount_due"],
    "body": ["email_body", "message_body"],
    "to_addr": ["recipient", "dest_addr"],
    "msg": ["message", "email_msg"],
    "s": ["server", "smtp_client"],
    "reason": ["void_reason", "cause"],
    "conn": ["db_conn", "connection", "database"],
    "cur": ["cursor", "db_cursor"],
    "rows": ["results", "records", "row_list"],
    "sql": ["query", "statement", "sql_text"],
    "name": ["customer_name", "full_name"],
    "out_path": ["output_path", "dest_path", "target_path"],
    "year": ["report_year", "yr"],
    "month": ["report_month", "mo"],
    "rates": ["rate_table", "state_rates"],
    "amount": ["base_amount", "taxable_amount"],
    "state": ["region", "state_code"],
    "issued": ["issued_dt", "issue_time"],
    "now": ["current_time", "as_of"],
}

# The T2 contract surface. tasks/T2-multi-agent.md pins
# `apply_discount(invoice_id, pct)`; these names must survive rotation so the
# task spec keeps referring to the same stub.
FROZEN = {"apply_discount", "invoice_id", "pct"}


def eprint(*args):
    print(*args, file=sys.stderr)


# ---------------------------------------------------------------- map
def build_rename_map(seed):
    """Seeded canonical -> alternative mapping, with collision checks."""
    rmap = {}
    for canon, pool in POOLS.items():
        rng = random.Random("rotate:v1:%d:%s" % (seed, canon))
        rmap[canon] = rng.choice(pool)
    # 1. every alternative is a usable identifier
    for canon, alt in rmap.items():
        if not alt.isidentifier() or keyword.iskeyword(alt):
            raise ValueError("bad alternative %r for %r" % (alt, canon))
    # 2. injectivity: two canonicals never map to the same alternative
    if len(set(rmap.values())) != len(rmap):
        seen, dupes = {}, []
        for canon, alt in rmap.items():
            if alt in seen:
                dupes.append((canon, seen[alt], alt))
            seen[alt] = canon
        raise ValueError("rename collision: %r" % dupes)
    # 3. no alternative collides with a bare identifier the renamer leaves
    #    alone (would silently merge two distinct names in one namespace).
    #    Attribute names on non-fixture objects are excluded: `conn.cursor()`
    #    can never merge with a renamed bare `cur`. Attribute names on
    #    fixture modules (`billing.X`) are included conservatively — the
    #    renamer rewrites those sites, and a clash there must fail loudly.
    untouched = (_bare_identifiers() - set(rmap) - FROZEN) \
        | _fixture_module_attrs()
    bad = {a for a in rmap.values() if a in untouched}
    if bad:
        raise ValueError("alternatives collide with unrenamed names: %r"
                         % sorted(bad))
    # 4. alternatives must not be frozen T2-contract names either
    bad = set(rmap.values()) & FROZEN
    if bad:
        raise ValueError("alternatives collide with frozen names: %r" % bad)
    return rmap


def _bare_identifiers():
    """Every identifier occupying the bare-name namespace in the canonical
    fixture .py files: Name/arg/def names AND import aliases.

    Import aliases matter: `from config import TAX_RATE` introduces the bare
    name TAX_RATE in the importing module, so an alternative colliding with
    an unrenamed import would silently merge two distinct names.
    Deliberately EXCLUDES Attribute.attr: `conn.cursor()` lives in the
    attribute namespace and can never merge with a renamed bare local
    (the old check rejected 103/200 seeds on exactly this false positive).
    """
    names = set()

    class V(ast.NodeVisitor):
        def visit_Name(self, node):
            names.add(node.id)
        def visit_arg(self, node):
            names.add(node.arg)
        def visit_FunctionDef(self, node):
            names.add(node.name)
            self.generic_visit(node)
        visit_AsyncFunctionDef = visit_FunctionDef
        def visit_Import(self, node):
            for a in node.names:
                names.add((a.asname or a.name).split(".")[0])
            self.generic_visit(node)
        def visit_ImportFrom(self, node):
            for a in node.names:
                names.add(a.asname or a.name)
            self.generic_visit(node)

    for root, _, files in os.walk(CODE_DIR):
        for fn in sorted(files):
            if not fn.endswith(".py"):
                continue
            with open(os.path.join(root, fn), encoding="utf-8") as f:
                V().visit(ast.parse(f.read()))
    return names


def _fixture_module_attrs():
    """Attribute names accessed on fixture modules (`billing.X`, `db.X`, …).

    The renamer rewrites cross-module fixture calls (`billing.run_query` ->
    `billing.exec_query`), so an alternative equal to such an attribute is
    treated as a collision (conservative: the failure is a loud ValueError,
    never a silent merge). Attributes on non-fixture objects (`conn.cursor()`,
    `datetime.datetime.now()`) are excluded — separate namespace, no merge.
    """
    modules = set()
    for root, _, files in os.walk(CODE_DIR):
        for fn in sorted(files):
            if fn.endswith(".py"):
                modules.add(os.path.splitext(fn)[0])
    attrs = set()

    class V(ast.NodeVisitor):
        def visit_Attribute(self, node):
            v = node.value
            if isinstance(v, ast.Name) and v.id in modules:
                attrs.add(node.attr)
            self.generic_visit(node)

    for root, _, files in os.walk(CODE_DIR):
        for fn in sorted(files):
            if not fn.endswith(".py"):
                continue
            with open(os.path.join(root, fn), encoding="utf-8") as f:
                V().visit(ast.parse(f.read()))
    return attrs


# ---------------------------------------------------------------- AST edit collection
class _EditCollector(ast.NodeVisitor):
    """Collect (lineno, col_offset, old, new) for every mapped identifier.

    NOTE (fixture-fragile): this collector handles Name/arg/FunctionDef and
    import aliases, plus cross-module fixture Attribute calls. It does NOT
    handle `self.x`/`cls.x`, decorators, class names, globals, or string
    annotations — none exist in the current fixture, so those cases are
    unreachable today. If the fixture ever gains them with a name in POOLS,
    extend this collector first (the suite's behavioral-equivalence test
    would likely catch a silent break, but do not rely on luck).
    """

    def __init__(self, rmap):
        self.rmap = rmap
        self.edits = []

    def _add(self, node, old, col=None):
        if old in self.rmap:
            self.edits.append((node.lineno,
                               node.col_offset if col is None else col,
                               old, self.rmap[old]))

    def visit_Name(self, node):
        self._add(node, node.id)

    def visit_arg(self, node):
        self._add(node, node.arg)

    def _def_name_col(self, node, line_text):
        # node.col_offset points at `def`/`async`/`class`; the name follows.
        idx = line_text.find(node.name, node.col_offset)
        if idx < 0:
            raise ValueError("cannot locate def name %r on line %d"
                             % (node.name, node.lineno))
        return idx

    def visit_FunctionDef(self, node):
        self._add(node, node.name, col="DEFER")
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Attribute(self, node):
        # Attribute.col_offset points at the VALUE; the attr name sits after
        # value.end_col_offset + 1 (the dot). Verified per-edit below.
        # Rename the attribute ONLY for cross-module calls into fixture
        # modules (billing.calculate_tax in test_billing.py). Any other
        # attribute (datetime.datetime.now, cur.execute, msg.as_string, ...)
        # belongs to someone else's API and must never be renamed — renaming
        # .now() once produced datetime.datetime.current_time(), which
        # compiles fine and explodes at runtime.
        if (isinstance(node.value, ast.Name)
                and node.value.id in ("billing", "config", "db", "reports")
                and node.attr in self.rmap):
            self.edits.append((node.lineno,
                               node.value.end_col_offset + 1,
                               node.attr, self.rmap[node.attr],
                               "ATTR"))
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        self._alias_edits(node)
        self.generic_visit(node)

    def visit_Import(self, node):
        self._alias_edits(node)
        self.generic_visit(node)

    def _alias_edits(self, node):
        for a in node.names:
            if a.name in self.rmap and not a.asname:
                # alias nodes carry positions on 3.10+; verified per-edit.
                self.edits.append((a.lineno, a.col_offset, a.name,
                                   self.rmap[a.name], "ALIAS"))
            elif a.asname in self.rmap:
                self.edits.append((a.lineno, a.col_offset, a.asname,
                                   self.rmap[a.asname], "ALIAS"))


def collect_edits(source, rmap, path="<source>"):
    tree = ast.parse(source, filename=path)
    lines = source.splitlines()
    collector = _EditCollector(rmap)
    collector.visit(tree)
    resolved = []
    for edit in collector.edits:
        lineno, col, old, new = edit[0], edit[1], edit[2], edit[3]
        kind = edit[4] if len(edit) > 4 else None
        line = lines[lineno - 1]
        if col == "DEFER":  # def/class name: locate after the keyword
            col = _EditCollector._def_name_col(
                collector, _FakeNode(lineno, 0, old), line)
        lb = line.encode("utf-8")
        old_b = old.encode("utf-8")
        if lb[col:col + len(old_b)] != old_b:
            # fall back to a forward search from col (never backwards:
            # an earlier occurrence on the same line belongs to another node)
            found = lb.find(old_b, col)
            if found < 0:
                raise ValueError(
                    "%s:%d: cannot locate %r for rename" % (path, lineno, old))
            col = found
        if kind == "ATTR" and lb[col - 1:col] != b".":
            raise ValueError(
                "%s:%d: expected '.' before attribute %r" % (path, lineno, old))
        resolved.append((lineno, col, old, new))
    return resolved


class _FakeNode:
    def __init__(self, lineno, col_offset, name):
        self.lineno = lineno
        self.col_offset = col_offset
        self.name = name


def apply_edits(source, edits):
    """Splice replacements right-to-left per line; line count never changes."""
    lines = source.split("\n")
    by_line = {}
    for lineno, col, old, new in edits:
        by_line.setdefault(lineno, []).append((col, old, new))
    for lineno, subs in by_line.items():
        lb = lines[lineno - 1].encode("utf-8")
        for col, old, new in sorted(subs, reverse=True):
            old_b, new_b = old.encode("utf-8"), new.encode("utf-8")
            if lb[col:col + len(old_b)] != old_b:
                raise ValueError("edit drift at line %d col %d (%r)"
                                 % (lineno, col, old))
            lb = lb[:col] + new_b + lb[col + len(old_b):]
        lines[lineno - 1] = lb.decode("utf-8")
    return "\n".join(lines)


def rename_source(source, rmap, path="<source>"):
    """Rename identifiers in one .py source; return (new_source, n_edits)."""
    edits = collect_edits(source, rmap, path)
    new_source = apply_edits(source, edits)
    # The renamed code must still parse and compile.
    compile(new_source, path, "exec")
    return new_source, len(edits)


# ---------------------------------------------------------------- guards
def _inside(child, parent):
    try:
        return os.path.commonpath(
            [os.path.realpath(child), os.path.realpath(parent)]
        ) == os.path.realpath(parent)
    except ValueError:
        return False


# ---------------------------------------------------------------- inventory remap
SECTION_RE = re.compile(r"^(### D\d+ `[^`]+`)\s*[-\u2013\u2014]\s*(.+)$")
EXPECT_RE = re.compile(r"^Expect:\s*(.+)$")


def _token_rename(text, rmap):
    """Rename NAME tokens via the map, spliced by position so spacing is
    preserved exactly. Falls back to word-boundary regex when the fragment
    is not tokenizable (e.g. an unbalanced Expect substring)."""
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        toks = None
    if toks is not None:
        lines = text.split("\n")
        by_line = {}
        for tok in toks:
            if tok.type == tokenize.NAME and tok.string in rmap:
                (srow, scol), (erow, ecol) = tok.start, tok.end
                if srow == erow:  # NAME tokens never span lines
                    by_line.setdefault(srow, []).append(
                        (scol, ecol, tok.string, rmap[tok.string]))
        if by_line:
            for row, subs in by_line.items():
                # tokenize columns are str offsets: splice on str directly.
                l = lines[row - 1]
                for scol, ecol, old, new in sorted(subs, reverse=True):
                    assert l[scol:ecol] == old, \
                        "token splice drift: %r" % text
                    l = l[:scol] + new + l[ecol:]
                lines[row - 1] = l
            return "\n".join(lines)
        return text
    pat = re.compile(r"\b(" + "|".join(
        sorted(rmap, key=len, reverse=True)) + r")\b")
    return pat.sub(lambda m: rmap[m.group(0)], text)


def remap_inventory(rmap, renamed_lines):
    """Return the variant DEBT-INVENTORY.md text.

    renamed_lines: {basename.py -> [lines]} of the renamed code tree, used to
    verify every remapped Expect against the actual renamed anchored line.
    """
    with open(CANON_INVENTORY, encoding="utf-8") as f:
        src = f.read().splitlines()

    file_of = {
        "billing.py": "billing.py", "db.py": "db.py", "config.py": "config.py",
        "reports.py": "reports.py",
        "test_billing.py": os.path.join("tests", "test_billing.py"),
        "requirements.txt": "requirements.txt",
    }

    out = []
    current_head = None
    # Names genuinely introduced by renaming in the variant code; prose
    # remapping is restricted to these (see _prose_rename_spans).
    code_names = _variant_code_names(renamed_lines)
    for line in src:
        m = SECTION_RE.match(line)
        if m:
            current_head = m.group(1)  # e.g. '### D1 `config.py:5`'
            head, title = m.group(1), m.group(2)
            out.append(head + " — " + _prose_rename_spans(title, rmap,
                                                          code_names))
            continue
        m = EXPECT_RE.match(line.strip())
        if m:
            raw = m.group(1).strip()
            if " ~ in " in raw:
                sub, _, ctx = raw.partition(" ~ in ")
                new_sub = _verify_expect(sub.strip(), ctx.strip(), rmap,
                                         renamed_lines, file_of, current_head)
                new_ctx = _token_rename(ctx.strip(), rmap)
                _verify_context(new_ctx, renamed_lines, file_of, current_head)
                out.append("Expect: %s ~ in %s" % (new_sub, new_ctx))
            else:
                out.append("Expect: " + _verify_expect(
                    raw, None, rmap, renamed_lines, file_of, current_head))
            continue
        out.append(_prose_rename_spans(line, rmap, code_names))
    return "\n".join(out) + "\n"


def _variant_code_names(renamed_lines):
    """Set of NAME tokens in the variant code tree.

    Used to prove a rename really happened in code before touching judges'
    prose: an alternative is a genuine rename of `old` iff it occurs as a
    NAME token here (collision checks 2+3 make this biconditional — an
    alternative cannot coincide with an unrenamed identifier or with another
    rename's alternative).
    """
    names = set()

    class V(ast.NodeVisitor):
        def visit_Name(self, node):
            names.add(node.id)
        def visit_arg(self, node):
            names.add(node.arg)
        def visit_FunctionDef(self, node):
            names.add(node.name)
            self.generic_visit(node)
        visit_AsyncFunctionDef = visit_FunctionDef

    for rel, lines in renamed_lines.items():
        if not rel.endswith(".py"):
            continue
        V().visit(ast.parse("\n".join(lines)))
    return names


def _prose_rename_spans(text, rmap, code_names):
    """Remap identifiers in judges' prose (titles, body lines) — but ONLY
    bare identifiers inside backtick code spans, and ONLY when the new name
    provably occurs in the variant code.

    Everything else is left verbatim: English words that happen to match a
    rename key ("tax", "name", "s"), possessives, and dotted/API references
    like `datetime.datetime.now()`. Rewriting those produced false statements
    in the judge's answer key (e.g. `datetime.datetime.current_time()`,
    "`fetchall`server", "mo-end") — the one corruption class that could make
    a judge penalize a candidate for citing true code.
    """
    def sub(m):
        inner = m.group(1).strip()
        if inner.isidentifier() and inner in rmap \
                and rmap[inner] in code_names:
            return "`" + rmap[inner] + "`"
        return m.group(0)
    return re.sub(r"`([^`]+)`", sub, text)


def _anchor_target(head):
    m = re.search(r"`([^`]+)`", head)
    base, num = m.group(1).split(":")
    return os.path.basename(base), int(num)


def _verify_expect(sub, ctx, rmap, renamed_lines, file_of, raw_line):
    base, num = _anchor_target(raw_line)
    target = renamed_lines[file_of[base]][num - 1]
    candidate = _token_rename(sub, rmap)
    if candidate in target:
        return candidate
    if sub in target:
        # The Expect refers to text the renamer deliberately leaves alone
        # (SQL string, docstring prose). Keep it — but only because it still
        # matches the renamed line.
        return sub
    raise ValueError(
        "remapped Expect %r matches neither renamed line %r (anchor %s)"
        % (candidate, target, raw_line.strip()))


def _verify_context(new_ctx, renamed_lines, file_of, raw_line):
    base, num = _anchor_target(raw_line)
    lines = renamed_lines[file_of[base]]
    defs = [l for l in lines[:num] if l.startswith("def ")]
    if not defs or not defs[-1].startswith("def " + new_ctx):
        raise ValueError(
            "remapped context %r does not match enclosing def of %s"
            % (new_ctx, raw_line.strip()))


# ---------------------------------------------------------------- generate
def generate(seed, out):
    out = os.path.realpath(out)
    if _inside(out, os.path.realpath(CODE_DIR)) \
            or out == os.path.realpath(FIXTURE_DIR):
        raise ValueError(
            "refusing: %r is inside the canonical fixture tree" % out)
    if os.path.exists(out):
        raise ValueError("refusing: dest %r already exists" % out)

    rmap = build_rename_map(seed)
    vintage = "v2-seed%d" % seed

    renamed_lines = {}  # rel path -> lines, for inventory verification
    total_edits = 0
    for root, _, files in os.walk(CODE_DIR):
        for fn in sorted(files):
            if fn.endswith("__pycache__") or fn.endswith((".pyc", ".pyo")):
                continue
            src_path = os.path.join(root, fn)
            rel = os.path.relpath(src_path, CODE_DIR)
            with open(src_path, encoding="utf-8") as f:
                content = f.read()
            if fn.endswith(".py"):
                new_content, n = rename_source(content, rmap, rel)
                total_edits += n
            else:
                new_content = content  # requirements.txt: no identifiers
            renamed_lines[rel] = new_content.splitlines()
            dest_path = os.path.join(out, "legacy-billing", rel)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with open(dest_path, "w", encoding="utf-8") as f:
                f.write(new_content)

    # line counts must be identical: anchors must not shift
    for rel, lines in renamed_lines.items():
        with open(os.path.join(CODE_DIR, rel), encoding="utf-8") as f:
            canon_n = sum(1 for _ in f)
        if len(lines) != canon_n:
            raise ValueError("line count changed for %s: %d -> %d"
                             % (rel, canon_n, len(lines)))

    inv_text = remap_inventory(rmap, renamed_lines)
    with open(os.path.join(out, "DEBT-INVENTORY.md"), "w",
              encoding="utf-8") as f:
        f.write(inv_text)

    with open(os.path.join(out, "VINTAGE"), "w", encoding="utf-8") as f:
        f.write(vintage + "\n")

    return {"vintage": vintage, "out": out, "edits": total_edits,
            "renames": len(rmap)}


def main():
    ap = argparse.ArgumentParser(
        description="Generate a rotated fixture variant (deterministic "
                    "identifier rotation).")
    ap.add_argument("--seed", type=int, required=True,
                    help="rotation seed; vintage becomes v2-seed<seed>")
    ap.add_argument("--out", default=None,
                    help="output dir (default: fixture/variants/v2-seed<seed>)")
    args = ap.parse_args()

    out = args.out or DEFAULT_OUT.format(seed=args.seed)
    try:
        info = generate(args.seed, out)
    except ValueError as e:
        eprint("ERROR: %s" % e)
        sys.exit(2)
    print("wrote variant %(vintage)s -> %(out)s "
          "(%(renames)d identifiers, %(edits)d edits)" % info)


if __name__ == "__main__":
    main()
