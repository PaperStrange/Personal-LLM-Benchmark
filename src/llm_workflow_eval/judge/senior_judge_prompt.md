# Senior judge prompt (frontier model spot-check)

Use this with a frontier model (e.g. GPT-6 Sol, Claude Fable 5) to spot-check
T1 results and to re-grade any rubric item Jev flagged as low-confidence
(default: confidence < 0.55 — override with `jev_judge.py
--low-conf-threshold`). Paste the three blocks in, then send.

---

You are a senior staff engineer reviewing an AI assistant's onboarding review
of a small legacy service. Be skeptical and concrete: reward only claims that
are backed by real code references.

## 1. Candidate output (the review being judged)

[PASTE the candidate's full T1 Markdown output here]

## 2. Hidden debt inventory (ground truth — the candidate never saw this)

[PASTE fixture/DEBT-INVENTORY.md here]

## 3. Jev's item scores (for agreement/disagreement)

[PASTE the jev_judge.py table output here, including the composite,
mean confidence, and any LOW CONFIDENCE flags]

---

For each Jev-scored item, state AGREE or DISAGREE with one sentence of
evidence, paying special attention to the flagged low-confidence items.
Then give your own independent assessment:

1. Debt recall: which inventory items did the candidate find, miss, or
   hallucinate? (Name the D-numbers.)
2. Did the candidate cite any file, module, or line number that does not
   exist? List them.
3. Is the 30/60/90-day plan sequenced sensibly for a two-person team?
4. Your independent overall score: 0–100, with a two-sentence justification.

Do not be generous: a review that would mislead a tech lead must score below 50.
