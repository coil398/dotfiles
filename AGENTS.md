# Dotfiles Project Guidance

この指示はdotfiles repositoryを保守するときに適用します。全project共通の作業方針は `.agents/global-instructions.md` を原本とし、生成・配布先で読み込みます。このroot fileはdotfiles固有の保守方法だけを定めます。

## 原本と生成物

- AI workflowの構成・runtime間の接続仕様は [AI-WORKFLOW-SPEC.md](AI-WORKFLOW-SPEC.md) が正本です。
- 共通指示のsourceは `.agents/global-instructions.md`、dotfilesのproject指示はこの `AGENTS.md` です。root `CLAUDE.md` はこのfileだけを `@AGENTS.md` で読み込みます。
- Claude Codeはnativeの `.claude/CLAUDE.md` から `@~/.agents/AGENTS.md` で共通本文を読みます。Claude原本をCodex/OpenCodeの内容から生成しません。
- Codex nativeの原本は `.codex/codex-native-supplement.md` と `.codex/config.base.toml` です。`.codex/AGENTS.md` と `.codex/config.toml` は生成物なので手編集せず、sourceまたはadapterを直して再生成します。
- Cursorの `.cursor/rules/shared-agents.mdc` と `.cursor/mcp.json` は生成物です。`.cursor/rules/skill-procedure.mdc`、`.cursor/agents/**`、`.cursor/skills/**` はnative側の原本です。
- `.codex/AGENTS.override.md` はrepo内の生成物編集に関する別の指示です。rootの `AGENTS.override.md` と混同せず、共通原本化・home配布・削除をしません。
- `AGENTS.md`、`.agents/skills/**`、`.agents/global-instructions.md`、runtime native sources、`mcp-servers.json`、`.codex/config.base.toml`、`etc/sync-*.sh` はworkflow/source fileとして扱います。
- 生成・配布に関わるsourceを変更したら、該当runtimeのsync/linkを実行し、sourceと生成物の差分を照合します。生成物の差分だけを手編集で作りません。

## セットアップと配布

- 新規の一般セットアップは `etc/init.sh`、Codespaces専用セットアップは `install.sh`、既存設定のリンク再展開は `sh etc/link.sh` を使います。
- 共通指示だけを更新・配布するときは `bash etc/link.sh --global-instructions-only` を使います。全runtimeのsourceやnative設定を反映する場合は対象に合ったsync/linkを選びます。
- Codex/Cursorだけを生成・配布するときは `bash etc/link.sh --codex-cursor-only` を使います。`bash etc/link.sh --ai-runtimes-only` はClaude globalの配布やOpenCode生成を含まないため、それだけで全runtime反映済みと扱いません。OpenCodeは必要に応じて `bash etc/sync-opencode.sh` を実行します。
- setup/linkは冪等に保ちます。新しいdotfileや `.claude/` 直下のnative sourceを追加したら、`etc/link.sh` の除外・allowlistと実際のhome配置を確認します。
- `link.sh` は `~/dotfiles` がない場合、自身の物理位置からrepository rootを解決します。任意のcheckout位置で動くことを保ちます。
- link処理で既存の実directoryを置き換えず、nested symlinkを作りません。組込みskillや既存のuser設定を保全します。
- `~/.codex` 全体をsymlinkにせず、管理対象だけを個別配置します。認証・履歴・組込み/個人skillを保全します。Cursor skillはhomeへ実体copyする既存処理を使います。
- `.claude/skills` はClaude home側へlinkします。Claude globalの共通本文は `~/.agents/AGENTS.md` へ、共有skillは `~/.agents/skills` へ配布します。
- `.devin/` をrootに置きません。`link.sh` のhidden-file loopにより `~/.devin` へ誤linkされる可能性があります。project configが必要なら、先にlink処理の除外対象へ加えます。

## MCP・hook・Claude設定

- `mcp-servers.json` はuser-scope MCPのsourceです。entryとruntime filterはJSONおよび各sync実装から確認します。Claudeのuser-scope反映は `bash etc/sync-mcp.sh` を使います。この処理は原本にない管理対象登録も除去するため、対象と副作用を確認します。
- project固有MCPは対象repositoryの `.mcp.json` に置き、homeへlinkしません。`claude` commandをMCP設定用aliasへ置き換えません。
- `.claude/lib/` はhomeのsymlink経由で動作します。`SCRIPT_DIR` の解決は `cd -P` を使い、相対参照がrepositoryの実体へ届くことを確認します。
- `.claude/settings.json` を変えたらhome linkと内容を照合します。UIのatomic renameでhome側が実fileになっていた場合は、その変更を保全・統合してから既存配布手順で反映します。起動時cacheの変更は新しいsessionで確認します。
- `.claude/` の変更は全projectへ届きます。`<!-- CORE -->` で囲まれた保護領域（例: `.agents/skills/codex/references/runner.md`）は明示依頼なしに変更しません。
- Codex/Cursor/Devin/Grokの任意Jev hookに関するsource、送信範囲、設定、利用量・推定費用は `jev-hooks/README.md` を参照します。

## 個別設定

- `.zshrc` のPATH追加ではOS分岐を考慮します。tmux設定は `tmux source-file ~/.tmux.conf` で反映を確かめます。
- 方針変更後は、その作業で不要になった生成物・設定・hook登録をdiffで確認し、userの既存変更と区別して整理します。
- 共通Skill・workflow・配布構造を変更する場合は、必要な原本・adapter・hook・README・仕様書の説明を揃えます。Skillの専用手順や長い知識は共有 `.agents/skills/` の該当原本に置き、native側へ複写しません。

## dotfiles作業別reference

このrepository内のSkill/reference sourceは `.agents/skills/` にあります。

| 読む条件 | 読むもの |
|---|---|
| dotfilesで共通原本・runtime native source・adapter・hook・生成・配布経路を変更する | [AI-WORKFLOW-SPEC.md](AI-WORKFLOW-SPEC.md) とこの `AGENTS.md` |
| `.githooks/` を変更する | `.githooks/CLAUDE.md` |
| Neovim設定（`.config/nvim/`）を変更する | `.config/nvim/CLAUDE.md` |
