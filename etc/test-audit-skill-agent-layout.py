#!/usr/bin/env python3
"""Focused tests for the live Cursor agents directory audit."""

from __future__ import annotations

import importlib.util
import io
import os
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("audit-skill-agent-layout.py")
SPEC = importlib.util.spec_from_file_location("audit_skill_agent_layout", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {MODULE_PATH}")
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def make_directory_link(link: Path, target: Path) -> None:
    if os.name != "nt":
        link.symlink_to(target, target_is_directory=True)
        return

    def quote_ps(value: Path) -> str:
        return str(value).replace("'", "''")

    command = (
        f"New-Item -ItemType Junction -Path '{quote_ps(link)}' "
        f"-Target '{quote_ps(target)}' | Out-Null"
    )
    subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
        check=True,
        capture_output=True,
        text=True,
    )


class CursorHomeAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="audit-cursor-home-")
        root = Path(self.temp.name)
        self.dotfiles = root / "dotfiles"
        self.home = root / "home"
        (self.dotfiles / ".cursor" / "agents").mkdir(parents=True)
        (self.home / ".cursor").mkdir(parents=True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    @property
    def source_agents(self) -> Path:
        return self.dotfiles / ".cursor" / "agents"

    @property
    def home_agents(self) -> Path:
        return self.home / ".cursor" / "agents"

    def run_audit(self) -> tuple[int, str]:
        output = io.StringIO()
        with redirect_stdout(output):
            result = AUDIT.audit_live_cursor_home(self.dotfiles, self.home)
        return result, output.getvalue()

    def test_canonical_directory_link_passes(self) -> None:
        make_directory_link(self.home_agents, self.source_agents)

        result, output = self.run_audit()

        self.assertEqual(result, 0, output)
        self.assertIn("cursor-home", output)
        self.assertIn("-> dotfiles", output)
        if os.name == "nt":
            self.assertFalse(self.home_agents.is_symlink())

    def test_real_directory_fails(self) -> None:
        self.home_agents.mkdir()

        result, output = self.run_audit()

        self.assertGreater(result, 0, output)
        self.assertIn("real directory", output)

    def test_wrong_target_link_fails(self) -> None:
        wrong_target = self.home / "wrong-target"
        wrong_target.mkdir()
        make_directory_link(self.home_agents, wrong_target)

        result, output = self.run_audit()

        self.assertGreater(result, 0, output)
        self.assertIn("want", output)

    def test_broken_target_fails(self) -> None:
        broken_target = self.home / "broken-target"
        broken_target.mkdir()
        make_directory_link(self.home_agents, broken_target)
        shutil.rmtree(broken_target)

        result, output = self.run_audit()

        self.assertGreater(result, 0, output)
        self.assertIn("want", output)


if __name__ == "__main__":
    unittest.main(verbosity=2)
