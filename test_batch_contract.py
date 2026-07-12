"""Regression tests for the public AMD Track 1 batch-file contract.

Run with::

    python -m unittest -v test_batch_contract.py

The suite deliberately uses only the Python standard library so it can also run
inside the submission image.
"""

from __future__ import annotations

import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

import agent


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _processed(task: dict, answer: str | None = None) -> dict:
    """Return the full internal shape produced by ``process_task``."""
    return {
        "task_id": task["task_id"],
        "answer": answer if answer is not None else f"answer:{task['prompt']}",
        "route": "test",
        "tokens_used": 0,
        "time_ms": 0,
        "method": "test",
    }


class LoadTasksContractTests(unittest.TestCase):
    def test_accepts_the_public_list_schema(self) -> None:
        tasks = [
            {"task_id": "one", "prompt": "first prompt"},
            {"task_id": 2, "prompt": "second prompt"},
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tasks.json"
            _write_json(path, tasks)

            self.assertEqual(agent.load_tasks(path), tasks)

    def test_rejects_non_contract_input_shapes(self) -> None:
        invalid_payloads = {
            "object wrapper": {"tasks": [{"task_id": "1", "prompt": "p"}]},
            "non-object task": ["not a task"],
            "missing task_id": [{"prompt": "p"}],
            "missing prompt": [{"task_id": "1"}],
            "non-string prompt": [{"task_id": "1", "prompt": 123}],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tasks.json"
            for label, payload in invalid_payloads.items():
                with self.subTest(label=label):
                    _write_json(path, payload)
                    with self.assertRaises(ValueError):
                        agent.load_tasks(path)


class RunBatchContractTests(unittest.TestCase):
    def test_output_has_exact_schema_and_preserves_all_ids_in_order(self) -> None:
        # Numeric, duplicate-after-stringification, and empty IDs catch common
        # scorer mismatches without imposing uniqueness beyond the public schema.
        tasks = [
            {"task_id": 17, "prompt": "first"},
            {"task_id": "alpha", "prompt": "second"},
            {"task_id": "17", "prompt": "third"},
            {"task_id": "", "prompt": "fourth"},
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "input" / "tasks.json"
            output_path = root / "output" / "results.json"
            _write_json(input_path, tasks)

            with patch.object(agent, "process_task", side_effect=_processed):
                agent.run_batch(input_path, output_path)

            results = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertIsInstance(results, list)
        self.assertEqual(len(results), len(tasks))
        self.assertEqual(
            [result["task_id"] for result in results],
            ["17", "alpha", "17", ""],
        )
        self.assertEqual(
            [result["answer"] for result in results],
            ["answer:first", "answer:second", "answer:third", "answer:fourth"],
        )
        for result in results:
            self.assertEqual(set(result), {"task_id", "answer"})
            self.assertIsInstance(result["task_id"], str)
            self.assertIsInstance(result["answer"], str)

    def test_one_task_failure_is_checkpointed_and_does_not_drop_later_tasks(self) -> None:
        tasks = [
            {"task_id": "first", "prompt": "ok"},
            {"task_id": "broken", "prompt": "raise"},
            {"task_id": "last", "prompt": "still run"},
        ]
        snapshots: dict[str, list] = {}

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "input" / "tasks.json"
            output_path = root / "output" / "results.json"
            _write_json(input_path, tasks)

            def flaky_process(task: dict) -> dict:
                if output_path.exists():
                    snapshots[str(task["task_id"])] = json.loads(
                        output_path.read_text(encoding="utf-8")
                    )
                if task["task_id"] == "broken":
                    raise RuntimeError("deliberate per-task failure")
                return _processed(task)

            with patch.object(agent, "process_task", side_effect=flaky_process):
                agent.run_batch(input_path, output_path)

            results = json.loads(output_path.read_text(encoding="utf-8"))

        # All IDs exist before processing begins, and each completed/failing task
        # is checkpointed without ever regressing to a partial-ID result file.
        self.assertEqual(
            snapshots["broken"],
            [
                {"task_id": "first", "answer": "answer:ok"},
                {"task_id": "broken", "answer": ""},
                {"task_id": "last", "answer": ""},
            ],
        )
        self.assertEqual(
            snapshots["last"],
            [
                {"task_id": "first", "answer": "answer:ok"},
                {"task_id": "broken", "answer": ""},
                {"task_id": "last", "answer": ""},
            ],
        )
        self.assertEqual(
            [item["task_id"] for item in results],
            ["first", "broken", "last"],
        )
        self.assertEqual(len(results), len(tasks))
        for result in results:
            self.assertEqual(set(result), {"task_id", "answer"})
            self.assertIsInstance(result["answer"], str)


class EnvironmentParsingTests(unittest.TestCase):
    def test_allowed_models_accepts_csv_and_json_array_forms(self) -> None:
        expected = [
            "accounts/fireworks/models/primary",
            "accounts/fireworks/models/fallback",
        ]
        csv_value = "  accounts/fireworks/models/primary, accounts/fireworks/models/fallback  "
        json_value = json.dumps(expected)

        self.assertEqual(agent.parse_allowed_models(csv_value), expected)
        self.assertEqual(agent.parse_allowed_models(json_value), expected)

    def test_completion_url_accepts_a_base_or_complete_endpoint(self) -> None:
        endpoint = "https://api.fireworks.ai/inference/v1/chat/completions"

        self.assertEqual(agent.completion_url(endpoint), endpoint)
        self.assertEqual(
            agent.completion_url("https://api.fireworks.ai/inference/v1"),
            endpoint,
        )
        self.assertEqual(
            agent.completion_url("https://api.fireworks.ai/inference/v1/"),
            endpoint,
        )

    def test_category_model_preferences_and_accuracy_escalation(self) -> None:
        allowed = ["gemma-4-31b-it", "minimax-m3", "kimi-k2p7-code"]
        with patch.object(agent, "ALLOWED_MODELS", allowed):
            self.assertEqual(agent.candidate_models("factual_qa", "What is HTTP? ")[0], "kimi-k2p7-code")
            self.assertEqual(
                agent.candidate_models("factual_qa", "Compare HTTP and HTTPS")[0],
                "minimax-m3",
            )

    def test_fireworks_base_path_and_model_failover(self) -> None:
        requests: list[tuple[str, str]] = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                length = int(self.headers["Content-Length"])
                body = json.loads(self.rfile.read(length))
                requests.append((self.path, body["model"]))
                if body["model"] == "primary-bad":
                    self.send_response(404)
                    self.end_headers()
                    return
                payload = json.dumps({
                    "choices": [{"message": {"content": "fallback answer"}}],
                    "usage": {"total_tokens": 7},
                }).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *_args: object) -> None:
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{server.server_port}/v1"
            with (
                patch.object(agent, "FIREWORKS_API_KEY", "test-key"),
                patch.object(agent, "FIREWORKS_BASE_URL", base),
                patch.object(agent, "ALLOWED_MODELS", ["primary-bad", "fallback-good"]),
            ):
                answer, _elapsed, tokens = agent.call_fireworks("A factual question")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

        self.assertEqual(answer, "fallback answer")
        self.assertEqual(tokens, 7)
        self.assertEqual(
            requests,
            [
                ("/v1/chat/completions", "primary-bad"),
                ("/v1/chat/completions", "fallback-good"),
            ],
        )

    def test_model_response_validation_enforces_requested_shape(self) -> None:
        self.assertFalse(
            agent.valid_model_answer("Partial", "factual_qa", "Question", "length")
        )
        self.assertFalse(
            agent.valid_model_answer(
                "mixed",
                "sentiment",
                "Classify as positive or negative: mixed text",
            )
        )
        self.assertTrue(
            agent.valid_model_answer(
                "Positive",
                "sentiment",
                "Classify as positive or negative: good text",
            )
        )
        summary_prompt = "Summarize in exactly two sentences: source text"
        self.assertFalse(agent.valid_model_answer("Only one sentence.", "summarization", summary_prompt))
        self.assertTrue(agent.valid_model_answer("First sentence. Second sentence.", "summarization", summary_prompt))
        self.assertFalse(
            agent.valid_model_answer("not python", "code_generation", "Write a Python function called solve")
        )
        self.assertTrue(
            agent.valid_model_answer("def solve():\n    return 1", "code_generation", "Write a Python function called solve")
        )
        self.assertEqual(
            agent.clean_model_answer("Sentiment: **Positive** because it is good.", "sentiment", "Classify as positive or negative: text"),
            "positive",
        )
        self.assertEqual(
            agent.clean_model_answer("Work here\nFinal answer: 144", "math", "How many remain?"),
            "144",
        )
        self.assertEqual(
            agent.clean_model_answer("```python\ndef solve():\n    return 1\n```", "code_generation", "Write a Python function called solve"),
            "def solve():\n    return 1",
        )


class RoutingRegressionTests(unittest.TestCase):
    def local_answer(self, prompt: str) -> str | None:
        answer, _method, _elapsed = agent.try_local(prompt)
        return answer

    def test_compound_or_cross_category_prompts_escalate(self) -> None:
        prompts = [
            "What is the capital of Australia, and what body of water is it near?",
            "Summarize in one sentence: A good system highlights useful patterns.",
            "Write a Python function to calculate the fibonacci sequence up to n.",
            "Classify the sentiment: This is not good.",
            "Classify the sentiment: Great, another update that crashes.",
            "Extract all named entities and types from Ada Lovelace at ACME in London on 2026-07-10.",
        ]
        for prompt in prompts:
            with self.subTest(prompt=prompt):
                self.assertIsNone(self.local_answer(prompt))

    def test_verified_math_forms_are_correct(self) -> None:
        cases = {
            "What is 3.14159 * 2.71828?": "8.539721",
            "Calculate: (15 * 3) + (20 / 4) - 7": "43",
            "What is the product of 14 and 6?": "84",
            "Solve for x: 4x + 7 = 31.": "6",
            "A store has 240 items. It sells 15% on Monday and 60 more on Tuesday. How many items remain?": "144",
            "15% off 80": "68.0",
        }
        for prompt, expected in cases.items():
            with self.subTest(prompt=prompt):
                self.assertEqual(self.local_answer(prompt), expected)

    def test_fact_matching_does_not_use_prefix_substrings(self) -> None:
        self.assertIsNone(self.local_answer("What is the capital of Ukraine?"))
        self.assertEqual(self.local_answer("What is the capital of the UK?"), "London")

    def test_category_inference_covers_scored_intents(self) -> None:
        cases = {
            "Fix this Python function so it includes the final item.": "code_debugging",
            "Provide an SQL query that returns all customers.": "code_generation",
            "Identify the people, organizations, locations, and dates in this text.": "ner",
            "If a report is approved, it is archived. It is not archived. Can it be approved?": "logic",
            "Give a one-sentence overview of the following passage.": "summarization",
            "What is the main idea behind binary search?": "factual_qa",
        }
        for prompt, expected in cases.items():
            with self.subTest(prompt=prompt):
                self.assertEqual(agent.infer_task_category(prompt), expected)


if __name__ == "__main__":
    unittest.main()
