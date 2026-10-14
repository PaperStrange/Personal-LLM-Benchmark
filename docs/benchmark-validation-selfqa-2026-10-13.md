# Self-Q&A: validating our benchmark pack's goals vs OmegaUse-OfficeVal, AssemblyAI Voice Bench, MLPerf v6.1 post-training

Date: 2026-10-13. Purpose: Sakura's instruction — "validate the goal of our benchmark against
existed one to iterate the whole framework." Solo adversarial pass BEFORE the iteration proposal.

## Our pack's goal (from GOAL.md + methodology.md)

Pick the right LLM + harness for a startup's legacy-codebase workflow under a $25 budget
(standing chat decision, Sakura 2026-10-03 — not yet written into GOAL.md/methodology.md).
Three tasks mirror the actual work: T1 legacy review, T2 multi-agent feature build,
T3 plugin/skill install. Judge tiering T0 (free deterministic) → Jev (cheap) → senior (expensive
spot-checks). Synthetic private fixture for contamination resistance. pass@k + pass^k, calibration
ritual, tie bands, mandatory harness disclosure, raw-model baselines.

## Q1: Is our goal the same as theirs, or are we measuring something different?

- **OmegaUse**: same *shape* of decision (which agent for real work?) but different *work*
  (office-suite deliverables vs code workflow) and a sharper economic frame: they don't ask
  "which scores highest" but "which captures the most economically important tasks." Their
  headline result — ranking FLIPS under value weighting — is a direct challenge to our goal:
  our scorecard currently can't even express "task A matters 5× task B."
- **AssemblyAI**: same shape (which model per workload under cost constraint), narrower domain
  (voice post-processing). Their goal is explicitly *routing*, not ranking: "start with the model
  in the column you optimize for." Our pack produces one ranked list; we never ask whether the
  answer should be "Luna for T1, Astra for T2." **Honest caveat**: if scale stratification
  (proposed Tier 2.4) ever reveals rank crossovers, the single-ranked-list output is wrong and
  this routing question reopens — not pre-decided here.
- **MLPerf**: different goal entirely (rank training *systems*, fixed model). Not a competitor
  to our goal; useful only as methodology validation.

**Verdict**: Our goal is distinct and defensible (code-workflow + harness selection under startup
budget — none of the three cover this). But OmegaUse exposes that our goal is *under-specified*:
"pick the right model" without economic weights is a ranking without a decision rule.

## Q2: What do they prove that we merely assert?

- **pass@k**: we assert pass@k + pass^k is the right framing (citing τ-bench). MLPerf *measured*
  it: pass@4 has the lowest coefficient of variance among the alternatives, even at temperature 0.
  → Adopt pass@4 as headline with their citation; it's no longer just our assertion.
- **Harness disclosure**: we require it (citing Claw-SWE-Bench 27.4pp swings). MLPerf found
  harness choice "strongly influenced solve rate" in RLVR rollouts. → We're directionally right;
  consider *weighting* harness in the analysis, not just disclosing it.
- **Hidden answer keys**: we assert contamination resistance via synthetic fixture + hidden
  inventory. OmegaUse *never discusses contamination* — novel-by-construction but no stated
  defense against future ingestion. Our rotation is arguably stronger but its effectiveness is
  [OPEN] (unmeasured) — no superiority claimed.
- **Cost as first-class**: we assert budget matters ($25 cap, per-tuple soft caps). All three
  *operationalize* it (MLPerf: budget IS the benchmark; OmegaUse: value-weighted scores;
  AssemblyAI: $/audio-hour in every cell). We only use budget as an abort threshold. →
  Biggest validated gap.

## Q3: What's the strongest argument AGAINST adopting their ideas?

- **OmegaUse price proxies**: requires human experts/quotes per task. For a 3-task pack this is
  bounded (not 100 tasks), but expert estimates are still subjective and the consistency rule
  is ad hoc. Risk: we add noisy weights that flip rankings on noise, not signal. Mitigation:
  report BOTH raw and price-weighted rankings (as they do) and let the flip be visible.
- **OmegaUse human labor baselines**: needs ≥2 people doing each task under quality gates.
  That's Sakura's time or hired time — real cost for a zero-spend-leaning project. Mitigation:
  defer to "moderate" tier; the $/task column (free, from token logs) captures 80% of the value.
- **AssemblyAI dual judges**: doubles judge spend on the sampled items. Our judge budget is
  already the binding constraint ($25). Mitigation: sample small (e.g. 20% of items), and the
  Jev key is reportedly landing tonight — reprice after.
- **AssemblyAI scale stratification**: needs a second fixture scale. We have the rotation
  script (`rotate_fixture.py`) but not a *larger* fixture. Building one is real work.
  Mitigation: tier as "moderate," do after the first candidate campaign.
- **MLPerf post-training lineage**: free to record, but risks becoming trivia if it doesn't
  predict anything. Mitigation: record it, test the correlation after 2+ campaigns, drop if null.

## Q4: What would make our framework *worse* if we copied blindly?

- **AssemblyAI's "no composite score"**: they leave the tradeoff to the reader because their
  audience is engineers routing workloads. Our audience is Sakura making ONE buy decision —
  he needs a ranked list with a decision rule, not a scatter plot. → Take their $/task column
  and tie-break rules, NOT their refusal to rank.
- **OmegaUse's pure-verifier grading**: they reject LLM judges for cross-time stability. Our
  tasks (code review quality, coordination) can't be graded by execution alone — T1's rubric
  needs judgment. → Take their negative-weight damage items and usability gates, NOT their
  no-LLM-judge stance.
- **MLPerf's fixed-quality framing**: pinning quality and measuring time-to-target works for
  training systems, not for picking between fixed models. → Take "budget as metric," NOT their
  experimental design.

## Q5: What does the Jev key landing tonight change?

Everything priced in "judge spend" gets cheaper to test. The dual-judge sample (Q3) and the
calibration-convergence loop both become affordable. Priority order for tonight if the key lands:
(1) verify key + response shape [already planned], (2) run Gate 4 calibration, (3) THEN apply
the cheap framework iterations ($/task column, reliability metric, latency, tie-break rule —
all free), (4) candidate runs with the new columns live.

## Q6: What is the single highest-leverage iteration?

**$/task per candidate per task in the scorecard, with a stated decision rule for when the
quality-per-dollar ranking governs.** It's cheap (manual population from dashboards; the schema
columns already exist), all three external benchmarks converge on it, and it directly serves
the $25-cap decision. Everything else is refinement; this is the missing column that makes the
budget a metric instead of a guardrail.

## Sources (evidence trail)

- OmegaUse-OfficeVal: https://arxiv.org/html/2607.27155v1 · https://omegause-officeval.github.io
- AssemblyAI Voice Standard Bench: https://www.assemblyai.com/blog/voice-standard-bench
- MLPerf Training v6.1 post-training: https://mlcommons.org/2026/09/mlperf-training-llm-post-training/
- All external claims [SECONDARY] (researcher-read 2026-10-13, not first-hand).
