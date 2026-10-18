import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ai_lint


class RuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = ai_lint.load_rules()
        cls.by_id = {rule["id"]: rule for rule in cls.rules}

    def test_each_rule_has_positive_and_negative_example(self):
        samples = {
            "hash-fingerprint": ("digest = hashlib.sha256(data)", "data = source"),
            "provenance-manifest": ("manifest_path = path", "provide a filename"),
            "mismatch-gate": ("if mismatch: raise ValueError()", "if values differ: log.info('changed')"),
            "contract-version": ("schema_version = 2", "schema_name = 'user'"),
            "new-option": ("parser.add_argument('--dry-run')", "source = args.source"),
            "compat-path": ("legacy_reader = old_value", "current_reader = value"),
            "fallback-default": ("value = data.get('x', [])", "value = data['x']"),
            "swallow-error": ("except Exception: pass", "except ValueError: raise"),
            "retry-sleep": ("time.sleep(2)", "timeout_seconds = 2"),
            "test-skip": ("pytest.mark.skip(reason='x')", "pytest.mark.parametrize('x', [1])"),
            "lint-suppress": ("value = item  # noqa", "value = item"),
            "placeholder": ("raise NotImplementedError()", "raise RuntimeError('failed')"),
            "lock-name": ('name = "session.lock"', 'name = "body lockstep"'),
            "state-marker": ("state_file = 'state.json'", "state_name = 'profile.json'"),
            "ensure-guard": ("def ensure_ready():", "def load_ready():"),
            "feature-flag": ("FEATURE_SEARCH = True", "SEARCH_MODE = 'full'"),
            "transaction-wrap": ("db.BeginTx(ctx)", "db.QueryContext(ctx, query)"),
            "history-comment": ("# temporary compatibility workaround", "# Load the current account"),
            "double-write": ("dual_write(record)", "write_record(record)"),
        }
        for rule_id, (positive, negative) in samples.items():
            with self.subTest(rule=rule_id):
                rule = self.by_id[rule_id]
                self.assertTrue(any(pattern.search(positive) for pattern in rule["compiled"]))
                self.assertFalse(any(pattern.search(positive) for pattern in rule["excluded"]))
                self.assertFalse(any(pattern.search(negative) and not any(ex.search(negative) for ex in rule["excluded"]) for pattern in rule["compiled"]))

    def test_lock_name_only_matches_path_or_lockfile_literals(self):
        rule = self.by_id["lock-name"]
        self.assertTrue(any(pattern.search('path = "var/session.lock"') for pattern in rule["compiled"]))
        self.assertFalse(any(pattern.search('message = "lockstep is enabled"') for pattern in rule["compiled"]))
        self.assertTrue(any(pattern.search('path = "uv.lock"') for pattern in rule["excluded"]))
        self.assertTrue(any(pattern.search('"uv_lock": uv_lock_provenance(lock)') for pattern in rule["excluded"]))
        self.assertTrue(any(pattern.search('FACET_UV_LOCK_SHA256_BEFORE') for pattern in rule["excluded"]))
        self.assertTrue(any(pattern.search('stage == "lock-hash"') for pattern in rule["excluded"]))

    def test_hash_comparison_is_a_gate_candidate(self):
        rule = self.by_id["mismatch-gate"]
        self.assertTrue(any(pattern.search("unchanged = before_sha256 == after") for pattern in rule["compiled"]))
        self.assertFalse(any(pattern.search("unchanged = before_count == after") for pattern in rule["compiled"]))

    def test_transaction_rule_ignores_patch_markers(self):
        rule = self.by_id["transaction-wrap"]
        self.assertTrue(any(pattern.search("BEGIN TRANSACTION;") for pattern in rule["compiled"]))
        self.assertEqual(rule["excluded"], [])

    def test_shell_guard_definitions_and_options(self):
        guards = self.by_id["ensure-guard"]["compiled"]
        for line in ("ensure_ledger() {", "ensure_run_dir() {", "ensure_record_id_unique() {"):
            self.assertTrue(any(pattern.search(line) for pattern in guards), line)
        self.assertFalse(any(pattern.search("load_ledger() {") for pattern in guards))

        options = self.by_id["new-option"]["compiled"]
        for line in ('value=${SYNC_CODEX_LEGACY_MIRROR:-0}', "--dry-run)"):
            self.assertTrue(any(pattern.search(line) for pattern in options), line)
        self.assertFalse(any(pattern.search("--other") for pattern in options))

    def test_contract_version_requires_contract_identifier(self):
        patterns = self.by_id["contract-version"]["compiled"]
        self.assertTrue(any(pattern.search("CONTRACT_VERSION = 2") for pattern in patterns))
        self.assertTrue(any(pattern.search("validate_contract(payload)") for pattern in patterns))
        self.assertFalse(any(pattern.search("# stdin prompt contract") for pattern in patterns))
        self.assertFalse(any(pattern.search("CONTRACT = 'prompt' ") for pattern in patterns))

    def test_double_write_only_matches_write_identifiers(self):
        patterns = self.by_id["double-write"]["compiled"]
        for line in ("mirror_to_store(record)", "sync_to_ledger(record)", "dual_write(record)", "write_both(record)"):
            self.assertTrue(any(pattern.search(line) for pattern in patterns), line)
        for line in ('logger.info("mirror enabled")', 'echo "mirror complete"', 'assert "mirror" in output', "# mirror the record"):
            self.assertFalse(any(pattern.search(line) for pattern in patterns), line)

    def test_transaction_rule_only_matches_sql_or_transaction_apis(self):
        patterns = self.by_id["transaction-wrap"]["compiled"]
        self.assertTrue(any(pattern.search("BEGIN;") for pattern in patterns))
        self.assertTrue(any(pattern.search("BEGIN WORK;") for pattern in patterns))
        self.assertFalse(any(pattern.search("# BEGIN") for pattern in patterns))
        self.assertFalse(any(pattern.search("cat <<'BEGIN'") for pattern in patterns))
        self.assertFalse(any(pattern.search('message = "BEGIN TRANSACTION;"') for pattern in patterns))


class InputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = ai_lint.load_rules()

    def test_claude_structured_patch(self):
        event = {"tool_name": "Edit", "cwd": str(ai_lint.ROOT), "tool_input": {"file_path": "sample.py"}, "tool_response": {"structuredPatch": [{"newStart": 10, "lines": [" context", "+hashlib.sha256(x)", "-old"]}]}}
        lines = ai_lint.parse_claude(event)
        self.assertEqual([(line.number, line.text) for line in lines], [(11, "hashlib.sha256(x)")])

    def test_claude_edit_multiedit_write_fallback(self):
        cases = [
            ({"tool_name": "Edit", "tool_input": {"file_path": "sample.py", "new_string": "digest = hashlib.sha1(x)"}}, "hashlib.sha1"),
            ({"tool_name": "MultiEdit", "tool_input": {"file_path": "sample.py", "edits": [{"new_string": "legacy_call()"}]}}, "legacy_call"),
            ({"tool_name": "Write", "tool_input": {"file_path": "sample.py", "content": "TODO finish"}}, "TODO finish"),
        ]
        for data, expected in cases:
            event = {**data, "cwd": str(ai_lint.ROOT)}
            self.assertTrue(any(expected in line.text for line in ai_lint.parse_claude(event)))

    def test_codex_apply_patch_additions(self):
        patch = "*** Begin Patch\n*** Update File: sample.py\n@@ -3,1 +3,2 @@\n old\n+raise NotImplementedError()\n*** End Patch"
        lines = ai_lint.parse_codex({"tool_name": "apply_patch", "cwd": str(ai_lint.ROOT), "tool_input": {"command": patch}})
        self.assertEqual([(line.path, line.number, line.text) for line in lines], [("sample.py", 4, "raise NotImplementedError()")])

    def test_ignores_non_code_and_generated_and_ai_lint_paths(self):
        for path in ("notes.md", ".codex/generated/config.toml", "ai-lint/rules.json", "ai-lint/tests/test_ai_lint.py"):
            with self.subTest(path=path):
                self.assertFalse(ai_lint.eligible_path(path))
        self.assertTrue(ai_lint.eligible_path("/tmp/outside.py"))

    def test_scan_absolute_path_outside_cwd_reports_hits(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "outside.py"
            source.write_text("value = hashlib.sha256(data)\n", encoding="utf-8")
            result = subprocess.run([sys.executable, str(Path(ai_lint.__file__)), "scan", str(source)], cwd=str(ai_lint.ROOT), text=True, capture_output=True)
        self.assertIn("[hash-fingerprint]", result.stdout)
        self.assertIn("hash-fingerprint: 1", result.stdout)

    def test_scan_unsupported_extension_reports_skip_reason(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "notes.md"
            source.write_text("hashlib.sha256(data)\n", encoding="utf-8")
            result = subprocess.run([sys.executable, str(Path(ai_lint.__file__)), "scan", str(source)], cwd=str(ai_lint.ROOT), text=True, capture_output=True)
        self.assertIn("no hits (0 files scanned, 1 skipped)", result.stdout)
        self.assertIn("reason=unsupported extension", result.stderr)

    def test_claude_hook_detects_edit_outside_cwd(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "outside.py"
            source.write_text("value = 1\n", encoding="utf-8")
            event = {"tool_name": "Edit", "cwd": str(ai_lint.ROOT), "tool_input": {"file_path": str(source), "new_string": "value = hashlib.sha256(data)"}}
            result = subprocess.run([sys.executable, str(Path(ai_lint.__file__)), "--hook", "claude"], input=json.dumps(event), text=True, capture_output=True)
        self.assertIn("[hash-fingerprint]", result.stdout)

    def test_render_caps_hits(self):
        hits = [ai_lint.Hit("sample", "Question?", "a.py", i, "x") for i in range(1, 20)]
        rendered = ai_lint.render(hits)
        self.assertLessEqual(rendered.count("[sample] a.py:"), 3)
        self.assertIn("ほか 16 件", rendered)

    def test_record_permissions_and_no_source_content(self):
        hit = ai_lint.Hit("hash-fingerprint", "?", "source.py", 1, "SECRET_SOURCE_TEXT")
        with tempfile.TemporaryDirectory() as directory:
            old = os.environ.get("XDG_STATE_HOME")
            os.environ["XDG_STATE_HOME"] = directory
            try:
                ai_lint.record_hits([hit], "claude", "/work")
                path = Path(directory) / "ai-lint" / "hits.jsonl"
                self.assertEqual(path.parent.stat().st_mode & 0o777, 0o700)
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
                record = json.loads(path.read_text())
                self.assertEqual(record["rules"], {"hash-fingerprint": 1})
                self.assertNotIn("SECRET_SOURCE_TEXT", path.read_text())
            finally:
                if old is None:
                    os.environ.pop("XDG_STATE_HOME", None)
                else:
                    os.environ["XDG_STATE_HOME"] = old

    def test_broken_hook_input_exits_zero(self):
        result = subprocess.run([sys.executable, str(Path(ai_lint.__file__)), "--hook", "claude"], input="{", text=True, capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("analysis_failed", result.stderr)

    def test_only_added_diff_lines_are_scanned(self):
        diff = "--- a/a.py\n+++ b/a.py\n@@ -1,2 +1,2 @@\n-hashlib.md5(x)\n+value = 1\n"
        lines = ai_lint.parse_unified_diff(diff)
        hits = ai_lint.scan_lines(lines, self.rules)
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
