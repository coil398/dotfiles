# AI Workflow Architecture Spec

この文書はdotfilesのAgent / Skill運用の設計と保守方針の正本である。共有の責任・専門知識・結果の意味を揃え、Codex、Cursor、Claude Code、OpenCode、Grok、Antigravityの固有の実行方式を保持する。個々のSkill全文やモデル表を再掲せず、実行時に読む原本へ案内する。

## 責任と読者

| 要素 | 責任 | 原本の置き場所 |
|---|---|---|
| 親の進行用Skill | 対象・範囲・完了条件、資料と担当の選択、配分、結果統合、次の処理、最終判断 | `.agents/skills/<name>/SKILL.md`。runtime固有の進行はnative package |
| 実行者用Skill / reference | 割り当てられた仕事の専門手順、評価基準、必要資料、返却内容 | 既存Skillの`references/`、または独立して再利用する実行者Skill |
| 今回のタスク指示 | 対象版、目的、確定事実、所有範囲、制約、重点、完了条件、資料の実体パス | 親から各担当へ渡す入力 |
| runtime設定・入口 | 公開起動API、モデル・推論量、権限、ツール、発見・互換性 | runtimeのconfig、native supplement、必要な短い入口 |
| scripts / CI | 決まった変換、ビルド、再現、検証、生成・配布 | 既存の`etc/`または担当Skillの`scripts/`・`tests/` |
| 運用文書 | 設計、原本の所在、使い方、保守方法、必要な例外 | 本文書。READMEは入口 |

親がSkillを切り替えることは新しい司令塔の起動ではない。同じ親が、必要な段階の手順を読む。専門知識を毎回長いタスク指示に作り直さず、短い単発作業や親だけで完結する対話・定型操作に不要なSkillや親子分割を加えない。常時必要な制約は[AGENTS.md](AGENTS.md)に置く。

### 誰が何を読むか

| 場面 | 親 | 実行者 |
|---|---|---|
| 親が委任する | 進行手順、担当選択の説明、入出力、結果契約、runtime方針を読む。専門本文を委任のためだけに先読みしない | 渡された専門Skillと必要referenceを自身で読む |
| 親が直接実行する | 実行者として該当する専門手順・必要referenceを読む | 親自身 |
| 親が結果を統合する | 返却と根拠を照合し、判定の対立や不足を確かめるために必要な専門部分を読む | 根拠、確認範囲、未確認を返す |

親はロードしたSkillの実体を起点に、子から読める原本パスを解決して渡す。対象repoのcwdに個人Skillがあること、親の読込状態が子へ継承されること、同名Skillの自動選択には依存しない。解決方法と副作用・階層委任の常時規則は[AGENTS.mdの作業の配分とSkill](AGENTS.md#作業の配分とskill)に従う。

通常の実行者へ親用の配分Skillを渡して工程を再起動させない。明示的な協働用途は既存の親が範囲・起動権限・統合責任を限定する。readerの結果は親へ返し、必要な保存は親または許可済みwriterが行う。ビルドやテストの生成物も書き込みとして扱う。文章上の変更禁止、runtimeによるアクセス拒否、外部ツールの権限は別の事実である。

## 原本と参照関係

| 内容 | 正本 |
|---|---|
| 常時の作業・権限・委任境界 | [AGENTS.md](AGENTS.md) |
| レビュー対象・観点の解釈、配分、独立性、統合手順 | [reviewer](.agents/skills/reviewer/SKILL.md) |
| 実際の評価と観点別の専門基準 | [code-review-guidance](.agents/skills/code-review-guidance/SKILL.md)とそのreference |
| COVERAGE / VERDICT、重大度・完了阻害性、未完了・集約の意味 | [result-contract.md](.agents/skills/code-review-guidance/references/result-contract.md) |
| テスト選択・実行 | [tester](.agents/skills/tester/SKILL.md)と[test-procedure.md](.agents/skills/tester/references/test-procedure.md) |
| 調査・分析・仮説の専門知識 | [research](.agents/skills/research/SKILL.md)の担当reference |
| 振り返りの専門知識 | [retro](.agents/skills/retro/SKILL.md)の通常・meta reference |
| Codex通常設定 | [.codex/config.base.toml](.codex/config.base.toml) |
| Codex起動・モデル選択方針 | [native supplement](.codex/codex-native-supplement.md) |
| Codex native委任・明示CLIの入力と証跡 | [worker-delegation](.codex/skills/worker-delegation/SKILL.md)とrunner reference |
| Cursor通常モデル選択 | [AGENTS.mdのCursor Task方針](AGENTS.md#shared-core-and-native-overlays)。生成Rulesは参照用adapter |
| Cursor Fableの指定と失敗時の扱い | [fable-model.md](.cursor/skills/deepthink/references/fable-model.md) |
| MCP構成 | [mcp-servers.json](mcp-servers.json) |
| 生成・配布 | [sync-codex.sh](etc/sync-codex.sh)、[sync-cursor.sh](etc/sync-cursor.sh)、[link-codex-runtime.sh](etc/link-codex-runtime.sh)、[link.sh](etc/link.sh) |

PIR²、IR、debug、epic、review-prは共通レビューの入力を渡し、返却を消費する。観点一覧や判定規則を別に保守しない。研究の不確実性、リファクタ提案、Git同期、熟考の十分性は各手順固有の意味を持ち、評価の全体集約に参加する場合だけ共通結果契約へ接続する。

## 実行例

### PIR²からレビュー・テストへ

1. 同じ親が[pir2](.agents/skills/pir2/SKILL.md)を読み、対象版・要求・担当範囲を確定し、必要な実装を進める。
2. レビュー段階で親が[reviewer](.agents/skills/reviewer/SKILL.md)を読む。対象diff、受入条件、ユーザーが指定した観点と独立性をそのまま渡して担当を決める。
3. 評価子には`code-review-guidance/SKILL.md`の実体パス、選択したreference、対象と今回の重点を渡す。子が専門原本と共通結果契約を読み、対象を評価して親へ返す。
4. 親が根拠と結果を統合する。直接評価する部分があれば親もその専門原本を読む。修正後は影響した範囲を再確認する。
5. 親が[tester](.agents/skills/tester/SKILL.md)の進行を使い、実行者に`test-procedure.md`と実在するコマンド・許可した出力範囲を渡す。評価と実行結果を区別して完了を判断する。

必要な観点と子の人数は別の入力である。複数観点を一つの実行者が扱う場合と、明示的な五観点独立評価を別コンテキストへ分ける場合の選択はreviewerの正本に従う。枠数を満たすこと自体を目的にしない。

### research

親が[research](.agents/skills/research/SKILL.md)で問いと範囲を確定する。探索・技術比較を分ける場合は、それぞれ`references/explorer.md`・`tech-validator.md`の実体パスと具体的なサブ問いを担当へ渡す。集約した証拠の分析や仮説を分けるなら`thinker.md`・`hypothesizer.md`を使う。各子が自身の専門資料を読み、事実と推測・不確実性を返す。親が直接分析する場合も同じ専門資料を読む。保存する研究レポートは親が統合する。

### retro

親が[retro](.agents/skills/retro/SKILL.md)で対象の実績と明示されたモードを確定する。通常分析には`references/retrospector.md`、明示metaには`meta-retrospector.md`の実体パスを渡す。子は分析を返し、親が採否・許可された変更・保存を判断する。親自身が分析する場合は対応referenceを読む。記憶・registryの有無を推測で補わず、通常の振り返りから勝手にworkflow骨格の変更へ拡張しない。

### Cursor deepthink

親が[Cursor deepthink](.cursor/skills/deepthink/SKILL.md)とモデル正本`references/fable-model.md`を読む。single / panelで選んだ熟考担当に`deliberator.md`の実体パスと問い・入力・レンズを渡し、担当が読む。親自身が統合・十分性確認を行う場合は`synthesizer.md`・`gate.md`を読み、その仕事を委任する場合は各実体パスを担当へ渡す。Fable指定を別モデルや親だけの熟考で代替せず、利用できない場合の扱いはnative手順へ従う。

### 短い通常作業と親の直接評価

小さな単発修正は具体的なタスク指示と関連確認で完結できる。独立評価が不要で親が評価を担当するなら、親が`code-review-guidance`と必要referenceを読む。短い作業のために全専門資料、別司令塔、多重のplan/reportを作らない。

## 管理対象Skill一覧

`S`は`.agents/skills`、`C`は`.codex/skills`、`X`は`.cursor/skills`。各行は一つの用途を持つbasenameであり、「入口」は実在する`SKILL.md`の配置を示す。空directoryやsupport referenceだけのdirectoryは入口として数えない。資料の相対名は、その行の共有packageを起点とし、X専用と明記したものはnative packageを起点とする。親自身が実行者となる場合も実行者資料を読む。

| Skill | 入口 | 用途 | 主な読者 | 実行者が読む資料 | runtime差分 | 維持する例外 |
|---|---|---|---|---|---|---|
| `agent-skill-migrate` | [S](.agents/skills/agent-skill-migrate/SKILL.md) / [X](.cursor/skills/agent-skill-migrate/SKILL.md) | 指定repoの運用整理 | 親 | 各対象が使う既存専門原本 | Xは共有進行入口 | 明示起動専用。対象外repoを変更しない |
| `ai-design-system` | [S](.agents/skills/ai-design-system/SKILL.md) / [X](.cursor/skills/ai-design-system/SKILL.md) | design SSOTの生成・監査・維持 | 直接実行者／配分する親 | BOOTSTRAP / AUDIT / AESTHETIC等、選択したモード資料 | Xは共有資料へ接続 | audit-onlyと生成・修正を区別 |
| `ai-diary` | [S](.agents/skills/ai-diary/SKILL.md) / [X](.cursor/skills/ai-diary/SKILL.md) | 会話から日記を保存 | 直接実行する親 | 本文 | Xは共有入口 | ユーザーが求める日記出力。readerに保存を要求しない |
| `ai-ltm` | [S](.agents/skills/ai-ltm/SKILL.md) / [X](.cursor/skills/ai-ltm/SKILL.md) | 長期記憶の検索・記録・同期 | 親／限定したrecall実行者 | session_recall.py、vector_search.py等 | Xは共有入口 | 既存DBと非同期recall、writerの同期境界 |
| `brainstorm` | [S](.agents/skills/brainstorm/SKILL.md) / [X](.cursor/skills/brainstorm/SKILL.md) | 対話で要件・設計を明確化 | 親 | 必要時research探索・writing-plan計画reference | Xは共有専門資料へ接続 | 親の対話を不要に分割しない |
| `chat` | [S](.agents/skills/chat/SKILL.md) / [X](.cursor/skills/chat/SKILL.md) | 根拠を伴う深掘り対話 | 親 | 必要時researchの担当reference | Xは共有専門資料へ接続 | 短い対話は直接返す |
| `check-updates` | [S](.agents/skills/check-updates/SKILL.md) / [X](.cursor/skills/check-updates/SKILL.md) | 明示root内cloneの更新 | 直接実行者 | scripts/check-updates.sh | Xは共有engineへの入口とroot候補 | 独立cloneのclean fast-forward。dotfiles同期と別 |
| `code-review-guidance` | [S](.agents/skills/code-review-guidance/SKILL.md) / [X](.cursor/skills/code-review-guidance/SKILL.md) | 割当範囲の専門評価 | 評価者（親の直接評価を含む） | result-contract＋選択した観点reference | Xは共有評価への入口 | 配分・追加担当起動をしない |
| `codex` | [S](.agents/skills/codex/SKILL.md) / [C](.codex/skills/codex/SKILL.md) / [X](.cursor/skills/codex/SKILL.md) | Codexへの限定相談 | 親／相談実行者 | 選択した相談の専門資料、CLI時のbridge手順 | Sは汎用相談、Cはnative、Xは外部CLI | 明示された別runtimeの実行証拠を保持 |
| `debug` | [S](.agents/skills/debug/SKILL.md) / [X](.cursor/skills/debug/SKILL.md) | 再現・原因特定・修正 | 親 | 調査reference、reviewer接続、tester実行者資料 | Xはruntime進行差分 | 実測から修正し、影響範囲を再確認 |
| `deepplan` | [S](.agents/skills/deepplan/SKILL.md) / [X](.cursor/skills/deepplan/SKILL.md) | 計画を深く検討 | 親 | writing-plan planner、必要な調査reference | Xはdeepthink/Fable経路 | Codexは親が計画を所有。C deepthinkを要求しない |
| `deepthink` | [X](.cursor/skills/deepthink/SKILL.md) | 指定モデルによる熟考 | 親＋熟考・統合・十分性確認担当 | X referencesのdeliberator / synthesizer / gate、親はfable-model | X専用 | Fable必須single / panel、親の直接統合も専門手順を読む |
| `design-review` | [S](.agents/skills/design-review/SKILL.md) | 外部design正本に基づく評価 | レビューを進める親 | bootstrapから解決したcanonical Skill・必須基準 | Sから既存Claude bootstrapへ接続。X固有入口なし | S用入口と既存Claude互換入口を保持。Cursorでの発見は実機未確認 |
| `dotfiles-autosync` | [S](.agents/skills/dotfiles-autosync/SKILL.md) / [X](.cursor/skills/dotfiles-autosync/SKILL.md) | dotfilesの明示同期 | 直接実行する親 | etc/dotfiles-autosync.sh | Xは共有入口 | 既存engineの保全・merge・push境界 |
| `epic` | [S](.agents/skills/epic/SKILL.md) / [X](.cursor/skills/epic/SKILL.md) | 大型作業の分割・統合 | 親 | references/decomposition、各単位の専門資料 | Xは協働起動差分 | 所有とDAG、必要な長期再開 |
| `field-notes` | [S](.agents/skills/field-notes/SKILL.md) / [X](.cursor/skills/field-notes/SKILL.md) | 短期の判断を記録・再利用 | 親 | 本文、選択した既存note | Xは共有入口 | LTM・日記と二重記録しない |
| `geminify` | [X](.cursor/skills/geminify/SKILL.md) | 読みにくい日本語を Gemini 3.8 Flash で人間向けに書き直す | 親 | X scripts/geminify.py | X専用 | 親は言い換えず Gemini 出力をそのまま返す。キーは GEMINI_API_KEY |
| `git-sync` | [S](.agents/skills/git-sync/SKILL.md) / [X](.cursor/skills/git-sync/SKILL.md) | 現在repoの明示同期 | 直接実行する親 | 本文、必要時競合の専門資料 | Xは共有入口 | 上流・未コミット変更・許可済pushの境界 |
| `instruction-refactor` | [S](.agents/skills/instruction-refactor/SKILL.md) / [X](.cursor/skills/instruction-refactor/SKILL.md) | 指示の責任・重複を整理 | 親／割当範囲の評価者 | references/checklist、strategies、official-criteria | Xは共有資料へ接続 | 再編そのものが用途。別の運用全監査へ広げない |
| `ir` | [S](.agents/skills/ir/SKILL.md) / [X](.cursor/skills/ir/SKILL.md) | 小さな変更と確認 | 親 | reviewer接続、tester実行者資料 | Xはruntime進行差分 | 短い作業に多重の記録を強制しない |
| `overlay-audit` | [S](.agents/skills/overlay-audit/SKILL.md) / [X](.cursor/skills/overlay-audit/SKILL.md) | Skill / Agentの配置点検 | 直接実行者 | etc/audit-skill-agent-layout.py | Xはruntime root解決 | 配置の証拠と実モデル・権限の観測を区別 |
| `pir2` | [S](.agents/skills/pir2/SKILL.md) / [X](.cursor/skills/pir2/SKILL.md) | 実装全体の進行 | 親 | 必要な実装資料、reviewer、tester、retro接続 | Xはnative進行、Cはsupport referenceのみ | 同じ親が工程を切り替え、長期再開を保持 |
| `pir2async` | [S](.agents/skills/pir2async/SKILL.md) / [X](.cursor/skills/pir2async/SKILL.md) | 明示的な協働実装 | 親／限定された作業単位 | 共有pir2と各単位の実行者資料 | Xの協働機構 | 明示協働の範囲・起動権限・統合責任を保持 |
| `pir2codex` | [X](.cursor/skills/pir2codex/SKILL.md) | 外部Codexへ実装を委任 | Cursorの親／CLI実行者 | CLI bridge手順、今回のtask / requirements | X専用外部CLI | 既存artifact・provenance・完了確認 |
| `refactor-advisor` | [S](.agents/skills/refactor-advisor/SKILL.md) / [X](.cursor/skills/refactor-advisor/SKILL.md) | 改善候補を提案 | 親＋提案担当 | references/refactor-guidance | Xは共有専門資料へ接続 | 提案数・優先度をレビュー合否と混同しない |
| `research` | [S](.agents/skills/research/SKILL.md) / [X](.cursor/skills/research/SKILL.md) | 調査・分析・仮説形成 | 親＋担当実行者 | references/explorer、tech-validator、thinker、hypothesizer | Xは共有専門資料へ接続 | 出典・反証・不確実性という研究固有の結果 |
| `retro` | [S](.agents/skills/retro/SKILL.md) / [X](.cursor/skills/retro/SKILL.md) | 実績から学び・改善を抽出 | 親＋分析担当 | references/retrospector、meta-retrospector | Xは共有専門資料へ接続 | 明示meta / dream、既存の保存と変更権限 |
| `review-pr` | [S](.agents/skills/review-pr/SKILL.md) / [X](.cursor/skills/review-pr/SKILL.md) | PRの取得とレビュー接続 | 親 | 共有reviewer、評価子はcode-review-guidance | XはPR取得のnative入口 | 確定したbase/headを渡し、公開操作は別の許可 |
| `reviewer` | [S](.agents/skills/reviewer/SKILL.md) / [X](.cursor/skills/reviewer/SKILL.md) | レビュー対象・配分・統合 | 親 | result-contract、子または直接評価者がcode-review-guidance | Xは共有進行への入口 | 観点・独立性の正本 |
| `sentinel-review` | [S](.agents/skills/sentinel-review/SKILL.md) / [X](.cursor/skills/sentinel-review/SKILL.md) | IaCの専門評価 | 親＋IaC評価者 | references/findings-schema、redaction、対応評価基準 | Xは共有専門資料へ接続 | IaC findings schemaを保持し集約へ接続 |
| `tester` | [S](.agents/skills/tester/SKILL.md) / [X](.cursor/skills/tester/SKILL.md) | テスト選択・実行・結果統合 | 親＋テスト実行者 | references/test-procedure、実在する試験手順 | Xは実行条件の入口 | 許可済の一時出力生成と既存データ変更を区別 |
| `unity-mcp-skill` | [S](.agents/skills/unity-mcp-skill/SKILL.md) / [X](.cursor/skills/unity-mcp-skill/SKILL.md) | Unity Editorの専門操作 | 直接実行者／配分する親 | references/tools-reference、workflows、指定project資料 | Xは共有専門資料へ接続 | 実在MCP・project wrapper・Editorの操作境界 |
| `walkthrough` | [S](.agents/skills/walkthrough/SKILL.md) / [X](.cursor/skills/walkthrough/SKILL.md) | コード理解と説明 | 親／読取担当 | research探索資料、references/html-modeとtemplate | Xは共有専門資料へ接続 | 明示HTML、既存の保存・再開 |
| `worker-delegation` | [C](.codex/skills/worker-delegation/SKILL.md) | 具体作業の委任・明示runner | Codexの親／指定実行者 | runner利用時だけreferencesとscripts | C固有 | 通常native委任とCLI固有証跡を分離 |
| `writing-plan` | [S](.agents/skills/writing-plan/SKILL.md) / [X](.cursor/skills/writing-plan/SKILL.md) | 計画と実施記録 | 親 | references/planner、必要な調査資料 | Xは共有専門資料へ接続 | 計画責任は親。長期記録と短い作業を区別 |

### 管理外入口

.claude/skills/design-reviewの既存bootstrapはSの外部正本解決にも使う。X固有のdesign-review入口は設けず、Cursorでの互換発見は実機の確認範囲として区別する。

Claude専用Skill・Agent、OpenCodeのClaude由来本文、`.system`、インストール済み外部plugin・個人Skillはこの一覧の移行対象ではない。互換発見されても管理対象へ自動編入しない。design-reviewが案内する外部design repoやUnityのプロジェクト固有wrapperも外部原本として扱い、取得・実操作の可否を区別する。

## runtimeと生成・配布

### Codex

共有Skillは`.agents/skills`から直接発見する。Codex固有の相談入口とCLI runnerを`.codex/skills`に置き、専門職・モデル別の独自Agent集合は要求しない。標準子の選択と公開引数の使い方はnative supplement、通常値はconfig baseを読む。専門Skillと本書にモデル表を複製しない。

`etc/sync-codex.sh`はconfig base・MCP原本から`.codex/config.toml`を生成し、共有AGENTSとnative supplementから`.codex/AGENTS.md`を生成する。設定の信頼・認証・承認境界は既存の生成処理が保全する。native Agent/Skillを他runtimeの本文から再作成しない。

補助文書の生成元は同scriptが所有する。長期再開の`.codex/pir-handoff.md`・`.codex/pir2-protocol.md`は`.codex/skills/pir2/references/`のnative support原本を使う。このdirectoryにSkill入口はなく、共有PIR²の別コピーを意味しない。UI/UX評価は共有専門資料を読む。

`etc/link-codex-runtime.sh`は管理対象config・support文書・Agent directory・実在する固有Skillをhomeへリンクする。孤児の管理Skillリンクを清掃し、管理外リンク・個人Skillは保持する。名前だけのdirectoryから入口を配布しない。named profileと`codex-motitan`は明示用途の既存入口であり、通常設定の変更を意味しない。

### Cursor

`.cursor/skills`の入口は`etc/link.sh`で`~/.cursor/skills`へ実体コピーする。共有専門資料はnative入口の実体から解決し、別配置では親が確認した実体パスを使う。`.cursor/{agents,rules,mcp.json}`は既存のリンク・保全手順に従う。

`etc/sync-cursor.sh`は`AGENTS.md`への参照を持つ要約Rulesと、MCP原本から`.cursor/mcp.json`を生成する。RulesはAGENTS全文のコピーではない。native Skill/Agent本文は再生成しない。slash名とdirectory名は一致させる。

Taskは公開された起動APIとAGENTSのモデル方針を使う。`.cursor/agents`の短い入口は、同名の他runtime互換定義が選ばれるのを制御し、必要なreadonly設定と共有実行者資料へ接続する。標準Taskを妨げる職種別の固定モデル表にしない。`.cursor`の同名優先を利用し、readonlyという名前やfrontmatterから外部MCP全体の隔離を推測しない。

User Rulesの登録はCursor Settings → Customize → Rules → Userで行う。登録した規則が実際のdotfilesの`AGENTS.md`、homeの共有Rules、作業先AGENTSを参照することを確認する。ファイルの配布・`--check`だけでUI登録済みとは扱わない。

### 維持する固有差分

| 差分 | 理由 | 保守場所 |
|---|---|---|
| Cursor Fable熟考 | 指定モデルによるsingle / panelの思考が用途そのもの | `.cursor/skills/deepthink`、Cursor deepplan |
| Cursorの短いAgent / Skill入口 | 互換発見・readonly・Task固有の接続 | `.cursor/agents`、`.cursor/skills` |
| Codex標準子とCursor Task | 実在する起動schemaとconfigの優先順位が異なる | Codex native supplement、AGENTSのCursor方針 |
| 明示CLI bridge | 外部Codex実行と必要な実行証拠 | `codex`、Cursor `pir2codex`、Codex `worker-delegation` |
| PIR² native supportとasync | 長期再開・既存成果物consumer・明示協働 | Codex PIR² support、各runtimeの`pir2async` |
| 記憶・同期・専門操作 | 既存DB・同期境界・外部正本・固有出力 | 該当Skillとscript。reviewer形式を一律適用しない |

## 追加先と保守方法

| 追加したい内容 | 置き場所 |
|---|---|
| 常時または特定pathで守る制約 | AGENTS / 生成Rulesの原本 |
| 対象確定・配分・統合という一つの進行用途 | 既存の親Skill。別用途として独立するときだけ新規Skill |
| 既存の用途の専門手順・長い資料 | 既存packageのreference |
| 複数の進行から同じ仕事を直接依頼する専門手順 | 再利用する実行者Skill |
| 一回限りの対象・重点・確定事実 | 今回のタスク指示 |
| 決まった変換・ビルド・検証 | 既存script / test / CI |
| 標準起動引数で表現できない実行条件、互換入口 | 必要な短いcustom Agent / native入口 |

Skillの長さ・file数・階層や`writer` / `reader`という名前を統一条件にしない。新規作成前に既存構造を確認し、同義Skill、モデル別Agent、専門知識の二重原本を増やさない。

### 変更時の最小確認

1. 主な読者、専門原本、呼出先、結果の消費先と今回の差分を確認する。委任と直接実行の読込が接続しているか、未使用referenceや子の親工程再起動がないか読む。
2. 変更した挙動だけ代表確認する。観点選択・独立性・未確認伝播・限定再評価を変更した場合は該当ケースを含める。scriptは関連する既存試験を使い、必要な失敗ケースを最小追加する。
3. 相対参照は実体から解決し、Markdown・metadata・生成元/生成物・配布先を確認する。ファイル数や文字列一致だけを意味の正しさと扱わない。
4. 生成・配布に影響する原本を変更した場合だけ、下表の処理を実行する。新しいSkillの発見は新規セッションで確認する。
5. 実行したコマンドと結果、未確認、残る例外を報告し、許可されたGit操作だけ行う。

| 変更した原本 | 必要な生成・配布 |
|---|---|
| 共有Skill / reference | Codexは共有リンクから読む。Cursor入口に変更があればmaterialize。入口の追加削除は発見・seed/checkerを確認 |
| Codex config / AGENTS / native supportの生成元 | `bash etc/sync-codex.sh`。homeリンクは`bash etc/link-codex-runtime.sh` |
| Cursor Rules / MCPの生成元 | `bash etc/sync-cursor.sh`。native入口の配布はlink.sh |
| Codex・Cursorをまとめて反映 | `bash etc/link.sh --codex-cursor-only` |
| 他runtimeの生成元にも影響する共有原本 | 当該runtimeの既存syncを使い、その専用本文や設定へ移行を広げない |

配布は既存のbackup・リンク保全・materializeを使う。seedは欠けた専門本文を他runtimeから再構築せず、意図的な入口省略を保つ。`check-shared-drift.sh`と`audit-skill-agent-layout.py`は原本とruntimeの有効な配置を確認し、固定のAgent集合を必須にしない。自動syncの対象選択は既存hookが持ち、生成が依存する原本変更に限定する。

### 別リポジトリへの適用

既存の[agent-skill-migrate](.agents/skills/agent-skill-migrate/SKILL.md)を明示的に使う。例: `$agent-skill-migrate mode=apply runtime=both scope=repo`に、対象repoと今回の要件を渡す。個人共通設定を変えるときだけ`scope=dotfiles`を選ぶ。

現在のHEAD・未コミット変更・既存文書から開始し、管理対象の実体を列挙する。既存の専門知識・結果契約・有効な入口を保持して責任と参照先を揃え、必要な生成配布と代表確認を行う。対象repoの正式文書とREADMEへ現行形を残す。dotfilesの固定パス・人数・モデル別定義をコピーせず、管理外pluginや未指定repoへ範囲を広げない。

### 実装と確認の区別

原本・参照・configが存在することを「実装済み」、コマンドや実際の処理結果を観測した範囲を「実行確認済み」、利用できないruntime・model metadata・外部アプリ等を「未確認」と分ける。配置確認とTask実行、行動上の禁止と技術的権限は別の確認である。今回の証拠とGit状態は[統一作業の完了報告](AI-WORKFLOW-UNIFICATION-REPORT.md)に記録する。

## 他runtimeの境界

Claude Codeは`.claude`の専用本文と設定を使い、Codex/Cursorから逆生成しない。共通文書・adapter hookの関連変更では有効な専用入口を保持する。以下は各runtimeの既存生成・発見契約であり、Codex/Cursorの標準子設計をそのまま移植しない。

## sync-opencode.sh Contract

Default `bash etc/sync-opencode.sh` does:

- Generate `~/.config/opencode/opencode.json` from `mcp-servers.json` (excluding `claudeCodeOnly` and `codexOnly`; `openCodeOnly` servers are included), an OpenCode-specific permission policy owned by the script (bash allow-by-default with dangerous-command asks, edit allow, read deny list inherited from `.claude/settings.json#permissions.deny`, and `external_directory: {"~/**": "allow"}` because OpenCode defaults it to ask and "always" approvals are session-scoped, which caused approval fatigue for any out-of-cwd reference; the Claude Code allow allowlist is intentionally not carried over), and `lsp: true` (OpenCode disables LSP when the key is omitted).
- Sync OpenCode plugins from the repo-native SSOT `.opencode/plugins/*` to `~/.config/opencode/plugins/` with a provenance header. OpenCode has no settings.json-style hooks; PreToolUse / PostToolUse / Stop equivalents are implemented as plugins (`tool.execute.before`, `tool.execute.after`, `session.idle`). Orphan cleanup and hand-written-file protection follow the same rules as agents.
- Generate `~/.config/opencode/AGENTS.md`: full copy of shared `AGENTS.md` plus an OpenCode-specific supplement owned by the script itself (tool-name remap table, skill availability classification, compatibility gaps, model alias mapping notes).
- Convert `.claude/agents/*.md` to `~/.config/opencode/agents/<name>.md`: frontmatter reduced to `description` / `mode: subagent` / `model` (bare aliases mapped by `map_model_name`: `sonnet`→`anthropic/claude-sonnet-5`, `opus`→`anthropic/claude-opus-4-8`, `fable`→`anthropic/claude-fable-5-1`); body copied verbatim. Orphan AUTO-GENERATED agents are removed.
- Support `bash etc/sync-opencode.sh --check` (no write; exit non-zero if generated outputs would change or an orphan agent would be removed).

Default `bash etc/sync-opencode.sh` does **not**:

- Convert agent-frontmatter `tools:` restrictions or per-agent permissions. Bodies claiming tools-based role isolation are not enforced by the runtime; the generated AGENTS.md supplement states this explicitly.
- Create repo-side native overlays (`.opencode/**`). OpenCode stays fully generated under `~/.config/opencode/**`; a native overlay remains deferred until runtime needs diverge.

Contract test: `bash etc/test-opencode-contracts.sh` (live `--check`, fake-HOME fresh sync + idempotency, MCP/permission shape, agent frontmatter + verbatim-body contract, supplement sections, stale-reference regression, orphan cleanup + hand-written protection). It is included in the `etc/test-all-contracts.sh` aggregate runner.

Skills are not registered via an `opencode.json#skills` key. Discovery relies on OpenCode's external-skill autoload of `~/.agents/skills/**` and `~/.claude/skills/**`, backed by the `~/.agents` symlink created by `etc/link.sh`.

## Grok runtime boundary

Grok uses shared project guidance and its own `.grok/rules/runtime.md`.
`etc/link.sh` links individual native rules into `~/.grok/rules` without
replacing real user files or unrelated links. It does not generate Grok
credentials, model settings, permission policy, MCP or hooks.

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
- Generate `.gemini/config/mcp_config.json` from `mcp-servers.json` (excluding `claudeCodeOnly`, `openCodeOnly`, `codexOnly`, and `cursorOnly` servers).
- Warn if the native `.gemini/config/hooks.json` or `.gemini/config/scripts/auto-gate.py` is missing; request executable permissions for the script during generation. This adapter does not validate the native hook schema. `etc/test-auto-gate.py` verifies the configured command and gate behavior.
- Ensure `.gemini/config/skills` symlink points to `.agents/skills`.
- Support `bash etc/sync-antigravity.sh --check` (no write; exit non-zero if generated outputs would change).

`etc/link.sh` deploys Antigravity configuration to `~/.gemini/config/` and symlinks `~/.agents/skills` to ensure all shared skills are discovered.
If Antigravity sync or any required link operation fails, `etc/link.sh` exits
nonzero and does not report the deployment as complete.


## 専門外の更新と公開仕様

`check-updates`は明示したSkill/plugin root内の独立cloneを既存upstreamへclean fast-forwardする。dotfiles・submodule同期やcommit/pushはその操作に含めない。dotfilesの同期は既存の`etc/dotfiles-autosync.sh`の明示用途に従う。

公開runtime仕様を確かめる必要があるときは[Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)、[Cursor subagents](https://cursor.com/docs/subagents)、[Cursor skills](https://cursor.com/docs/skills)等の公式資料と、実際の公開起動schema・local configを照合する。API機能とruntime設定を混同せず、設定整理だけでアプリのAPI移行を開始しない。

## 同期の実行範囲と復旧

`git-sync` / `dotfiles-autosync` の依頼は、対象内の通常のWIP保全、競合統合、関連生成物・ホーム配備の整合、検証、commit・pushまでを含む。`git-sync` は本体同期のあと、同じターンで `check-updates` を実行する。手での `git pull` に置換しない。親はこれらを工程ごとに再承認させず、実コンテンツやgitlinkの競合も双方の意図を保持して統合する。共通手順は `.agents/skills/git-sync/SKILL.md` に置き、dotfilesは中央engineを使う。

engineの非ゼロ終了とmarkerは失敗を正確に伝える境界であり、親の作業終了条件ではない。親はhook・generator・配備・通信等の原因を解消し、進行中操作を完了してengineへ戻る。既存のバックアップ・配備関数を使い、hook無効化や無条件retryを追加しない。実アクセス制御、送り先の未確定、保全不能など依存操作を実行できない条件だけを具体的に報告し、独立した作業は継続する。
