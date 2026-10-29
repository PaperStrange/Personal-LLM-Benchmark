# Ruflo G-1 dry run report (zero-spend)

**Date:** 2026-10-28. **Tip:** `89b0cd02dd99ea1f63437fde6c05992ec53cc22b`
("release: 3.63.8 (#4566)"), verified against the remote HEAD check value.
**Spend:** $0. **Model calls:** zero. Every executed claim below is [REAL];
everything not executed is labeled [OPEN].

## Verdict: G-1 COMPLETE (mechanics only; substance [OPEN])

The zero-spend scope is complete: the tree is verified, the verdict-merge
function executes, the CLI and MCP server run, and swarm state initializes.
No kill criterion fired. But the brief's pass criteria are NOT met — roles
genuinely separate, approval actually blocking in a flow, memory shared
across agents, failures logged to the run-log format — all remain [OPEN],
because none is observable without models. This verdict is a completion of
the mechanics phase, not a pass of the substance. G-1's backlog item closes
only for its zero-spend scope; the substance criteria move to G-2.

## What ran [REAL]

1. **Repo verified.** Clean checkout on `main`, tip matches. LICENSE is MIT
   (read from the file, not the badge).
2. **Guard verdict logic unit-tested standalone: 6/6 synthetic cases pass.**
   Compiled `plugins/ruflo-mods/hooks/guard/verdict.ts` standalone and ran
   `stricter()` through six combinations (allow+deny→deny, allow+ask→ask,
   ask+deny→deny, deny+allow→deny, allow+undefined→allow, ask+ask→ask with
   the chain's rule kept on ties). This proves the merge function implements
   strictest-wins — not that the guard enforces anything in a real flow
   (hook wiring, rule loading, effect application all untested). Integration
   is unproven.
3. **CLI runs — after a monorepo build.** A bare checkout does NOT run:
   `npm install` + `npm run build` fails (`tsc` missing in the workspace,
   sibling `dist/` folders absent). Working recipe, reproduced: tsc 5.9.3
   from the root `npm install` (root `node_modules/typescript`) + `tsc -b`
   on cli (builds shared, swarm) + `tsc -b` on cli-core + `tsc -b` on
   security. Then `ruflo --help` prints v3.63.8 with commands
   including `swarm`, `policy`, `hive-mind`, `mcp`, `pair`.
4. **`status`:** swarm stopped, 0 agents — empty state.
5. **`swarm init --v3-mode`:** swarm `swarm-1793250533966-sjkfe3`,
   hierarchical-mesh topology, max 15 agents, auto-scale enabled,
   message-bus protocol. `.claude-flow/` + `.swarm/` created. `swarm status`
   shows 0 agents, no tasks.
6. **`policy evaluate` on a production deploy:** outcome **allowed**,
   reason **legacy-default-allow**, mode **legacy**, zero matched rules —
   but WITH a sha256 decision receipt. See F2.
7. **MCP server (stdio):** initializes as `ruflo` 3.0.0, `tools/list`
   returns **379 tools** (banked: `results/ruflo-mcp-tools-2026-10-28.json`,
   names + count + method) — including `agent_spawn`, `swarm_*`,
   `memory_*`, `hooks_*`, `policy_evaluate`, `hive-mind_*`, `claims_*`
   (claim/release/board/steal), `team_*`, `mission_*`, `workflow_*`.
   Note: server version 3.0.0 is the MCP server component's own version
   (source: `v3/@claude-flow/mcp/src/server.ts`), distinct from CLI
   v3.63.8 — separate components, separate versions.

## Findings

**F1 — Ruflo is an integration layer, not a standalone runner.**
[Docs-derived, not executed.] Per its own user guide: "After running `init`,
just use Claude Code normally — the hooks system automatically routes tasks."
Agents run inside Claude Code (plugins) or Codex (MCP). Consequence for G-2:
the live eval must run **inside Claude Code or Codex with Ruflo's hooks
active** — there is no "run Ruflo" as a separate harness. This reframes the
evaluation, it does not block it.

**F2 — The approval mechanism is real; the default is allow-all.**
Policy model from code: decisions `allow | ask | deny`, strictest-wins
merging, effects including `require_approval`, modes `observe | enforce`.
But out of the box (legacy mode, no rules), a production deploy evaluates
to **allowed**. The control-plane claim therefore holds only after rules
are written and mode is set to **`enforce`** — `observe` is audit-only
(it reports `wouldBe`, it blocks nothing) and does not make a gate
protective. G-2 must configure enforce mode + rules FIRST, or the approval
gate is permissive by default — not cosmetic, but not protective either.

**F3 — 379 MCP tools, not "310+".** The tool surface exceeds the guide's
number. The `claims_*` family maps directly onto T2's "no two agents
editing the same file without coordination" rule — but whether claiming
actually prevents concurrent edits is [OPEN] until a live run.

**F4 — Build friction is real but reproducible.** A bare checkout does not
run; the recipe in item 3 works. G-2 setup must budget the monorepo build.

**F5 — Download figure discrepancy [OPEN].** The handoff said 12.5M npm
downloads over 12 months; the README badge says "Verified dataset:
97,022,120 download events" — and the same badge alt text opens
"Illustrative download counter starts at 98,000,000 and adds varied amounts
each second in a 30 second loop," which strengthens the case that the
badge number is illustrative, not measured. Different windows, different
counting, or both — not resolved here. Neither figure is load-bearing for
the criterion-(2) case.

## T2 discipline mapping (mechanism vs. live proof)

| T2 rule | Ruflo mechanism (from code/docs) | Live proof? |
|---|---|---|
| PLAN.md before any code edit | No ordering gate found in guard/route code | [OPEN] — G-2 |
| One shared todo list | Task state + memory_* tools exist | [OPEN] — G-2 |
| Implementer may not approve own work | Roles exist; enforcement of reviewer ≠ implementer not found in guard code | [OPEN] — G-2 |
| No concurrent edits without coordination | `claims_*` family | [OPEN] — G-2 |
| Reviewer runs tests, pastes output | Behavioral requirement on the agent; a harness can enable, not guarantee | [OPEN] — G-2 |
| Status claims backed by tool output | Decision receipts (sha256) exist for policy; agent-output receipts untested | [OPEN] — G-2 |

## Kill-criterion check (from the brief)

- Cannot run offline without API spend → **NOT triggered.** CLI, MCP,
  policy, swarm init all ran with zero model calls (no network capture was
  taken, so the claim is scoped to model calls, not all egress).
- Roles collapse to one session → **NOT triggered, NOT cleared.** No agents
  exist without models; unobservable zero-spend. G-2 must check it.
- Approval gate cosmetic (logs but never blocks) → **NOT triggered, NOT
  cleared.** `deny` and `require_approval` exist in code and the merge
  function executes standalone — but no action has ever been observed being
  blocked in a real flow, so the gate is not cleared either. Same standard
  as role collapse: existence in code is not clearance.

On the brief's pass criteria, stated plainly: (a) roles genuinely separate
— [OPEN]; (b) approval actually blocking in a flow — [OPEN]; (c) memory
shared across agents — [OPEN]; (d) failures logged to the run-log format —
partially evidenced (sha256 decision receipts exist for policy
evaluations; agent-output failure logging untested).

## What G-2 must do

1. Run inside Claude Code or Codex with Ruflo hooks active (F1) — which
   presumes access to those harnesses.
2. Author policy enforce-mode rules before the T2 run (F2) — observe mode
   does not count as protection.
3. Resolve the T2 table's [OPEN] rows, especially role separation and the
   claims-vs-concurrent-edit question (F3).
4. Fuel gauge first (GPT credit, Codex reset status) — G-2 is a spend
   decision, not a dry run.
5. Grading still needs C-1 (judge decision) — unchanged by this report.

## Backlog

G-1 → DONE for its zero-spend scope only; substance criteria carried to
G-2. G-2 still needs: C-1 (judge) + fuel gauge + enforce-mode rules
authored + T2 run design inside Claude Code/Codex.
