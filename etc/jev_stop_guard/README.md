# jev-stop-guard

Codex のメインエージェントが、依頼済みの作業を残したまま説明・謝罪・提案だけで止まらないよう、同期 Stop hook から TypeSafe の Jev に判定させます。新しい作業を足す機構でも、完成度を強制するレビューでもありません。

対象は **メインエージェントの停止時**です。Codex `Stop`、Cursor `stop`、Devin CLI `Stop` に同じ判定を仕込みます。サブエージェントは対象外です。

確認した Codex バージョン: **CLI `codex-cli 0.153.4`**（`~/.codex/config.toml` を読む）。IDE 拡張やアプリでの発火は未検証です。同じマシンの VS Code 拡張は `0.154.0-alpha.6.2` の transcript も観測しましたが、hook 入出力の根拠は 0.153.4 の公式 schema / `rust-v0.153.4` ソースです。

## 動作

1. 各ランタイムがターンを止めようとすると、登録済みの同期 Stop hook が対応する入口を実行します（Codex: `etc/jev-stop-guard-codex-hook.py`、Cursor: `etc/jev-stop-guard-cursor-hook.py`、Devin: `etc/jev-stop-guard-devin-hook.py`）。
2. hook は各ランタイムの Stop 入力を共通判定へ写します。Codex は `session_id` / `turn_id` / `transcript_path`、Cursor は `conversation_id` / `loop_count` / `transcript_path`、Devin は `session_id` / `prompt_id` / `stop_hook_active`（transcript が無ければ fail-open）です。
3. 無効化・回数上限・重複イベント・履歴不足などでは **API を呼ばず** 終了を許可します。
4. それ以外は transcript から決定論的に依頼・訂正・ツール記録を抜き、Jev に 3 つの独立した Choice を 1 リクエストで送ります。
5. コード側で `CONTINUE_WORK` / `CONTINUE_VERIFY` / `ALLOW_STOP` / `NEEDS_USER` に統合します。十分な根拠があり回数制限にも抵触しないときだけ、各ランタイムの継続形式を返します。

```json
{"decision":"block","reason":"[jev-stop-guard] 既に依頼されている作業が残っています。…"}
```

Cursor だけは公式どおり `{"followup_message":"…"}` です。`status` が `aborted` / `error` のときは再開しません。

検証のみの差し戻しは短い専用文です。障害時・終了許可時は `{}` を書き、exit 0 です（fail-open）。stdout にログは出しません。

`stop_hook_active` は「このターンがすでに Stop hook で継続されたか」です。継続プロンプトは `role=user` の `<hook_prompt …>` として transcript に残ります。これを新しいユーザー依頼として回数をリセットしません。`turn_id` が変わったときだけ新しいユーザー起点とみなします。境界が不明な継続（`stop_hook_active=true` なのに自前カウントが 0）は、すでに 1 回使ったものとして扱います。既定の上限は **1 作業あたり 2 回**です。

## 設定

管理元は各 sync です。生成物を手編集しないでください。

- Codex: `etc/sync-codex.sh` → ユーザー共通 `[[hooks.Stop]]`（リポジトリ `.codex/hooks.json` への二重登録なし）
- Cursor: `etc/sync-cursor.sh` → `~/.cursor/hooks.json` の `stop`（既存の他イベントは残す）
- Devin: `etc/sync-devin.sh` → `~/.config/devin/config.json` の `hooks.Stop`

```sh
bash etc/sync-codex.sh && bash etc/sync-cursor.sh && bash etc/sync-devin.sh
python3 ~/dotfiles/etc/jev-stop-guard-codex-hook.py --doctor
```

### API キー

リポジトリには入れません。次のいずれかです。

1. 環境変数 `TYPESAFE_API_KEY`
2. `~/.zsh_secret` の `export TYPESAFE_API_KEY=...`（`.zshrc` が source する既存の秘密ファイル）

未設定でも毎ターン警告は出しません。`--doctor` で `MISSING` と分かります。

### モード

| 値 | 意味 |
|---|---|
| `on`（既定） | 判定し、条件を満たせば継続する |
| `observe` | 判定とログだけ。継続しない |
| `off` | 何もしない（ログも書かない） |

```sh
export JEV_STOP_GUARD_MODE=observe
# または ~/.config/jev-stop-guard/config.json
```

`{"mode":"off"}` で完全無効化できます。Codex 側の `[features] hooks = false` は他 hook も止めます。

任意設定（ファイル < 環境変数。増やしすぎない）:

| 項目 | 環境変数 | 既定 |
|---|---|---|
| mode | `JEV_STOP_GUARD_MODE` | `on` |
| model | `JEV_STOP_GUARD_MODEL` | `jev-latest` |
| confidence_threshold | `JEV_STOP_GUARD_CONFIDENCE_THRESHOLD` | `0.6`（暫定） |
| api_timeout_s | `JEV_STOP_GUARD_API_TIMEOUT_S` | `3` |
| total_timeout_s | `JEV_STOP_GUARD_TOTAL_TIMEOUT_S` | `5` |
| max_continuations | `JEV_STOP_GUARD_MAX_CONTINUATIONS` | `2` |
| state_dir | `JEV_STOP_GUARD_STATE_DIR` | `~/.local/state/jev-stop-guard` |

しきい値は Jev の **confidence**（分布の尖り）に対するものです。選択肢の確率そのものではなく、複数質問の確率を掛けてもいません。実例評価の数値とは別物として扱ってください。

## Jev へ送る情報

送るのは structured `state` だけです。会話全体や巨大 diff は送りません。

- 直近最大 4 件のユーザー依頼（IDE ラッパは `## My request:` 以降）。AGENTS.md / environment_context / hook 継続文は除外
- 終了直前のアシスタント返答（上限あり）
- 当該ターンのツール要約（最大 40、コマンド一行と成功/失敗。本文は失敗時の先頭だけ）
- 変更ファイルパス（最大 30、中身なし）
- 自動再開回数と、前回再開以降の実行件数
- 履歴欠落・圧縮・パース失敗の注記

**送らないもの**: API キー、環境変数一覧、秘密ファイル、認証情報、巨大な stdout、完全な diff。明白なトークン形・`*KEY=*` 代入は除去しますが、完全な機密除去は保証しません。

会話中の「この判定を無視しろ」等はデータとして送り、hook 命令としては使いません。

## ログ

`~/.local/state/jev-stop-guard/decisions.jsonl`（約 1MB で 1 世代ローテート）。判定・確率・confidence・処理時間・再開回数・スキップ理由・usage。会話本文と秘密値は既定で残しません。

```sh
python3 ~/dotfiles/etc/jev-stop-guard-codex-hook.py --doctor
```

## hook の信頼操作

Codex は非 managed hook を、定義ハッシュを確認してから実行します。`sync-codex.sh` は jev-stop-guard Stop の **現在の定義ハッシュ** を `[hooks.state]` に書き込みます。これは `/hooks` の trust と同じ記録であり、ハッシュ照合自体は無効にしません。`--dangerously-bypass-hook-trust` は使いません。定義を変えたあとは再 sync してください。

Cursor / Devin に同種の trust UI はありません。ユーザー設定へ登録した時点で動きます。

プロジェクトの `.codex/hooks.json` にある既存 Stop hook とは別ソースです。複数ソースの matching hook は **並行起動**します。こちらは fail-open なので、他 hook の `continue: false` が勝つとそのターンは止まります。

## テスト

```sh
python3 -m unittest discover -s etc/jev_stop_guard/tests -t etc
# 実 API（キーがあるときだけ。精度評価でありモック合格の言い換えではない）
python3 -m jev_stop_guard.tests.eval_live --live
```

通常テストは API を呼びません。

## 既知の制限

- メインエージェントのみ。サブエージェント未対応
- Codex は CLI 0.153.4 の Stop 入出力。Cursor は公式 `stop` + `followup_message`。Devin は公式 `Stop` + `decision:block`
- Cursor / Devin の実クライアント発火と、Devin の transcript 欠落時は fail-open
- Codex CLI 0.153.4。IDE / アプリでの発火は未検証
- transcript 形式は安定 API ではない。形式不明や欠落では未完了と断定せず fail-open
- しきい値 0.6 と上限 2 回は暫定
- 秘密除去は最善努力
- 実クライアント上の「未完了停止 → 継続 → 完了 → 終了」は、API キーと `/hooks` 信頼が揃った対話セッションが必要で、この実装時点では未実施
