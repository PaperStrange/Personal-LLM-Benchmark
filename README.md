# Personal LLM Benchmark

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![tests](https://github.com/PaperStrange/Personal-LLM-Benchmark/actions/workflows/tests.yml/badge.svg)](https://github.com/PaperStrange/Personal-LLM-Benchmark/actions/workflows/tests.yml)
[![Evidence](https://img.shields.io/badge/claims-%5BREAL%5D%2F%5BSIM%5D%2F%5BOPEN%5D-blue.svg)](docs/methodology.md)

Evaluate new models and agent harnesses against **your** workflow — not the news cycle — without burning work time or subscription budget. Three workflow criteria, three concrete tasks, on a small synthetic fixture codebase. Every claim carries an evidence label: `[REAL]` genuinely executed, `[SIM]` fabricated input through real plumbing, `[OPEN]` unvalidated gap.

## The three tasks

| Task | Criterion | What the candidate does |
|---|---|---|
| T1 | Plan & solve legacy; global project review for alignment | Onboard read-only to the fixture and write an architecture map, debt inventory, risk register, and 30/60/90-day plan |
| T2 | Multi-agent co-working, efficient and disciplined | Implement `apply_discount` via 3 separate subagents: planner → implementer → reviewer |
| T3 | Expandability: third-party plugins/agents/GitHub repos | Install one third-party plugin/skill/MCP server from GitHub and complete a real task with it |

Fixture: `fixture/legacy-billing/` — a fictional invoicing service whose owner left in 2023. Synthetic and private: no public repo, no training footprint, contamination-resistant by construction.

## Quickstart

```bash
# 1. Validate the evaluator itself (stdlib only, zero spend)
python3 tests/run_all.py

# Optional: install as a package for `import llm_workflow_eval`
pip install -e .

# 2. Run the free T0 gate on a candidate BEFORE any judge spend
python3 src/llm_workflow_eval/judge/t0_checks.py --task T1 \
  --candidate examples/t1-sample-candidate.md \
  --inventory fixture/DEBT-INVENTORY.md \
  --workdir fixture/legacy-billing
# exit 0 required — fix the run and re-check if it fails

# 3. Grade with Jev (cents per call)
export TYPESAFE_API_KEY=...
python3 src/llm_workflow_eval/judge/jev_judge.py \
  --rubric rubrics/rubric-T1.json --candidate examples/t1-sample-candidate.md \
  --inventory fixture/DEBT-INVENTORY.md --json-out results/t1-r1.json
```

See `examples/` for a runnable sample.

## The funnel: evaluate many, pay for few

| Stage | Cost | What |
|---|---|---|
| 0 — Reuse public data | $0 | Pre-screen on DeepSWE / Artificial Analysis leaderboards; kill obvious losers |
| 1 — Free-tier smoke tests | $0 | One T1 run per survivor on free tiers (GPT Luna, Gemini) |
| 2 — Jev-graded pack runs | cents | T1–T3 on finalists, graded by `jev_judge.py` |
| 3 — Deep runs (gated) | $$ | Top 1–2 tuples only: `--repeat 5+`, senior spot checks, credit check first |

## Methodology (summary)

**Tier order: T0 → Jev → senior.** `t0_checks.py` is the free deterministic hard gate (section presence, `file:line` refs within bounds, ≥1 ref required since gate v2). A T0 pass buys one Jev call; the senior judge only sees sampled runs plus low-confidence items. **Baselines:** run each task once raw, no harness — the delta is the harness's measured contribution. **Repeats:** minimum 3 per (task, candidate); report **pass@k** (capability) and **pass^k** (reliability) — single runs mean nothing. **Calibration ritual:** log senior spot-checks, recalibrate quarterly.

Full methodology, threats-to-validity, and the research survey: [`docs/`](docs/).

## Layout

```
src/llm_workflow_eval/   the machinery (judge, drivers)
tasks/  rubrics/  fixture/   the benchmark definition
docs/      methodology and runbooks
tests/     the pack's own regression suite ("eval the evals")
results/   curated qualification evidence
examples/  runnable examples
dashboard/  admin dashboard (ngx-admin: overview, gates, results pages)
```

## Citation

```bibtex
@misc{personal-llm-benchmark-2026,
  title = {Personal LLM Benchmark: A 3-Task Workflow Eval Pack for Models and Agent Harnesses},
  howpublished = {\url{https://github.com/PaperStrange/Personal-LLM-Benchmark}},
  year = {2026}
}
```

## License

MIT — see [LICENSE](LICENSE). Contributing: [CONTRIBUTING.md](CONTRIBUTING.md). Security: [SECURITY.md](SECURITY.md).
