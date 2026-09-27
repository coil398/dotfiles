#!/usr/bin/env python3
# deny-guard.py (Devin CLI PreToolUse hook)
#
# permissions.deny の拒否はヒットした時点でエージェントのターンごと止まる
# ("Permission denied")。この hook は全 deny ルールを先に評価し、
# decision=block + reason を返すことで「禁止。別手段で継続せよ」を
# エージェントへ伝え、ターンを生かす。v3000.6.2 以降、PreToolUse hook の
# block は reason をエージェントへ返してターンを継続する。
#
# deny ルール自体は各 config に残す。hook が壊れた・見逃した場合の backstop
# であり、Read(...) deny は sandbox のパス隠しにも使われる。org/team 由来の
# deny は別ファイル層なのでこの hook では拾わず、engine の強制拒否のまま。
#
# 配置: ~/.config/devin/config.json の hooks.PreToolUse (matcher "")
# 入力: stdin に hook payload JSON ({tool_name, tool_input})
# 出力: 一致時 {"decision":"block","reason":"..."}、それ以外・異常時は無言で exit 0

import json
import os
import re
import shlex
import sys

READ_TOOLS = {"read", "notebook_read", "grep", "glob", "code_search"}
WRITE_TOOLS = {"write", "edit", "notebook_edit", "apply_patch"}
PATH_KEYS = ("file_path", "notebook_path", "path", "search_folder_absolute_uri")


def glob_to_regex(pat):
    out = []
    i, n = 0, len(pat)
    while i < n:
        c = pat[i]
        if c == "*":
            if pat.startswith("**/", i):
                out.append("(?:.*/)?")
                i += 3
            elif pat.startswith("**", i):
                out.append(".*")
                i += 2
            else:
                out.append("[^/]*")
                i += 1
        elif c == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(c))
            i += 1
    return "".join(out)


def glob_match(pat, path):
    try:
        return re.fullmatch(glob_to_regex(pat), path) is not None
    except re.error:
        return False


def path_candidates(raw, cwd):
    expanded = os.path.expanduser(raw)
    cands = [raw, expanded]
    if not os.path.isabs(expanded):
        cands.append(os.path.normpath(os.path.join(cwd, expanded)))
    seen, out = set(), []
    for c in cands:
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out


def exec_path_candidates(cmd, cwd):
    """Extract path-like tokens from a shell command for Read/Write deny checks.

    The engine denies exec calls whose path arguments hit a Read/Write deny
    glob, so the guard must evaluate those too — Exec() prefix rules alone
    miss e.g. `ls ~/.cache` (allowed Exec prefix, denied path). `p + '/_'`
    additionally matches "p is a denied directory itself" (`**/.cache/**`
    needs a trailing segment). Bare words get no dir fallback so routine
    commands like `npm run build` do not collide with `**/build/**`.
    """
    try:
        tokens = shlex.split(cmd, posix=True)
    except ValueError:
        tokens = cmd.split()
    out = []
    for tok in tokens:
        tok = re.sub(r"^[0-9]*[<>]+", "", tok)
        for t in [tok, tok.split("=", 1)[1] if "=" in tok else ""]:
            if not t or t.startswith("-"):
                continue
            pathish = "/" in t or t.startswith(("~", "."))
            for p in path_candidates(os.path.expandvars(t), cwd):
                out.append(p)
                if pathish:
                    out.append(p + "/_")
    return out


def url_match(pat, url):
    if pat.startswith("domain:"):
        host = re.sub(r"^https?://", "", url).split("/")[0].split(":")[0]
        return host == pat[len("domain:"):]
    if "*" in pat:
        try:
            return re.fullmatch(re.escape(pat).replace(r"\*", ".*"), url) is not None
        except re.error:
            return False
    return url == pat or url.startswith(pat)


def deny_entries(paths):
    entries = []
    for p in paths:
        try:
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        deny = (data.get("permissions") or {}).get("deny") or []
        if isinstance(deny, list):
            entries.extend(e for e in deny if isinstance(e, str))
    return entries


# Exec deny matching: the engine denies a rule's command anywhere it runs as
# a segment of the line — `cd /tmp && rm -rf x` hits `Exec(rm -rf)` even though
# the line starts with `cd`. A leading-prefix-only check let compound commands
# slip past the guard into the raw engine deny (turn-killing "Permission
# denied"), so segments are evaluated individually.

# Tokens that put a real command later in the same segment:
# env/command/nice take -flag args and VAR=val before the command; `if`/`while`
# style keywords precede a command list. (`for`/`select` are absent — their
# in-word list is not a command position.)
EXEC_WRAPPERS = {
    "env", "command", "nice", "nohup", "time", "builtin", "stdbuf", "ionice",
    "if", "then", "elif", "else", "while", "until", "do", "done", "{", "}", "!",
}
# Shells whose `-c <string>` payload is itself a command line.
EXEC_SHELLS = {"sh", "bash", "zsh", "dash", "eval"}


def exec_segments(cmd):
    """Split a command line into list/pipeline segments on && || ; | newline.

    Quoted operators stay literal (posix shlex handles that). Segment text is
    NOT rejoined — tokens are kept so `rm -rf` compares word-wise.
    """
    try:
        lex = shlex.shlex(cmd, posix=True, punctuation_chars=";&|()")
        lex.whitespace_split = True
        toks = list(lex)
    except (ValueError, TypeError):
        toks = cmd.split()
    segs, cur = [], []
    for t in toks:
        if t and all(c in ";&|()" for c in t):
            if cur:
                segs.append(cur)
                cur = []
        else:
            cur.append(t)
    if cur:
        segs.append(cur)
    return segs


def exec_cmd_matches(cmd, arg, depth=0):
    """True when deny payload `arg` (e.g. 'rm -rf') runs as a command in any
    segment. Segments whose first token is a wrapper/env-assignment/keyword
    put the real command later — for those every token position is a
    candidate (`nice -n 5 rm -rf` denies at the `rm`), so wrapper flag-args
    cannot hide the command."""
    arg_toks = arg.split()
    if not arg_toks or depth > 3:
        return False
    for seg in exec_segments(cmd):
        if not seg:
            continue
        leading = (
            seg[0] in EXEC_WRAPPERS
            or seg[0] in EXEC_SHELLS
            or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", seg[0]) is not None
        )
        positions = range(len(seg) - len(arg_toks) + 1) if leading else range(1)
        for i in positions:
            if seg[i : i + len(arg_toks)] == arg_toks:
                return True
        # descend into `sh -c '...'` / `eval ...` — one indirection level at a
        # time. Only command-position shells count for plain commands (an
        # `echo sh -c …` string is not an execution).
        for i, t in enumerate(seg):
            if not leading and i > 0:
                break
            if t not in EXEC_SHELLS:
                continue
            rest = seg[i + 1 :]
            if t == "eval":
                payload = " ".join(rest)
            else:
                ci = next(
                    (j for j, w in enumerate(rest)
                     if re.fullmatch(r"-[a-zA-Z]*c[a-zA-Z]*", w)),
                    None,
                )
                payload = rest[ci + 1] if ci is not None and ci + 1 < len(rest) else None
            if payload and exec_cmd_matches(payload, arg, depth + 1):
                return True
    return False


def matching_rule(tool, tool_input, cwd, entries):
    cmd = ""
    epaths = []
    if tool == "exec":
        cmd = str(tool_input.get("command") or "").lstrip()
        epaths = exec_path_candidates(cmd, cwd)
    paths = []
    if tool in READ_TOOLS | WRITE_TOOLS:
        for k in PATH_KEYS:
            v = tool_input.get(k)
            if isinstance(v, str) and v:
                paths.extend(path_candidates(v, cwd))
    url = ""
    if tool == "webfetch":
        url = str(tool_input.get("url") or "")

    for e in entries:
        if e == tool or (e.startswith("mcp__") and tool.startswith(e.rstrip("*"))):
            return e
        m = re.fullmatch(r"(Exec|Read|Write|Fetch)\((.*)\)", e)
        if not m:
            continue
        kind, arg = m.group(1), m.group(2)
        if kind == "Exec" and tool == "exec":
            if exec_cmd_matches(cmd, arg):
                return e
        elif kind in ("Read", "Write") and tool == "exec":
            if any(glob_match(arg, p) for p in epaths):
                return e
        elif kind == "Read" and tool in READ_TOOLS:
            if any(glob_match(arg, p) for p in paths):
                return e
        elif kind == "Write" and tool in WRITE_TOOLS:
            if any(glob_match(arg, p) for p in paths):
                return e
        elif kind == "Fetch" and tool == "webfetch" and url:
            if url_match(arg, url):
                return e
    return None


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return
    tool = payload.get("tool_name") or ""
    tool_input = payload.get("tool_input") or {}
    if not tool or not isinstance(tool_input, dict):
        return

    cfgs = [os.environ.get("DEVIN_CONFIG")
            or os.path.expanduser("~/.config/devin/config.json")]
    proj = os.environ.get("DEVIN_PROJECT_DIR") or ""
    if proj:
        cfgs += [os.path.join(proj, ".devin/config.json"),
                 os.path.join(proj, ".devin/config.local.json")]
    entries = deny_entries([c for c in cfgs if os.path.isfile(c)])
    if not entries:
        return

    rule = matching_rule(tool, tool_input, proj or os.getcwd(), entries)
    if not rule:
        return

    reason = (
        f"このツール呼出しは permissions.deny の `{rule}` に一致するため実行できません。"
        "deny でターンごと止まるのを避けるため PreToolUse hook が block しました。"
        "同じ呼出しの再試行・表記違い・sudo や別ラッパー経由での回避はせず、"
        "別手段で目的を達成してください (例: ファイル削除は mv での退避、"
        "deny 済みパスの情報は許可された別ファイルから取得)。"
        "どうしても必要な場合だけユーザーに実行を依頼してください。"
    )
    json.dump({"decision": "block", "reason": reason}, sys.stdout,
              ensure_ascii=False)


if __name__ == "__main__":
    main()
