---
name: "overlay-audit"
description: >-
  指定した起動ディレクトリと、親が確定した dotfiles root のスキル配置・エージェント定義を点検する。
  判定の正は etc/audit-skill-agent-layout.py。実効 runtime の native 優先順、Cursor の name、
  agent の model/role、生成物の状態を報告する。「overlay 点検」「スキル配置」
  「エージェント定義は共通か」「layout audit」「/overlay-audit」で使う。
argument-hint: "[起動ディレクトリ]"
---

<!-- Cursor native overlay: 指定 cwd と runtime の native 優先順を engine へ渡す -->

# /overlay-audit — スキル / エージェント配置点検

指定された起動ディレクトリと、親が実在確認した dotfiles root を監査します。修正・再生成はせず、判定 engine の実測結果だけを要約します。あるべき形と合否は etc/audit-skill-agent-layout.py が決めます。

## 実効配置と優先順

- 共有 Skill の種は .agents/skills です。Claude は .claude/skills の配布先を使います。
- Codex は、存在する .codex/skills/<name> の native overlay を優先し、無い場合は共有 Skill を使います。
- Cursor は .cursor/skills/<name> の native overlay を優先し、link.sh が ~/.cursor/skills に実体 directory として materialize した内容を読みます。overlay と共有側の本文差は、生成器が lockstep を宣言している場合を除き単独の FAIL としません。
- Cursor agent の model / role、Skill frontmatter の name と親 directory、home materialize の一致は engine の出力を正とします。Skill 本文へ判定規則を複製しません。

## 手順

### 1. 入力の確定

起動ディレクトリ引数は runtime の構造化された引数として受け取ります。省略時は runtime が渡した現在のディレクトリを使い、未引用の shell word splitting、glob、eval で再解釈しません。dotfiles root も親が実在確認した値を使い、未確認の home path を補いません。

~~~bash
TARGET_CWD="<runtime が確定した起動ディレクトリ>"
DOTFILES_ROOT="<親が実在確認した dotfiles root>"
python3 "$DOTFILES_ROOT/etc/audit-skill-agent-layout.py"   --cwd "$TARGET_CWD" --dotfiles "$DOTFILES_ROOT"
~~~

起動ディレクトリが repository 内なら engine が Git top-level を解決します。対象が存在しない、dotfiles root や engine が存在しない場合は、状態を変えずに停止して理由を報告します。

### 2. 判定結果の扱い

出力の LEVEL<TAB>repo<TAB>topic<TAB>message と SUMMARY fails=N を読み、FAIL は engine が示した壊れた生成物・配置だけを報告します。WARN は現行 native overlay 方針に沿う限りエラーへ昇格しません。生成器、seed、link、home materialize を起動して結果を補いません。

報告は次の順で、対象と実測値を明示します。

- 対象: 指定起動ディレクトリから解決された Git root、dotfiles root
- Skill: .agents の件数、Claude 配布、native overlay の有無
- Cursor: overlay の name == folder、実行時契約、home materialize
- Agent: 各 runtime の件数、欠け、Cursor の model / role
- 本文: identical / vocab-only / substantive / generated-stale / native-overlay
- generator: engine が出した生成器検査の結果

### 3. 不変条件

- ファイルを Edit、Write、seed、sync、再生成しない
- 判定ルールをこの Skill に追加せず、engine の判定を正とする
- SYNC_CODEX_LEGACY_MIRROR=1 を実行しない
- overlay 本文を byte 一致させる修正を提案しない
