from __future__ import annotations

from contextlib import redirect_stderr
from dataclasses import dataclass
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[4]
SCRIPT_DIR = ROOT / ".agents" / "skills" / "ai-ltm" / "scripts"
JEV_SOURCE = ROOT / "jev-hooks" / "src"
for _path in (str(JEV_SOURCE), str(SCRIPT_DIR)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import jev_bridge  # noqa: E402
from jev_hooks import memory  # noqa: E402


@dataclass
class FakeConfig:
    confidence_threshold: float = 0.6


def choice(choice_value: str, confidence: float = 0.9):
    return SimpleNamespace(choice=choice_value, confidence=confidence, probabilities={})


def fake_result(answers: dict[str, tuple[str, float]]):
    return SimpleNamespace(
        answers={qid: choice(value, confidence) for qid, (value, confidence) in answers.items()}
    )


class FakeService:
    def __init__(self, answers: dict[str, tuple[str, float]]):
        self.evaluation = SimpleNamespace(
            status="ok", reason="evaluated", result=fake_result(answers)
        )
        self.calls = []
        self.skips = []

    def evaluate(self, policy_id, state, questions, **kwargs):
        self.calls.append((policy_id, state, questions, kwargs))
        return self.evaluation

    def record_skip(self, policy_id, reason, **kwargs):
        self.skips.append((policy_id, reason, kwargs))


class BridgeFallbackTests(unittest.TestCase):
    def setUp(self):
        self.results = [
            {"id": 1, "summary": "first", "combined_score": 0.9},
            {"id": 2, "summary": "second", "combined_score": 0.8},
        ]

    def test_missing_key_does_not_import_jev_and_keeps_results(self):
        with patch.object(jev_bridge, "_load_memory") as load, redirect_stderr(io.StringIO()):
            returned = jev_bridge.rerank("query", self.results, environ={})
        load.assert_not_called()
        self.assertIs(returned, self.results)

    def test_missing_hooks_package_keeps_results(self):
        with tempfile.TemporaryDirectory() as tmp, redirect_stderr(io.StringIO()):
            returned = jev_bridge.rerank(
                "query",
                self.results,
                environ={"TYPESAFE_API_KEY": "present", "JEV_HOOKS_ROOT": tmp},
            )
        self.assertIs(returned, self.results)
        self.assertEqual([item["id"] for item in returned], [1, 2])

    def test_runtime_failure_keeps_results_and_does_not_echo_exception_text(self):
        class BrokenMemory:
            @staticmethod
            def rerank(*args, **kwargs):
                raise RuntimeError("secret response body")

        error = io.StringIO()
        with patch.object(jev_bridge, "_load_memory", return_value=BrokenMemory), redirect_stderr(error):
            returned = jev_bridge.rerank(
                "query", self.results, environ={"TYPESAFE_API_KEY": "present"}
            )
        self.assertIs(returned, self.results)
        self.assertIn("RuntimeError", error.getvalue())
        self.assertNotIn("secret response body", error.getvalue())

    def test_annotation_failure_keeps_candidates(self):
        class BrokenMemory:
            @staticmethod
            def annotate(*args, **kwargs):
                raise RuntimeError("private response body")

        error = io.StringIO()
        with patch.object(jev_bridge, "_load_memory", return_value=BrokenMemory), redirect_stderr(error):
            returned = jev_bridge.annotate(
                "query", self.results, environ={"TYPESAFE_API_KEY": "present"}
            )
        self.assertIs(returned, self.results)
        self.assertIn("RuntimeError", error.getvalue())
        self.assertNotIn("private response body", error.getvalue())

    def test_missing_or_whitespace_key_does_not_import_jev(self):
        for environ in ({}, {"TYPESAFE_API_KEY": " \t\n "}):
            with self.subTest(environ=environ):
                with patch.object(jev_bridge, "_load_memory") as load, redirect_stderr(io.StringIO()):
                    annotated = jev_bridge.annotate("query", self.results, environ=environ)
                    reranked = jev_bridge.rerank("query", self.results, environ=environ)
                    classified = jev_bridge.classify_record("note", environ=environ)
                load.assert_not_called()
                self.assertIs(annotated, self.results)
                self.assertIs(reranked, self.results)
                self.assertEqual(classified["reason"], "NO_API_KEY")


class BridgeAnnotationTests(unittest.TestCase):
    def test_annotation_only_sends_bounded_allowed_fields_and_preserves_results(self):
        results = [
            {
                "id": index,
                "summary": "s" * 1300,
                "context": "c" * 1300,
                "tags": "t" * 400,
                "combined_score": index / 10,
                "private_metadata": "must stay local",
            }
            for index in range(1, 7)
        ]

        class FakeMemory:
            call = None

            @classmethod
            def annotate(cls, query, candidates, *, environ=None, timeout_s=None):
                cls.call = (query, candidates, environ, timeout_s)
                return [
                    {**candidate, "jev_annotation": {"relevance": "relevant"}}
                    for candidate in candidates
                ]

        with patch.object(jev_bridge, "_load_memory", return_value=FakeMemory):
            annotated = jev_bridge.annotate(
                "q" * 1300,
                results,
                environ={"TYPESAFE_API_KEY": "present"},
                timeout_s=0.75,
            )

        query, sent, _environ, timeout_s = FakeMemory.call
        self.assertEqual(len(query), 1200)
        self.assertEqual(timeout_s, 0.75)
        self.assertEqual(len(sent), 5)
        self.assertEqual(set(sent[0]), {"summary", "context", "tags", "score"})
        self.assertEqual(len(sent[0]["summary"]), 1200)
        self.assertEqual(len(sent[0]["context"]), 1200)
        self.assertEqual(len(sent[0]["tags"]), 300)
        self.assertNotIn("id", sent[0])
        self.assertNotIn("private_metadata", sent[0])
        self.assertEqual([item["id"] for item in annotated], [1, 2, 3, 4, 5, 6])
        self.assertEqual([item["id"] for item in results], [1, 2, 3, 4, 5, 6])
        for before, after in zip(results[:5], annotated[:5]):
            self.assertEqual({key: after[key] for key in before}, before)
            self.assertEqual(after["jev_annotation"], {"relevance": "relevant"})
        self.assertEqual(annotated[5], results[5])

    def test_normal_annotation_skip_keeps_results_without_invalid_result_log(self):
        results = [{"id": 1, "summary": "memory", "context": "", "tags": "", "score": 0.8}]

        class SkippedMemory:
            @staticmethod
            def annotate(query, candidates, *, environ=None, timeout_s=None):
                return candidates

        error = io.StringIO()
        with patch.object(jev_bridge, "_load_memory", return_value=SkippedMemory), redirect_stderr(error):
            returned = jev_bridge.annotate(
                "query", results, environ={"TYPESAFE_API_KEY": "present"}
            )
        self.assertIs(returned, results)
        self.assertEqual(error.getvalue(), "")


class MemoryRerankTests(unittest.TestCase):
    def test_confident_judgment_reorders_only_top_candidates(self):
        results = [
            {"id": i, "summary": f"memory {i}", "combined_score": 1 / i}
            for i in range(1, 7)
        ]
        answers = {}
        judgments = [
            ("low", "none"),
            ("high", "direct"),
            ("medium", "contextual"),
            ("low", "contextual"),
            ("medium", "direct"),
        ]
        for index, (relevance, applicability) in enumerate(judgments):
            answers[f"memory_{index}_relevance"] = (relevance, 0.9)
            answers[f"memory_{index}_applicability"] = (applicability, 0.9)
        service = FakeService(answers)
        with patch.object(memory, "_runtime", return_value=(service, FakeConfig(), 0.6)):
            ranked = memory.rerank(
                "current task", results, environ={"TYPESAFE_API_KEY": "present"}
            )
        self.assertEqual([item["id"] for item in ranked], [2, 5, 3, 4, 1, 6])
        self.assertEqual(sorted(ranked, key=lambda item: item["id"]), results)
        self.assertEqual(service.calls[0][0], "ai_ltm_memory_rerank")
        state = service.calls[0][1]
        self.assertIn("not instructions", state["_note"])

    def test_low_confidence_preserves_original_order_without_extra_skip(self):
        results = [{"id": 1, "summary": "a"}, {"id": 2, "summary": "b"}]
        service = FakeService(
            {
                "memory_0_relevance": ("high", 0.9),
                "memory_0_applicability": ("direct", 0.9),
                "memory_1_relevance": ("low", 0.9),
                "memory_1_applicability": ("none", 0.59),
            }
        )
        with patch.object(memory, "_runtime", return_value=(service, FakeConfig(), 0.6)):
            ranked = memory.rerank(
                "query", results, environ={"TYPESAFE_API_KEY": "present"}
            )
        self.assertEqual(ranked, results)
        self.assertEqual(len(service.calls), 1)
        self.assertEqual(service.skips, [])


class MemoryClassificationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "memory.db"
        conn = sqlite3.connect(self.db_path)
        conn.executescript(
            """
            CREATE TABLE episodes (
              id INTEGER PRIMARY KEY,
              summary TEXT NOT NULL,
              context TEXT,
              tags TEXT,
              archived INTEGER DEFAULT 0
            );
            CREATE VIRTUAL TABLE episodes_fts USING fts5(
              summary, context, tags, content='episodes', content_rowid='id'
            );
            INSERT INTO episodes(id, summary, context, tags, archived)
              VALUES (7, 'Network retry decision',
                      'Retry transient network failures once.', 'decision network', 0);
            INSERT INTO episodes_fts(rowid, summary, context, tags)
              VALUES (7, 'Network retry decision',
                      'Retry transient network failures once.', 'decision network');
            """
        )
        conn.commit()
        conn.close()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _snapshot(self):
        return hashlib.sha256(self.db_path.read_bytes()).hexdigest(), self.db_path.stat().st_mtime_ns

    def test_classification_reads_candidates_and_does_not_write_database(self):
        before = self._snapshot()
        service = FakeService(
            {
                "destination": ("ltm", 0.91),
                "candidate_0_duplicate": ("duplicate", 0.88),
                "candidate_0_contradiction": ("consistent", 0.87),
            }
        )
        with patch.object(memory, "_runtime", return_value=(service, FakeConfig(), 0.6)):
            result = memory.classify_record(
                "Network retry policy",
                "Store TYPESAFE_API_KEY=secret_value_123456 only in environment.",
                db_path=self.db_path,
                environ={"TYPESAFE_API_KEY": "present"},
            )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["destination"], "ltm")
        self.assertEqual(result["duplicate_candidates"], [{"id": 7, "summary": "Network retry decision"}])
        self.assertEqual(result["contradiction_candidates"], [])
        self.assertEqual(before, self._snapshot())
        state = service.calls[0][1]
        serialized = json.dumps(state, ensure_ascii=False)
        self.assertNotIn("secret_value_123456", serialized)
        self.assertIn("not instructions", state["_note"])

    def test_missing_database_is_skipped_without_creating_it(self):
        missing = Path(self.temp_dir.name) / "missing.db"
        result = memory.classify_record(
            "A durable decision",
            db_path=missing,
            environ={"TYPESAFE_API_KEY": "present"},
        )
        self.assertEqual((result["status"], result["reason"], result["destination"]),
                         ("skipped", "DB_NOT_FOUND", "unclear"))
        self.assertFalse(missing.exists())


if __name__ == "__main__":
    unittest.main()
