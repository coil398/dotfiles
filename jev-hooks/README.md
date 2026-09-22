# Jev hooks

コーディングエージェントの完了・質問・再試行・差分・スキル選択を、TypeSafe Jevの構造化判定で補助します。新しいツール判定は助言です。権限を広げたり、ツール引数を書き換えたりしません。Stopのみ、依頼済み成果物が未提出で続行できると判断した場合に回数制限付きで継続します。

## 任意実行と起動コスト

`TYPESAFE_API_KEY` はプロセス環境変数だけから読みます。秘密ファイルの自動読込はありません。キーが空なら`hook.sh`はPythonを起動せず`{}`で終了し、通信・状態書込・ログ記録もしません。この早期スキップ回数は計測対象外です。`doctor`でキーの有無と有効モードを確認できます。

API失敗、低confidence、未知のイベント、履歴不足では元の操作を続行します。`off`も無操作です。`observe`は判定と利用量を記録し、助言や継続を返しません。

## コマンド

以下はdotfilesのルートから実行します。別ディレクトリでは`jev.py`を絶対パスで指定してください。

```sh
python3 jev-hooks/jev.py doctor
python3 jev-hooks/jev.py usage --days 30
python3 jev-hooks/jev.py usage --days 30 --cwd .
python3 jev-hooks/jev.py usage --days 30 --json
python3 jev-hooks/jev.py usage --days 30 --html /tmp/jev-usage.html
printf '%s' '{"query":"PRのコードレビュー","cwd":"/path/to/repo"}' | python3 jev-hooks/jev.py skills
```

HTMLはローカルの静的レポートです。外部CDNやサーバーは不要で、生成時点のデータを表示します。最新情報は同じコマンドで再生成します。

## 利用量と推定費用

`~/.local/state/jev-hooks/usage.sqlite3`へAPIリクエストごとに1件記録します。複数質問をまとめた1リクエストを重複課金として数えません。API判定に進む前の主なスキップも別レコードで記録します。判定対象外のread等を含む全hook発火数ではありません。会話・差分・記憶本文・キーは保存しません。

各記録には、記録時の作業ディレクトリを解決した絶対パスをローカルmetadataとして保存します。通常は実行プロセスのcwdで、`service.evaluate(..., cwd=...)`から指定することもできます。この値をAPIへ送るstateへ自動追加しません。`usage --cwd PATH`はそのディレクトリに帰属する記録だけを集計し、`--cwd .`はコマンドを実行した場所を示します。オプションを省略すれば全体を集計します。

既存DBは次のusage記録時にnullableの`cwd`列を追加します。旧レコードは帰属先が分からないためNULLのまま残り、`--cwd`指定時には含めません。usage集計とdoctorの参照はread-onlyで、閲覧だけではDBや古い記録を変更しません。

- API呼出し、入力/出力tokens、待ち時間、policy/runtime別、UTC日/月別の集計。
- skip/errorの理由、利用量や価格が不明の呼出し数。
- `jev-1.13.0`は入力$0.042/百万tokens、出力無料として推定。実請求額ではありません。
- 未知モデル・usage欠落・応答の取れない失敗を費用ゼロにしません。既知費用の合計と不明件数を分けます。
- `JEV_HOOKS_INPUT_USD_PER_MILLION`で既知モデルの入力単価を上書きできます。適用した単価は各レコードに残します。
- ログ書込障害は元の作業を止めません。レポートの読込不能を空の正常データと混同しないでください。

型付きの判定結果はサイズ制限付き`decisions.jsonl`にも作業ディレクトリmetadataとともに保存します。`doctor`は現在のcwdに帰属する直近のpolicy判定と過去30日の利用件数を表示します。判定には記録時のmodeを表示し、現在の機能有効状態とは区別します。リクエスト本文とAPIキーは保存しません。既存のcwdなし記録は現在のcwdへ推測で割り当てません。

従来の`~/.local/state/jev-stop-guard/decisions.jsonl`は変更しません。このレポートは新しい記録先の利用量を集計します。

料金・モデル仕様の一次ソース: https://docs.typesafe.ai/models

## 判定とランタイム

| 入り口 | Codex | Cursor | Grok Build | Devin CLI |
|---|---|---|---|---|
| 完了・成果物・不要な再承認 | Stop継続 | stop継続 | 未登録 | Stop継続 |
| 入力からスキル候補提示 | UserPromptSubmit | 明示CLI | 明示CLI | 明示CLI |
| 質問前・再試行・編集・委譲 | PreToolUse助言 | 未登録 | PreToolUse観測 | 未登録 |
| ツール結果・失敗 | PostToolUse | postToolUse/Failure | PostToolUse/Failure観測 | 未登録 |
| 子の返却内容 | SubagentStopのUI警告 | 未登録 | 未登録 | 未登録 |

Codexのtool/prompt追加context（SubagentStopはUI警告）、Cursorのpost-tool追加context、Grokの観測専用出力を区別します。Grokのpassiveイベントはstdoutが無視されるため、Stop再開を実装済みとは扱いません。CursorのpreToolUseは追加contextを安全に渡す契約を確認できないため登録しません。ハーネスの内部で行うスキル選択・事前読込まですべて捕捉できるわけではありません。

スキルは実在する`SKILL.md`のname/descriptionから候補を提示します。実効カタログの置換や、ユーザー明示指定の取り消しはしません。`JEV_HOOKS_SKILL_ROOTS`で探索ルートをOSのパス区切り文字で指定できます。

## 設定

設定は`~/.config/jev-hooks/config.json`、優先順位は既定値 < JSON < 環境変数です。APIキーはJSONに保存しません。

| 環境変数 | 既定 |
|---|---|
| `JEV_HOOKS_MODE` | `on` (`observe` / `off`も可) |
| `JEV_HOOKS_MODEL` | `jev-latest` |
| `JEV_HOOKS_CONFIDENCE_THRESHOLD` | `0.6`（暫定、正答率ではない） |
| `JEV_HOOKS_API_TIMEOUT_S` | `3` |
| `JEV_HOOKS_TOTAL_TIMEOUT_S` | `5` |
| `JEV_HOOKS_MAX_CONTINUATIONS` | `2` |
| `JEV_HOOKS_STATE_DIR` | `~/.local/state/jev-hooks` |
| `JEV_HOOKS_CONFIG` | 任意の設定JSONパス |

設定例は`{"mode":"observe"}`。既存ファイルがある場合は他の項目を保って対象キーだけ更新してください。環境変数による上書きがあるとJSON変更より優先されます。

## 送信内容

- 完了判定: 直近最大8件の依頼（各100文字）、最後の返答（600文字）、ツールの種別・成否ごとの件数、変更ファイル数。ツールのコマンド・出力・失敗本文、変更パス、作業ディレクトリは送信しません。
- 新判定: 対象イベントのツール引数/結果の短い抜粋、依頼の抜粋、直近失敗の要約。readだけではAPIを呼びません。
- スキル選択: 依頼と候補のname/description。

機密キー名や典型的な秘密値を除去し、入力サイズを制限します。除去は最善努力で、未知の秘密形式すべてを保証するものではありません。モデルはデータからのみ選択し、hookへの命令として取り扱いません。

## ai-ltm（任意）

`session_recall.py`は検索結果の上位最大5件のID・要約・本文抜粋・タグ・スコアをmainへ返します。環境変数`TYPESAFE_API_KEY`があり検索の残り時間がある場合、任意の`memory.annotate`で関連性・現在の指示との衝突・前提の相違・判断不能を注記します。候補の順序や内容は保持し、採否はmainが決めます。実際に使った記憶だけをmainが別途mark-usedします。

キーなし・連携パッケージなし・API失敗・低confidence・検索の残り時間不足なら、注記なしで候補をmainへ渡します。`off`は通信せず、`observe`は利用量を記録して候補への注記を返しません。DBがない場合は既存recallの状態報告を維持し、DBの作成や記憶の自動保存はしません。

注記の送信範囲は現在の検索文と最大5候補の要約/本文（それぞれ最大1,200文字）、タグ（最大300文字）、スコアです。候補IDは一時的な番号に置換し、共通の秘密値除去を適用します。既定送信先はTypeSafeの`https://api.typesafe.ai/v1/systemone`です。呼出し・待ち時間・推定費用は同じusage DBの`ai-ltm`集計に含まれます。

手動CLIの`memory-annotate`はstdinの`query`と`results`を受け取ります。`memory-rerank`は最大5件内の順位調整、`memory-classify`は保存先/重複/矛盾の参考を返す補助です。記録分類は保存予定の要約/本文と、read-only検索した最大5件の要約/本文（最大1,800文字）/タグを送ります。保存・削除・embed・mark-usedは実行しません。

## 配備

```sh
bash etc/sync-codex.sh
bash etc/sync-cursor.sh
bash etc/sync-devin.sh
python3 jev-hooks/install.py grok
```

既存の他hook・設定を保持し、Jev所有エントリを更新します。`etc/link.sh`のGrok配備もinstallerを呼びます。Codexの生成設定は手編集せず、syncが通常のhook定義hashを記録します。現在のセッションへの即時反映は前提にせず、新セッションで実際の発火を確認してください。

CODEX_HOMEを既定以外に設定している場合は、python3 jev-hooks/codex-hook.py --install-codex-hook "$CODEX_HOME" でCodex Stop hookを配備できます。他の設定は保持され、既存の設定ファイルは .backup-* を作って更新します。

実行中のセッションが保持する`etc/jev-stop-guard-*-hook.py`への登録も、同じ`hook.sh`へ処理を渡します。

## 検証

```sh
uv run --project jev-hooks python -m unittest discover -s jev-hooks/src/jev_hooks/tests -t jev-hooks/src
PYTHONPATH=jev-hooks/src uv run --project jev-hooks python -m jev_hooks.tests.eval_live --live
```

通常テストはAPIを呼びません。`--live`は匿名fixtureを実APIで評価し、実際の課金が発生します。単体テスト合格、モデル精度、実クライアント上のhook発火を別々に確認します。

公式hook仕様: [Codex](https://learn.chatgpt.com/docs/hooks)、[Cursor](https://cursor.com/docs/hooks)、[Grok](https://docs.x.ai/build/features/hooks)。
