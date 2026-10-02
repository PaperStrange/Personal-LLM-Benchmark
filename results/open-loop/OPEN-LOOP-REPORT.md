# Open-loop report: one true calling loop with a local model (T1)

Date: 2026-09-30. Author: operator (Harry). Senior review: operator, labeled **non-independent**.

## Verdict

One genuine evaluation loop is closed: **real local candidate call → T0 gate → real local judge call → aggregate → scorecard**, zero spend, zero credentials. [REAL]

The loop's honest output is not a candidate ranking. It is two findings:

1. **The candidate (Qwen2.5-1.5B-Instruct, Q4_K_M) cannot do T1's core demand.** Deterministic debt recall is **0/22 in all 3 repeats**. It writes plausible-sounding reviews that cite zero exact `file:line` anchors. [REAL]
2. **The stand-in judge cannot be trusted to say so.** It scored these reviews 63.6–70.7/100 — every repeat above the 60 "success" threshold — and its recall item disagrees with the deterministic ground truth it was shown (scored 1/3, 2/3, 2/3 for an identical, unambiguous 0/22). The pipeline's own pass@k=1 / pass^3=1 therefore measures the judge's leniency, not candidate capability. [REAL]

This validates the plumbing and exposes exactly the weakness the Jev calibration gate exists to catch. It proves nothing about Jev, nothing about stronger candidates, and nothing about T2/T3.

## What ran

| Slot | Value | Evidence |
|---|---|---|
| Candidate | `ollama/qwen2.5-1.5b-local` — Qwen2.5-1.5B-Instruct GGUF (Q4_K_M) via local ollama 0.35.0, CPU-only | [REAL] local calls |
| Judge | `ollama/qwen2.5-1.5b-local` — open-weight stand-in for the cheap-judge role; **NOT Jev**; the **same model as the candidate, so NOT independent** | [REAL] local calls |
| Task | T1 global review, verbatim prompt from `tasks/T1-global-review.md`; fixture code/text files inlined verbatim including README.md (`__pycache__` excluded; harness adaptation — the model cannot browse files; task text unmodified) | [REAL] |
| Fixture vintage | v1-2026-09 (canonical; stamped in all 3 judge payloads) | [REAL] |
| Repeats | 3 independent rollouts (temperature 0.7) | [REAL] |
| Senior review | operator read of run 1 candidate vs judge payload; labeled **non-independent** (builder reviewing own loop) | [REAL] but not independent |
| Cost | $0.0000 — no API calls, no credentials used | [REAL] |
| Model license | Apache-2.0 for Qwen2.5-1.5B-Instruct (multiple secondary sources agree; the 3B/72B sizes carry custom licenses, 1.5B does not) — GGUF used is the official `Qwen/Qwen2.5-1.5B-Instruct-GGUF` quantization | [SECONDARY] |

Driver: `tools/open-loop/driver.py` (`--run 1..3`). Aggregation: `judge/aggregate.py` (guarded: independence + vintage; the numbers above were cross-checked by the new `tools/open-loop/aggregate.py` wrapper, which reuses `judge/aggregate.py`'s `aggregate_files` and adds the run-meta layer — T0 status, wall time, incomplete-run listing — writing `aggregate.json`). Scorecard: `results/open-loop/scorecard.csv`.

One additional genuine attempt preceded these runs: with the generation budget at 2500 tokens the model ran out of budget mid-risk-register, the 30/60/90-day plan section was never written, and T0 failed honestly (2/3 checks). The budget was raised to 4500 — a harness parameter, not a prompt change. Honest correction: the failed attempt's raw artifacts (candidate file, T0 log) were overwritten by the successful rerun under the same filenames, so only its outcome is recorded here — T0 FAIL at a 2500-token budget, then PASS at 4500. That outcome is real variance data; the raw files are not retained.

## Results

| Run | T0 | Composite | Deterministic recall | Judge recall item |
|---|---|---|---|---|
| 1 | PASS 3/3 | 63.6 | 0/22 | 1/3 (conf 0.90) |
| 2 | PASS 3/3 | 70.7 | 0/22 | 2/3 (conf 0.85) |
| 3 | PASS 3/3 | 70.7 | 0/22 | 2/3 (conf 0.95) |

Aggregate: composite mean **68.3**, std 3.3, min 63.6, max 70.7. pass@k=1, pass^3=1 at threshold 60 — **read the senior review before quoting this.**

All other judge items sat at 2/3 (arch, risks, plan, trust) and precision at noul 0.95, with confidences 0.85–0.95 and zero low-confidence flags.

## Senior review findings (non-independent)

Reading run 1's candidate against the rubric:

- **t1_recall 1/3 → should be 0/3.** Ground truth is 0/22 with correct references — the rubric's own bottom criterion ("Found almost none of the known debts"). The judge was shown the inventory and still gave 1/3, then 2/3 twice for the same ground truth.
- **The semantic-credit objection — answered.** A skeptic could argue 0/22 exact-anchor matching is too strict: the candidates describe several real debts in prose, so 1/3 or 2/3 might be defensible on a semantic reading. Three replies. (1) The T1 task contract is explicit — "Every issue you find, each with … an exact `file:line` reference" (`tasks/T1-global-review.md`) — and the rubric item the judge scored asks "what share of the known debts did the candidate actually find, *with correct file references*?" References are part of the graded construct, not optional decoration. (2) Run 1 names no files at all — not even `billing.py` — so its 1/3 is indefensible on any reading. (3) Conceded in part: runs 2/3 name real files (billing.py ×14, reports.py ×9 in run 2) without line numbers, so a lenient semantic reading could defend 1/3 ("a minority"); the judge's 2/3 ("most") still overshoots against 0/22 exact anchors. The discrimination critique therefore rests on the full pattern — risks/plan/trust at 2/3 vs senior 1/3, vacuous precision noul 0.95 for zero cited references, uniform 0.85–0.95 confidence with zero low-confidence flags — not on recall alone.
- **t1_risks 2/3 → should be 1/3.** The risk register is a verbatim copy of the debt list — no likelihood×impact ranking, no code cited, exactly what the prompt forbade.
- **t1_plan 2/3 → should be 1/3.** The plan is an unsequenced imperative rewrite of the same 7 items, naming no files per step, with no risk-reduction ordering.
- **t1_trust 2/3 → should be 1/3.** I would not trust this review as a basis for a real modernization decision.
- **t1_precision noul 0.95 is vacuous.** The candidate cited zero `file:line` references, so "cites only real references" holds trivially. A discriminating judge should penalize citing nothing at all.
- The judge is ~1 point generous on 3 of 6 items, uniformly confident (0.85–0.95), and never flags low confidence. That is the signature of a weak judge defaulting to middle scores — not of calibration.

## What this proves

- [REAL] The full evaluation pipeline executes against a real model with no mocks: prompt → generation → T0 → judge → aggregate → scorecard, with vintage stamping and independence guards intact. The scorecard.csv row is hand-written, not generated (disclosed in the driver docstring); everything upstream of it is executed.
- [REAL] T0 behaves as designed: it failed a genuinely truncated candidate and passed three structurally complete ones. T0 says "worth grading," and the grading then exposed the weakness — the pipeline stages compose correctly.
- [REAL] The deterministic recall check (0/22) is the trustworthy signal in this loop; it agrees with the senior read and disagrees with the stand-in judge.
- [REAL] A weak judge inflates composites past the success threshold. **Any pass@k/pass^k claim from this loop is a claim about the judge, not the candidate.** The 60 threshold is arbitrary for an uncalibrated judge.

## What this does NOT prove

- Nothing about Jev's discrimination or calibration — the live-Jev gate remains [OPEN] and is still required before any candidate comparison.
- Nothing about stronger candidates — a 1.5B CPU model was the smallest viable local option, chosen to close the loop at zero spend, not to represent candidate quality.
- Nothing about T2/T3 — only T1 ran.
- The judge and candidate being the same model means there is no independence anywhere in this loop. The sharpest form: *correlated blind spots* — the model's failures as candidate are the same model's failures as judge, so shared errors are undetectable by this loop — plus possible self-preference for its own generation style. It is plumbing validation, one level up from the dry run (real calls, real variance) but still not measurement validation.

## Open methodology questions raised by the loop

1. **[OPEN] T0 vacuous pass.** `t1_refs_valid` passes when a review cites zero `file:line` references. The T1 prompt demands exact references per debt item, so a zero-reference review is structurally non-compliant — yet T0 calls it worth grading. No comparison is in flight, so nothing is being ranked; the reason to defer the fix is that three runs already passed under current semantics, and a hotfix would retroactively reclassify completed runs. The change belongs in a reviewed design pass, so it is recorded, not changed.
2. **[OPEN] Success thresholds for uncalibrated judges.** pass@k/pass^k at threshold 60 is meaningless when the judge is lenient. Thresholds must be set per judge after calibration, not carried over from the Jev design point.
3. **[CLOSED 2026-09-30] Model license.** Qwen2.5-1.5B-Instruct is Apache-2.0 [SECONDARY] (convergent secondary sources; only the 3B/72B sizes carry custom licenses). The GGUF used is the official Qwen quantization. "Open-weight" was the honest label until this check.
4. **[OPEN] Stronger local candidates.** CPU-viable options (larger Qwen, Llama-3.x, Mistral instruct builds) are untested; a stronger local candidate is the next zero-spend step if Stage −1 stays blocked on credentials.

## Second loop: Llama-3.2-1B-Instruct (2026-09-30)

Same T1 task, same driver, second model — `ollama/llama3.2-1b-local` (Llama-3.2-1B-Instruct GGUF, Q4_K_M, bartowski quantization, sha256 `6f85a640…` [REAL — verified against ollama's content-addressed blob store], Llama 3.2 Community License [SECONDARY]; repro: `tools/open-loop/Modelfile.llama32-1b`). Driver changes for multi-model runs: `OPEN_LOOP_OUT` selects the results dir, `MODEL_PROVENANCES` stamps per-model provenance (unknown tags fail fast), and judge failures now persist raw output to `judge-runN.error.log`. Raw artifacts: `results/open-loop-llama32-1b/`. Scorecard: `results/open-loop-llama32-1b/scorecard.csv` (handwritten, as before).

**What happened: 3 attempts, 1 complete measurement.**

| Repeat | T0 | Judge | Composite | Deterministic recall |
|---|---|---|---|---|
| 1 | PASS 3/3 (4233-char candidate) | complete | 85.7 | 0/22 |
| 2 | FAIL 2/3 (1672-char truncated candidate: no risk register, no 30/60/90 plan) | not run — gate behaved | — | — |
| 3 | PASS 3/3 (3484-char candidate) | **FAILED** — judge failed to produce a parseable score within the 3-attempt retry budget (operator-observed console error: `ValueError: float() argument must be a string or a real number, not 'list'`; raw emission not retained — harness gap, now fixed; "invalid JSON" is not established, since valid JSON with a wrong-typed score field fails identically) | — | — |

The repeat set stands as run — no reruns to fill the gaps. Rationale: run 2 is genuine candidate variance, so rerunning would be cherry-picking; run 3's preregistered retry budget (`MAX_ATTEMPTS=3` in the judge shim) was already exhausted, and post-hoc extra retries would move the goalposts while selecting toward judge-compliant emissions. The one complete repeat's judge items: five items at 3.00/3 with confidence 1.00, `t1_precision` at 0.00 with confidence 0.00 (flagged for senior review). Mean confidence 0.83.

**Findings (observations [REAL]; interpretations preliminary — sample is 3 attempts, 1 complete run):**

1. **In this 3-attempt sample, the 1B rung fell below the stability floor for this loop.** T0 passed 2/3 (one truncated candidate) and 1 of the 2 judge calls failed to return a parseable score. The harness's cheap-judge plumbing assumes a judge model that can reliably emit structured JSON; Llama-3.2-1B breaks that assumption. This is a rung hypothesis, not an established property — but the loop is validated *by* failing informatively.
2. **In the single complete run, the leniency pattern is worse, not better.** It scored **85.7** — above the qwen stand-in's 63.6–70.7 — while deterministic recall was again **0/22** and the judge still awarded `t1_recall` 3.00/3 at confidence 1.00 (the qwen judge at least scored 1–2/3). If this pattern held, a weaker model as judge would be a *more* lenient judge here, not a stricter one — and the 85.7 would characterize judge leniency, not candidate capability. On n=1 that is an interpretation, not a measurement.
3. **pass@k over complete runs only.** `tools/open-loop/aggregate.py` now reports attempts vs complete runs separately and lists incomplete repeats with reasons; pass@k/pass^k are computed over complete runs (here pass@k=1, pass^1=1 at threshold 60 — a trivial statistic over n=1, labeled as such).
4. **Harness gap found and fixed.** Run 3's judge failure left no record of what the model emitted. The driver now writes the full judge stdout/stderr to `judge-runN.error.log` on failure.

**What this does NOT prove:** nothing about Llama-3.2-1B as a candidate beyond "too small for this T1 harness at this budget" — the T0 failure is a 1B-model finding, the judge failure is a 1B-as-judge finding, and the 85.7 is a judge-leniency artifact. No senior review was done on the llama candidates (scorecard: `senior_reviewed=no`). Still no Jev, no T2/T3, zero spend.

## Reproduction

```bash
cd ~/workspace/your_files/llm-workflow-eval-pack   # repo root; commands below are root-relative
export PATH="$HOME/workspace/.local/ollama-pkg/bin:$PATH"   # repo-local ollama; not on system PATH

# 1. Start the server detached (once; survives the shell):
setsid nohup ollama serve >/tmp/ollama.log 2>&1 < /dev/null &

# 2. Provision the model (once). Weights are NOT in the repo; download the
#    official Qwen Q4_K_M GGUF next to tools/open-loop/Modelfile and create:
#    curl -fsSL -o tools/open-loop/qwen2.5-1.5b-instruct-q4_k_m.gguf \
#      https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf
#    (sha256 6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e)
#    cd tools/open-loop && ollama create qwen2.5-1.5b-local -f Modelfile && cd ../..
#    Full provenance is also recorded per run in runN-meta.json (model_provenance).

# 3. Run the loop (each repeat: candidate -> T0 -> judge):
for n in 1 2 3; do python3 tools/open-loop/driver.py --run $n; done
python3 tools/open-loop/aggregate.py --out results/open-loop
#    (or the bare guarded judge path, without the run-meta layer:)
#    python3 judge/aggregate.py results/open-loop/judge-run1.json \
#        results/open-loop/judge-run2.json results/open-loop/judge-run3.json
# 4. The scorecard row is written by hand (disclosed in the driver docstring).

# Second model (llama3.2-1b-local). Provision once:
#    curl -fsSL -o tools/open-loop/Llama-3.2-1B-Instruct-Q4_K_M.gguf \
#      https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-3.2-1B-Instruct-Q4_K_M.gguf
#    (sha256 6f85a640a97cf2bf5b8e764087b1e83da0fdb51d7c9fab7d0fece9385611df83)
#    cd tools/open-loop && ollama create llama3.2-1b-local -f Modelfile.llama32-1b && cd ../..
# Then:
#    export OLLAMA_MODEL=llama3.2-1b-local
#    export OPEN_LOOP_OUT=$PWD/results/open-loop-llama32-1b
#    for n in 1 2 3; do python3 tools/open-loop/driver.py --run $n; done
#    python3 tools/open-loop/aggregate.py --out $PWD/results/open-loop-llama32-1b
```

Raw artifacts: `results/open-loop/` — candidates, T0 logs, judge payloads (each stamped with the stand-in judge's identity and a notional-only cost label), run metadata with model provenance, scorecard.
