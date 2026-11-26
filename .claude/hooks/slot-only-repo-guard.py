#!/usr/bin/env python3
"""slot-only-repo-guard: 常設の作業枠だけで扱う repository の worktree / clone 作成を止める。

PreToolUse hook (Claude Code / Codex 共通, matcher=Bash)。stdin の hook input JSON から
shell command を読み、次の場合に exit 2 で block して理由を stderr に出す。

- `git ... worktree add`: 対象 repository（`git -C <path>` があればその path、なければ hook input の cwd）
  の `git config --bool agent.slotOnly` が true のとき。
- `git clone` / `gh repo clone`: command が `~/.config/agent-guards/slot-only-remotes` の
  いずれかの行（`owner/repo`）を含むとき。

対象の設定は各 project の枠管理 helper が書き込む。案内文は対象 repository の
`git config agent.slotOnlyHint`（clone では remotes ファイルの同じ行の tab 以降）を使う。
"""
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

REMOTES = Path.home() / ".config/agent-guards/slot-only-remotes"
DEFAULT_HINT = "この repository は常設の作業枠だけで扱う。枠を借りてその中でブランチを切り替える。"


def git_config(repo: str, *args: str) -> str:
    r = subprocess.run(["git", "-C", repo, "config", *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def segments(cmd: str):
    for part in re.split(r"&&|\|\||;|\||\n", cmd):
        try:
            words = shlex.split(part)
        except ValueError:
            words = part.split()
        if words:
            yield words


def worktree_target(words: list[str], cwd: str) -> str | None:
    if "git" not in words:
        return None
    i = words.index("git")
    rest = words[i + 1:]
    repo = cwd
    j = 0
    while j < len(rest) and rest[j].startswith("-"):
        if rest[j] == "-C" and j + 1 < len(rest):
            repo = str(Path(cwd, rest[j + 1]).expanduser())
            j += 2
            continue
        j += 2 if rest[j] in ("-c", "--git-dir", "--work-tree") else 1
    if rest[j:j + 2] == ["worktree", "add"]:
        return repo
    return None


def block(msg: str) -> None:
    print(f"slot-only-repo-guard: {msg}", file=sys.stderr)
    sys.exit(2)


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return
    ti = data.get("tool_input") or {}
    cmd = ti.get("command", "")
    if isinstance(cmd, list):
        cmd = " ".join(cmd)
    if not isinstance(cmd, str) or not cmd:
        return
    cwd = data.get("cwd") or ti.get("workdir") or "."
    for words in segments(cmd):
        repo = worktree_target(words, cwd)
        if repo and git_config(repo, "--bool", "agent.slotOnly") == "true":
            block(f"{repo} では git worktree を作らない。" +
                  (git_config(repo, "agent.slotOnlyHint") or DEFAULT_HINT))
    if not re.search(r"\bgit\b.*\bclone\b|\bgh\s+repo\s+clone\b", cmd) or not REMOTES.is_file():
        return
    for line in REMOTES.read_text().splitlines():
        name, _, hint = line.partition("\t")
        name = name.strip()
        if name and re.search(re.escape(name) + r"(\.git)?(?![\w.-])", cmd):
            block(f"{name} を clone しない。" + (hint.strip() or DEFAULT_HINT))


if __name__ == "__main__":
    main()
