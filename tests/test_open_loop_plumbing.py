#!/usr/bin/env python3
"""Regression tests for the open-loop plumbing.

Covers the ollama judge shim (tests/helpers/ollama_judge/typesafe_sdk.py)
and the open-loop driver's prompt construction — all hermetic, no ollama
server needed. The live end-to-end behavior is proven by the genuine runs
in results/open-loop/, not by these tests.
"""
import importlib.util
import os
import unittest

PACK = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SHIM_DIR = os.path.join(PACK, "tests", "helpers", "ollama_judge")
DRIVER = os.path.join(PACK, "src", "llm_workflow_eval", "drivers", "open-loop", "driver.py")


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


shim = load_module("ollama_shim",
                   os.path.join(SHIM_DIR, "typesafe_sdk.py"))
driver = load_module("open_loop_driver", DRIVER)


class TestShimJsonExtraction(unittest.TestCase):
    def test_raw_json(self):
        d = shim._extract_json('{"score": 2, "confidence": 0.9}')
        self.assertEqual(d["score"], 2)

    def test_fenced_json(self):
        d = shim._extract_json(
            '```json\n{"score": 1, "confidence": 0.5}\n```')
        self.assertEqual(d["score"], 1)

    def test_leading_prose(self):
        d = shim._extract_json(
            'Here is my judgment: {"noul": 0.95, "confidence": 0.8} done.')
        self.assertAlmostEqual(d["noul"], 0.95)

    def test_multiple_json_objects_takes_first(self):
        # S5: a greedy first-{ to last-} span would be unparseable here.
        d = shim._extract_json(
            '{"score": 1} and also {"score": 2}')
        self.assertEqual(d["score"], 1)

    def test_trailing_braces_in_prose(self):
        d = shim._extract_json(
            '{"noul": 0.7} (see section {3} for details)')
        self.assertAlmostEqual(d["noul"], 0.7)

    def test_braces_inside_strings(self):
        d = shim._extract_json(
            '{"rationale": "uses {braces} fine", "score": 2}')
        self.assertEqual(d["rationale"], "uses {braces} fine")

    def test_unbalanced_raises(self):
        with self.assertRaises(ValueError):
            shim._extract_json('{"score": 1')

    def test_garbage_raises(self):
        with self.assertRaises(ValueError):
            shim._extract_json("no json here at all")

    def test_clamp(self):
        self.assertEqual(shim._clamp(5, 0, 3), 3)
        self.assertEqual(shim._clamp(-1, 0, 3), 0)
        self.assertAlmostEqual(shim._clamp(0.5, 0.0, 1.0), 0.5)


class TestShimQuestionKinds(unittest.TestCase):
    """system_one dispatches Score/Choice/Noul with a stubbed model."""

    def setUp(self):
        self.calls = []
        calls = self.calls

        def fake_call(prompt):
            calls.append(prompt)
            return self.scripted.pop(0)

        self._orig = shim._call_ollama
        shim._call_ollama = fake_call

    def tearDown(self):
        shim._call_ollama = self._orig

    def test_score_path(self):
        self.scripted = ['{"score": 2, "confidence": 0.9, '
                         '"rationale": "solid"}']
        client = shim.TypeSafeClient()
        q = shim.Score(instructions="grade it",
                       criteria=["bad", "ok", "good", "great"])
        resp = client.system_one(
            state={"candidate_output": "x"}, questions={"q1": q})
        ans = resp.answers["q1"]
        self.assertEqual(ans.score, 2)
        self.assertAlmostEqual(ans.confidence, 0.9)

    def test_score_clamped_to_criteria(self):
        self.scripted = ['{"score": 99, "confidence": 1.5}']
        client = shim.TypeSafeClient()
        q = shim.Score(instructions="grade it", criteria=["bad", "ok"])
        ans = client.system_one(questions={"q1": q}).answers["q1"]
        self.assertEqual(ans.score, 1)  # clamped to n-1
        self.assertAlmostEqual(ans.confidence, 1.0)

    def test_noul_path(self):
        self.scripted = ['{"noul": 0.95, "confidence": 0.8}']
        client = shim.TypeSafeClient()
        q = shim.Noul(instructions="holds?")
        ans = client.system_one(questions={"q1": q}).answers["q1"]
        self.assertAlmostEqual(ans.noul, 0.95)

    def test_choice_path(self):
        self.scripted = ['{"choice": "b", "probabilities": {"a": 0.2, '
                         '"b": 0.8}, "confidence": 0.7}']
        client = shim.TypeSafeClient()
        q = shim.Choice(instructions="pick", criteria=["a", "b"])
        ans = client.system_one(questions={"q1": q}).answers["q1"]
        self.assertEqual(ans.choice, "b")
        self.assertAlmostEqual(ans.probabilities["b"], 0.8)

    def test_retry_then_success(self):
        self.scripted = ["garbage, no json",
                         '{"score": 1, "confidence": 0.6}']
        client = shim.TypeSafeClient()
        q = shim.Score(instructions="grade it", criteria=["bad", "ok"])
        ans = client.system_one(questions={"q1": q}).answers["q1"]
        self.assertEqual(ans.score, 1)
        self.assertEqual(len(self.calls), 2)

    def test_non_integer_score_burns_retry(self):
        # S2: a judge emitting 2.7 must not be silently truncated to 2.
        self.scripted = ['{"score": 2.7, "confidence": 0.6}',
                         '{"score": 2, "confidence": 0.6}']
        client = shim.TypeSafeClient()
        q = shim.Score(instructions="g", criteria=["a", "b", "c"])
        ans = client.system_one(questions={"q1": q}).answers["q1"]
        self.assertEqual(ans.score, 2)
        self.assertEqual(len(self.calls), 2)

    def test_unexpected_want_error_burns_retry_not_run(self):
        # S4: a non-(ValueError/KeyError/TypeError) failure inside want()
        # must consume a retry, not kill the whole judge run.
        calls = {"n": 0}

        def flaky(data):
            calls["n"] += 1
            if calls["n"] == 1:
                raise RuntimeError("weird want() failure")
            return shim._Answer(score=2)

        self.scripted = ['{"score": 0}', '{"score": 2}']
        client = shim.TypeSafeClient()
        q = shim.Score(instructions="g", criteria=["a", "b", "c"])
        orig_ask_score = client._ask_score
        client._ask_score = lambda qid, q, state: client._ask(
            "p", flaky)
        try:
            ans = client.system_one(questions={"q1": q}).answers["q1"]
        finally:
            client._ask_score = orig_ask_score
        self.assertEqual(ans.score, 2)
        self.assertEqual(len(self.calls), 2)

    def test_persistent_garbage_raises(self):
        self.scripted = ["nope"] * 5
        client = shim.TypeSafeClient()
        q = shim.Score(instructions="grade it", criteria=["bad", "ok"])
        with self.assertRaises(ValueError):
            client.system_one(questions={"q1": q})
        self.assertEqual(len(self.calls), shim.MAX_ATTEMPTS)

    def test_unknown_kind_raises(self):
        client = shim.TypeSafeClient()

        class Weird:
            pass

        with self.assertRaises(ValueError):
            client.system_one(questions={"q1": Weird()})

    def test_state_block_labels_inventory_as_unseen(self):
        client = shim.TypeSafeClient()
        block = client._state_block(
            {"candidate_output": "C", "debt_inventory": "D"})
        self.assertIn("CANDIDATE OUTPUT", block)
        self.assertIn("did NOT see this", block)


class TestDriverPrompt(unittest.TestCase):
    def test_prompt_contains_verbatim_task_and_fixture(self):
        prompt = driver.build_candidate_prompt()
        with open(os.path.join(PACK, "tasks", "T1-global-review.md")) as f:
            task = f.read().split("## Candidate prompt", 1)[1].strip()
        # Verbatim task text: the prompt must start with it, unmodified.
        self.assertTrue(prompt.startswith(task))
        # Fixture files are inlined verbatim with FILE markers.
        self.assertIn("===== FILE: billing.py =====", prompt)
        self.assertIn("===== FILE: config.py =====", prompt)
        # README.md carries candidate-side rules and must be inlined too.
        self.assertIn("===== FILE: README.md =====", prompt)
        with open(os.path.join(PACK, "fixture", "legacy-billing",
                               "billing.py")) as f:
            self.assertIn(f.read()[:200], prompt)
        # Disclosure of the harness adaptation is present.
        self.assertIn("read-only; do not edit", prompt)

    def test_split_task_prompt_guards_missing_header(self):
        with self.assertRaises(ValueError):
            driver._split_task_prompt("# no candidate prompt header here\n")
        self.assertEqual(
            driver._split_task_prompt("# x\n## Candidate prompt\nhello\n"),
            "hello")

    def test_pack_resolution(self):
        # The driver resolves the pack root from its own path.
        self.assertTrue(os.path.isdir(
            os.path.join(driver.PACK, "tasks")))
        self.assertTrue(os.path.isdir(
            os.path.join(driver.PACK, "fixture", "legacy-billing")))


if __name__ == "__main__":
    unittest.main()
