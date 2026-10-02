#!/usr/bin/env python3
"""Gate 2 rehearsal driver: genuine planner/implementer/reviewer separation.

Each role runs in a FRESH model context (no shared history); the only
handoff between roles is files on disk (PLAN.md, the implementation diff).
The planted-bug manifest is JUDGES ONLY: it lives outside the work tree and
is never inserted into any prompt -- a mechanical leak-scan in --mock mode
asserts this.

Usage:
    python3 tools/qualification/gate2_driver.py --mock
        Self-test with canned model outputs (validation gate for the driver
        itself): expects one green run, one red run (reviewer misses a bug),
        and a clean prompt-leak scan.
    python3 tools/qualification/gate2_driver.py --run N --out DIR --seed 7
        One real rehearsal run against the local ollama model.

Per-run layout under DIR:
    tree/               disposable planted copy (candidate-visible)
    plant_manifest.json JUDGES ONLY (outside tree/)
    PLAN.md             written into tree/ by the planner turn
    REVIEW.md           written into tree/ by the reviewer turn
    trace.jsonl         harness action trace (TRACE-FORMAT.md)
    prompts/            every prompt sent (for the leak audit)
    report.json         grading: t0, hidden tests, t2_coord_1/2, verdict

"Green" (predeclared): T0 T2 checks pass AND hidden tests pass AND reviewer
verdict is approve AND reviewer identifies both planted bugs.
Zero retries: unparseable model output fails the run honestly.
"""
import argparse
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

PACK = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(PACK, "tasks", "t2-discount-fix"))
from plant_bugs import plant  # noqa: E402

MODEL = "qwen2.5-1.5b-local"


_OLLAMA = None


def ollama_bin():
    """Lazily resolve the ollama binary on first use (not at import), so
    the module stays importable — and --mock runnable — without ollama."""
    global _OLLAMA
    if _OLLAMA is None:
        for cand in (
            shutil.which("ollama"),
            os.path.expanduser("~/workspace/.local/ollama-pkg/bin/ollama"),
            os.path.expanduser("~/.local/ollama-pkg/bin/ollama"),
        ):
            if cand and os.path.isfile(cand) and os.access(cand, os.X_OK):
                _OLLAMA = cand
                break
        if _OLLAMA is None:
            raise RuntimeError(
                "ollama binary not found on PATH or in known locations")
    return _OLLAMA

# Bug ids whose signatures must NEVER appear in a candidate-facing prompt.
LEAK_NEEDLES = ["plant_manifest", "off_by_one_qty", "swapped_tax_rates",
                "dropped_none_guard", "_judges_only", "JUDGES ONLY"]

SNAPSHOT_FILES = ["billing.py", "config.py", "db.py", "README.md",
                  "tests/test_billing.py"]

PLANNER_PROMPT = """You are the PLANNER in a disciplined multi-agent build. You NEVER write implementation code.

Task: implement `apply_discount(invoice_id, pct)` in billing.py:
- Validate 0 < pct <= 100; raise ValueError otherwise.
- Recompute the invoice total with the discount applied, persist the change to the invoices table, return the new total.
- Handle edge cases: unknown invoice_id, already-voided invoices.
- Add or fix tests covering the new behavior.

Codebase snapshot (read-only; file list then contents):
{tree}

Write PLAN.md with: approach, files to touch, test plan, risks.
Output ONLY the PLAN.md content between <<<PLAN>>> and <<<END>>> markers.
Do not write any implementation code."""

IMPLEMENTER_PROMPT = """You are the IMPLEMENTER in a disciplined multi-agent build. You execute the plan; you do not rewrite it.

PLAN.md (written by the planner, authoritative):
{plan}

Codebase snapshot (the files you may change):
{tree}

Implement apply_discount per the plan. You may also add tests in tests/.
Output each changed file's COMPLETE new content between markers:
<<<FILE:relative/path.py>>>
...full file content...
<<<END>>>
One block per changed file. Do not modify PLAN.md. Output only the file blocks."""

REVIEWER_PROMPT_T1 = """You are the REVIEWER in a disciplined multi-agent build. You did not write this code. You are independent: judge only what you see.

PLAN.md:
{plan}

Implementation diff (implementer's changes vs the original tree):
{diff}

You may request: (a) the full content of any listed file, (b) a test-suite run.
Reply with your requests between <<<REQUESTS>>> and <<<END>>> markers, e.g.
READ billing.py
RUN python3 -m unittest discover -s tests -v
Or reply NO_REQUESTS if you need nothing further."""

REVIEWER_PROMPT_T2 = """Test output from the run you requested:
{test_output}

File contents you requested:
{files}

Now write REVIEW.md: verdict line exactly `VERDICT: APPROVE` or `VERDICT: REQUEST-CHANGES`, evidence (including the test output pasted or summarized with pass/fail counts), and any defects you found with file:line references.
Output ONLY the REVIEW.md content between <<<REVIEW>>> and <<<END>>> markers."""


def eprint(*a):
    print(*a, file=sys.stderr)


def ollama_generate(prompt, timeout=900, num_predict=None):
    """Generate via ollama. num_predict caps output tokens (via the API);
    None means uncapped (may ramble — the 900s timeout is the backstop)."""
    if num_predict is None:
        p = subprocess.run(
            [ollama_bin(), "run", MODEL], input=prompt,
            capture_output=True, text=True, timeout=timeout)
        if p.returncode != 0:
            raise RuntimeError("ollama run failed: %s" % p.stderr[-500:])
        return p.stdout
    import urllib.request
    body = json.dumps({"model": MODEL, "prompt": prompt, "stream": False,
                       "options": {"num_predict": num_predict}}).encode()
    req = urllib.request.Request("http://127.0.0.1:11434/api/generate",
                                 data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())["response"]
    except Exception as e:
        raise RuntimeError("ollama api generate failed: %s" % e)


def clean(text):
    """Strip ANSI escape sequences some model runtimes emit mid-generation."""
    return re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]|\x1b[()][AB0]", "", text)


def extract(text, start, end, fallback_whole=True):
    m = re.search(re.escape(start) + r"(.*?)" + re.escape(end),
                  clean(text), re.DOTALL)
    if m:
        return m.group(1).strip()
    return clean(text).strip() if fallback_whole else None


def snapshot(tree):
    parts = []
    for rel in SNAPSHOT_FILES:
        path = os.path.join(tree, rel)
        if not os.path.isfile(path):
            parts.append("### %s\n(MISSING)\n" % rel)
            continue
        with open(path, encoding="utf-8") as f:
            parts.append("### %s\n%s" % (rel, f.read()))
    listing = []
    for root, _dirs, files in os.walk(tree):
        for fn in sorted(files):
            listing.append(os.path.relpath(os.path.join(root, fn), tree))
    return "Files:\n" + "\n".join(sorted(listing)) + "\n\n" + "\n\n".join(parts)


def unified_diff(tree, originals):
    """Diff current tree files vs captured originals."""
    chunks = []
    for rel, old in sorted(originals.items()):
        path = os.path.join(tree, rel)
        new = ""
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as f:
                new = f.read()
        if new != old:
            d = difflib.unified_diff(
                old.splitlines(), new.splitlines(),
                fromfile="a/" + rel, tofile="b/" + rel, lineterm="")
            chunks.append("\n".join(d))
    return "\n".join(chunks) if chunks else "(no changes)"


class Run:
    def __init__(self, outdir, seed, mock_outputs=None):
        self.out = outdir
        self.seed = seed
        self.mock = list(mock_outputs) if mock_outputs else None
        self.tree = os.path.join(outdir, "tree")
        self.manifest_path = os.path.join(outdir, "plant_manifest.json")
        self.trace_path = os.path.join(outdir, "trace.jsonl")
        self.prompts_dir = os.path.join(outdir, "prompts")
        self.step = 0
        self.trace_fh = None
        self.manifest = None
        os.makedirs(self.prompts_dir, exist_ok=True)

    # -- trace ---------------------------------------------------------
    def log(self, role, action, target, outcome, note=""):
        self.step += 1
        rec = {"step": self.step, "role": role, "action": action,
               "target": target, "outcome": outcome}
        if note:
            rec["note"] = note
        self.trace_fh.write(json.dumps(rec) + "\n")

    # -- model call ----------------------------------------------------
    def generate(self, role, prompt, prompt_name):
        ph = os.path.join(self.prompts_dir, prompt_name + ".txt")
        with open(ph, "w", encoding="utf-8") as f:
            f.write(prompt)
        self.log("harness", "send_prompt",
                 "%s/%s" % (role, prompt_name),
                 "ok", note="sha256=%s" % hashlib.sha256(
                     prompt.encode()).hexdigest()[:12])
        t0 = time.time()
        if self.mock is not None:
            if not self.mock:
                raise RuntimeError("mock outputs exhausted at " + prompt_name)
            text = self.mock.pop(0)
        else:
            text = ollama_generate(prompt)
        dt = time.time() - t0
        raw = os.path.join(self.prompts_dir, prompt_name + ".raw.txt")
        with open(raw, "w", encoding="utf-8") as f:
            f.write(text)
        self.log(role, "generate", prompt_name, "ok",
                 note="wall_s=%.1f chars=%d" % (dt, len(text)))
        return text

    # -- phases --------------------------------------------------------
    def plant(self):
        t0 = time.time()
        self.manifest = plant(
            os.path.join(PACK, "fixture", "legacy-billing"),
            self.tree, seed=self.seed, manifest_path=self.manifest_path)
        self.log("harness", "plant_bugs", self.tree, "ok",
                 note="seed=%d bugs=%s wall_s=%.1f" % (
                     self.seed,
                     ",".join(b["id"] for b in self.manifest["bugs"]),
                     time.time() - t0))

    def phase_planner(self):
        snap = snapshot(self.tree)
        prompt = PLANNER_PROMPT.format(tree=snap)
        text = self.generate("planner", prompt, "planner")
        plan = extract(text, "<<<PLAN>>>", "<<<END>>>")
        with open(os.path.join(self.tree, "PLAN.md"), "w",
                  encoding="utf-8") as f:
            f.write(plan + "\n")
        self.log("planner", "write_file", "PLAN.md", "ok",
                 note="chars=%d" % len(plan))
        # Isolation check: planner may only have created PLAN.md.
        return plan

    def phase_implementer(self, plan):
        originals = {}
        for root, _d, files in os.walk(self.tree):
            _d[:] = [d for d in _d if d != "__pycache__"]
            for fn in files:
                fp = os.path.join(root, fn)
                try:
                    with open(fp, encoding="utf-8") as f:
                        originals[os.path.relpath(fp, self.tree)] = f.read()
                except (UnicodeDecodeError, OSError):
                    continue  # binary/byproduct files are not diffed
        plan_before = open(os.path.join(self.tree, "PLAN.md"),
                           encoding="utf-8").read()
        snap = snapshot(self.tree)
        prompt = IMPLEMENTER_PROMPT.format(plan=plan, tree=snap)
        text = self.generate("implementer", prompt, "implementer")
        # Accept <<<FILE:path>>> and the bare <<<path>>> form (the model
        # sometimes drops the FILE: prefix); intent is unambiguous.
        # The filename class excludes <, >, and newlines so a malformed
        # marker (e.g. <<<billing.py>> with two '>') cannot make the
        # capture run away into the file body.
        blocks = re.findall(r"<<<(?:FILE:)?([^<>\n]+?)>>>\s*\n(.*?)<<<END>>>",
                            clean(text), re.DOTALL)
        # Sanity: filename must look like a relative path.
        good = []
        for rel, content in blocks:
            rel = rel.strip()
            if (rel and ".." not in rel and not rel.startswith("/")
                    and re.fullmatch(r"[A-Za-z0-9_./-]+", rel)):
                good.append((rel, content))
        blocks = good
        if not blocks:
            self.log("implementer", "emit_files", None, "error",
                     note="no <<<FILE>>> blocks found")
            raise RuntimeError("implementer emitted no file blocks")
        for rel, content in blocks:
            rel = rel.strip()
            if rel == "PLAN.md" or ".." in rel or rel.startswith("/"):
                self.log("implementer", "write_file", rel, "error",
                         note="forbidden target refused")
                raise RuntimeError("implementer tried to write " + rel)
            dest = os.path.join(self.tree, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "w", encoding="utf-8") as f:
                f.write(content.strip() + "\n")
            self.log("implementer", "write_file", rel, "ok")
        plan_after = open(os.path.join(self.tree, "PLAN.md"),
                          encoding="utf-8").read()
        if plan_after != plan_before:
            self.log("harness", "isolation_check", "PLAN.md", "error",
                     note="implementer modified PLAN.md")
            raise RuntimeError("implementer modified PLAN.md")
        self.log("harness", "isolation_check", "PLAN.md", "ok")
        return unified_diff(self.tree, originals)

    def phase_reviewer(self, plan, diff):
        snap = snapshot(self.tree)
        prompt = REVIEWER_PROMPT_T1.format(plan=plan, diff=diff)
        # Reviewer gets the snapshot inline; file re-reads served on request.
        req_text = self.generate("reviewer", prompt + "\n\n" + snap,
                                 "reviewer_t1")
        reqs = extract(req_text, "<<<REQUESTS>>>", "<<<END>>>")
        test_output, files = "(no test run requested)", ""
        for line in reqs.splitlines():
            line = line.strip()
            if line.upper().startswith("READ "):
                rel = line[5:].strip().strip("./")
                path = os.path.join(self.tree, rel)
                if os.path.isfile(path) and ".." not in rel:
                    with open(path, encoding="utf-8") as f:
                        files += "\n### %s\n%s" % (rel, f.read())
                    self.log("reviewer", "read_file", rel, "ok")
                else:
                    self.log("reviewer", "read_file", rel, "error",
                             note="not found/refused")
            elif line.upper().startswith("RUN "):
                cmd = line[4:].strip()
                parts = cmd.split()
                allowed = (parts[0] == "pytest"
                           or (parts[:3] == ["python3", "-m", "unittest"])
                           or (parts[:3] == ["python", "-m", "unittest"]))
                if not allowed:
                    self.log("reviewer", "run_tests", cmd, "error",
                             note="only pytest or python3 -m unittest allowed")
                    continue
                if parts[0] == "pytest":
                    parts = [sys.executable, "-m"] + parts
                t0 = time.time()
                p = subprocess.run(
                    parts, cwd=self.tree, capture_output=True,
                    text=True, timeout=600)
                test_output = ("$ %s\n[exit %d, %.1fs]\n%s\n%s"
                               % (cmd, p.returncode, time.time() - t0,
                                  p.stdout[-4000:], p.stderr[-2000:]))
                self.log("reviewer", "run_tests", cmd,
                         "ok" if p.returncode == 0 else "error",
                         note="exit=%d" % p.returncode)
        prompt2 = REVIEWER_PROMPT_T2.format(test_output=test_output,
                                           files=files or "(none)")
        text = self.generate("reviewer", prompt2, "reviewer_t2")
        review = extract(text, "<<<REVIEW>>>", "<<<END>>>")
        with open(os.path.join(self.tree, "REVIEW.md"), "w",
                  encoding="utf-8") as f:
            f.write(review + "\n")
        self.log("reviewer", "write_file", "REVIEW.md", "ok",
                 note="chars=%d" % len(review))
        return review, test_output

    # -- grading -------------------------------------------------------
    def write_deliverable(self, plan, diff, test_output, review):
        """Concatenate the T2 deliverables into one file for the judge
        (per tasks/T2-multi-agent.md), plus the role/time note."""
        self.trace_fh.flush()  # else buffered log lines are invisible below
        with open(os.path.join(self.tree, "PLAN.md"), encoding="utf-8") as f:
            plan_text = f.read()
        roles = []
        for line in open(self.trace_path, encoding="utf-8"):
            rec = json.loads(line)
            if rec["action"] == "generate":
                roles.append("%s wall=%s" % (rec["role"], rec.get("note", "")))
        doc = ("# T2 deliverable (concatenated per task spec)\n\n"
               "## PLAN.md\n%s\n\n## Implementation diff\n```diff\n%s\n```\n\n"
               "## Reviewer-requested test output\n```\n%s\n```\n\n"
               "## REVIEW.md\n%s\n\n## Roles and wall-clock\n%s\n"
               % (plan_text, diff, test_output, review, "\n".join(roles)))
        path = os.path.join(self.out, "deliverable.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(doc)
        self.log("harness", "write_file", "deliverable.md", "ok")
        return path

    def grade(self, review, candidate_path):
        # T0
        p = subprocess.run(
            [sys.executable, os.path.join(PACK, "judge", "t0_checks.py"),
             "--task", "T2", "--candidate", candidate_path,
             "--workdir", self.tree],
            capture_output=True, text=True, cwd=PACK)
        t0_pass = (p.returncode == 0)
        self.log("harness", "t0_check", "T2", "ok" if t0_pass else "error",
                 note=p.stdout.strip().splitlines()[-1][:120]
                 if p.stdout.strip() else p.stderr[-120:])
        # Hidden tests (authored fresh for qualification; never in prompts)
        hidden = os.path.join(PACK, "results", "qualification", "t2",
                              "hidden", "test_t2_hidden.py")
        hp = subprocess.run(
            [sys.executable, hidden, "-v"],
            capture_output=True, text=True, cwd=self.tree,
            env={**os.environ, "T2_TREE": self.tree})
        hidden_pass = (hp.returncode == 0)
        self.log("harness", "hidden_tests", "test_t2_hidden.py",
                 "ok" if hidden_pass else "error",
                 note=(hp.stdout.strip().splitlines()[-1][:120]
                       if hp.stdout.strip() else hp.stderr[-120:]))
        # t2_coord_1/2: reviewer identifies each planted bug (file + line or
        # signature/paraphrase keywords), without ever seeing the manifest.
        coord = {}
        rl = review.lower()
        for i, bug in enumerate(self.manifest["bugs"], 1):
            key = "t2_coord_%d" % i
            file_hit = bug["file"] in rl
            line_hit = ("%s:%d" % (bug["file"], bug["line"])) in rl
            sig_hit = bug["signature"].lower() in rl
            kw = {"off_by_one_qty": ["off-by-one", "off by one", "qty+1",
                                     "qty + 1"],
                  "swapped_tax_rates": ["swap", "swapped",
                                        "0.0625", "0.0725"],
                  "dropped_none_guard": ["none", "guard", "indexerror",
                                         "rows[0]"]}[bug["id"]]
            # swapped_tax_rates: require "swap"/"swapped" or BOTH transposed
            # values. Mere mention of CA/TX/tax-rate is not detection.
            if bug["id"] == "swapped_tax_rates":
                kw_hit = ("swap" in rl or "swapped" in rl or
                          ("0.0625" in rl and "0.0725" in rl))
            else:
                kw_hit = sum(k in rl for k in kw) >= 2
            hit = file_hit and (line_hit or sig_hit or kw_hit)
            coord[key] = {"bug": bug["id"],
                         "file:line": "%s:%d" % (bug["file"], bug["line"]),
                         "identified": bool(hit),
                         "signals": {"file": file_hit, "line": line_hit,
                                     "signature": sig_hit, "keywords": kw_hit}}
            self.log("harness", "grade_coord", key,
                     "ok" if hit else "error",
                     note="bug=%s" % bug["id"])
        verdict = bool(re.search(r"^VERDICT:\s*APPROVE", review,
                                 re.IGNORECASE | re.MULTILINE))
        green = (t0_pass and hidden_pass and verdict
                 and all(v["identified"] for v in coord.values()))
        return {"t0_pass": t0_pass, "t0_output": p.stdout,
                "hidden_pass": hidden_pass,
                "hidden_output": (hp.stdout + hp.stderr)[-2000:],
                "coord": coord, "verdict_approve": verdict,
                "green": green}

    def leak_scan(self):
        """Every candidate-facing prompt must be free of manifest material."""
        hits = []
        for fn in sorted(os.listdir(self.prompts_dir)):
            if not fn.endswith(".txt") or fn.endswith(".raw.txt"):
                continue
            with open(os.path.join(self.prompts_dir, fn),
                      encoding="utf-8") as f:
                text = f.read()
            for needle in LEAK_NEEDLES:
                if needle.lower() in text.lower():
                    hits.append((fn, needle))
        return hits

    def execute(self):
        self.trace_fh = open(self.trace_path, "w", encoding="utf-8")
        report = {"seed": self.seed, "model": MODEL}
        try:
            self.plant()
            plan = self.phase_planner()
            diff = self.phase_implementer(plan)
            with open(os.path.join(self.out, "diff.txt"), "w",
                      encoding="utf-8") as f:
                f.write(diff + "\n")
            review, test_output = self.phase_reviewer(plan, diff)
            candidate = self.write_deliverable(plan, diff, test_output,
                                               review)
            report["grading"] = self.grade(review, candidate)
            report["status"] = ("GREEN" if report["grading"]["green"]
                                else "RED")
        except Exception as exc:  # honest failure, never a silent one
            self.log("harness", "run_abort", None, "error", note=str(exc)[:200])
            report["status"] = "ABORTED"
            report["error"] = str(exc)[:500]
        finally:
            self.trace_fh.close()
        report["leak_scan"] = [
            {"prompt": fn, "needle": n}
            for fn, n in self.leak_scan()]
        with open(os.path.join(self.out, "report.json"), "w",
                  encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        # trace_check.py summary (reporter, exit 0 always)
        p = subprocess.run(
            [sys.executable, os.path.join(PACK, "judge", "trace_check.py"),
             self.trace_path], capture_output=True, text=True)
        with open(os.path.join(self.out, "trace_summary.json"), "w",
                  encoding="utf-8") as f:
            f.write(p.stdout)
        return report


# -- mock self-test ----------------------------------------------------
MOCK_PLAN = """<<<PLAN>>>
# PLAN: implement apply_discount

## Approach
Read billing.py invoice model (sqlite rows via db.get_conn), implement
apply_discount(invoice_id, pct): validate 0 < pct <= 100 (ValueError),
fetch row, ValueError on unknown id or void status, new_total =
round(total*(1-pct/100),2), UPDATE invoices SET total, return new_total.

## Files to touch
- billing.py (implement apply_discount)
- tests/test_billing.py (add discount tests)

## Test plan
pytest tests/ -q; new tests for bounds, persistence, unknown/void.

## Risks
- Row tuple layout must be confirmed (id, customer_id, subtotal, tax, total, status).
- Must not break existing tests.
<<<END>>>"""

MOCK_IMPL = """<<<FILE:billing.py>>>
PLACEHOLDER
<<<END>>>"""

MOCK_REQ = """<<<REQUESTS>>>
RUN python3 -m unittest discover -s tests -v
<<<END>>>"""

MOCK_REVIEW_GOOD = """<<<REVIEW>>>
# REVIEW

VERDICT: APPROVE

## Test evidence
$ python3 -m unittest discover -s tests -v
Ran 8 tests in 0.42s
OK

The implementation matches PLAN.md: validation, persistence, edge cases.

## Defects found (pre-existing, not introduced by this change)
1. billing.py:20 — off-by-one: `it["price"] * (it["qty"] + 1)` bills qty+1
   units per line item, inflating every subtotal.
2. config.py:13 — swapped tax rates: CA is 0.0625 and TX is 0.0725; the
   correct values are CA 0.0725 / TX 0.0625.
<<<END>>>"""

MOCK_REVIEW_MISS = """<<<REVIEW>>>
# REVIEW

VERDICT: APPROVE

## Test evidence
$ python3 -m unittest discover -s tests -v
Ran 8 tests in 0.42s
OK

Implementation matches the plan. No defects found in the changed code.
<<<END>>>"""


def _mock_tree_with_impl(outdir):
    """Build a mock implementer output: real billing.py with a correct
    apply_discount spliced in (reference implementation, scratch-only)."""
    with open(os.path.join(PACK, "fixture", "legacy-billing", "billing.py"),
              encoding="utf-8") as f:
        src = f.read()
    impl = '''
def apply_discount(invoice_id, pct):
    """Percent discount on an invoice total."""
    if isinstance(pct, bool) or not isinstance(pct, (int, float)) \\
            or not 0 < pct <= 100:
        raise ValueError("pct must satisfy 0 < pct <= 100, got %r" % (pct,))
    rows = run_query("SELECT * FROM invoices WHERE id = %d" % int(invoice_id))
    if not rows:
        raise ValueError("unknown invoice_id: %r" % (invoice_id,))
    _id, _cid, _sub, _tax, total, status = rows[0]
    if status == "void":
        raise ValueError("invoice %d is void" % (invoice_id,))
    new_total = round(total * (1 - pct / 100.0), 2)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE invoices SET total = ? WHERE id = ?",
                (new_total, int(invoice_id)))
    conn.commit()
    conn.close()
    return new_total

'''
    stub_start = src.index("def apply_discount(invoice_id, pct):")
    stub_end = src.index('if __name__ == "__main__":')
    new = src[:stub_start] + impl.strip() + "\n\n\n" + src[stub_end:]
    return MOCK_IMPL.replace("PLACEHOLDER", new)


def mock_selftest():
    """Validation gate for this driver: plumbing must discriminate."""
    tmp = tempfile.mkdtemp(prefix="gate2-mock-")
    ok = True
    try:
        # Run 1 (green): reviewer catches both planted bugs.
        r1 = os.path.join(tmp, "run1")
        os.makedirs(r1)
        run1 = Run(r1, seed=7,
                   mock_outputs=[MOCK_PLAN, _mock_tree_with_impl(r1),
                                 MOCK_REQ, MOCK_REVIEW_GOOD])
        rep1 = run1.execute()
        # The mock reviewer asked for one pytest run; feed canned output.
        checks = [
            ("run1 status GREEN", rep1["status"] == "GREEN"),
            ("run1 t0 pass", rep1["grading"]["t0_pass"]),
            ("run1 hidden pass", rep1["grading"]["hidden_pass"]),
            ("run1 coord_1 identified",
             rep1["grading"]["coord"]["t2_coord_1"]["identified"]),
            ("run1 coord_2 identified",
             rep1["grading"]["coord"]["t2_coord_2"]["identified"]),
            ("run1 leak scan clean", rep1["leak_scan"] == []),
        ]
        # Run 2 (red): reviewer misses both bugs -> coord must fail.
        r2 = os.path.join(tmp, "run2")
        os.makedirs(r2)
        run2 = Run(r2, seed=7,
                   mock_outputs=[MOCK_PLAN, _mock_tree_with_impl(r2),
                                 MOCK_REQ, MOCK_REQ, MOCK_REVIEW_MISS])
        rep2 = run2.execute()
        checks += [
            ("run2 status RED", rep2["status"] == "RED"),
            ("run2 coord_1 not identified",
             not rep2["grading"]["coord"]["t2_coord_1"]["identified"]),
            ("run2 coord_2 not identified",
             not rep2["grading"]["coord"]["t2_coord_2"]["identified"]),
            ("run2 leak scan clean", rep2["leak_scan"] == []),
        ]
        # Manifest isolation: manifest outside tree/, prompts lack it.
        checks += [
            ("manifest outside tree",
             os.path.isfile(os.path.join(r1, "plant_manifest.json"))
             and not os.path.exists(os.path.join(
                 r1, "tree", "plant_manifest.json"))),
            ("PLAN.md before code (mtime)",
             os.path.getmtime(os.path.join(r1, "tree", "PLAN.md"))
             <= os.path.getmtime(os.path.join(r1, "tree", "billing.py"))),
        ]
        for name, passed in checks:
            print(("PASS " if passed else "FAIL ") + name)
            ok = ok and passed
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("MOCK SELF-TEST: " + ("ALL GREEN" if ok else "FAILURES PRESENT"))
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true",
                    help="self-test with canned model outputs")
    ap.add_argument("--run", type=int, default=None,
                    help="run number (real model)")
    ap.add_argument("--out", default=None, help="per-run output dir")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args(argv)
    if args.mock:
        return mock_selftest()
    if args.run is None or args.out is None:
        ap.error("--run N --out DIR required (or --mock)")
    os.makedirs(args.out, exist_ok=True)
    run = Run(args.out, seed=args.seed)
    t0 = time.time()
    rep = run.execute()
    print("run %d: %s (%.0fs)" % (args.run, rep["status"],
                                  time.time() - t0))
    print(json.dumps(rep.get("grading", {}), indent=2)[:1500])
    return 0 if rep["status"] == "GREEN" else 1


if __name__ == "__main__":
    sys.exit(main())
