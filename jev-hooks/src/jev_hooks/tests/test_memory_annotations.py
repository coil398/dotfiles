from __future__ import annotations

import sys
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from jev_hooks import memory, service  # noqa: E402
from jev_hooks.config import Config  # noqa: E402
from jev_hooks.jev_client import ChoiceAnswer, JevResult  # noqa: E402
from jev_hooks.telemetry import summarize  # noqa: E402


@dataclass
class FakeConfig:
    confidence_threshold: float = 0.6
    mode: str = "on"


def _result(count: int, *, confidence: float = 0.9, choices: dict | None = None):
    answers = {}
    choices = choices or {}
    options = {
        "relevance": ("relevant", "unrelated", "unclear"),
        "current_instruction_conflict": ("compatible", "conflict", "unclear"),
        "assumption_mismatch": ("consistent", "mismatch", "unclear"),
    }
    for index in range(count):
        for dimension, allowed in options.items():
            qid = f"candidate_{index}_{dimension}"
            choice = choices.get(qid, allowed[0])
            answers[qid] = ChoiceAnswer(
                choice=choice,
                probabilities={label: (1.0 if label == choice else 0.0) for label in allowed},
                confidence=confidence,
            )
    return JevResult(answers=answers)


class FakeService:
    def __init__(self, evaluation):
        self.evaluation = evaluation
        self.calls = []
        self.skips = []

    def evaluate(self, policy_id, state, questions, **kwargs):
        self.calls.append((policy_id, state, questions, kwargs))
        return self.evaluation

    def record_skip(self, policy_id, reason, **kwargs):
        self.skips.append((policy_id, reason, kwargs))


class MemoryAnnotationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.results = [
            {
                "id": f"opaque-database-id-{index}",
                "summary": f"memory summary {index}",
                "context": f"context {index}",
                "tags": f"tag-{index}",
                "combined_score": 1.0 - index / 10,
                "custom": {"kept": index},
            }
            for index in range(7)
        ]
        self.env = {"TYPESAFE_API_KEY": "mock-key-only"}

    def test_missing_key_returns_identical_results_without_loading_jev(self) -> None:
        with patch.object(memory, "_runtime") as runtime:
            returned = memory.annotate("task", self.results, environ={})
        self.assertIs(returned, self.results)
        runtime.assert_not_called()

    def test_blank_key_is_missing_and_does_not_load_jev(self) -> None:
        with patch.object(memory, "_runtime") as runtime:
            returned = memory.annotate("task", self.results, environ={"TYPESAFE_API_KEY": " \t\n"})
        self.assertIs(returned, self.results)
        runtime.assert_not_called()

    def test_existing_annotation_returns_original_without_runtime_or_overwrite(self) -> None:
        results = [dict(item) for item in self.results]
        existing = {"relevance": "unrelated", "source": "earlier-pass"}
        results[2]["jev_annotation"] = existing
        with patch.object(memory, "_runtime") as runtime:
            returned = memory.annotate("new task", results, environ=self.env)
        self.assertIs(returned, results)
        self.assertIs(returned[2]["jev_annotation"], existing)
        runtime.assert_not_called()

    def test_nonpositive_or_nonfinite_timeout_returns_before_runtime(self) -> None:
        for timeout in (0, -0.01, float("nan"), float("inf"), float("-inf"), "invalid"):
            with self.subTest(timeout=timeout), patch.object(memory, "_runtime") as runtime:
                returned = memory.annotate("task", self.results, environ=self.env, timeout_s=timeout)
            self.assertIs(returned, self.results)
            runtime.assert_not_called()

    def test_success_adds_typed_annotations_to_first_five_without_reordering(self) -> None:
        answers = {}
        for index in range(5):
            answers[f"candidate_{index}_relevance"] = "unrelated" if index == 1 else "relevant"
            answers[f"candidate_{index}_current_instruction_conflict"] = "conflict" if index == 2 else "compatible"
            answers[f"candidate_{index}_assumption_mismatch"] = "mismatch" if index == 3 else "consistent"
        service_fake = FakeService(SimpleNamespace(status="ok", reason="evaluated", result=_result(5, choices=answers)))
        cfg = FakeConfig()
        query = "current task " + "q" * 1400 + " ghp_" + "x" * 30
        self.results[0]["summary"] = "summary TYPESAFE_API_KEY=" + "s" * 30 + "a" * 1400
        self.results[0]["context"] = "c" * 1400
        self.results[0]["tags"] = "t" * 350

        with patch.object(memory, "_runtime", return_value=(service_fake, cfg, cfg.confidence_threshold)):
            returned = memory.annotate(query, self.results, environ=self.env, timeout_s=0.25)

        self.assertEqual([item["id"] for item in returned], [item["id"] for item in self.results])
        self.assertEqual(len(returned), len(self.results))
        self.assertEqual(len(service_fake.calls), 1)
        self.assertEqual(service_fake.skips, [])
        policy_id, state, questions, kwargs = service_fake.calls[0]
        self.assertEqual(policy_id, "ai_ltm_memory_annotation")
        self.assertEqual(kwargs["runtime"], "ai-ltm")
        self.assertEqual(kwargs["event"], "annotate")
        self.assertEqual(kwargs["timeout_s"], 0.25)
        self.assertEqual(len(state["memories"]), 5)
        self.assertEqual(set(state["memories"][0]), {"candidate_index", "summary", "context", "tags", "score"})
        self.assertNotIn("opaque-database-id", str(state))
        self.assertNotIn("ghp_", state["current_request"])
        self.assertNotIn("s" * 30, state["memories"][0]["summary"])
        self.assertIn("TYPESAFE_API_KEY=[REDACTED]", state["memories"][0]["summary"])
        self.assertEqual(len(state["current_request"]), 1200)
        self.assertLessEqual(len(state["memories"][0]["summary"]), 1200)
        self.assertLessEqual(len(state["memories"][0]["context"]), 1200)
        self.assertLessEqual(len(state["memories"][0]["tags"]), 300)
        self.assertEqual(state["memories"][4]["candidate_index"], 4)
        self.assertEqual(questions["candidate_0_relevance"]["type"], "choice")
        self.assertEqual(
            set(questions["candidate_0_current_instruction_conflict"]["criteria"]),
            {"conflict", "compatible", "unclear"},
        )
        self.assertEqual(
            set(questions["candidate_0_assumption_mismatch"]["criteria"]),
            {"mismatch", "consistent", "unclear"},
        )
        for index in range(5):
            annotation = returned[index]["jev_annotation"]
            self.assertEqual(annotation["relevance"], answers[f"candidate_{index}_relevance"])
            self.assertEqual(annotation["current_instruction_conflict"], answers[f"candidate_{index}_current_instruction_conflict"])
            self.assertEqual(annotation["assumption_mismatch"], answers[f"candidate_{index}_assumption_mismatch"])
            self.assertEqual(annotation["confidence"], {"relevance": 0.9, "current_instruction_conflict": 0.9, "assumption_mismatch": 0.9})
            self.assertEqual(
                {key: value for key, value in returned[index].items() if key != "jev_annotation"},
                self.results[index],
            )
            self.assertNotIn("jev_annotation", self.results[index])
        self.assertNotIn("jev_annotation", returned[5])
        self.assertNotIn("jev_annotation", returned[6])
        self.assertIs(returned[5], self.results[5])
        self.assertIs(returned[6], self.results[6])

    def test_low_confidence_and_failed_evaluation_return_original_results_without_skip_record(self) -> None:
        low_service = FakeService(SimpleNamespace(status="ok", reason="evaluated", result=_result(5, confidence=0.59)))
        with patch.object(memory, "_runtime", return_value=(low_service, FakeConfig(), 0.6)):
            low = memory.annotate("task", self.results, environ=self.env)
        self.assertIs(low, self.results)
        self.assertEqual(len(low_service.calls), 1)
        self.assertEqual(low_service.skips, [])

        failed_service = FakeService(SimpleNamespace(status="error", reason="API_TIMEOUT", result=None))
        with patch.object(memory, "_runtime", return_value=(failed_service, FakeConfig(), 0.6)):
            failed = memory.annotate("task", self.results, environ=self.env)
        self.assertIs(failed, self.results)
        self.assertEqual(len(failed_service.calls), 1)
        self.assertEqual(failed_service.skips, [])

    def test_observe_mode_records_one_mocked_api_call_but_returns_unannotated_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Config(
                mode="observe",
                model="unknown-test-model",
                api_url="https://example.invalid/jev",
                api_timeout_s=0.8,
                total_timeout_s=1.2,
                state_dir=str(Path(tmp) / "state"),
            )
            captured = {}
            results = [dict(item) for item in self.results]
            results[0]["summary"] = "TYPESAFE_API_KEY=service-scrub-secret-123456"

            def mock_ask(**kwargs):
                captured.update(kwargs)
                return _result(5)

            with patch.object(memory, "_runtime", return_value=(service, cfg, cfg.confidence_threshold)), patch.object(
                memory.redact, "scrub", side_effect=lambda text, limit: text
            ), patch.object(service.jev_client, "ask", side_effect=mock_ask):
                returned = memory.annotate("task", results, environ=self.env, timeout_s=0.25)

            self.assertIs(returned, results)
            self.assertEqual(captured["timeout_s"], 0.25)
            sent = captured["state"]
            self.assertNotIn("opaque-database-id", str(sent))
            self.assertNotIn("service-scrub-secret-123456", str(sent))
            self.assertIn("[REDACTED]", sent["memories"][0]["summary"])
            self.assertEqual(len(sent["memories"]), 5)
            report = summarize(cfg.state_path())
            self.assertEqual(report["totals"]["calls"], 1)
            self.assertEqual(report["totals"]["api_attempted"], 1)
            self.assertEqual(report["totals"]["cost_unknown_calls"], 1)

    def test_off_mode_does_not_call_api_or_create_usage_store(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Config(
                mode="off",
                state_dir=str(Path(tmp) / "state"),
                api_url="https://example.invalid/jev",
            )
            with patch.object(memory, "_runtime", return_value=(service, cfg, cfg.confidence_threshold)), patch.object(
                service.jev_client, "ask", side_effect=AssertionError("must not call API")
            ):
                returned = memory.annotate("task", self.results, environ=self.env)
            self.assertIs(returned, self.results)
            self.assertFalse(cfg.state_path().exists())


if __name__ == "__main__":
    unittest.main()
