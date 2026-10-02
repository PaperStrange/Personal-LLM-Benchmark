"""Ollama-backed typesafe_sdk shim — a REAL open-source model as the cheap judge.

Implements the same interface as the real typesafe_sdk (TypeSafeClient,
Score / Choice / Noul question types, .system_one(state, questions)) but
calls a local ollama model over HTTP. Used to close one true evaluation
loop with zero spend and zero credentials.

HONESTY (read before using): this is NOT Jev. Every result produced
through this shim must be labeled
  "judge: ollama/<model> (open-source stand-in for the cheap-judge role)".
It exercises the judge plumbing (prompt -> score -> aggregate -> scorecard)
with a real model, but says nothing about Jev's discrimination or
calibration — those remain [OPEN] until a live Jev call.

Usage:
    ollama serve &                         # once
    # import or pull a local model, e.g.
    # ollama create qwen2.5-1.5b-local -f Modelfile   # once
    PYTHONPATH=tests/helpers/ollama_judge TYPESAFE_API_KEY=shim \
        python3 judge/jev_judge.py --rubric rubrics/rubric-T1.json \
        --candidate <cand> --inventory <inv> --json-out <out>

Env:
    OLLAMA_MODEL  model tag (default qwen2.5-1.5b-local)
    OLLAMA_HOST   base URL (default http://localhost:11434)
    OLLAMA_TIMEOUT_S  per-call timeout (default 600)
"""

import json
import os
import sys
import urllib.request

MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5-1.5b-local")
HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
def _get_timeout():
    raw = os.environ.get("OLLAMA_TIMEOUT_S", "600")
    try:
        return float(raw)
    except ValueError:
        raise ValueError(
            "OLLAMA_TIMEOUT_S=%r is not a number; set it to seconds "
            "(default 600)" % raw)


TIMEOUT_S = _get_timeout()
MAX_ATTEMPTS = 3


class _Question:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class Score(_Question):
    pass


class Choice(_Question):
    pass


class Noul(_Question):
    pass


class _Answer:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class _Response:
    def __init__(self, answers):
        self.answers = answers


def _call_ollama(prompt):
    body = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0, "num_predict": 400},
    }).encode("utf-8")
    req = urllib.request.Request(
        HOST + "/api/generate", data=body,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        return json.load(resp)["response"]


def _extract_json(text):
    """Pull the first JSON object out of model output. Raises ValueError.

    Tries a raw parse first, then scans for a balanced {...} span starting
    at the first '{' (string-aware), so multiple objects or trailing braces
    in prose don't burn retries on an unparseable greedy span.
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    if start < 0:
        raise ValueError("no JSON object in judge output: %r" % text[:300])
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i + 1])
    raise ValueError("unbalanced JSON object in judge output: %r" % text[:300])


def _clamp(x, lo, hi):
    clamped = max(lo, min(hi, x))
    if clamped != x:
        # Clamping hides a misbehaving judge; say so on stderr so a run
        # log shows it happened.
        print("warning: judge value %r clamped to [%r, %r]" % (x, lo, hi),
              file=sys.stderr)
    return clamped


class TypeSafeClient:
    """system_one(state, questions) -> _Response, via the local model."""

    def system_one(self, state=None, questions=None):
        state = state or {}
        questions = questions or {}
        answers = {}
        for qid, q in questions.items():
            kind = type(q).__name__
            if kind == "Score":
                answers[qid] = self._ask_score(qid, q, state)
            elif kind == "Noul":
                answers[qid] = self._ask_noul(qid, q, state)
            elif kind == "Choice":
                answers[qid] = self._ask_choice(qid, q, state)
            else:
                raise ValueError("unknown question kind: %r" % kind)
        return _Response(answers)

    def _state_block(self, state):
        parts = []
        if state.get("candidate_output"):
            parts.append("## CANDIDATE OUTPUT (the work being graded)\n"
                         + state["candidate_output"])
        if state.get("debt_inventory"):
            parts.append("## KNOWN DEBT INVENTORY (ground truth answer key; "
                         "the candidate did NOT see this)\n"
                         + state["debt_inventory"])
        return "\n\n".join(parts)

    def _ask(self, prompt, want):
        last_err = None
        for _ in range(MAX_ATTEMPTS):
            raw = _call_ollama(prompt)
            try:
                data = _extract_json(raw)
                return want(data)
            except Exception as e:  # noqa: BLE001 - any per-attempt failure
                # burns one retry, never the whole run
                last_err = e
        raise ValueError(
            "judge model failed to emit valid JSON after %d attempts: %s"
            % (MAX_ATTEMPTS, last_err))

    def _ask_score(self, qid, q, state):
        n = len(q.criteria)
        crit = "\n".join("%d: %s" % (i, c) for i, c in enumerate(q.criteria))
        prompt = (
            "You are a strict technical judge. Read the material, then "
            "return ONLY a JSON object.\n\n"
            "## TASK\n%s\n\n## RUBRIC (score 0-%d; higher is better)\n%s\n\n%s\n\n"
            "Return ONLY this JSON (no prose, no markdown fences):\n"
            '{"score": <integer 0-%d>, "confidence": <0.0-1.0>, '
            '"rationale": "<one sentence>"}'
            % (q.instructions, n - 1, crit, self._state_block(state), n - 1))

        def want(data):
            raw_score = data["score"]
            # A non-integer score is a misbehaving judge: burn a retry
            # rather than silently truncating (int(2.7) -> 2).
            if isinstance(raw_score, bool) or float(raw_score) != int(
                    float(raw_score)):
                raise ValueError(
                    "non-integer score %r from judge" % (raw_score,))
            score = _clamp(int(float(raw_score)), 0, n - 1)
            conf = _clamp(float(data["confidence"]), 0.0, 1.0)
            return _Answer(score=score, confidence=conf,
                           rationale=str(data.get("rationale", ""))[:200])

        return self._ask(prompt, want)

    def _ask_noul(self, qid, q, state):
        prompt = (
            "You are a strict technical judge. Read the material, then "
            "return ONLY a JSON object.\n\n"
            "## TASK\n%s\n\n%s\n\n"
            "Return ONLY this JSON (no prose, no markdown fences):\n"
            '{"noul": <0.0-1.0, higher means the statement holds>, '
            '"confidence": <0.0-1.0>, "rationale": "<one sentence>"}'
            % (q.instructions, self._state_block(state)))

        def want(data):
            noul = _clamp(float(data["noul"]), 0.0, 1.0)
            conf = _clamp(float(data["confidence"]), 0.0, 1.0)
            return _Answer(noul=noul, confidence=conf,
                           rationale=str(data.get("rationale", ""))[:200])

        return self._ask(prompt, want)

    def _ask_choice(self, qid, q, state):
        crit = "\n".join("- %s" % c for c in q.criteria)
        prompt = (
            "You are a strict technical judge. Read the material, then "
            "return ONLY a JSON object.\n\n"
            "## TASK\n%s\n\n## OPTIONS\n%s\n\n%s\n\n"
            "Return ONLY this JSON (no prose, no markdown fences):\n"
            '{"choice": "<exactly one option string>", '
            '"probabilities": {"<option>": <0.0-1.0>, ...}, '
            '"confidence": <0.0-1.0>}'
            % (q.instructions, crit, self._state_block(state)))

        def want(data):
            probs = {str(k): _clamp(float(v), 0.0, 1.0)
                     for k, v in dict(data["probabilities"]).items()}
            return _Answer(choice=str(data["choice"]),
                           probabilities=probs,
                           confidence=_clamp(float(data["confidence"]),
                                             0.0, 1.0))

        return self._ask(prompt, want)
