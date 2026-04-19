#!/bin/sh
# PIR² 系スキル（/pir2, /pir2async, /debug）の preflight。
# 各プロジェクトの .claude/settings.local.json に additionalDirectories として
# ~/.ai-pir-runs と ~/.claude/projects を追加する。
#
# 冪等: 既に含まれていれば no-op。JSON が壊れていれば skip して警告。
# 初回実行時のみ settings.local.json への書き込みが発生する（以降 no-op）。

set -eu

command -v python3 >/dev/null 2>&1 || {
  echo "ensure-pir-permissions: python3 not found, skipping" >&2
  exit 0
}

settings="$(pwd)/.claude/settings.local.json"

python3 - "$settings" <<'PYEOF'
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
path.parent.mkdir(parents=True, exist_ok=True)

if path.exists():
    text = path.read_text().strip() or "{}"
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        print(
            f"ensure-pir-permissions: {path} is invalid JSON, skipping ({e})",
            file=sys.stderr,
        )
        sys.exit(0)
else:
    data = {}

perms = data.setdefault("permissions", {})
dirs = perms.setdefault("additionalDirectories", [])

targets = ["~/.ai-pir-runs", "~/.claude/projects"]
added = [t for t in targets if t not in dirs]
for t in added:
    dirs.append(t)

if added:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"ensure-pir-permissions: added {added} to {path}")
PYEOF
