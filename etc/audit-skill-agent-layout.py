#!/usr/bin/env python3
"""Audit skill + agent layout for a repo (cwd) and optionally dotfiles.

Policy (product + repo direction):
- Skills SSOT: .agents/skills
- Claude discovery: .claude/skills (symlink into .agents is PASS)
- Cursor/Codex discover .agents/skills natively; overlays are optional
- Agent files live per runtime; model slugs may differ
- Cursor agent YAML: model is inherit or a real ID; job class is role: coding|reasoning
- Cursor overlay SKILL.md: frontmatter name == folder; overlay notice uses inherit/role (not role-as-model)
- Shared *body* is expected when a generator claims lockstep
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"
INFO = "INFO"

VENDOR_MODELS = re.compile(
    r"^(opus|sonnet|haiku|fable|gpt-[\w.-]+|o\d[\w.-]*|codex|composer-[\w.-]+)$",
    re.I,
)
ROLE_AS_MODEL = re.compile(r"^(coding|reasoning)$", re.I)
INHERIT_MODEL = re.compile(r"^inherit$", re.I)
STALE_VENDOR_BANNER = "ベンダーモデル名"
STALE_ROLE_EQ_BANNER = "role=reasoning|coding"
CURSOR_INHERIT_BANNER = "Cursor agent の `model` は `inherit`"
CURSOR_ROLE_BANNER = "仕事の分類は"
VALID_ROLES = {"coding", "reasoning"}


def emit(level: str, repo: str, topic: str, msg: str) -> None:
    print(f"{level}\t{repo}\t{topic}\t{msg}")


def git_root(path: Path) -> Path | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if out.returncode != 0:
        return None
    return Path(out.stdout.strip())


def list_dirs(root: Path) -> list[str]:
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir() and not p.name.startswith("."))


def list_stems(root: Path, suffix: str) -> list[str]:
    if not root.is_dir():
        return []
    return sorted(p.stem for p in root.iterdir() if p.is_file() and p.suffix == suffix and not p.name.startswith("."))


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    fm_raw = text[4:end]
    body = text[end + 4 :].lstrip("\n")
    fields: dict[str, str] = {}
    for line in fm_raw.splitlines():
        if ":" not in line or line[:1] in " \t-":
            continue
        key, val = line.split(":", 1)
        fields[key.strip()] = val.strip().strip('"').strip("'")
    return fields, body


def strip_overlay_banner(body: str) -> str:
    lines = body.splitlines()
    out: list[str] = []
    skipping = True
    for line in lines:
        s = line.strip()
        if skipping and (
            s == ""
            or s.startswith("<!--")
            or s.startswith("> **Cursor")
            or s.startswith("> - ")
            or s.startswith("> **")
        ):
            continue
        skipping = False
        out.append(line)
    return "\n".join(out).strip() + "\n"


def normalize_vocab(text: str) -> str:
    repl = [
        ("`Task` ツール", "`Agent` ツール"),
        ("`Task`", "`Agent`"),
        ("Task ツール", "Agent ツール"),
        ("Task({", "Agent({"),
        ("background Task", "background Agent"),
        ("メインエージェント", "メイン Claude"),
        ("Cursor の Edit", "Claude Code の Edit"),
        ("Cursor (Task/subagent)", "Claude Code"),
        ("Bearer <demo-token>", "Bearer DemoAccount"),
    ]
    for a, b in repl:
        text = text.replace(a, b)
    return text


def skill_kind(path: Path) -> str:
    if path.is_symlink():
        return f"symlink->{path.readlink()}"
    if path.is_dir():
        return "dir"
    return "missing"


def points_at_agents(link: Path, agents_skill: Path) -> bool:
    try:
        return link.resolve() == agents_skill.resolve()
    except OSError:
        return False


def toml_first_line(path: Path) -> str:
    try:
        with path.open(encoding="utf-8") as fh:
            return fh.readline().rstrip("\n")
    except OSError:
        return ""


def extract_toml_instructions(text: str) -> str | None:
    m = re.search(r"^developer_instructions\s*=\s*(.*)$", text, re.M)
    if not m:
        return None
    raw = m.group(1).strip()
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(value, str):
        return None
    marker = "--- Shared agent instructions ---"
    if marker in value:
        value = value.split(marker, 1)[1]
    return value.strip() + "\n"


def extract_toml_model(text: str) -> str:
    m = re.search(r"^model\s*=\s*\"([^\"]+)\"", text, re.M)
    return m.group(1) if m else ""


def classify_model(value: str) -> str:
    v = value.strip()
    if not v:
        return "absent"
    if ROLE_AS_MODEL.match(v):
        return "role-as-model"
    if INHERIT_MODEL.match(v):
        return "inherit"
    if VENDOR_MODELS.match(v):
        return "vendor"
    return "other"


def audit_cursor_agent_contract(label: str, name: str, umodel: str, urole: str) -> int:
    fails = 0
    kind = classify_model(umodel)
    if kind == "role-as-model":
        emit(
            FAIL,
            label,
            "agents",
            f"{name} cursor model={umodel} is a job class; use model: inherit and role: {umodel}",
        )
        fails += 1
        return fails
    if kind == "inherit" and urole not in VALID_ROLES:
        emit(
            FAIL,
            label,
            "agents",
            f"{name} cursor model=inherit requires role: coding|reasoning (got {urole or '-'})",
        )
        fails += 1
    if kind == "absent":
        emit(
            WARN,
            label,
            "agents",
            f"{name} cursor model omitted (runtime inherit); set model: inherit and role:",
        )
    return fails


def audit_cursor_skill_file(label: str, skill_dir: Path) -> int:
    fails = 0
    name = skill_dir.name
    topic = "cursor-skill"
    if name.startswith("cursor-"):
        emit(FAIL, label, topic, f"legacy cursor-* directory {name}")
        fails += 1
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        emit(FAIL, label, topic, f"{name} missing SKILL.md")
        return fails + 1
    text = skill_md.read_text(encoding="utf-8")
    fm, _ = split_frontmatter(text)
    fm_name = fm.get("name", "").strip()
    if fm_name != name:
        emit(FAIL, label, topic, f"{name} frontmatter name={fm_name!r} != folder")
        fails += 1
    if STALE_VENDOR_BANNER in text:
        emit(FAIL, label, topic, f"{name} stale banner {STALE_VENDOR_BANNER!r}")
        fails += 1
    if STALE_ROLE_EQ_BANNER in text:
        emit(FAIL, label, topic, f"{name} stale banner {STALE_ROLE_EQ_BANNER!r}")
        fails += 1
    if "Cursor 実行時の注意" in text:
        if CURSOR_INHERIT_BANNER not in text or CURSOR_ROLE_BANNER not in text:
            emit(
                FAIL,
                label,
                topic,
                f"{name} overlay notice missing inherit/role contract",
            )
            fails += 1
    return fails


def audit_cursor_overlays(repo: Path, label: str) -> int:
    fails = 0
    cursor = repo / ".cursor" / "skills"
    if not cursor.is_dir():
        return 0
    names = list_dirs(cursor)
    emit(INFO, label, "cursor-skill", f".cursor/skills count={len(names)}")
    for name in names:
        fails += audit_cursor_skill_file(label, cursor / name)
    return fails


def audit_skills(repo: Path, label: str) -> int:
    fails = 0
    agents = repo / ".agents" / "skills"
    claude = repo / ".claude" / "skills"
    cursor = repo / ".cursor" / "skills"
    codex = repo / ".codex" / "skills"

    if not agents.is_dir():
        emit(INFO, label, "skills", "no .agents/skills (shared core absent)")
        if claude.is_dir():
            emit(WARN, label, "skills", "Claude skills exist without .agents/skills SSOT")
        return 0

    names = list_dirs(agents)
    emit(INFO, label, "skills", f".agents/skills count={len(names)}")
    for name in names:
        src = agents / name
        cl = claude / name
        if cl.exists() or cl.is_symlink():
            if cl.is_symlink() and points_at_agents(cl, src):
                emit(PASS, label, "skills", f"claude/{name} symlink -> .agents")
            elif cl.is_symlink():
                emit(
                    WARN,
                    label,
                    "skills",
                    f"claude/{name} symlink -> {cl.readlink()} (not .agents/skills/{name})",
                )
            else:
                emit(
                    WARN,
                    label,
                    "skills",
                    f"claude/{name} is a real directory ({skill_kind(cl)}); SSOT is .agents",
                )
        else:
            emit(INFO, label, "skills", f"claude/{name} absent (Claude discovery will miss it)")

        if (cursor / name).is_dir():
            emit(INFO, label, "skills", f"cursor overlay present: {name}")
        if (codex / name).is_dir():
            emit(INFO, label, "skills", f"codex overlay present: {name}")

    if claude.is_dir():
        for name in list_dirs(claude):
            if name not in names:
                emit(WARN, label, "skills", f"claude-only skill {name} (not in .agents/skills)")
    return fails


def audit_agents(repo: Path, label: str) -> int:
    fails = 0
    claude_dir = repo / ".claude" / "agents"
    cursor_dir = repo / ".cursor" / "agents"
    codex_dir = repo / ".codex" / "agents"
    if not claude_dir.is_dir() and not cursor_dir.is_dir() and not codex_dir.is_dir():
        emit(INFO, label, "agents", "no agent directories")
        return 0

    claude = list_stems(claude_dir, ".md")
    cursor = list_stems(cursor_dir, ".md")
    codex = list_stems(codex_dir, ".toml")
    emit(INFO, label, "agents", f"counts claude={len(claude)} cursor={len(cursor)} codex={len(codex)}")

    for name in claude:
        if name not in cursor and cursor_dir.is_dir():
            emit(FAIL, label, "agents", f"cursor missing {name}.md")
            fails += 1
        if name not in codex and name != "codex-runner" and codex_dir.is_dir():
            emit(WARN, label, "agents", f"codex missing {name}.toml")

        cpath = claude_dir / f"{name}.md"
        ctext = cpath.read_text(encoding="utf-8")
        cfm, cbody = split_frontmatter(ctext)
        cbody = strip_overlay_banner(cbody)
        cmodel = cfm.get("model", "")
        emit(INFO, label, "agents", f"{name} claude model={cmodel or '-'} ({classify_model(cmodel)})")

        upath = cursor_dir / f"{name}.md"
        if upath.is_file():
            utext = upath.read_text(encoding="utf-8")
            ufm, ubody = split_frontmatter(utext)
            ubody = strip_overlay_banner(ubody)
            umodel = ufm.get("model", "")
            urole = ufm.get("role", "")
            emit(INFO, label, "agents", f"{name} cursor model={umodel or '-'} ({classify_model(umodel)}) role={urole or '-'}")
            fails += audit_cursor_agent_contract(label, name, umodel, urole)
            if cbody == ubody:
                emit(PASS, label, "agents", f"{name} claude/cursor body identical (model may differ)")
            elif normalize_vocab(cbody) == normalize_vocab(ubody):
                emit(PASS, label, "agents", f"{name} claude/cursor body vocab-only (Agent/Task etc)")
            else:
                emit(
                    WARN,
                    label,
                    "agents",
                    f"{name} claude/cursor body substantive drift (native overlay or stale seed)",
                )

        tpath = codex_dir / f"{name}.toml"
        if tpath.is_file():
            ttext = tpath.read_text(encoding="utf-8")
            first = toml_first_line(tpath)
            tmodel = extract_toml_model(ttext)
            emit(INFO, label, "agents", f"{name} codex model={tmodel or '-'} ({classify_model(tmodel)}) marker={first[:60]}")
            generated = "AUTO-GENERATED" in first or "LEGACY-GENERATED" in first
            native = "Codex-native" in first or "editable overlay" in first
            instr = extract_toml_instructions(ttext)
            if generated:
                if instr is None:
                    emit(FAIL, label, "agents", f"{name} generated toml but developer_instructions unreadable")
                    fails += 1
                elif normalize_vocab(strip_overlay_banner(instr)) == normalize_vocab(cbody):
                    emit(PASS, label, "agents", f"{name} generated toml body matches claude")
                else:
                    emit(FAIL, label, "agents", f"{name} generated toml body stale vs claude")
                    fails += 1
            elif native:
                emit(INFO, label, "agents", f"{name} codex is native overlay (body lockstep not required)")
            else:
                emit(WARN, label, "agents", f"{name} codex toml has no generator/native marker")

    for name in cursor:
        if name not in claude:
            emit(WARN, label, "agents", f"cursor-only agent {name}")
            upath = cursor_dir / f"{name}.md"
            ufm, _ = split_frontmatter(upath.read_text(encoding="utf-8"))
            umodel = ufm.get("model", "")
            urole = ufm.get("role", "")
            fails += audit_cursor_agent_contract(label, name, umodel, urole)
    for name in codex:
        if name not in claude:
            emit(WARN, label, "agents", f"codex-only agent {name}")
    return fails


def audit_generators(repo: Path, label: str) -> int:
    fails = 0
    sync_py = repo / "scripts" / "sync-codex.py"
    if sync_py.is_file():
        proc = subprocess.run(
            [sys.executable, str(sync_py), "--check"],
            cwd=str(repo),
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0:
            emit(PASS, label, "generator", "scripts/sync-codex.py --check")
        else:
            emit(FAIL, label, "generator", f"scripts/sync-codex.py --check exit {proc.returncode}")
            if proc.stderr.strip():
                emit(INFO, label, "generator", proc.stderr.strip().splitlines()[-1][:200])
            fails += 1

    sync_sh = repo / "etc" / "sync-codex.sh"
    if sync_sh.is_file():
        emit(
            INFO,
            label,
            "generator",
            "etc/sync-codex.sh default does not regenerate .codex/agents (native overlay)",
        )

    seed = repo / "etc" / "seed-cursor-overlay.sh"
    if seed.is_file():
        emit(
            INFO,
            label,
            "generator",
            "etc/seed-cursor-overlay.sh never overwrites existing .cursor/agents (stale seed possible)",
        )

    automata_seed = repo / "scripts" / "seed-cursor-skill-overlays.sh"
    if automata_seed.is_file():
        emit(
            INFO,
            label,
            "generator",
            "scripts/seed-cursor-skill-overlays.sh seeds skills only; no cursor agent lockstep check",
        )
    return fails


def audit_repo(repo: Path, label: str) -> int:
    emit(INFO, label, "repo", str(repo))
    fails = 0
    fails += audit_skills(repo, label)
    fails += audit_cursor_overlays(repo, label)
    fails += audit_agents(repo, label)
    fails += audit_generators(repo, label)
    return fails


def resolve_dotfiles(explicit: str | None) -> Path | None:
    if explicit:
        p = Path(explicit).expanduser().resolve()
        return p if p.is_dir() else None
    env = os.environ.get("DOTFILES_ROOT")
    if env:
        p = Path(env).expanduser().resolve()
        if p.is_dir():
            return p
    home = Path.home() / "dotfiles"
    if home.is_dir():
        return home.resolve()
    here = Path(__file__).resolve()
    candidate = here.parent.parent
    if (candidate / "etc" / "audit-skill-agent-layout.py").is_file():
        return candidate
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", type=Path, default=Path.cwd(), help="launch directory")
    parser.add_argument("--dotfiles", type=Path, default=None)
    parser.add_argument("--skip-dotfiles", action="store_true")
    args = parser.parse_args()

    cwd = args.cwd.expanduser().resolve()
    launch = git_root(cwd) or cwd
    repos: list[tuple[str, Path]] = [("cwd", launch)]

    if not args.skip_dotfiles:
        df = resolve_dotfiles(str(args.dotfiles) if args.dotfiles else None)
        if df is None:
            emit(WARN, "dotfiles", "repo", "dotfiles root not found")
        elif df.resolve() != launch.resolve():
            repos.append(("dotfiles", df))
        else:
            emit(INFO, "cwd", "repo", "launch dir is dotfiles; audited once")

    fails = 0
    for label, path in repos:
        fails += audit_repo(path, label)

    print(f"SUMMARY\tfails={fails}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
