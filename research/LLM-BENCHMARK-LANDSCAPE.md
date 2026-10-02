# LLM Benchmark Landscape — knowledge base for this pack

Surveyed 2026-09-30. Each entry: what the work found, and the concrete
implication for this evaluation pack. This is a living document — add new
findings with their implications as the field moves.

## A. Agentic coding benchmarks

**1. SWE-bench (Jimenez et al., ICLR 2024, arXiv 2310.06770).**
2,294 real GitHub issues graded by executing fail-to-pass / pass-to-pass
tests — no judge model. Established that execution-based grading is objective and cheap — but only
as strong as the tests behind it (see item 4: 31% of SWE-bench "successes"
passed via weak tests). No model can talk its way past a good test; a bad
test is no gate at all.
→ *Implication:* the precedent for our T0 deterministic gate running before
any judge spend. Execution checks are the only grade no model can talk past.

**2. SWE-bench Verified (OpenAI, 2024).** 500 human-validated instances;
frontier models hit ~70–80% by 2025, and OpenAI withdrew from it, citing
contamination and flawed tests that reward shortcuts.
→ *Implication:* our synthetic, private, disposable fixture is structurally
immune to this failure mode (no public repo, no training leakage). State this
as a design advantage, not a convenience.

**3. SWE-bench Pro (Scale AI, 2025, arXiv 2509.16941).** 1,865 problems,
multi-file patches (avg 107 lines / 4.1 files), contamination-resistant via
GPL/commercial code acquisition; top models below ~45–59% Pass@1.
→ *Implication:* adopt the anti-contamination principle as pack policy —
rotate/regenerate the synthetic fixture's identifiers periodically so the
debt inventory never becomes a static target. Caveat: copyleft-sourcing as
a "legal deterrent" against training inclusion is an assumption, not a
measured guarantee — our immunity claim rests on the fixture being private
and synthetic, not on any license property.

**4. SWE-bench+ (Oct 2024, arXiv 2410.06992).** Manual audit of "successful"
patches: 32.67% passed via solution leakage (fix visible in issue text),
31.08% via weak tests; filtering dropped SWE-Agent+GPT-4 from 12.47% to
3.97% resolution.
→ *Implication:* the empirical justification for our hidden
`DEBT-INVENTORY.md` — the candidate must never see the grading key, only the
code. Add a leakage audit: check no debt anchor is spelled out in
comments/docstrings the candidate can read.

**5. Terminal-Bench 2.x (Harbor, 2025).** 89 containerized terminal tasks;
its 2.0 leaderboard ran 101 agent configurations across 23 scaffolds.
LangChain reported jumping from outside the top-30 to top-5 by changing
only the harness (self-reported by the vendor, Feb 2026 — treat as a
directional datapoint, not an independent measurement).
→ *Implication:* the gold-standard precedent for our "vary the harness, fix
the model" protocol and for `tasks/BASELINES.md` — candidates must disclose
their harness, not just the model.

**6. Commit0 (2024, arXiv 2412.01769).** Agents generate entire libraries from
specs + starter repos, iterating on execution feedback — repo-level
generation, not single-function completion.
→ *Implication:* supports our T2 implement-and-self-verify loop; suggests a
future stress variant — delete a fixture module and require regeneration with
tests as the only oracle.

**7. DevEval (Li et al., 2024, arXiv 2405.19856).** 1,874 samples across 117
repos, decomposing development into staged tasks with per-phase reference
inputs, measuring correctness, robustness, and quality — not just binary
pass.
→ *Implication:* supports our staged T2 artifacts (PLAN → code → tests →
REVIEW) and grading intermediate artifacts, not only the final diff.

**8. BountyBench (2025, arXiv 2505.15216).** Attacker/defender agents on
bug-bounty scenarios scored across Detect → Exploit → Patch tiers.
→ *Implication:* a template for T3 expandability scoring — tier plugin
installs (discovered / installed / functional / recovered-from-error) rather
than binary success.

**9. SWE-rebench (Nebius, 2025, arXiv 2505.20411).** Continuously refreshed,
decontaminated, temporally-filtered tasks (21,000+); shows a ~20pp gap vs
SWE-bench Verified scores.
→ *Implication:* justification for fixture rotation — report our scores as
"on this fixture vintage" with a date stamp.

## B. Judge models & calibration

**10. Trust or Escalate (arXiv 2407.18370, 2024).** Selective evaluation:
cheap models judge first, escalate to stronger ones only when needed, with a
provable guarantee of a user-specified human-agreement level.
→ *Implication:* the paper inspires our T0 → Jev → senior cascade shape —
cheap first, escalate on uncertainty. Its provable-guarantee machinery is
*not* implemented here: our 0.55 confidence cutoff is exactly the kind of
uncalibrated threshold the paper's method replaces. Long-term goal: replace
the cutoff with a calibrated target agreement level.

**11. Overconfidence in LLM-as-a-Judge (2025, arXiv 2508.06225) + Rethinking
Verbalized Confidence (Hsiao, 2026, arXiv 2609.10996).** Predicted confidence
systematically overstates correctness; on post-2025 proprietary models,
verbalized confidence is now the more robust soft signal than logprobs.
→ *Implication:* never trust Jev's raw confidence — our calibration.csv
ritual exists precisely because of this. Consider TH-Score-style
high/low-interval agreement in `calibration.py`.

**12. A Survey on LLM-as-a-Judge (Gu et al., 2024, arXiv 2411.15594).**
Taxonomy of judge biases (position, verbosity, self-preference) and
calibration methods.
→ *Implication:* keep as the reference citation; its bias list is a checklist
for auditing `judge/jev_judge.py`'s rubric wording.

**13. Autorubric diagnostics (2025, arXiv 2603.00077).** Diagnoses severe
validity failures in LLM-as-judge benchmarks; cites Feuer et al. (2025),
who found ~55% of judgment variance on Arena-Hard-Auto unexplained by
rubric criteria (over 90% for some judges). Proposes *schematic adherence*
(how much the verdict is explained by the explicit rubric) and
psychometric validity; warns ELO/Bradley-Terry aggregation can mask true
uncertainty.
→ *Implication:* (a) log how often Jev's verdicts cite specific rubric
items; (b) don't over-interpret small composite-score differences between
candidates — report T0, pass@k/pass^k, and calibration alongside.

## C. Reliability, gaming & contamination

**14. τ-bench (Yao et al., 2024, arXiv 2406.12045).** Introduced **pass^k** —
probability *all* k independent trials succeed (GPT-4o: pass^1 = 61.2% but
pass^8 < 25% on retail); τ²-bench (2025) extends it.
→ *Implication:* the canonical citation for our pass@k vs pass^k reporting:
pass@k = capability, pass^k = reliability.

**15. Beyond Pass@k (Jiang et al., arXiv 2608.14711).** Diagnoses a
widespread operationalization error: implementations set *n* to the number
of unit tests in one submission rather than the number of *independent
rollouts*, inflating scores by 0.85–0.97 absolute. Proposes reliability@k
with n = independent rollouts.
→ *Implication:* `judge/aggregate.py` now asserts its inputs are distinct
independent rollout JSONs (see the independence guard in the code). Never
aggregate tests-within-a-run as if they were rollouts.

**16. Reliability at long horizons (2025–2026, direction; specific metric
proposals unsourced — do not cite the acronyms below as established).**
Capability ≠ reliability: several field reports note rankings inverting
between medium and very-long horizons, and propose trace-based signals
(e.g. sliding-window entropy over tool-call sequences as a cheap,
model-agnostic loop/thrash detector). The concrete metric names floating
around this space still lack a citable source.
→ *Implication:* consider a lightweight thrash check for T2 — compute
tool-call entropy over the agent's action trace and flag looping as a
discipline signal. Source a proper citation before building on any named
metric.

**17. The SWE-Bench Illusion (ICSE 2026, arXiv 2506.12286).** Models
identify buggy file paths from issue text alone at 76% on SWE-bench repos
vs 53% off-benchmark (5-gram overlap 35% vs 18%) — memorization, not
reasoning.
→ *Implication:* the fixture must stay private and synthetic; any future
evaluation on real repos needs a memorization-control probe (e.g.
file-localization on repos outside the training window).

**18. Test overfitting (arXiv 2511.16858) + Goodhart taxonomy (Manheim &
Garrabrant, MIRI 2018).** Agent patches routinely pass *visible* tests while
failing held-out ones — any test the agent can see, it can overfit. Static
benchmarks are ultimately gameable; defenses are dynamic/rotating
benchmarks and the "five walls" (frozen instrument, blind judge, holdout).
→ *Implication:* our hidden-T2-tests design is exactly the recommended
defense — never show candidates the hidden tests.

## D. Multi-agent & harness evaluation

**19. MultiAgentBench / MARBLE (Zhu et al., ACL 2025, arXiv 2503.01935).**
First comprehensive multi-agent benchmark across topologies, with
milestone-based KPIs — coordination quality, planning scores, communication
metrics — beyond task completion. Follow-ups: MASBENCH (2026), Silo-Bench.
→ *Implication:* our T2 currently grades artifacts + timestamps; MARBLE
gives the vocabulary for the next upgrade — grade *coordination quality*
(did the reviewer actually catch planted issues? did the plan match the
implementation?) as explicit rubric items.

**20. Claw-SWE-Bench (2026, arXiv 2606.12344) + the 176-setting harness
analysis (Decoding AI / Towards AI newsletter, Sept 2026 — industry
analysis, not peer-reviewed).** Pinning everything except the harness
moves Pass@1 by up to 27.4pp — nearly the full spread across nine
frontier models. The newsletter analysis found one context-management
setting swinging a single model 6.40% → 58.40% on SWE-bench Verified.
→ *Implication:* the empirical backbone of `tasks/BASELINES.md` — a reported
score is a (harness, model, config) tuple, and the harness is a first-class
experimental variable. Harness disclosure on every candidate report is
non-negotiable.

**21. MCP-Atlas (Scale AI, 2026, arXiv 2602.00933).** 1,000 tasks across 36
real MCP servers; prompts never name tools (discovery among distractors);
scored by **claim-level rubric** — ground truth decomposed into atomic
verifiable claims, Coverage = mean, Pass at ≥ 0.75 — so valid alternative
trajectories get full credit; 500 public + 500 private tasks for leaderboard
integrity.
→ *Implication:* the best template for our T3 rubric — score plugin installs
by atomic verifiable claims (discovered / installed / configured /
functional / recovered-from-error) and keep a private holdout split of
extension tasks.

**22. Anthropic: "Demystifying Evals for AI Agents" (2026) + "A Statistical
Approach to Model Evals" (arXiv 2411.00640).** Start with 20–50 tasks from
real failures; combine code-based, model-based, and human graders; **grade
what the agent produced, not the path**; report error bars and paired
per-case differences; isolate trials (one model gained advantage by reading
git history across trials); pin the judge model, inject ground truth the
judge can't invent, keep a human-labeled anchor set to detect judge drift.
→ *Implication:* near-total alignment with our pack — adopt paired-difference
candidate comparisons and the anchor-set-detects-drift practice; the
git-history anecdote is a concrete T2 isolation rule (fresh fixture copy per
trial).

## Where the literature pressures our current design

1. **Our |diff| ≤ 0.15 agreement rule is ad hoc.** Literature supports
   Cohen's κ (categorical verdicts), TH-Score (confidence), or psychometric
   validity — not a flat threshold. Keep as a v1 heuristic; plan a κ-based
   upgrade once ≥ 2 senior graders exist.
2. **22 anchors is small for statistical discrimination.** Anthropic's 20–50
   task guidance and SWE-bench Pro's scale imply our debt inventory will
   struggle to separate close candidates — report confidence intervals, not
   point estimates, and consider growing the inventory.
3. **The 0.55 escalation cutoff should become a target agreement level.**
   Item 10's provable-guarantee framing is strictly better: "escalate until
   senior-agreement ≥ 0.80" is auditable; "conf < 0.55" is not.
4. **T2 grading should include coordination quality** (item 19) — planted
   reviewer-catchable issues would be a real coordination test; our timestamp
   check is only a start.
5. **Harness disclosure is non-negotiable** (items 5, 20, 22) — any score
   reported without naming the harness attributes the score to the wrong
   cause. `results/scorecard.csv` already requires a `harness` column.
6. **Don't over-interpret small composite differences** (item 13) — report
   T0, pass@k/pass^k, and calibration alongside every composite.
