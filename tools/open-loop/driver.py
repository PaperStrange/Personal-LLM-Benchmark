#!/usr/bin/env python3
"""Close one true T1 evaluation loop with a local open-weight model.

Pipeline per repeat: candidate generation (ollama) -> T0 gate ->
cheap judge (ollama-backed typesafe_sdk shim, NOT Jev).
Aggregation is done afterwards with tools/open-loop/aggregate.py; the scorecard
row is written by hand so its labels stay honest.

Usage:
    python3 tools/open-loop/driver.py --run 1   # repeat 1..k

Outputs (all under $OPEN_LOOP_OUT, default results/open-loop/):
    T1-candidate-ollama-run<N>.md, t0-run<N>.log,
    judge-run<N>.json (stamped with the stand-in judge identity),
    run<N>-meta.json (with model provenance)

Honest labels: candidate = ollama/<model>; judge = ollama/<model>
(open-weight stand-in for the cheap-judge role, and the SAME model as
the candidate, so the judge is NOT independent). Senior review is done
separately by the operator and labeled non-independent.

Env:
    LLM_PACK_REPO   pack checkout (default: derived from this file's path)
    OLLAMA_MODEL    model tag (default qwen2.5-1.5b-local)
    OLLAMA_HOST     base URL (default http://localhost:11434)
    OPEN_LOOP_OUT   results dir (default results/open-loop)
"""
import argparse
import datetime
import json
import os
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PACK = os.environ.get("LLM_PACK_REPO",
                       os.path.abspath(os.path.join(HERE, "..", "..")))
OUT = os.environ.get("OPEN_LOOP_OUT",
                     os.path.join(PACK, "results", "open-loop"))
FIXTURE = os.path.join(PACK, "fixture", "legacy-billing")
SHIM = os.path.join(PACK, "tests", "helpers", "ollama_judge")

MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5-1.5b-local")
HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
# num_predict=4500: the first genuine attempt used 2500 and the model
# ran out of budget mid-risk-register, failing T0 on the missing
# 30/60/90-day plan section. This is a harness parameter, not a prompt
# change — the candidate prompt stays verbatim.
NUM_PREDICT = int(os.environ.get("OLLAMA_NUM_PREDICT", "4500"))

# Provenance per model tag, recorded into every run meta so the loop is
# reproducible from the artifacts. OLLAMA_MODEL selects the entry; an
# unknown tag fails fast instead of stamping the wrong provenance.
MODEL_PROVENANCES = {
    "qwen2.5-1.5b-local": {
        "tag": "qwen2.5-1.5b-local",
        "gguf_source_url": "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF"
                           "/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf",
        "quantization": "Q4_K_M",
        "gguf_sha256": "6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e",
        "gguf_bytes": 1117320736,
        "import": "ollama create qwen2.5-1.5b-local -f Modelfile "
                  "(Modelfile: FROM <gguf path>)",
        "license": "Apache-2.0 [SECONDARY]",
    },
    "llama3.2-1b-local": {
        "tag": "llama3.2-1b-local",
        "gguf_source_url": "https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF"
                           "/resolve/main/Llama-3.2-1B-Instruct-Q4_K_M.gguf",
        "quantization": "Q4_K_M",
        "gguf_sha256": "6f85a640a97cf2bf5b8e764087b1e83da0fdb51d7c9fab7d0fece9385611df83",
        "gguf_bytes": 807694464,
        "import": "ollama create llama3.2-1b-local -f Modelfile.llama32-1b "
                  "(Modelfile: FROM <gguf path>)",
        "license": "Llama 3.2 Community License [SECONDARY]",
    },
}


def model_provenance():
    try:
        return MODEL_PROVENANCES[MODEL]
    except KeyError:
        raise SystemExit(
            "unknown OLLAMA_MODEL %r: add its provenance to MODEL_PROVENANCES "
            "in tools/open-loop/driver.py before running" % MODEL)

JUDGE_STAMP = ("ollama/%s "
               "(open-weight stand-in for the cheap-judge role; NOT Jev; "
               "same model as the candidate, so not independent)" % MODEL)


def ollama_generate(prompt, num_predict=NUM_PREDICT):
    body = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.7, "num_predict": num_predict},
    }).encode()
    req = urllib.request.Request(
        HOST + "/api/generate", data=body,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=1200) as resp:
        return json.load(resp)["response"]


def _split_task_prompt(task_text):
    """Return the candidate prompt: everything after '## Candidate prompt'."""
    parts = task_text.split("## Candidate prompt", 1)
    if len(parts) != 2 or not parts[1].strip():
        raise ValueError(
            "tasks/T1-global-review.md is missing the "
            "'## Candidate prompt' section the candidate prompt is built from")
    return parts[1].strip()


def build_candidate_prompt():
    with open(os.path.join(PACK, "tasks", "T1-global-review.md")) as f:
        task = f.read()
    # Candidate prompt is everything after the "## Candidate prompt" header.
    prompt = _split_task_prompt(task)
    files = []
    for root, _, fns in os.walk(FIXTURE):
        for fn in sorted(fns):
            # .md included: README.md carries candidate-side rules
            # ("Read-only for task T1..."); __pycache__ stays excluded.
            if fn.endswith((".py", ".txt", ".md", ".cfg", ".ini", ".toml")):
                p = os.path.join(root, fn)
                rel = os.path.relpath(p, FIXTURE)
                with open(p) as f:
                    files.append("===== FILE: %s =====\n%s" % (rel, f.read()))
    # Harness adaptation, disclosed: the model cannot browse files, so the
    # fixture's code/text files are inlined verbatim (__pycache__ excluded).
    # The task text itself is not modified.
    return (prompt + "\n\nHere are the complete contents of "
            "fixture/legacy-billing/ (read-only; do not edit):\n\n"
            + "\n\n".join(files))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=int, required=True)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    n = args.run
    started = datetime.datetime.now().isoformat(timespec="seconds")
    meta = {
        "run": n,
        "started": started,
        "candidate": "ollama/%s [REAL local call]" % MODEL,
        "judge": "ollama/%s (open-weight stand-in for the cheap-judge "
                 "role; NOT Jev; SAME model as candidate -> not "
                 "independent) [REAL local calls]" % MODEL,
        "fixture": "fixture/legacy-billing (verbatim T1 prompt + inlined "
                   "fixture code/text files incl. README.md; prompt text "
                   "unmodified; __pycache__ excluded)",
        "model_provenance": model_provenance(),
        "t0": None,
    }

    print("== run %d: generating T1 candidate with %s ==" % (n, MODEL),
          flush=True)
    cand = ollama_generate(build_candidate_prompt())
    cand_path = os.path.join(OUT, "T1-candidate-ollama-run%d.md" % n)
    with open(cand_path, "w") as f:
        f.write(cand)
    print("candidate written: %s (%d chars)" % (cand_path, len(cand)),
          flush=True)

    print("== run %d: T0 gate ==" % n, flush=True)
    t0 = subprocess.run(
        [sys.executable, os.path.join(PACK, "judge", "t0_checks.py"),
         "--task", "T1", "--candidate", cand_path,
         "--inventory", os.path.join(PACK, "fixture", "DEBT-INVENTORY.md"),
         "--workdir", FIXTURE],
        capture_output=True, text=True)
    t0_log = os.path.join(OUT, "t0-run%d.log" % n)
    with open(t0_log, "w") as f:
        f.write(t0.stdout + t0.stderr)
    print(t0.stdout[-500:], flush=True)
    meta["t0"] = "PASS" if t0.returncode == 0 else "FAIL"
    if t0.returncode != 0:
        print("T0 GATE FAILED — no judge spend. Stopping.", flush=True)
        _write_meta(n, meta, judge_out=None)
        sys.exit(2)

    print("== run %d: cheap judge (ollama shim, NOT Jev) ==" % n, flush=True)
    judge_out = os.path.join(OUT, "judge-run%d.json" % n)
    env = dict(os.environ)
    env["PYTHONPATH"] = SHIM + os.pathsep + env.get("PYTHONPATH", "")
    env["TYPESAFE_API_KEY"] = "open-loop-shim"  # shim ignores the key
    j = subprocess.run(
        [sys.executable, os.path.join(PACK, "judge", "jev_judge.py"),
         "--rubric", os.path.join(PACK, "rubrics", "rubric-T1.json"),
         "--candidate", cand_path,
         "--inventory", os.path.join(PACK, "fixture", "DEBT-INVENTORY.md"),
         "--json-out", judge_out],
        capture_output=True, text=True, env=env)
    print(j.stdout[-800:], flush=True)
    if j.returncode != 0:
        print("JUDGE FAILED:", j.stderr[-1000:], flush=True)
        # Persist the full judge output: a weak stand-in judge can fail to
        # emit valid JSON, and the raw emission is the evidence.
        err_log = os.path.join(OUT, "judge-run%d.error.log" % n)
        with open(err_log, "w") as f:
            f.write("=== STDOUT ===\n" + j.stdout
                    + "\n=== STDERR ===\n" + j.stderr)
        print("judge failure output saved: %s" % err_log, flush=True)
        _write_meta(n, meta, judge_out=None)
        sys.exit(3)
    print("judge payload: %s" % judge_out, flush=True)
    _stamp_judge_payload(judge_out)
    _write_meta(n, meta, judge_out=judge_out)


def _stamp_judge_payload(judge_out):
    """Stamp the stand-in judge's identity into the payload (R1).

    jev_judge.py writes the payload with a Jev-priced cost estimate and no
    judge identity; when it is driven through the ollama shim, the payload
    must say so itself rather than relying on prose elsewhere.
    """
    with open(judge_out) as f:
        d = json.load(f, object_pairs_hook=dict)
    d["judge"] = JUDGE_STAMP
    if "est_cost_usd" in d:
        d["est_cost_usd_notional"] = d.pop("est_cost_usd")
    d["cost_note"] = ("Notional only: computed from Jev pricing constants, "
                      "which do not apply to a local stand-in. "
                      "Actual API spend was $0.")
    with open(judge_out, "w") as f:
        json.dump(d, f, indent=2)


def _write_meta(n, meta, judge_out):
    meta["finished"] = datetime.datetime.now().isoformat(timespec="seconds")
    meta["judge_payload"] = judge_out
    with open(os.path.join(OUT, "run%d-meta.json" % n), "w") as f:
        json.dump(meta, f, indent=2)


if __name__ == "__main__":
    main()
