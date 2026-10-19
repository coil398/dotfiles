---
name: logging
description: 実行単位を持つ処理を書く・直すときに、記録する内容とlevelを定める。script、batch、bot、API処理、data処理などの実装や、log不足を調べるときに使う。typo修正や表示だけの変更には適用しない。
---

# Logging

実行単位を持つ処理（script、batch、bot、API処理、data処理など）を書く・直すときに適用する。typo修正や表示だけの変更には適用しない。

実装時に、実行後の調査に必要なlogを入れる。logだけを読んで「何が入り、何をどう判断し、何件処理し、どこで何秒かかり、なぜ失敗したか」が分かる状態にする。

## 残すもの

| 種類 | 内容 | 例 |
|---|---|---|
| 入力 | 起動引数、設定値、読んだfileのpathと件数・期間・hash | `loaded path=... rows=1440 start=... end=...` |
| 判断 | 分岐ごとの結果と理由（閾値と実際の値） | `skip item=alpha reason=value_below_min value=1.2e6 min=5e6` |
| 件数 | 入力・処理・成功・skip・失敗の件数 | `done total=120 ok=117 skipped=2 failed=1` |
| 時間 | 処理全体と重い区間の所要時間 | `fetch elapsed_ms=842` |
| 失敗 | 例外の種類、message、traceback、対象のID、retry回数、最終的な扱い | `logger.exception(...)` |
| 外部呼出 | 宛先（host/endpoint）、status code、件数、retry | `GET host=api.example.com status=429 retry=2` |

## level

- `DEBUG`: 1件ごとの詳細、中間値。通常は出さず、調査時に有効にする。
- `INFO`: 開始・終了、入力の要約、主要な判断、件数、所要時間。通常運用で読む。
- `WARNING`: 続行できるが想定外のこと（欠損、fallback、retry、skip）。理由を書く。
- `ERROR`: その単位の処理が失敗した。`logger.exception` でtracebackを残す。
- 黙って握りつぶす `except: pass` は書かない。続行するならWARNING以上で理由を残す。

## 書き方

- module単位で `logger = logging.getLogger(__name__)`（または用途名）を使い、`print` で代用しない。
- messageは「固定のevent名 + `key=value`」の形にし、grepと集計がしやすいようにする。値は `%s` 形式の引数で渡す。
- 1回の実行を追えるよう、run ID・対象ID（item、user、file名など）を各行に含める。
- 長い一覧やpayload全体は出さず、件数・先頭数件・hashで要約する。
- 時刻はtimezone付き（ISO 8601）で残す。

## 出し先

- 既定はstderr。長時間処理・batch・botはfileにも出す（例: `logs/<name>.log`、または実行記録directory内）。
- 実験の実行記録がある場合は、その実行のdirectoryにlogを一緒に保存し、結果と対応させる。
- logの設定（handler、level、format）は入口（`main`）で一度だけ行い、libraryの中では設定しない。

## 秘密情報を出さない

- token、password、API key、cookie、Authorization header、private keyはlogに出さない。DEBUGでも出さない。
- URLのquery、request header、設定dict、例外messageに秘密が混ざる場合は、出す前に伏せる（`***`）。
- 設定を出すときは許可したkeyだけを出す（allowlist）。dict全体をそのまま出さない。

## Pythonの例

```python
import logging
import time
import uuid

logger = logging.getLogger("batch_processor")

SAFE_CONFIG_KEYS = ("items", "start", "end", "min_value")


def setup_logging(log_path: str, level: int = logging.INFO) -> None:
    fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"
    logging.basicConfig(
        level=level,
        format=fmt,
        handlers=[logging.StreamHandler(), logging.FileHandler(log_path, encoding="utf-8")],
    )


def run(config: dict, rows_by_item: dict[str, list[dict]]) -> dict:
    run_id = uuid.uuid4().hex[:8]
    t0 = time.perf_counter()
    safe = {k: config.get(k) for k in SAFE_CONFIG_KEYS}
    logger.info("start run_id=%s config=%s items=%d", run_id, safe, len(rows_by_item))

    ok = skipped = failed = 0
    for item, rows in rows_by_item.items():
        value = sum(r["value"] for r in rows)
        if value < config["min_value"]:
            skipped += 1
            logger.warning(
                "skip run_id=%s item=%s reason=value_below_min value=%.0f min=%.0f",
                run_id, item, value, config["min_value"],
            )
            continue
        t1 = time.perf_counter()
        try:
            result = evaluate(rows)
        except Exception:
            failed += 1
            logger.exception("evaluate_failed run_id=%s item=%s rows=%d", run_id, item, len(rows))
            continue
        ok += 1
        logger.info(
            "evaluated run_id=%s item=%s rows=%d result=%.4f elapsed_ms=%.0f",
            run_id, item, len(rows), result, (time.perf_counter() - t1) * 1000,
        )

    elapsed = time.perf_counter() - t0
    logger.info(
        "done run_id=%s total=%d ok=%d skipped=%d failed=%d elapsed_s=%.2f",
        run_id, len(rows_by_item), ok, skipped, failed, elapsed,
    )
    return {"ok": ok, "skipped": skipped, "failed": failed}
```

外部APIを呼ぶときは、tokenを含まない宛先とstatusだけを残す。

```python
resp = session.get(url, params=params, timeout=10)
logger.info("http_get host=%s path=%s status=%d items=%d",
            urlsplit(url).hostname, urlsplit(url).path, resp.status_code, len(resp.json()))
```

## 確認

- 実装後に一度実行し、logだけで入力・判断・件数・時間・失敗が読み取れるか見る。
- logに秘密情報が出ていないか、`rg -i "token|secret|password|authorization"` などで確認する。
