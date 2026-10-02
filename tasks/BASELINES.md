# Baselines: raw model, no harness

Run each task once with a **plain chat model and no tools, agents, or
harness** before (or alongside) the harnessed runs. The baseline is the
control group for the whole pack.

## Why

A score is always a (harness, model, config) tuple. Without a baseline you
cannot tell whether a good T2 came from the *model* being strong or the
*harness* orchestrating well — which is exactly the split between your
criterion 1 (model capability: legacy planning, global review) and criteria
2–3 (harness capability: multi-agent discipline, expandability). The
**baseline-vs-harness delta is the harness's measured contribution.**

Baselines also calibrate the judge: a Jev score of 70 means something
different if the raw model scores 68 (harness added little) versus 35
(harness did the heavy lifting).

## T1 baseline (global project review)

Paste the prompt from `tasks/T1-global-review.md` plus the full text of the
fixture files into a plain chat session of the candidate model. No tools, no
code execution, no agents — just the model and the text. Save the Markdown
output and grade it with the same rubric + T0 gate. Compare against the
harnessed run (where the model explored the repo with tools): the delta is
what tooling and onboarding flow buy you.

## T2 baseline (multi-agent feature build)

One chat session plays **all three roles sequentially** — planner, then
implementer, then reviewer — with no subagents and no parallelism. The same
person-in-one-context writes PLAN.md, the code, and REVIEW.md.

Discipline items that require *true* role separation are **failed (or N/A) by
construction** in the baseline: there is no independent reviewer (the reviewer
saw the code being written), no timestamp separation between PLAN.md and
edits, and self-approval is unavoidable. Say so in the run notes — do not
hand-wave it. The baseline measures what a single context can do; the delta
to the harnessed run measures what real subagent isolation adds. This is the
item where harnesses should win by the largest margin.

## T3 baseline (expandability)

A **human** does the install manually, following the same
`tasks/T3-expandability.md` steps: find a third-party plugin/skill/MCP on
GitHub, install it into the harness's config by hand, get it to do the small
task. Record wall-clock **time-to-working** — that is the number to beat. A
harness whose agent-assisted install cannot beat (or at least match) a human
doing it by hand has an expandability problem, no matter how good its docs
look.

## Recording

Label baseline runs clearly in `results/scorecard.csv`: `harness=none`,
`model=<model name>`, and note the baseline protocol in `notes`. Baselines
are cheap (one T1 run ≈ $0.02 on Luna) — there is no reason to skip them.

## Harness attribution: the evidence

The literature says the harness is often the *larger* variable, not the
model:

- Terminal-Bench 2.0 ran 101 agent configurations across 23 scaffolds, 5
  attempts each: LangChain jumped from outside the top-30 to top-5 by
  changing **only the harness**.
- Claw-SWE-Bench pins everything except the harness and finds swapping it
  moves Pass@1 by up to **27.4pp** — nearly the full model-to-model spread
  across nine frontier models. One context-management setting alone swung a single
  model 6.40% → 58.40% on SWE-bench Verified (industry analysis, Sept 2026 —
  directional, not peer-reviewed).
- Anthropic's eval guidance: isolate trials — one model gained an advantage
  by reading git history across trials.

Rules this imposes on our pack:

1. **Fresh fixture copy per trial.** Never reuse a workdir across runs;
   prior runs' artifacts (git history, caches, notes) are contamination.
2. **Paired-difference comparisons.** When comparing two candidates, run
   both on the same fixture vintage and report per-case differences, not
   just aggregate means.
3. **Anchor set detects judge drift.** Keep a fixed set of human-graded
   candidate outputs; re-run the judge on them whenever the judge model or
   rubric changes — drift in anchor scores means the judge moved, not the
   candidates.

Full citations: `docs/landscape.md`, items A5, D20, D22.
