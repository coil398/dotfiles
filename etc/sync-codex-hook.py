#!/usr/bin/env python3
"""Filter Codex PostToolUse apply_patch events before running the generator.

The native hook uses tool_input.command and event.cwd, not Claude's
file_path payload. No model call is made; unrelated edits and successful
syncs produce no model-visible output.
"""

import json
from pathlib import Path
import re
import subprocess
import sys


SOURCE_FILES = {
    "AGENTS.md",
    "mcp-servers.json",
    ".codex/config.base.toml",
    ".codex/codex-native-supplement.md",
    ".claude/format.md",
    ".claude/user-feedback-protocol.md",
    ".claude/dev-server.md",
    ".codex/skills/pir2/references/handoff-protocol.md",
    ".codex/skills/pir2/references/protocol.md",
    "etc/sync-codex.sh",
}
PATCH_PATH = re.compile(r"^\*\*\* (?:Add File|Update File|Delete File|Move to): (.+)$")


def feedback(message):
    """Report a failure without blocking or replacing the completed edit."""
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": "[codex-sync-hook] " + message,
    }}))


def touches_source(event, root):
    if not isinstance(event, dict):
        raise ValueError("hook input must be an object")
    if event.get("hook_event_name") != "PostToolUse":
        return False
    if event.get("tool_name") != "apply_patch":
        return False
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        raise ValueError("apply_patch input must be an object")
    patch = tool_input.get("command")
    cwd = event.get("cwd")
    if not isinstance(patch, str) or not isinstance(cwd, str):
        raise ValueError("apply_patch command and cwd must be strings")
    base = Path(cwd)
    if not base.is_absolute():
        raise ValueError("hook cwd must be absolute")
    lines = patch.strip().splitlines()
    if not lines or lines[0] != "*** Begin Patch" or lines[-1] != "*** End Patch":
        raise ValueError("unrecognized apply_patch envelope")
    for line in lines[1:-1]:
        match = PATCH_PATH.match(line)
        if not match:
            continue
        # Never execute patch text. Leading '+'/'-'/' ' in file contents
        # prevents embedded header-like text from matching this expression.
        path = Path(match.group(1))
        absolute = (path if path.is_absolute() else base / path).resolve()
        try:
            relative = absolute.relative_to(root)
        except ValueError:
            continue
        if relative.as_posix() in SOURCE_FILES:
            return True
        parts = relative.parts
        # Only top-level Skill entries affect duplicate suppression. The
        # implementation and reference bodies are read directly by Codex.
        if (len(parts) == 4 and parts[0] in {".agents", ".codex"}
                and parts[1] == "skills" and parts[3] == "SKILL.md"):
            return True
    return False


def main():
    root = Path(__file__).resolve().parent.parent
    try:
        event = json.load(sys.stdin)
        relevant = touches_source(event, root)
    except (ValueError, OSError, RuntimeError):
        feedback("Cannot classify the edit; sync was not run. Check the hook input format.")
        return 0
    if not relevant:
        return 0
    producer = root / "etc" / "sync-codex.sh"
    try:
        result = subprocess.run(
            ["bash", str(producer)], cwd=str(root), stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            timeout=120, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        feedback("Configuration sync could not complete. Run the generator directly to inspect the failure.")
        return 0
    if result.returncode:
        # Do not inject producer logs (which may contain local settings) into
        # the model context. The exit code is enough to request diagnosis.
        feedback("Configuration sync failed (exit {}). Run {} directly to inspect it.".format(
            result.returncode, producer))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
