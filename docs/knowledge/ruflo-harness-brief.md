# Ruflo — harness candidate brief (criterion 2)

**Date:** 2026-10-28. **Status:** desk brief only — local clone still downloading
at brief time, so nothing below about the local tree is verified. **Harness
candidate, NOT a judge candidate** — the judge question (backlog C-1) stays
separate and untouched by this evaluation.

## What it is

Ruflo (Cognitum One / ruvnet, https://github.com/ruvnet/ruflo) — an agent
harness that turns a single mission into an end-to-end multi-agent workflow
("Ruflo Mods"), with a control plane that keeps human approval where agents
would otherwise act alone.

**Verified live (GitHub API, 2026-10-28):** 80,010 stars, 9,386 forks,
TypeScript, default branch `main`, repo description confirms multi-player
swarms, adaptive memory, federation, vector RAG, and native Claude Code /
Codex integration. The vendor figure "74,000+ stars" is conservative against
this live count.

**Vendor-reported [SECONDARY], not yet verified:** 100+ specialized agents,
coordinated swarms, shared memory, human approval controls, Ruflo Mods,
12.5M npm downloads over 12 months, MIT license. All to be checked against
the local tree once the clone finishes (remote HEAD check value:
`89b0cd02dd99ea1f63437fde6c05992ec53cc22b`).

## Why it fits the pack

The pack's criterion (2) is a **strong multi-agent co-working harness**.
Ruflo is a harness, not a model — the pack's unit of evaluation is
model+harness combos, so Ruflo pairs with candidate models; it does not
replace them.

- **T2 (multi-agent feature build) is the natural test bed.** T2's whole
  point is genuine role separation and reviewer discipline — exactly what
  Ruflo's swarms + shared memory + approval plane claim to provide. The
  standing failure mode to watch: the V1 dry run's "three roles played by
  one session" — if Ruflo's roles collapse to one session, it fails T2's
  premise outright.
- **T1 (global review)** tests single-agent depth; Ruflo adds little there
  unless its swarm coordination improves review coverage — a secondary
  question, not the entry test.
- **T3 (plugin/skill/MCP install + recovery)** touches criterion (3):
  Ruflo's MCP/skills claims are relevant but secondary to the criterion-(2)
  case.

## Zero-spend dry-run design (proposed, not started)

Standing rule: zero-spend dry run on synthetic fixtures before any model
spend. Steps, in order:

1. **Verify the tree.** Clone finishes → local tip must equal
   `89b0cd02dd99ea1f63437fde6c05992ec53cc22b`; confirm top-level structure,
   license, Mods docs, and the approval-plane implementation by reading the
   code — not the release copy.
2. **Exercise the CLI with no model calls.** Install locally; spawn a swarm
   on a canned mission; check role assignment, shared memory, and the
   approval gate's actual blocking behavior. Model layer mocked or local
   (Ollama) — no API spend.
3. **T2-shaped dry run.** Feed the existing synthetic T2 fixture; verify the
   harness assigns distinct roles, produces a diff, and runs a reviewer pass
   that can catch planted bugs — with model calls stubbed or local.
4. **Pass/fail criteria.** Roles genuinely separate (not one session);
   approval gate actually blocks autonomous action; memory shared across
   agents; failures logged to the run-log format (Sprint 1).
5. **Kill criteria.** Cannot run offline/mock without API spend → dead for
   the zero-spend path. Roles collapse to one session → disqualified as a
   T2 harness. Approval gate is cosmetic (logs but never blocks) → fails
   the control-plane claim.

## What this does NOT solve

- The judge problem. Ruflo runs candidates; it does not grade them. Gate 4
  (C-1) still needs Sakura's decision: Jev card, senior-only, or a new open
  judge passing the Gate 4b kill-test.
- Campaign 1 still needs the fuel gauge (GPT credit, Codex reset status).

## Backlog

Epic G (harness candidates) in `docs/backlog.md`: G-1 Ruflo zero-spend dry
run (this design), G-2 Ruflo live evaluation (BLOCKED on C-1 + fuel gauge +
G-1 pass).
