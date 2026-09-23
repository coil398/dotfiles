from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from jev_hooks import jev_client, skills
from jev_hooks.config import Config
from jev_hooks.service import Evaluation


class SkillSelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.cfg = Config(mode="on", state_dir=str(self.root / "state"), confidence_threshold=0.6)
        self.env = {"HOME": str(self.root), "TYPESAFE_API_KEY": "test-key"}

    def tearDown(self):
        self.temp.cleanup()

    def _skill(self, root: Path, folder: str, name: str, description: str, body: str = "") -> Path:
        directory = root / folder
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "SKILL.md"
        path.write_text(f"---\nname: {name}\ndescription: >\n  {description}\n---\n{body}\n", encoding="utf-8")
        return path

    def _ask_select(self, choice: str):
        def ask(_policy, _state, questions, **kwargs):
            qid, question = next(iter(questions.items()))
            options = list(question["criteria"])
            selected = choice if choice in options else "none"
            answer = jev_client.ChoiceAnswer(
                choice=selected,
                probabilities={option: (1.0 if option == selected else 0.0) for option in options},
                confidence=0.95,
            )
            return Evaluation("ok", "evaluated", jev_client.JevResult(answers={qid: answer}, model="fake", elapsed_ms=1))

        return ask

    def test_native_skill_shadows_shared_name_and_frontmatter_is_bounded(self):
        native = self.root / "native"
        shared = self.root / "shared"
        native_path = self._skill(native, "parser", "data-parser", "Parse structured data safely.", "body needle native")
        self._skill(shared, "parser-copy", "data-parser", "A different shared parser.", "body needle shared")
        self._skill(shared, "unrelated", "calendar", "Manage calendar meeting files.")
        self._skill(native, "bad", "bad", "")
        env = {**self.env, skills.SKILL_ROOTS_ENV: os.pathsep.join((str(native), str(shared)))}

        with patch("jev_hooks.service.evaluate", side_effect=self._ask_select("skill_0")) as call:
            result = skills.select_skills("parse this data", cwd=str(self.root), environ=env, runtime="codex", cfg=self.cfg)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["selected"][0]["path"], str(native_path))
        self.assertEqual([item["name"] for item in result["candidates"]].count("data-parser"), 1)
        sent_questions = call.call_args.args[2]
        self.assertIn("none", sent_questions["skill"]["criteria"])
        skill_choices = [choice for choice in sent_questions["skill"]["criteria"] if choice != "none"]
        self.assertTrue(skill_choices)
        self.assertTrue(all(choice.startswith("skill_") and "data" not in choice for choice in skill_choices))
        self.assertNotIn("body needle", json.dumps(call.call_args.args[1]))

    def test_no_api_key_skips_before_skill_root_scan(self):
        env = {"HOME": str(self.root)}
        with patch("jev_hooks.skills._skill_roots", side_effect=AssertionError("root scan")) as roots, patch("jev_hooks.service.record_skip") as skip:
            result = skills.select_skills("search for local docs", cwd=str(self.root), environ=env, cfg=self.cfg)
        self.assertEqual((result["status"], result["reason"]), ("skipped", "no_api_key"))
        roots.assert_not_called()
        skip.assert_called_once()

    def test_explicit_or_prohibited_skill_is_never_replaced_by_a_jevs_choice(self):
        root = self.root / "skills"
        self._skill(root, "research", "research", "Research local and web sources.")
        self._skill(root, "review", "reviewer", "Review code changes.")
        env = {**self.env, skills.SKILL_ROOTS_ENV: str(root)}
        only_reviewer = self.root / "only-reviewer"
        self._skill(only_reviewer, "review", "reviewer", "Review code changes.")
        prohibited_env = {**self.env, skills.SKILL_ROOTS_ENV: str(only_reviewer)}
        with patch("jev_hooks.service.evaluate") as evaluate:
            slash = skills.select_skills("/research check this", environ=env, cfg=self.cfg)
            dollar = skills.select_skills("$research check this", environ=env, cfg=self.cfg)
            explicit = skills.select_skills("Please use the reviewer skill.", environ=env, cfg=self.cfg)
            prohibited = skills.select_skills("Review the diff, but do not use reviewer.", environ=prohibited_env, cfg=self.cfg)
            prohibited_suffix = skills.select_skills("レビューして。reviewer は使わないで。", environ=prohibited_env, cfg=self.cfg)
        self.assertEqual(slash["reason"], "explicit_skill")
        self.assertEqual(dollar["reason"], "explicit_skill")
        self.assertEqual(explicit["reason"], "explicit_skill")
        self.assertEqual(prohibited["reason"], "skills_prohibited_by_request")
        self.assertEqual(prohibited_suffix["reason"], "skills_prohibited_by_request")
        evaluate.assert_not_called()

    def test_explicit_mention_of_disabled_skill_suggests_nothing(self):
        project = self.root / "project"
        (project / ".git").mkdir(parents=True)
        shared = project / ".agents" / "skills"
        self._skill(shared, "plan", "writing-plan", "Write implementation plans.")
        self._skill(shared, "pir2", "pir2", "Plan and implement complex changes.")
        (self.root / ".claude").mkdir()
        (self.root / ".claude" / "settings.json").write_text(
            json.dumps({"skillOverrides": {"writing-plan": "off"}}), encoding="utf-8"
        )
        with patch("jev_hooks.service.evaluate", side_effect=self._ask_select("skill_0")) as evaluate:
            result = skills.select_skills(
                "use writing-plan to plan this change", cwd=str(project), environ=self.env, runtime="claude", cfg=self.cfg
            )
        self.assertEqual((result["status"], result["reason"], result["selected"]), ("skipped", "explicit_skill", []))
        evaluate.assert_not_called()

    def test_choice_none_and_low_confidence_return_no_skill(self):
        root = self.root / "skills"
        self._skill(root, "one", "one", "A skill for unrelated tasks.")
        env = {**self.env, skills.SKILL_ROOTS_ENV: str(root)}
        with patch("jev_hooks.service.evaluate", side_effect=self._ask_select("none")):
            result = skills.select_skills("make a tiny calculation", environ=env, cfg=self.cfg)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["selected"], [])
        self.assertEqual(result["reason"], "no_matching_skill")

        low = jev_client.JevResult(
            answers={"skill": jev_client.ChoiceAnswer("skill_0", {"skill_0": 0.9, "none": 0.1}, 0.4)},
            model="fake",
        )
        with patch("jev_hooks.service.evaluate", return_value=type("E", (), {"status": "ok", "result": low})()):
            result = skills.select_skills("one", environ=env, cfg=self.cfg)
        self.assertEqual((result["status"], result["reason"], result["selected"]), ("skipped", "low_confidence", []))

    def test_candidate_limit_and_original_request_not_written_to_usage_log(self):
        root = self.root / "skills"
        for index in range(skills.MAX_CANDIDATES + 5):
            self._skill(root, f"skill-{index:02}", f"topic-{index:02}", f"Handles subject {index:02}.")
        env = {**self.env, skills.SKILL_ROOTS_ENV: str(root)}
        query = "PRIVATE_REQUEST_SENTINEL explain topic 03"

        def choose_none(**kwargs):
            qid, question = next(iter(kwargs["questions"].items()))
            options = list(question["criteria"])
            answer = jev_client.ChoiceAnswer("none", {option: (1.0 if option == "none" else 0.0) for option in options}, 0.95)
            return jev_client.JevResult(answers={qid: answer}, model="jev-1.13.0", elapsed_ms=1)

        with patch("jev_hooks.jev_client.ask", side_effect=choose_none):
            result = skills.select_skills(query, environ=env, cfg=self.cfg)
        self.assertEqual(result["status"], "ok")
        self.assertLessEqual(len(result["candidates"]), skills.MAX_CANDIDATES)
        usage = (self.cfg.state_path() / "usage.sqlite3").read_bytes()
        self.assertNotIn(query.encode(), usage)

    def test_explicit_override_roots_preserve_order_and_skip_missing_home_roots(self):
        first = self.root / "first"
        second = self.root / "second"
        self._skill(first, "a", "first", "First root skill.")
        self._skill(second, "b", "second", "Second root skill.")
        env = {**self.env, skills.SKILL_ROOTS_ENV: os.pathsep.join((str(first), str(self.root / "missing"), str(second)))}
        roots = skills._skill_roots(str(self.root), env, "codex")
        self.assertEqual(roots, [first, second])
        found = skills._discover(roots)
        self.assertEqual([skill.name for skill in found], ["first", "second"])

    def test_claude_skill_overrides_off_are_excluded_and_do_not_shadow(self):
        project = self.root / "project"
        (project / ".git").mkdir(parents=True)
        self._skill(project / ".claude" / "skills", "chat", "chat", "Native chat skill.")
        shared_chat = self._skill(project / ".agents" / "skills", "chat", "chat", "Shared chat skill.")
        self._skill(project / ".agents" / "skills", "plan", "writing-plan", "Write plans.")
        self._skill(project / ".agents" / "skills", "keep", "research", "Research sources.")
        (self.root / ".claude").mkdir()
        (self.root / ".claude" / "settings.json").write_text(
            json.dumps({"skillOverrides": {"writing-plan": "off", "chat": "off", "research": "on"}}), encoding="utf-8"
        )
        # Project-local settings take precedence over user settings.
        (project / ".claude" / "settings.local.json").write_text(json.dumps({"skillOverrides": {"chat": "on"}}), encoding="utf-8")
        roots = skills._skill_roots(str(project), self.env, "claude")
        found = skills._discover(roots, skills._disabled_check(str(project), self.env, "claude"))
        self.assertEqual(sorted(skill.name for skill in found), ["chat", "research"])
        self.assertNotEqual(next(skill.path for skill in found if skill.name == "chat"), str(shared_chat))

        (project / ".claude" / "settings.local.json").write_text("{invalid", encoding="utf-8")
        found = skills._discover(roots, skills._disabled_check(str(project), self.env, "claude"))
        self.assertEqual(sorted(skill.name for skill in found), ["research"])
        # Claude settings do not disable Codex suggestions.
        found = skills._discover(roots, skills._disabled_check(str(project), self.env, "codex"))
        self.assertEqual(sorted(skill.name for skill in found), ["chat", "research", "writing-plan"])

    def test_codex_disabled_skill_paths_are_excluded(self):
        shared = self.root / "shared"
        disabled = self._skill(shared, "codex", "codex", "Delegate to Codex.")
        self._skill(shared, "debug", "debug", "Debug failures.")
        codex_home = self.root / "codex-home"
        codex_home.mkdir()
        (codex_home / "config.toml").write_text(
            f'[[skills.config]]\npath = "{disabled}"\nenabled = false\n\n'
            f'[[skills.config]]\npath = "{shared / "debug" / "SKILL.md"}"\nenabled = true\n',
            encoding="utf-8",
        )
        env = {**self.env, "CODEX_HOME": str(codex_home)}
        found = skills._discover([shared], skills._disabled_check(str(self.root), env, "codex"))
        self.assertEqual([skill.name for skill in found], ["debug"])

        (codex_home / "config.toml").write_text("not = [valid", encoding="utf-8")
        found = skills._discover([shared], skills._disabled_check(str(self.root), env, "codex"))
        self.assertEqual([skill.name for skill in found], ["codex", "debug"])
        found = skills._discover([shared], skills._disabled_check(str(self.root), self.env, "codex"))
        self.assertEqual([skill.name for skill in found], ["codex", "debug"])


if __name__ == "__main__":
    unittest.main()
