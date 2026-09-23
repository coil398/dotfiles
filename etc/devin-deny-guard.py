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


def matching_rule(tool, tool_input, cwd, entries):
    cmd = ""
    if tool == "exec":
        cmd = str(tool_input.get("command") or "").lstrip()
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
            if cmd == arg or cmd.startswith(arg + " "):
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
