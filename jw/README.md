# jw：日本語の文章係

`jw` は、日本語の文を agy（Antigravity CLI）に1回だけ渡して読みやすく直させ、直した文だけを出力する小さなコマンドです。ほかの AI が書いた文を読みやすくする用途を想定しています。直す係には内容を作らせず、情報・確かさ・出どころを変えないことを最優先にしています。直したあとは別のモデルに元の文と直した文を比べさせ、中身が変わっていないかを確かめます。

## 中身

| ファイル | 役目 |
|---|---|
| `jw` | 本体の bash スクリプト。`~/.local/bin/jw` からシンボリックリンクで呼ぶ（置き方は下に書きます） |
| `rules.md` | 直す係（専用エージェント `jw`）のシステム指示。書き方の決まり |
| `check.md` | 確かめる係（専用エージェント `jw-check`）のシステム指示。比べるだけで文は直さない |
| `README.md` | この説明 |

## 使い方

```sh
jw [-m MODE] [-n CHARS] [--model MODEL] [--no-check] [FILE|-]
jw --check-only ORIGINAL FIXED [-m MODE]
```

- `-m rewrite`（既定）：リライト。言い方は整えるが、情報は減らさない。変更前の値（「10時からではなく」）や読み手への呼びかけ（「ぜひご活用ください」）も残す。消すのは「本記事では〜」「いかがでしたでしょうか」のような中身のない前置きと締めだけ。
- `-m proofread`：校正だけ（誤字・脱字・てにをは・文法）。
- `-m shorten`：短くする。`-n 200`（`--chars 200`）で目標の文字数（空白・改行を除く）を指定でき、省くと元の約半分を目標にする。
- `--no-check`：確かめる段階を外す。
- `--check-only ORIGINAL FIXED`：直さずに、2つのファイルを比べる段階だけを動かす。確認段階の試験や、ほかの道具で直した文の確認に使う。
- `FILE` を省くか `-` を渡すと標準入力から読む。本文は60000バイトまで。
- `JW_TIMING=1` を付けると、段階ごとの秒数を標準エラーに出す。

```sh
echo 'きょうは会議がありまsた。資料わ明日送ります。' | jw -m proofread
jw draft.md > draft.fixed.md
jw -m shorten -n 300 note.txt
jw --check-only original.txt fixed.txt
```

## 置き方

この箱では、`~/.local/bin/jw` は `~/.local/share/jw/dotfiles/jw/jw` を指しています。`~/.local/share/jw/dotfiles` は、dotfiles の origin/master を切り出した git の作業ツリー（`git worktree`、ブランチなし）です。

```sh
git -C ~/dotfiles worktree add --detach ~/.local/share/jw/dotfiles origin/master
ln -sfn ~/.local/share/jw/dotfiles/jw/jw ~/.local/bin/jw
```

`~/dotfiles` の作業ツリーに jw/ を未追跡のまま置くと、自動同期（`etc/dotfiles-autosync.sh`）が未追跡ファイルを「preserve local changes」のコミットにまとめてしまいます。同期の前に手で `git pull` すると「未追跡のファイルが上書きされる」と止まることもあります。それを避けるためです。新しい版にするときは `git -C ~/.local/share/jw/dotfiles fetch origin && git -C ~/.local/share/jw/dotfiles checkout --detach origin/master` を実行します。`~/dotfiles` の master に jw/ が取り込まれたあとは、リンク先を `~/dotfiles/jw/jw` に戻してかまいません。

## 出力と終了コード

| 終了コード | 意味 | 標準出力 | 標準エラー |
|---|---|---|---|
| 0 | 直した。確認で変化なし（`--no-check` なら確認なし） | 直した文 | なし |
| 3 | 直したが、確認で中身の変化が見つかった | 直した文 | 変化の一覧 |
| 4 | 直したが、確かめる段階そのものが失敗した | 直した文 | 失敗の理由 |
| 2 | 使い方の誤り | なし | 理由 |
| 1 | 直す段階の失敗（agy のエラーなど） | なし | 理由 |

変化の一覧は標準エラーに出します。`jw draft.md > fixed.md` のように標準出力をそのままファイルや次のコマンドに渡しても、一覧が本文に混ざらないためです。一覧は端末に表示されるので、人が読んで判断できます。スクリプトからは終了コード 3 で見分けます。一覧の例：

```
----- jw 確認: 中身の変化 2件（claude-sonnet-5-5-medium） -----
- [数字] 元: 843億円 → 後: 834億円
    第2四半期の売上高の数字が入れ替わっている。
- [出どころ] 元: …要因であると説明しました → 後: …要因です
    要因が社長の説明だという出どころが消え、断定の書き方になっている。
```

一覧の種類は、数字、固有名詞、主張、確かさ、出どころ、引用、追加、欠落です。

## モデル

| 段階 | 既定 | 変え方 |
|---|---|---|
| 直す | `gemini-4-argon-medium` | `--model` か `JW_MODEL` |
| 確かめる | `claude-sonnet-5-5-medium` | `--check-model` か `JW_CHECK_MODEL` |

名前は `agy models` に出るものを使います（例：`gemini-4-argon-low`、`gemini-4-argon-medium`、`gemini-4-argon-high`、`gemini-3.8-flash-medium`、`claude-sonnet-5-5-medium`）。

直す係を `gemini-4-argon-medium` にした理由：
- 3つの文（硬い段落、くだけたメモ、数字と名前の入った文）を書き比べたとき、数字と固有名詞を保ち、1回5〜8秒で返った。
- `gemini-3.8-flash-medium` は1回14〜20秒かかり、「〜と説明しました」という発言の出どころを落とした。
- `gemini-4-argon-high` は shorten で少しだけ短くできたが、1回90〜126秒かかった。

argon には原文にない「なお、」を足す癖があったので、`rules.md` に「原文にない接続詞を足さない」を入れています。

確かめる係は、直す係と別系統のモデルにしています。同じ系統だと同じ見落としをしやすいと考えたためです（この理由は推測で、比べて確かめてはいません）。わざと数字・固有名詞・発言者・確かさを変えた文で試し、変えた箇所はすべて見つかりました。

## かかる時間（目安）

- 短い文（100〜200字）：直す段階が約5〜8秒、確かめる段階が約3〜5秒。
- 約2,900字：直す段階が約15〜17秒、確かめる段階が約10〜14秒。
- shorten は rewrite より時間がかかることがあります（短い文で14〜32秒）。

## しくみ

1. 専用の作業ディレクトリ `${XDG_STATE_HOME:-~/.local/state}/jw/workspace`（`JW_WORKSPACE` で変更可）で agy を起動します。git リポジトリの中だと、そのリポジトリの `AGENTS.md` や `.agents/` が読み込まれるため、リポジトリの外に置きます。
2. その中に `.agents/agents/jw.md` と `.agents/agents/jw-check.md` を `rules.md`・`check.md` から作ります。本文がシステム指示になります。直す係は `tools: []` で道具なしです。確かめる係は、`--json-schema` の結果を返すのに要る `finish` だけを持ちます（`tools: []` だと構造化した結果を返せないことを確かめています）。
3. `agy -p` に、モード別の指示と `<本文>…</本文>` で囲んだ文を渡します。`--agent`、`--disable-slash-commands`、`--output-format json` を付け、`--settings` でこのセッションだけコマンド・ファイル・Web・MCP をすべて拒否します（`settings.json` には保存されません）。
4. 確かめる係には `--json-schema` で `{"changes":[{"kind","before","after","note"}]}` の形を強制し、`structured_output` から一覧を読みます。

## 共有のコーディング向け指示との関係

- agy のルールは足し算で読み込まれ、`--agent` を付けても消えません（作業ディレクトリに置いた `AGENTS.md` の内容が `--agent` 付きでも出力に反映されることを確かめています）。
- そのため `jw` は、リポジトリの外で起動して作業ディレクトリ側のルールを読ませないようにしています。
- グローバルの `~/.gemini/config/rules/shared-agents.md` は、今は YAML frontmatter がないため agy に読み込まれていません（中身に従えば答えが変わる質問をしても、従った答えになりません）。`sync-antigravity.sh` がこのファイルに frontmatter を付けるようになると `jw` にも読み込まれるので、そのときは見直します。
- `~/.gemini/config/skills` のスキル一覧はシステム指示に載ったままですが、ファイルを読む道具を持たせていないので、スキルの中身は読まれません。

## 守ること

- agy 本体をそのまま呼ぶだけにします。agy の中身や通信をまねたり差し替えたりしません。
- OAuth トークンや `~/.gemini` の認証ファイルを読まない・写さない・渡さない。`jw` は認証に関わるものに触りません。
- 無人で高頻度に回さない。ループや常駐はさせず、人が必要なときに1回ずつ呼びます。
- `~/.gemini/config/rules/shared-agents.md` は `etc/sync-antigravity.sh` が作る共有の指示なので、`jw` のために手を入れません。
- 終了コードが 3 のときは、一覧を読んでから直した文を使います。0 でも、確認は別のモデルの判断なので、大事な文は人が読みます。
- shorten は目標の文字数ちょうどにはなりません。数字と固有名詞を落とさない決まりを優先するため、元の約6〜7割で止まることがあります。
