# AI Workflow Architecture Spec

dotfilesのAgent / Skill運用の正本。スキルがどこに置かれてどう読み込まれるか、親エージェントが子（サブエージェント）をどう起動し、model / effortがどこで決まるか、生成・配布・hookがどう動くかをまとめる。対象runtimeはClaude Code、Codex、Cursor、OpenCode、Grok、Antigravity。

共有の責任・専門知識・結果の意味は1か所にまとめ、runtimeごとの起動方式の違いはnative側に残す。個々のSkill本文やモデル表はここに再掲せず、実行時に読む原本を案内する。常時守る制約は[AGENTS.md](AGENTS.md)に置く。

## 責任と読者

| 要素 | 責任 | 置き場所 |
|---|---|---|
| 親の進行用Skill | 対象・範囲・完了条件、担当の選択と配分、結果統合、最終判断 | `.agents/skills/<name>/SKILL.md`。runtime固有の進行はnative入口 |
| 実行者用Skill / reference | 割り当てられた仕事の専門手順、評価基準、返却内容 | Skillの`references/`、または独立して再利用する実行者Skill |
| 今回のタスク指示 | 対象と版、目的、確定事実、所有範囲、制約、重点、完了条件、資料の実体パス | 親から各担当へ渡す入力 |
| runtime設定・入口 | 起動API、model・推論量、権限、ツール、発見 | runtimeのconfig、native supplement、短い入口 |
| scripts / CI | 決まった変換、ビルド、検証、生成・配布 | `etc/`、またはSkillの`scripts/`・`tests/` |
| 運用文書 | 設計、原本の所在、保守方法、例外 | 本文書。READMEは入口 |

親がSkillを切り替えても新しい司令塔を起動するわけではない。同じ親が、その段階の手順を読む。短い単発作業や親だけで完結する対話に、不要なSkillや親子分割を加えない。

### 誰が何を読むか

| 場面 | 親 | 実行者 |
|---|---|---|
| 親が委任する | 進行手順、担当選択、入出力、結果契約、runtime方針を読む。専門本文を委任のためだけに先読みしない | 渡された専門Skill・referenceを自分で読む |
| 親が直接実行する | 実行者として該当する専門手順を読む | 親自身 |
| 親が結果を統合する | 返却と根拠を照合し、判定の対立や不足を確かめるのに必要な専門部分を読む | 根拠、確認範囲、未確認を返す |

親はロードしたSkillの実体から子が読める原本パスを解決して渡す。対象repoのcwdに個人Skillがあること、親の読込状態が子へ継承されること、同名Skillの自動選択には依存しない。常時の規則は[AGENTS.mdの作業の配分とSkill](AGENTS.md#作業の配分とskill)に従う。

通常の実行者へ親用の配分Skillを渡して工程を再起動させない。readerの結果は親へ返し、保存は親または許可済みwriterが行う。ビルドやテストの生成物も書き込みとして扱う。文章上の変更禁止、runtimeによるアクセス拒否、外部ツールの権限は別の事実である。

## 原本と参照関係

| 内容 | 正本 |
|---|---|
| 常時の作業・権限・委任境界 | [AGENTS.md](AGENTS.md) |
| レビュー対象・観点の解釈、配分、独立性、統合 | [reviewer](.agents/skills/reviewer/SKILL.md) |
| 実際の評価と観点別の専門基準 | [code-review-guidance](.agents/skills/code-review-guidance/SKILL.md)とそのreference |
| COVERAGE / VERDICT、重大度、未完了・集約の意味 | [result-contract.md](.agents/skills/code-review-guidance/references/result-contract.md) |
| テスト選択・実行 | [tester](.agents/skills/tester/SKILL.md)と[test-procedure.md](.agents/skills/tester/references/test-procedure.md) |
| 調査・分析・仮説 | [research](.agents/skills/research/SKILL.md)の担当reference |
| 振り返り | [retro](.agents/skills/retro/SKILL.md)の通常・meta reference |
| Codex CLIへの相談・実装委譲 | [codex](.agents/skills/codex/SKILL.md)と[runner.md](.agents/skills/codex/references/runner.md) |
| PIR²の長期再開と実験 | [handoff.md](.agents/skills/pir2/references/handoff.md)、[experimental.md](.agents/skills/pir2/references/experimental.md) |
| Claudeのモデル使い分け | `.claude/CLAUDE.md`の「Claude Agent運用」 |
| Codex通常設定 | [.codex/config.base.toml](.codex/config.base.toml) |
| Codexの起動・モデル選択・委譲の受け渡し | [.codex/codex-native-supplement.md](.codex/codex-native-supplement.md) |
| Cursor Taskのモデル・実行方針 | [AGENTS.mdのShared Core And Native Overlays](AGENTS.md#shared-core-and-native-overlays) |
| Cursor Fableの指定と失敗時の扱い | [fable-model.md](.cursor/skills/deepthink/references/fable-model.md) |
| MCP構成 | [mcp-servers.json](mcp-servers.json) |
| 生成・配布 | [sync-codex.sh](etc/sync-codex.sh)、[sync-cursor.sh](etc/sync-cursor.sh)、[sync-opencode.sh](etc/sync-opencode.sh)、[link-codex-runtime.sh](etc/link-codex-runtime.sh)、[link.sh](etc/link.sh) |

PIR²、IR、debug、epic、review-prは共通レビューへ入力を渡し、返却を消費する。観点一覧や判定規則を別に保守しない。研究の不確実性、リファクタ提案、Git同期、熟考の十分性は各手順固有の意味を持ち、全体集約に参加する場合だけ共通結果契約へ接続する。

## スキル

### 3つの層

| 層 | 置き場所 | 中身 |
|---|---|---|
| 共有原本 | `.agents/skills/<name>/` | `SKILL.md`（手順本体）、`references/`（子に渡す専門手順）、`scripts/`、`assets/` |
| runtime入口 | `.claude/skills/`、`.cursor/skills/` | そのruntimeから起動するための入口。本文は共有原本を読む |
| ホーム配備 | `~/.agents/skills`、`~/.claude/skills`、`~/.cursor/skills` など | `etc/link.sh`が配置する |

- 手順の本体は共有原本に1つだけ書く。runtime入口には、そのruntime固有の起動方法（子の起動API、model指定、CLI連携など）の差分だけを書く。
- 子に渡す専門手順（例: `research/references/explorer.md`、`code-review-guidance/references/<観点>.md`）も共有原本の`references/`に置く。親はそのファイルの絶対パスを子に渡し、子が自分でReadする。

### runtimeごとの入口

| runtime | 入口の形 | ホーム配備 |
|---|---|---|
| Claude Code | `.claude/skills/<name>` → `../../.agents/skills/<name>` の相対symlink。固有の起動機構が要る`codex`、`deepthink`、`design-review`だけnativeの`SKILL.md` | `~/.claude/skills` → repoの`.claude/skills`（ディレクトリごとsymlink） |
| Codex | `.agents/skills/*`を直接読む | `~/.agents/skills` → repoの`.agents/skills`。`~/.codex`は管理対象だけ個別にリンク |
| Cursor | `.cursor/skills/<name>/SKILL.md`。多くは薄い入口で、本文は共有原本を読む。frontmatterの`name`はディレクトリ名と一致させる | `~/.cursor/skills/<name>`へ実体コピー |
| OpenCode | 登録を生成しない。`~/.agents/skills/*`と`~/.claude/skills/*`から発見する | `~/.agents/skills`を共用 |
| Antigravity | `.gemini/config/skills` → `.agents/skills`のsymlink | `~/.gemini/config/`へ配備 |
| Grok | 共有`.agents/skills`と互換のCursor/Claude Skillを発見する | [Grok runtime boundary](#grok-runtime-boundary) |

### runtime固有の例外

- Claude native: `codex`（Codex CLI runnerの起動）、`deepthink`（Fable熟考。専門契約はCursor版`deepthink`の`references/`を読む）、`design-review`（外部design repoのcanonical Skillを`scripts/resolve-design-repo.sh`で解決するbootstrap）。
- Claudeで無効化: `.claude/settings.json`の`skillOverrides`で`ai-design-system`、`chat`、`writing-plan`を`off`にしている。
- Codexで無効化: 共有`codex`。`etc/sync-codex.sh`の`CODEX_EXCLUDED_SHARED_SKILLS`に載せた名前を、生成`config.toml`の`[[skills.config]] enabled = false`で抑止する。Codex内の同じ仕事はnative collaborationで行う。
- Cursor専用: `deepthink`（Fable熟考）、`geminify`（Gemini Flashで日本語を書き直し、誤解を照合する）。
- Cursor入口なし: `design-review`、`jev`、`wsl-windows`は共有原本だけを持つ。
- Claudeの`~/.claude/skills`はrepoの中を指すため、Claude Codeが`~/.claude/skills/synced/`に書くアカウントskillのキャッシュもrepoに入る。これは`.gitignore`で除外している。

Claude native入口、submoduleのSkill、`.system`、インストール済み外部plugin・個人Skillは管理対象ではない。互換発見されても管理対象へ編入しない。design-reviewが案内する外部design repoも外部原本として扱う。

### スキルを追加・変更するとき

1. 手順本体は`.agents/skills/<name>/SKILL.md`に書く。子に渡す手順は同じスキルの`references/`に置く。
2. Claudeは`.claude/skills/<name>` → `../../.agents/skills/<name>`の相対symlinkを作る。固有の起動機構が要る場合だけnativeの`SKILL.md`を置き、共有原本を読む形にする。
3. Cursorは`bash etc/seed-cursor-overlay.sh`で入口を作り（名前は`bash etc/normalize-cursor-skill-names.sh`で揃う）、`bash etc/link.sh --codex-cursor-only`でホームへ配備する。
4. Codexは共有原本をそのまま読む。Codexで使わせない共有スキルは`CODEX_EXCLUDED_SHARED_SKILLS`に足し、`bash etc/sync-codex.sh`を実行する。
5. `bash etc/test-cursor-contracts.sh`、`bash etc/check-shared-drift.sh`、`python3 etc/audit-skill-agent-layout.py`（`/overlay-audit`）を通す。新しいSkillの発見は新規セッションで確認する。

## サブエージェント

### 共通の考え方

- 専門手順はSkillの`SKILL.md`と`references/`に置く。役割ごとの専用エージェント定義は作らない。
- 親はruntime標準の汎用担当を起動し、読むべき手順ファイルの絶対パスをプロンプトで渡す。子はそれを自分でReadしてから作業する。
- 子のmodelとeffortの既定値はruntimeの設定で一度だけ決める。Skillにはmodel表を持たせない。例外は「そのモデルであること自体が目的」の場合だけ（`deepthink`のFable、Cursor探索担当の`composer-2.5[]`）。
- 難しい作業は、親が起動時にmodel・effortを明示して上書きする。入力不足・権限・環境の失敗はモデル不足として扱わない。
- 委任した子の読み取り専用は、Claude・Codex・Cursor（`explorer`以外）では指示による境界であり、技術的な強制ではない。プロンプトで編集禁止と書いてよい出力パスを明示し、親が返却後に`git status`とdiffで確認する。
- 必要な観点と子の人数は別の入力である。固定人数を目的化しない。

### runtimeごとの比較

| | Claude Code | Codex | Cursor | OpenCode |
|---|---|---|---|---|
| 親 | 起動時のモデル（`/model`） | `gpt-6-astra` / `low` | Auto | 有効設定 |
| 子の既定model | 親と同じ（`CLAUDE_CODE_SUBAGENT_MODEL`未設定） | `gpt-6-luna` | 省略（親のAutoを継承） | OpenCode標準 |
| 子の既定effort | 親セッションのeffort | `max` | Cursorの公開オプション | OpenCode標準 |
| 既定の置き場所 | `.claude/CLAUDE.md`の方針 | `.codex/config.base.toml`の`[agents]` | AGENTSのCursor Task方針。探索だけ`.cursor/agents/explorer.md` | `~/.config/opencode/opencode.json`（生成） |
| 呼び出しごとの上書き | Agent toolの`model`引数（effortは不可） | spawnのmodel / reasoning_effort | Task起動時に公開されている指定 | `task` toolの公開引数 |
| 専用エージェント定義 | なし | なし | `explorer`の1本だけ | なし |

### Claude Code

- 子は`Agent({ subagent_type: "general-purpose", model?, prompt })`で起動する。custom agent定義（`.claude/agents/`）は置かない。
- modelの優先順位: Agent toolの`model`引数 → agent定義のfrontmatter → `CLAUDE_CODE_SUBAGENT_MODEL` → 親のモデル。
- effortは呼び出しごとに指定できない。子は親セッションのeffortを使う。担当ごとに変えたいときは、その作業の前に親で`/effort`を変える。子を別モデルで起動したとき、そのモデル用`modelSettings`のeffortが使われるかは公式ドキュメントに記載がなく未確認。
- モデルの使い分けは`.claude/CLAUDE.md`の「Claude Agent運用」に書く。
  - 手を動かす実装・修正はCodexに任せる（`/codex`の実装経路。既定`gpt-6-luna` / `max`、難所は`gpt-6-sol`）。
  - Codexを使えないとき（使用量切れなど）は`general-purpose`を`model: "sonnet"`で起動して実装させる。
  - それ以外（探索・レビュー・テスト・熟考）は`model`を省略して親を引き継ぐ。Skillが固定するモデルはそれに従う。
- Claude native Skillで固定しているのは`deepthink`だけ。deliberator / synthesizer / gateに`claude-fable-5-1`（`--opus-panel`時は`opus`）を使う。
- Agent toolの`model`にはClaudeのモデルしか指定できない。GPT系は共有`codex` Skill経由でCodex CLIを使う。
  - 相談: `/codex <相談内容>`（read-only）。
  - 実装: `/codex <実装タスク>`（workspace-write）、または`/pir2 --codex`（計画・レビュー・テストはClaude、実装だけCodex）。
  - どちらもrunner（`general-purpose`、model省略、background）が[runner.md](.agents/skills/codex/references/runner.md)に従ってCLIを起動し、完了まで待つ。親は結果と実差分を照合する。
- 参照: <https://code.claude.com/docs/en/sub-agents.md>、<https://code.claude.com/docs/en/model-config.md>

### Codex

- `.codex/codex-native-supplement.md`は`etc/sync-codex.sh`が生成`.codex/AGENTS.md`（`~/.codex/AGENTS.md`へリンク）の末尾に連結する。そのためCodexの全セッションで読み込まれる。
- 親Astraが計画・統合・受入を持つ。子はbuilt-inの`default` / `worker` / `explorer`を使い分ける。
- 子の既定は`.codex/config.base.toml`の`[agents]`で決める。

  ```toml
  default_subagent_model = "gpt-6-luna"
  default_subagent_reasoning_effort = "max"
  ```

- 難しい独立推論は、親が起動時に`gpt-6-sol`と`high` / `max`を明示して選べる。
- supplementの「Concrete Work Delegation」が、実装・レビュー・テスト・探索を含む全委譲の受け渡しと受入の契約である。探索だけを渡すときは編集禁止を明示し、`.agents/skills/research/references/explorer.md`のパスを渡す。子は他の担当を起動せず、commit・push・既存変更の破棄をしない。親は`git status`・diff・確認結果で受け入れる。
- 新しい子には`fork_turns="none"`を明示し、親の会話履歴ではなく自己完結した指示を渡す。これは起動方針であり、設定で強制されるものではない。
- 使えるモデルは`codex debug models`で確認する。CLIが古いと新しいモデルが一覧に出ないので、先に`codex update`する。

#### 待機設定

親が子を待つ設定は`.codex/config.base.toml`の`[features.multi_agent_v2]`にある（V2を有効化し、`wait_agent`の下限600000ms・未指定時1200000ms・上限3600000ms）。値はCodex 0.153.4の公開型と照合したもので、旧版・別backendでの受理は保証しない。

- 下限は無条件のsleepではない。子の完了通知・mailbox・ユーザーの追加入力で期限より早く戻る。
- 子が通知しないまま止まると、親の次の確認は最大で未指定時20分、明示的な長待機なら60分後になり得る。待機timeoutは子の実行期限ではなく、終了・失敗・再起動の根拠にしない。
- 単体運用へ一時的に限定するときは`codex -c 'agents.enabled=false' -c 'features.multi_agent_v2.enabled=false'`で起動する。
- Cursor側の待機方針（Foreground / Background の選び方）はAGENTS.mdの「Cursor Task execution」に置く。数値や方針を専門Skillへ複製しない。

### Cursor

- Taskのmodelは基本的に省略して親のAutoを引き継ぐ。例外は次の2つ。
  - `explorer`: `composer-2.5[]`（空の角括弧は fast ではない標準版を選ぶ Cursor の指定）
  - `deepthink` / `deepplan`: 思考担当にFableを使う（`.cursor/skills/deepthink/references/fable-model.md`）。Fable指定を別モデルや親だけの熟考で代替しない。
- 委譲は標準Task（`subagent_type: "generalPurpose"`、model省略）で起動し、手順ファイルの絶対パスを渡す。
- 探索だけは`Task({ subagent_type: "explorer" })`で起動する。`.cursor/agents/explorer.md`（`composer-2.5[]`、`readonly: true`）が適用される。Cursorのエージェント定義はこの1本だけ。
- `readonly`はagent定義でしか設定できないため、探索以外のread-only担当（reviewerなど）はプロンプトで編集禁止を明示し、親が返却後に`git status` / diffを確認する。`readonly`という名前やfrontmatterから外部MCP全体の隔離を推測しない。
- Cursorからの`/codex`（`/pir2 --codex`を含む）は明示的なCLI連携で、Cursor自身のTask設定とは別管理。

### OpenCode

- エージェントは生成しない。委譲にはOpenCode標準の担当と`task` toolを使う。
- `etc/sync-opencode.sh`は、以前生成した`~/.config/opencode/agents/*.md`（AUTO-GENERATEDヘッダ付き）を削除する。詳細は[sync-opencode.sh Contract](#sync-opencodesh-contract)。

## 実行例

### PIR²からレビュー・テストへ

1. 同じ親が[pir2](.agents/skills/pir2/SKILL.md)を読み、対象版・要求・担当範囲を確定し、実装を進める。`/pir2 --codex`では実装だけを`/codex`の実装経路へ渡す。
2. レビュー段階で親が[reviewer](.agents/skills/reviewer/SKILL.md)を読み、対象diff、受入条件、ユーザーが指定した観点と独立性をそのまま渡して担当を決める。
3. 評価子には`code-review-guidance/SKILL.md`の実体パス、選択したreference、対象と今回の重点を渡す。子が専門原本と共通結果契約を読み、評価して親へ返す。
4. 親が根拠と結果を統合する。修正後は影響した範囲を再確認する。
5. 親が[tester](.agents/skills/tester/SKILL.md)の進行を使い、実行者に`test-procedure.md`と実在するコマンド・許可した出力範囲を渡す。
6. 長期作業の中断・再開は全runtime共通の[handoff.md](.agents/skills/pir2/references/handoff.md)を読む。終了時に[experimental.md](.agents/skills/pir2/references/experimental.md)のActiveな実験を確認し、対象なら`~/.ai-pir-runs/experimental-observations.md`へ観測を1件記録する。

複数観点を一つの実行者が扱うか、明示された五観点独立評価を別コンテキストへ分けるかはreviewerの正本に従う。

### research

親が[research](.agents/skills/research/SKILL.md)で問いと範囲を確定する。探索・技術比較を分ける場合は`references/explorer.md`・`tech-validator.md`、分析や仮説を分けるなら`thinker.md`・`hypothesizer.md`の実体パスと具体的なサブ問いを担当へ渡す。各子が事実と推測・不確実性を返し、保存する研究レポートは親が統合する。

### retro

親が[retro](.agents/skills/retro/SKILL.md)で対象の実績と明示されたモードを確定する。通常分析には`references/retrospector.md`、明示metaには`meta-retrospector.md`の実体パスを渡す。子は分析を返し、親が採否・変更・保存を判断する。通常の振り返りから勝手にworkflow骨格の変更へ広げない。

### Cursor deepthink

親が[Cursor deepthink](.cursor/skills/deepthink/SKILL.md)と`references/fable-model.md`を読む。single / panelで選んだ熟考担当に`deliberator.md`の実体パスと問い・入力・レンズを渡す。親自身が統合・十分性確認を行う場合は`synthesizer.md`・`gate.md`を読み、委任する場合は各実体パスを担当へ渡す。Claude nativeの`deepthink`も同じreferenceを読む。

### 短い通常作業

小さな単発修正は具体的なタスク指示と関連確認で完結する。独立評価が不要で親が評価するなら、親が`code-review-guidance`と必要referenceを読む。短い作業のために全専門資料、別司令塔、多重のplan/reportを作らない。

## 生成・配布とhook

### Codex

- `etc/sync-codex.sh`は`config.base.toml`・`mcp-servers.json`から`.codex/config.toml`を、`AGENTS.md`とnative supplementから`.codex/AGENTS.md`を生成する。`.claude/`の`format.md`・`user-feedback-protocol.md`・`dev-server.md`も`.codex/`へ生成する。project trustなどマシン固有の設定は既存の`config.toml`から引き継ぐ。
- `etc/link-codex-runtime.sh`が管理対象の生成ファイルを`~/.codex`へ個別にリンクする。管理外リンク・個人Skill・認証・履歴は保持する。
- Codexの`PostToolUse`は`Edit|Write|MultiEdit`に一致し、このmatcherはnativeの`apply_patch`にも一致する。そのため生成処理を直接登録せず、`python3 etc/sync-codex-hook.py`を登録している。helperは`tool_input.command`のpatchから変更パスを`event.cwd`基準で解決し、生成元（`SOURCE_FILES`）か`.agents/skills`直下の`SKILL.md`が変わった場合だけ`etc/sync-codex.sh`を1回実行する。通常の編集と同期成功は無出力で、失敗時だけ短い追加情報を返す。モデルは呼ばない。試験は`etc/test-codex-native-sync-hook.py`。
- Claude Codeで生成元を編集したときは、`.claude/settings.json`のPostToolUseが`~/.claude/lib/sync-codex-hook.sh`（OpenCode・Devinも同様の`sync-*-hook.sh`）を呼ぶ。試験は`etc/test-sync-hooks.sh`。
- 変更後の新規セッションで、生成された`config.toml`のhook commandとhook trustを確認する。

### Claude Code

`.claude/`が原本で、Codex/Cursorから逆生成しない。`etc/link.sh`が`.claude/skills`ごと`~/.claude/skills`へリンクする。Claude native Skillだけが使う手順はそのSkillの`references/`に置く。

### Cursor

- `etc/link.sh`が`.cursor/skills`の入口を`~/.cursor/skills`へ実体コピーする。共有専門資料はnative入口の実体から解決し、別配置では親が確認した実体パスを使う。
- `etc/sync-cursor.sh`は`AGENTS.md`を参照する要約Rules`.cursor/rules/shared-agents.mdc`と、MCP原本から`.cursor/mcp.json`を生成する。`.cursor/rules/skill-procedure.mdc`は手書きのnative Rule。native Skill/Agent本文は再生成しない。
- User RulesはCursor Settings → Customize → Rules → Userで登録する。登録した規則が実際のdotfilesの`AGENTS.md`、homeの共有Rules、作業先AGENTSを参照することを確認する。ファイル配布や`--check`だけでUI登録済みとは扱わない。

### 変更したときの反映

| 変えたもの | 編集する原本 | 反映 |
|---|---|---|
| 共有Skill / reference | `.agents/skills/**` | Codex・OpenCode・Antigravityはリンク経由で即時。Cursor入口が変わったら`bash etc/link.sh --codex-cursor-only` |
| Claudeの子の既定model | `.claude/settings.json`の`env.CLAUDE_CODE_SUBAGENT_MODEL` | 新しいセッション |
| Claudeの担当ごとのモデル方針 | `.claude/CLAUDE.md`の「Claude Agent運用」 | 新しいセッション |
| ClaudeのSkillごとのmodel | 該当native Skillの`SKILL.md` | 即時 |
| Codexの子の既定・待機設定 | `.codex/config.base.toml` | `bash etc/sync-codex.sh` |
| Codexの委譲・モデル選択方針 | `.codex/codex-native-supplement.md` | `bash etc/sync-codex.sh` |
| homeの`~/.codex`リンク | `etc/link-codex-runtime.sh` | `bash etc/link-codex-runtime.sh --write` |
| Cursor Rules / MCP | `AGENTS.md`、`mcp-servers.json`、`etc/sync-cursor.sh` | `bash etc/sync-cursor.sh` |
| Cursorの探索担当のmodel | `.cursor/agents/explorer.md`の`model:` | `bash etc/link.sh --codex-cursor-only` |
| Codex・Cursorをまとめて | 上記 | `bash etc/link.sh --codex-cursor-only` |
| OpenCode | `AGENTS.md`、`mcp-servers.json`、`.opencode/plugins/*`、`etc/sync-opencode.sh` | `bash etc/sync-opencode.sh`（opencodeの再起動が必要） |

配布は既存のbackup・リンク保全・materializeを使う。seedは欠けた専門本文を他runtimeから再構築しない。`check-shared-drift.sh`と`audit-skill-agent-layout.py`は原本とruntimeの有効な配置を確認し、固定のAgent集合を必須にしない。自動syncの対象選択は既存hookが持つ。

## 追加先と保守方法

| 追加したい内容 | 置き場所 |
|---|---|
| 常時または特定pathで守る制約 | AGENTS / 生成Rulesの原本 |
| 対象確定・配分・統合という一つの進行用途 | 既存の親Skill。別用途として独立するときだけ新規Skill |
| 既存の用途の専門手順・長い資料 | 既存packageのreference |
| 複数の進行から同じ仕事を直接依頼する専門手順 | 再利用する実行者Skill |
| 一回限りの対象・重点・確定事実 | 今回のタスク指示 |
| 決まった変換・ビルド・検証 | 既存script / test / CI |
| 標準起動引数で表現できない実行条件、互換入口 | 必要な短いnative入口 |

Skillの長さ・file数・階層を統一条件にしない。新規作成前に既存構造を確認し、同義Skill、モデル別Agent、専門知識の二重原本を増やさない。descriptionは能力と適用条件を短く示す。指示の監査・改善は[instruction-refactor](.agents/skills/instruction-refactor/SKILL.md)を使う。

### 変更時の最小確認

1. 主な読者、専門原本、呼出先、結果の消費先と今回の差分を確認する。委任と直接実行の読込が接続しているか、未使用referenceや子の親工程再起動がないか読む。
2. 変更した挙動だけ代表確認する。scriptは関連する既存試験を使い、必要な失敗ケースを最小追加する。
3. 相対参照は実体から解決し、Markdown・metadata・生成元/生成物・配布先を確認する。ファイル数や文字列一致だけを意味の正しさと扱わない。
4. 生成・配布に影響する原本を変えた場合だけ、上の反映を実行する。まとめた確認は`bash etc/test-all-contracts.sh`（隔離fixtureを含めるなら`--full`）。
5. 実行したコマンドと結果、未確認、残る例外を報告する。

### 実装と確認の区別

原本・参照・configが存在することを「実装済み」、コマンドや実際の処理結果を観測した範囲を「実行確認済み」、利用できないruntime・model metadata・外部アプリ等を「未確認」と分ける。配置確認とTask実行、行動上の禁止と技術的権限は別の確認である。保存した設定や子の自己申告は、実際に動いたモデルの証明にならない。

### 別リポジトリへの適用

[agent-skill-migrate](.agents/skills/agent-skill-migrate/SKILL.md)を明示的に使う。例: `$agent-skill-migrate mode=apply runtime=both scope=repo`に、対象repoと今回の要件を渡す。個人共通設定を変えるときだけ`scope=dotfiles`を選ぶ。

現在のHEAD・未コミット変更・既存文書から開始し、既存の専門知識・結果契約・有効な入口を保持して責任と参照先を揃える。対象repoの正式文書とREADMEへ現行形を残す。dotfilesの固定パス・人数・モデル別定義をコピーせず、管理外pluginや未指定repoへ範囲を広げない。

## sync-opencode.sh Contract

Default `bash etc/sync-opencode.sh` does:

- Generate `~/.config/opencode/opencode.json` from `mcp-servers.json` (excluding `claudeCodeOnly`, `codexOnly`, `cursorOnly` and `devinOnly`; `openCodeOnly` servers are included), an OpenCode-specific permission policy owned by the script (bash allow-by-default with dangerous-command asks, edit allow, read deny list inherited from `.claude/settings.json#permissions.deny`, and `external_directory: {"~/**": "allow"}` because OpenCode defaults it to ask and "always" approvals are session-scoped, which caused approval fatigue for any out-of-cwd reference; the Claude Code allow allowlist is intentionally not carried over), and `lsp: true` (OpenCode disables LSP when the key is omitted).
- Sync OpenCode plugins from the repo-native SSOT `.opencode/plugins/*` to `~/.config/opencode/plugins/` with a provenance header. OpenCode has no settings.json-style hooks; PreToolUse / PostToolUse / Stop equivalents are implemented as plugins (`tool.execute.before`, `tool.execute.after`, `session.idle`). Orphan AUTO-GENERATED plugins are removed; files without the provenance header are kept.
- Generate `~/.config/opencode/AGENTS.md`: full copy of shared `AGENTS.md` plus an OpenCode-specific supplement owned by the script itself. For duplicate shared/Claude skill names, explicitly read the verified shared source; this is an instruction, not a loader-precedence setting. The supplement selects an execution path from the skill's requirements and available tools; skill names or stage counts do not create a blanket prohibition. Required independence, model choices, permissions and unsupported native features remain explicit.
- Remove previously generated `~/.config/opencode/agents/*.md` that carry the AUTO-GENERATED header. No agents are generated; delegation uses OpenCode's standard agents.
- Support `bash etc/sync-opencode.sh --check` (no write; exit non-zero if generated outputs would change or a generated agent would be removed).

Default `bash etc/sync-opencode.sh` does **not**:

- Generate agents or per-agent permissions. Read-only instructions to delegated agents are behavioral boundaries; the generated AGENTS.md supplement states this explicitly.
- Create repo-side native overlays (`.opencode/**` other than plugins). OpenCode stays generated under `~/.config/opencode/**`.

Contract test: `bash etc/test-opencode-contracts.sh` (live `--check`, fake-HOME fresh sync + idempotency, MCP/permission shape, supplement sections, stale-reference regression, orphan cleanup + hand-written protection). It is included in the `etc/test-all-contracts.sh` aggregate runner.

This adapter does not register skills in `opencode.json`. Discovery uses `~/.agents/skills/**` and `~/.claude/skills/**`; `etc/link.sh` links the shared skill directory at `~/.agents/skills`.

## Grok runtime boundary

Grok uses shared project guidance and its own `.grok/rules/runtime.md`.
`etc/link.sh` links individual native rules into `~/.grok/rules` without
replacing real user files or unrelated links. It does not generate Grok
credentials, model settings, permission policy or MCP. It installs Jev-owned
observation hooks via `jev-hooks/install.py`, preserving other hook entries.

Grok can discover shared `.agents/skills` and vendor-compatible Cursor/Claude
skills. Compatibility discovery does not make their tool names, model IDs or
agent roles native Grok interfaces. The Grok rule preserves portable intent
while requiring the actual Grok tool schema for execution. Existing Grok
models and compatibility settings remain user-owned; the Codex model ladder
and Cursor Fable exception do not apply to Grok.

`grok inspect --json` checks discovery without starting a model task. Inspect
output can include sensitive configuration; expose only needed path/name and
compatibility fields. Foreign-session resume is explicit and does not confer
authority from historical instructions.

## sync-antigravity.sh Contract

Default `bash etc/sync-antigravity.sh` does:

- Generate `.gemini/config/rules/shared-agents.md` as a **summary + SSOT pointer** to `AGENTS.md` (not a full copy).
- Generate `.gemini/config/mcp_config.json` from `mcp-servers.json` (excluding `claudeCodeOnly`, `openCodeOnly`, `codexOnly`, `cursorOnly`, and `devinOnly` servers).
- Warn if the native `.gemini/config/hooks.json` or `.gemini/config/scripts/auto-gate.py` is missing; request executable permissions for the script during generation. This adapter does not validate the native hook schema. `etc/test-auto-gate.py` verifies the configured command and gate behavior.
- Ensure `.gemini/config/skills` symlink points to `.agents/skills`.
- Support `bash etc/sync-antigravity.sh --check` (no write; exit non-zero if generated outputs would change).

`etc/link.sh` deploys Antigravity configuration to `~/.gemini/config/` and symlinks `~/.agents/skills` to ensure all shared skills are discovered.
If Antigravity sync or any required link operation fails, `etc/link.sh` exits
nonzero and does not report the deployment as complete.

## Optional Jev judgments

`jev-hooks/` owns the shared API client, bounded policies, runtime adapters, and local usage reports. `etc/sync-codex.sh`, `etc/sync-cursor.sh`, `etc/sync-devin.sh` and Grok deployment register their supported entrypoints. `TYPESAFE_API_KEY` is read only from the process environment; without it the shell entry returns immediately without Python, network or state writes. API failures and missing optional ai-ltm integration preserve the original action.

Codex receives skill suggestions and tool/subagent feedback through supported additional context events. Cursor receives post-tool feedback and bounded Stop continuations. Grok hooks observe supported tool events; passive hook output is not treated as model context. Devin retains its bounded Stop adapter. New tool checks are advisory and do not widen permissions or rewrite tool input. Completion checks cover requested answers/plans as well as implementation, while honoring user stops and genuine blockers.

Jev request metadata and estimated USD are recorded once per request in `usage.sqlite3`. Unknown usage or model pricing remains unknown. Reports contain no conversation or secret values. ai-ltm recall delivers bounded candidate content to the main agent; optional Jev annotations describe relevance and conflicts without removing or reordering candidates. The main agent chooses which memories to apply. Record classification advises the caller without saving or deleting data.

設定・利用量・推定費用の詳細は[jev-hooks/README.md](jev-hooks/README.md)。

## 同期の実行範囲と復旧

`git-sync` / `dotfiles-autosync`の依頼は、対象内の通常のWIP保全、競合統合、関連生成物・ホーム配備の整合、検証、commit・pushまでを含む。`git-sync`は本体同期のあと、同じターンで`check-updates`を実行する。手での`git pull`に置換しない。親はこれらを工程ごとに再承認させず、実コンテンツやgitlinkの競合も双方の意図を保持して統合する。共通手順は`.agents/skills/git-sync/SKILL.md`に置き、dotfilesは中央engine`etc/dotfiles-autosync.sh`を使う。

engineの非ゼロ終了とmarkerは失敗を正確に伝える境界であり、親の作業終了条件ではない。親はhook・generator・配備・通信等の原因を解消し、進行中操作を完了してengineへ戻る。既存のバックアップ・配備関数を使い、hook無効化や無条件retryを追加しない。実アクセス制御、送り先の未確定、保全不能など依存操作を実行できない条件だけを具体的に報告し、独立した作業は継続する。

`check-updates`は明示したSkill/plugin root内の独立cloneを既存upstreamへclean fast-forwardする。dotfiles・submodule同期やcommit/pushはその操作に含めない。

## 公開仕様の確認

公開runtime仕様を確かめる必要があるときは[Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)、[Cursor subagents](https://cursor.com/docs/subagents)、[Cursor skills](https://cursor.com/docs/skills)、[Claude Code subagents](https://code.claude.com/docs/en/sub-agents.md)等の公式資料と、実際の公開起動schema・local configを照合する。API機能とruntime設定を混同せず、設定整理だけでアプリのAPI移行を開始しない。
