#!/usr/bin/env python3
"""Rewrite Japanese through Gemini 4 Hydrogen (via the agy runner), then check the rewrite for misunderstanding."""

from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

MODEL = "gemini-4-hydrogen-low"
MAX_REPAIRS = 2
AGY_RUN = Path(__file__).resolve().parents[2] / "agy" / "scripts" / "agy-run.py"
WORK_DIR = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")) / "geminify" / "agy-jobs"
SYSTEM_INSTRUCTION = """\
あなたは日本語の編集者です。与えられた文章を、人間が読んで自然に理解できる日本語に書き直してください。

守ること:
- 意味・事実・数値・固有名詞・コード・パス・URL・コマンドは変えない
- 情報を足さない。読みにくさの原因になる冗長な接続やメタ説明だけ整える
- AI翻訳調・硬すぎる文体・不自然な体言止めの連続を避ける
- 前置き・後書き・解説は出さない。書き直した本文だけを返す
"""
REVIEW_INSTRUCTION = """\
あなたは原文と書き直しを照合する。見るのは、書き直しが原文を誤解していないかだけ。

誤解にあたるもの:
- 主張、結論、話者、対象の取り違え
- 条件、否定、因果の逆転
- 数値、固有名詞、コード、パス、URL、コマンドのすり替え
- 原文にない断定を足して、意味を変えること

誤解にあたらないもの:
- 読みやすくするための言い換え
- 意味が同じまま短くした接続やメタ説明
- 意味が変わらない細部の省略

この照合で見つかった誤解は、この応答に全部出す。一つだけ出して残りを次に回さない。
各 point は「原文では〜。書き直しは〜になっている。」と書き、どの意味がずれているか特定する。
意味が同じ言い換えや、意味が変わらない省略は misunderstanding を false にする。文体の好みは point にしない。

JSON だけを返す。説明は付けない。
誤解がなければ {"misunderstanding": false}
誤解があれば {"misunderstanding": true, "points": ["原文では〜。書き直しは〜になっている。"]}
"""
REPAIR_INSTRUCTION = """\
原文が意味の正本です。書き直し全文を、指摘された誤解がすべて消えるように、この一回で書き直してください。

1. 指摘を全部読む。一つも次に残さない。
2. 指摘された文だけを穴埋めしない。その誤解が隣の文に残っていれば、原文の意味に合わせてそこも直す。
3. 指摘されていない箇所の意味は変えない。読みやすい日本語は保つ。
4. 原文にない断定は足さない。数値、固有名詞、条件、否定は原文に合わせる。
5. 前置きと解説は出さず、直した全文だけを返す。
"""


def read_source(args: argparse.Namespace) -> str:
    if args.text_b64:
        return base64.b64decode(args.text_b64).decode("utf-8")
    if args.file:
        return Path(args.file).read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise SystemExit("対象文が空です。--text-b64、--file、または stdin を渡してください。")


def build_prompt(system: str, user: str) -> str:
    return f"{system}\n\n---\n\n{user}"


def review_user(source: str, rewritten: str) -> str:
    return f"原文:\n{source}\n\n書き直し:\n{rewritten}"


def repair_user(source: str, rewritten: str, points: list[str]) -> str:
    listed = "\n".join(f"- {point}" for point in points)
    return f"原文:\n{source}\n\n書き直し:\n{rewritten}\n\n誤解:\n{listed}"


def parse_review(text: str) -> tuple[bool, list[str]]:
    raw = text.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines).strip()
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("review JSON must be an object")
    misunderstood = data.get("misunderstanding")
    if not isinstance(misunderstood, bool):
        raise ValueError("misunderstanding must be a boolean")
    points_raw = data.get("points")
    points: list[str] = []
    if isinstance(points_raw, list):
        points = [item.strip() for item in points_raw if isinstance(item, str) and item.strip()]
    if misunderstood and not points:
        raise ValueError("misunderstanding requires points")
    return misunderstood, points


def ask(prompt: str) -> str:
    """agy の runner で MODEL に 1 回だけ問い合わせ、最終応答の本文を返す。"""
    WORK_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    run_id = f"geminify-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    prompt_file = WORK_DIR / f"{run_id}-input.md"
    prompt_file.write_text(prompt, encoding="utf-8")
    proc = subprocess.run(
        [
            sys.executable, str(AGY_RUN),
            "--prompt-file", str(prompt_file),
            "--cwd", str(WORK_DIR),
            "--model", MODEL,
            "--mode", "plan",
            "--work-dir", str(WORK_DIR),
            "--run-id", run_id,
        ],
        capture_output=True,
        text=True,
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if not lines:
        raise SystemExit(f"agy の runner が要約を返しませんでした（exit {proc.returncode}）: {proc.stderr.strip()}")
    summary = json.loads(lines[-1])
    if summary.get("wait_status") != "completed" or summary.get("EXIT") != 0:
        raise SystemExit(f"agy の job が完了しませんでした: wait_status={summary.get('wait_status')} EXIT={summary.get('EXIT')} run_id={run_id}")
    body = (summary.get("final_response") or {}).get("body") or ""
    if not body.strip():
        raise SystemExit(f"agy の応答が空でした: run_id={run_id} warnings={summary.get('warnings')}")
    return body.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Rewrite Japanese with Gemini 4 Hydrogen via agy")
    parser.add_argument("--text-b64", help="UTF-8 source text, standard base64")
    parser.add_argument("--file", help="Path to a UTF-8 source file")
    args = parser.parse_args()

    source = read_source(args).strip()
    if not source:
        raise SystemExit("対象文が空です。")

    rewritten = ask(build_prompt(SYSTEM_INSTRUCTION, source))

    def review(text: str) -> tuple[bool, list[str]]:
        return parse_review(ask(build_prompt(REVIEW_INSTRUCTION, review_user(source, text))))

    try:
        misunderstood, points = review(rewritten)
    except (json.JSONDecodeError, ValueError) as exc:
        sys.stdout.write(rewritten if rewritten.endswith("\n") else rewritten + "\n")
        sys.stdout.write(f"\n照合: 判定できなかった ({exc})\n")
        return 0

    repaired = False
    review_error = None
    for _ in range(MAX_REPAIRS):
        if not misunderstood:
            break
        repaired = True
        previous = rewritten
        rewritten = ask(build_prompt(REPAIR_INSTRUCTION, repair_user(source, rewritten, points)))
        if rewritten == previous:
            break
        try:
            misunderstood, points = review(rewritten)
        except (json.JSONDecodeError, ValueError) as exc:
            misunderstood = True
            review_error = str(exc)
            points = [review_error]
            break

    if not repaired:
        label = "誤解はない"
        noted: list[str] = []
    elif review_error is not None:
        label = "再照合できなかった"
        noted = [review_error]
    elif not misunderstood:
        label = "誤解を直した"
        noted = []
    else:
        label = "まだ誤解がある"
        noted = points

    sys.stdout.write(rewritten if rewritten.endswith("\n") else rewritten + "\n")
    sys.stdout.write(f"\n照合: {label}\n")
    for point in noted:
        sys.stdout.write(f"- {point}\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        raise SystemExit(0)
