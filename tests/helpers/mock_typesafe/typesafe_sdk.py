"""MOCK typesafe_sdk — pack regression suite only. Canned answers for
pipeline validation (tests/test_judge_pipeline.py and tests/run_all.py).

Driven by MOCK_RUN=1|2|3 for repeat-run variation. Self-contained copy;
never import the dry-run one from results/. Scores are fixed to exercise
aggregation, flagging, and calibration — not to grade real candidates.
"""


class _Question:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class Score(_Question):
    pass


class Choice(_Question):
    pass


class Noul(_Question):
    pass


# (score_items, noul_value) per run; score items order:
# t1_arch, t1_recall, t1_risks, t1_plan, t1_trust (0-3 each)
_CANNED = {
    "1": {"scores": [2.5, 2.2, 2.6, 2.4, 2.3], "noul": 0.85,
          "conf": [0.82, 0.78, 0.70, 0.85, 0.80, 0.52]},
    "2": {"scores": [2.3, 2.0, 2.5, 2.2, 2.0], "noul": 0.80,
          "conf": [0.80, 0.75, 0.68, 0.82, 0.77, 0.60]},
    "3": {"scores": [2.6, 2.4, 2.7, 2.5, 2.4], "noul": 0.88,
          "conf": [0.85, 0.80, 0.72, 0.86, 0.83, 0.55]},
}


class _Answer:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class _Response:
    def __init__(self, answers):
        self.answers = answers


class TypeSafeClient:
    def __init__(self, *a, **k):
        pass

    def system_one(self, state=None, questions=None):
        import os
        run = os.environ.get("MOCK_RUN", "1")
        canned = _CANNED.get(run, _CANNED["1"])
        answers = {}
        score_ids = ["t1_arch", "t1_recall", "t1_risks", "t1_plan", "t1_trust"]
        all_ids = score_ids + ["t1_precision"]
        for i, qid in enumerate(all_ids):
            q = (questions or {}).get(qid)
            kind = type(q).__name__ if q is not None else (
                "Noul" if qid == "t1_precision" else "Score")
            if kind == "Score":
                answers[qid] = _Answer(
                    score=canned["scores"][score_ids.index(qid)],
                    confidence=canned["conf"][i])
            elif kind == "Noul":
                answers[qid] = _Answer(noul=canned["noul"],
                                       confidence=canned["conf"][i])
            else:
                answers[qid] = _Answer(choice="n/a", probabilities={},
                                       confidence=canned["conf"][i])
        return _Response(answers)
