"""Command line and standalone HTML reports for local Jev telemetry."""

from __future__ import annotations

import argparse
import html
import json
import math
import sys
from pathlib import Path
from typing import Any, Optional, Sequence

from .config import load_config
from .telemetry import summarize


def _money(value: Any) -> str:
    try:
        amount = float(value)
    except (TypeError, ValueError, OverflowError):
        return "不明"
    if isinstance(value, bool) or not math.isfinite(amount):
        return "不明"
    return f"USD {amount:.10f}"


def _escaped(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _number(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return "不明"
    if isinstance(value, bool) or not math.isfinite(number):
        return "不明"
    return f"{value:,}"


def _calls(bucket: dict) -> str:
    return (
        f"{bucket['calls']} calls / API {bucket['api_attempted']} / "
        f"tokens {bucket['input_tokens']} in, {bucket['output_tokens']} out / "
        f"cost {_money(bucket['estimated_cost_usd'])} / unknown {bucket['cost_unknown_calls']} / "
        f"avg latency {bucket['latency_ms_average'] if bucket['latency_ms_average'] is not None else '—'} ms / "
        f"skip {bucket['skip_count']} / error {bucket['error_count']}"
    )


def render_text(data: dict) -> str:
    totals = data["totals"]
    lines = [f"Jev 利用・費用レポート（直近 {data['days']} 日）"]
    if data.get("cwd") is not None:
        lines.append(f"cwd filter: {data['cwd']}")
    lines.append(_calls(totals))
    if not data["has_database"]:
        lines.append("まだ記録がありません。")
        return "\n".join(lines)
    if not data["available"]:
        lines.append("記録を読み込めませんでした。")
        return "\n".join(lines)
    if not totals["calls"]:
        lines.append("指定期間に記録はありません。")
        return "\n".join(lines)
    lines.append("\n日別費用:")
    for row in data["daily"]:
        lines.append(f"  {row['period']}: {_money(row['estimated_cost_usd'])} (unknown {row['cost_unknown_calls']})")
    lines.append("\n月別費用:")
    for row in data["monthly"]:
        lines.append(f"  {row['period']}: {_money(row['estimated_cost_usd'])} (unknown {row['cost_unknown_calls']})")
    lines.append("\nPolicy別:")
    for row in data["by_policy"]:
        lines.append(f"  {row['period']}: {_calls(row)}")
    lines.append("\nRuntime別:")
    for row in data["by_runtime"]:
        lines.append(f"  {row['period']}: {_calls(row)}")
    lines.append("\nSkip理由:")
    lines.extend(f"  {reason}: {count}" for reason, count in data["skip_reasons"].items())
    lines.append("失敗理由:")
    lines.extend(f"  {reason}: {count}" for reason, count in data["failure_reasons"].items())
    return "\n".join(lines)


def _table_rows(rows: list[dict], *, name: str = "period") -> str:
    if not rows:
        return '<tr><td colspan="8" class="empty">該当する記録はありません</td></tr>'
    output = []
    for row in rows:
        label = html.escape(str(row.get(name, "")), quote=True)
        output.append(
            "<tr>"
            f"<th scope=\"row\">{label}</th>"
            f"<td>{_escaped(_number(row['calls']))}</td><td>{_escaped(_number(row['api_attempted']))}</td>"
            f"<td>{_escaped(_number(row['input_tokens']))} / {_escaped(_number(row['output_tokens']))}</td>"
            f"<td>{_escaped(_money(row['estimated_cost_usd']))}</td>"
            f"<td>{_escaped(_number(row['cost_unknown_calls']))}</td>"
            f"<td>{_escaped(row['latency_ms_average'] if row['latency_ms_average'] is not None else '—')}</td>"
            f"<td>{_escaped(_number(row['skip_count']))} / {_escaped(_number(row['error_count']))}</td></tr>"
        )
    return "".join(output)


def _reason_rows(reasons: dict[str, int]) -> str:
    if not reasons:
        return '<tr><td colspan="2" class="empty">該当する記録はありません</td></tr>'
    return "".join(
        f"<tr><th scope=\"row\">{_escaped(reason)}</th><td>{_escaped(_number(count))}</td></tr>"
        for reason, count in reasons.items()
    )


def _daily_bars(rows: list[dict]) -> str:
    if not rows:
        return '<p class="empty">指定期間に記録はありません。</p>'
    amounts = []
    for row in rows:
        try:
            value = float(row["estimated_cost_usd"])
        except (TypeError, ValueError, OverflowError):
            value = 0.0
        amounts.append(value if math.isfinite(value) and value >= 0 else 0.0)
    max_cost = max(amounts, default=0.0)
    bars = []
    for row, amount in zip(rows, amounts):
        width = 0 if max_cost <= 0 else max(1, round(amount / max_cost * 100))
        date = html.escape(str(row["period"]), quote=True)
        cost = _escaped(_money(amount))
        unknown = _escaped(_number(row["cost_unknown_calls"]))
        bars.append(
            f'<div class="bar-row"><span class="bar-date">{date}</span>'
            f'<div class="bar-track"><div class="bar" style="width:{width}%"></div></div>'
            f'<span class="bar-value">{cost} · unknown {unknown}</span></div>'
        )
    return "".join(bars)


def render_html(data: dict) -> str:
    totals = data["totals"]
    if not data["has_database"]:
        notice = "まだ記録がありません。Jev の評価やローカル skip が記録されると、ここに表示されます。"
    elif not data["available"]:
        notice = "記録を読み込めませんでした。"
    elif not totals["calls"]:
        notice = "指定期間に記録はありません。"
    else:
        notice = ""
    notice_html = f'<p class="notice">{html.escape(notice)}</p>' if notice else ""
    cwd_label = f" · cwd: {_escaped(data['cwd'])}" if data.get("cwd") is not None else ""
    daily_rows = _table_rows(data["daily"])
    policy_rows = _table_rows(data["by_policy"])
    runtime_rows = _table_rows(data["by_runtime"])
    return f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Jev 利用・費用レポート</title>
<style>
:root {{ color-scheme: light; font-family: -apple-system, BlinkMacSystemFont, "Hiragino Kaku Gothic ProN", "Yu Gothic", sans-serif; color: #17212b; background: #f4f6f8; }}
body {{ max-width: 1120px; margin: 0 auto; padding: 2rem 1.25rem 4rem; }}
h1 {{ margin-bottom: .25rem; font-size: 1.7rem; }}
.sub {{ color: #526170; margin-top: 0; }}
.notice {{ background: #fff7db; border: 1px solid #ead58f; padding: .8rem 1rem; border-radius: .5rem; }}
.cards {{ display: grid; grid-template-columns: repeat(auto-fit,minmax(180px,1fr)); gap: .75rem; margin: 1.25rem 0 2rem; }}
.card, section {{ background: white; border: 1px solid #dce2e8; border-radius: .6rem; padding: 1rem; }}
.card span {{ display: block; color: #526170; font-size: .85rem; }} .card strong {{ display: block; margin-top: .35rem; font-size: 1.15rem; overflow-wrap: anywhere; }}
section {{ margin-top: 1rem; overflow-x: auto; }} h2 {{ margin: 0 0 .8rem; font-size: 1.1rem; }}
table {{ border-collapse: collapse; width: 100%; font-size: .9rem; }} th,td {{ padding: .55rem .6rem; border-bottom: 1px solid #e6eaee; text-align: left; white-space: nowrap; }}
thead th {{ color: #526170; font-weight: 600; }} .empty {{ color: #65727f; font-weight: normal; }}
.bar-row {{ display: grid; grid-template-columns: 7rem minmax(5rem,1fr) minmax(13rem,auto); align-items: center; gap: .75rem; margin: .55rem 0; font-variant-numeric: tabular-nums; }}
.bar-date {{ color: #526170; }} .bar-track {{ height: .8rem; background: #e9eef2; border-radius: 99px; overflow: hidden; }}
.bar {{ height: 100%; background: #276c8d; border-radius: inherit; }} .bar-value {{ text-align: right; }}
@media(max-width:650px) {{ .bar-row {{ grid-template-columns: 5.5rem 1fr; }} .bar-value {{ grid-column: 2; text-align: left; }} body {{ padding-inline: .75rem; }} }}
</style></head><body>
<h1>Jev 利用・費用レポート</h1><p class="sub">直近 {_escaped(data['days'])} 日 · UTC · 推定費用は利用量と適用単価から計算{cwd_label}</p>
{notice_html}
<div class="cards">
<div class="card"><span>Calls / API requests</span><strong>{_escaped(_number(totals['calls']))} / {_escaped(_number(totals['api_attempted']))}</strong></div>
<div class="card"><span>Input / output tokens</span><strong>{_escaped(_number(totals['input_tokens']))} / {_escaped(_number(totals['output_tokens']))}</strong></div>
<div class="card"><span>推定費用 / cost known / unknown</span><strong>{_escaped(_money(totals['estimated_cost_usd']))} / {_escaped(_number(totals['cost_known_calls']))} / {_escaped(_number(totals['cost_unknown_calls']))}</strong></div>
<div class="card"><span>平均 latency / skip / error</span><strong>{_escaped(totals['latency_ms_average'] if totals['latency_ms_average'] is not None else '—')} ms / {_escaped(_number(totals['skip_count']))} / {_escaped(_number(totals['error_count']))}</strong></div>
</div>
<section><h2>日別費用</h2>{_daily_bars(data['daily'])}</section>
<section><h2>Policy別</h2><table><thead><tr><th>Policy</th><th>Calls</th><th>API</th><th>Tokens in/out</th><th>Cost</th><th>Unknown</th><th>Latency avg ms</th><th>Skip/error</th></tr></thead><tbody>{policy_rows}</tbody></table></section>
<section><h2>Runtime別</h2><table><thead><tr><th>Runtime</th><th>Calls</th><th>API</th><th>Tokens in/out</th><th>Cost</th><th>Unknown</th><th>Latency avg ms</th><th>Skip/error</th></tr></thead><tbody>{runtime_rows}</tbody></table></section>
<section><h2>日別集計</h2><table><thead><tr><th>UTC date</th><th>Calls</th><th>API</th><th>Tokens in/out</th><th>Cost</th><th>Unknown</th><th>Latency avg ms</th><th>Skip/error</th></tr></thead><tbody>{daily_rows}</tbody></table></section>
<section><h2>月別集計</h2><table><thead><tr><th>UTC month</th><th>Calls</th><th>API</th><th>Tokens in/out</th><th>Cost</th><th>Unknown</th><th>Latency avg ms</th><th>Skip/error</th></tr></thead><tbody>{_table_rows(data['monthly'])}</tbody></table></section>
<section><h2>Skip理由</h2><table><thead><tr><th>理由</th><th>件数</th></tr></thead><tbody>{_reason_rows(data['skip_reasons'])}</tbody></table></section>
<section><h2>失敗理由</h2><table><thead><tr><th>理由</th><th>件数</th></tr></thead><tbody>{_reason_rows(data['failure_reasons'])}</tbody></table></section>
</body></html>"""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="jev-report", description="Jev 利用量・費用をローカル表示します")
    parser.add_argument("--days", type=int, default=30, help="集計する直近日数（既定: 30）")
    parser.add_argument("--cwd", metavar="PATH", help="指定した作業ディレクトリに帰属する記録だけを集計")
    parser.add_argument("--json", action="store_true", help="結果を JSON で出力")
    parser.add_argument("--html", metavar="PATH", help="standalone HTML dashboard を指定先へ保存")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.days < 1:
        parser.error("--days は1以上で指定してください")
    cfg = load_config()
    data = summarize(cfg.state_path(), days=args.days, cwd=args.cwd)
    if args.html:
        try:
            target = Path(args.html).expanduser()
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(render_html(data), encoding="utf-8")
        except OSError as exc:
            print(f"HTML を保存できませんでした: {exc}", file=sys.stderr)
            return 1
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        output = render_text(data)
        if args.html:
            output += f"\nHTML: {Path(args.html).expanduser()}"
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
