#!/usr/bin/env python3
import sys
import json
import re

# 危険・破壊的コマンドの正規表現パターン
DANGEROUS_PATTERNS = [
    r"\brm\s+-[rfRF]{1,2}\s+([/~]|\.\./|\*|$)",         # rm -rf /, rm -rf ~, rm -rf *
    r"\bgit\s+(push\s+--force|push\s+-f|reset\s+--hard)", # 強制pushやhard reset
    r"\bmkfs\b",                                         # ファイルシステム初期化
    r"\bdd\s+if=",                                       # 低レベルディスク書き込み
    r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;",             # fork bomb
    r"\bchmod\s+(-R\s+)?777\s+/",                        # ルート権限の全開放
    r"\b(drop|truncate)\s+(database|table)\b",           # DB破棄
]

def main():
    try:
        input_data = sys.stdin.read()
        if not input_data.strip():
            print(json.dumps({"decision": "allow"}))
            return
        data = json.loads(input_data)
    except Exception:
        # パース失敗時は通常動作を阻害しないよう allow
        print(json.dumps({"decision": "allow"}))
        return

    tool_call = data.get("toolCall", {})
    name = tool_call.get("name", "")
    args = tool_call.get("args", {})

    if name == "run_command":
        cmd = args.get("CommandLine", "")
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, cmd, re.IGNORECASE):
                print(json.dumps({
                    "decision": "ask",
                    "reason": f"⚠️ 危険・破壊的な可能性のあるコマンドを検出しました: {cmd}"
                }))
                return

    # 通常のコマンド、ファイル編集、ファイル作成等はすべて全自動承認
    print(json.dumps({"decision": "allow"}))

if __name__ == "__main__":
    main()
