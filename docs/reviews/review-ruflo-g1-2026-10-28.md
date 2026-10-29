# Review record: Ruflo G-1 dry-run report (2026-10-28)

Reviewers: adversarial (boss/partner lens) + mistake-hunt (independent
subagents, parallel). All findings applied.

## Adversarial — 1 BLOCKER, 3 MAJORs, 9 minors

- **B1 (verdict overclaims):** "G-1 PASS (scoped)" justified by "no kill
  criterion fired" while 3 of 4 brief pass criteria were unproven and the
  4th unaddressed. Fixed: verdict → "G-1 COMPLETE (mechanics only;
  substance [OPEN])"; pass criteria stated plainly as [OPEN]/partial in a
  new paragraph; backlog G-1 closes only for its zero-spend scope.
- **M1 (asymmetric kill handling):** approval got a clean "NOT triggered"
  on weaker evidence than role collapse's "NOT triggered, NOT cleared."
  Fixed: approval → "NOT triggered, NOT cleared" (same standard).
- **M2 (observe/enforce conflation):** observe is audit-only, not
  protection. Fixed: F2 and G-2 actions say enforce only.
- **M3 (unit vs system confidence):** 6/6 test is a standalone merge-function
  unit test, not system enforcement. Fixed: scoped language + the six cases
  described; integration explicitly unproven.
- **Minors:** verdict paragraph "approval mechanism executes" →
  "verdict-merge function executes"; "a swarm initializes" → "swarm state
  initializes (0 agents)"; "zero API calls" → "zero model calls" (no
  network capture taken); MCP 3.0.0 vs CLI 3.63.8 skew explained (separate
  component versions, source-confirmed); build recipe step 1 sourced (root
  `npm install` tsc 5.9.3); F1 labeled docs-derived; "G-2 unblocked on C-1
  + fuel gauge only" → full remaining-work list; 379-tool count banked as
  `results/ruflo-mcp-tools-2026-10-28.json`; "honest empty state" cut.

## Mistake-hunt — 2 minors

- **M1:** same observe/enforce conflation as adversarial M2 — fixed (see
  above). Also confirmed from code: observe reports only `wouldBe`;
  legacy-default-allow is exactly what `evaluator.ts:118` produces.
- **M2:** F5 omitted the badge's "Illustrative" self-label — added; it
  strengthens the report's own conclusion.
- Verified correct: tip, MIT license, verdict.ts RANK/stricter semantics,
  policy.ts modes/effects, swarm init defaults (hierarchical-mesh, 15
  agents), CLI/MCP command files, F1 quote verbatim, F5 badge quote
  verbatim. MCP 379 count not independently re-run (no runnable build in
  tree at review time) but source count (353 unique names in mcp-tools/
  alone) is the same order of magnitude — now banked from the actual run
  output.

## Standing

No verdict changed in substance — the dry run's mechanics findings stand;
only the verdict label and the clearance language were corrected. The
report no longer claims anything the zero-spend evidence doesn't support.
