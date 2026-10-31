# jw：日本語の文章係

`jw` は、日本語の文を agy（Antigravity CLI）に1回だけ渡して直させ、直した文だけを出力する小さなコマンドです。コーディング向けの共有指示やツールを使わせず、文章を直すことだけをさせます。

## 中身

| ファイル | 役目 |
|---|---|
| `jw` | 本体の bash スクリプト。`~/.local/bin/jw` からこのファイルへシンボリックリンクを張って使う |
| `rules.md` | 書き方の決まり。`jw` が専用エージェント `jw` のシステム指示として agy に渡す |
| `README.md` | この説明 |

## 使い方

```sh
jw [-m MODE] [--model MODEL] [FILE|-]
```

- `-m rewrite`（既定）：リライト
- `-m proofread`：校正だけ（誤字・脱字・てにをは・文法）
- `-m shorten`：短くする
- `FILE` を省くか `-` を渡すと標準入力から読みます。本文は100000バイトまでです。

```sh
echo 'きょうは会議がありまsた。資料わ明日送ります。' | jw -m proofread
jw draft.md > draft.fixed.md
jw -m shorten --model gemini-4-argon-medium note.txt
```

リンクの張り方：

```sh
ln -s ~/dotfiles/jw/jw ~/.local/bin/jw
```

## モデル

既定は `claude-sonnet-5-5-medium` です。`--model` か環境変数 `JW_MODEL` で変えられます。名前は `agy models` に出るものを使います（例：`gemini-4-argon-medium`、`gemini-4-argon-high`、`gemini-3.8-flash-medium`、`claude-sonnet-5-5-medium`、`claude-opus-5-5-medium`）。

既定にした理由：硬い段落・くだけたメモ・数字と名前の入った文の3つを `gemini-3.8-flash-medium`、`gemini-4-argon-medium`、`claude-sonnet-5-5-medium` で書き比べたところ、数字と固有名詞はどれも保たれました。そのうえで `claude-sonnet-5-5-medium` は1回あたり約3秒と最も速く、「〜と説明しました」のような発言の出どころを残し、「なお、」のような言葉も足しませんでした。`gemini-3.8-flash-medium` は1回14〜20秒かかり、発言の出どころを落としました。`gemini-4-argon-medium` は約6秒で出来もよい一方、「なお、」を足すことがありました。

## しくみ

1. 専用の作業ディレクトリ `${XDG_STATE_HOME:-~/.local/state}/jw/workspace`（`JW_WORKSPACE` で変更可）で agy を起動します。git リポジトリの中だと、そのリポジトリの `AGENTS.md` や `.agents/` が読み込まれるため、リポジトリの外に置きます。
2. その中に `.agents/agents/jw.md`（専用エージェント）を `rules.md` から作ります。本文がシステム指示になり、`tools: []` でツールを持たせません。
3. `agy -p` に、モード別の指示と `<本文>…</本文>` で囲んだ文を渡します。`--agent jw`、`--disable-slash-commands`、`--output-format json` を付け、`--settings` でこのセッションだけコマンド・ファイル・Web・MCP をすべて拒否します（`settings.json` には保存されません）。
4. 応答の `status` が `SUCCESS` で中身があれば、`response` だけを出力します。それ以外は標準エラーに理由を出して 0 以外で終わります。

## 共有のコーディング向け指示との関係

- agy のルールは足し算で読み込まれ、`--agent` を付けても消えません（作業ディレクトリに置いた `AGENTS.md` の内容が `--agent` 付きでも出力に反映されることを確かめています）。
- そのため `jw` は、リポジトリの外で起動して作業ディレクトリ側のルールを読ませないようにしています。
- グローバルの `~/.gemini/config/rules/shared-agents.md` は、今は YAML frontmatter がないため agy に読み込まれていません（中身に従えば答えが変わる質問をしても、従った答えになりません）。`sync-antigravity.sh` がこのファイルに frontmatter を付けるようになると `jw` にも読み込まれるので、そのときは見直します。
- `~/.gemini/config/skills` のスキル一覧はシステム指示に載ったままですが、ツールを持たせていないので、スキルの中身は読まれません。

## 守ること

- agy 本体をそのまま呼ぶだけにします。agy の中身や通信をまねたり差し替えたりしません。
- OAuth トークンや `~/.gemini` の認証ファイルを読まない・写さない・渡さない。`jw` は認証に関わるものに触りません。
- 無人で高頻度に回さない。ループや常駐はさせず、人が必要なときに1回ずつ呼びます。
- `~/.gemini/config/rules/shared-agents.md` は `etc/sync-antigravity.sh` が作る共有の指示なので、`jw` のために手を入れません。
- 結果は必ず人が読んでから使います。モデルが文の一部（締めのあいさつ、「〜じゃなくて」のような前の情報など）を削ることがあります。
