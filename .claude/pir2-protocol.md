# PIR² 系スキルの内部プロトコル

> このファイルは `~/.claude/CLAUDE.md` 「エージェント関連ルール」節のうち、PIR² 系スキル（/pir2, /pir2async, /debug, /ir 等）の実行時にのみ必要な内部プロトコルの詳細。**PIR² 系スキル実行時・UI 変更を含むタスク・チーム作業指示時に Read すること**。各担当固有の挙動ルールは、下記「担当の起動方法」の手順ファイル側に集約されている。

## 担当の起動方法

各担当は `Agent({ subagent_type: "general-purpose", model: <下表のmodel>, prompt })` で起動する。プロンプト先頭に「次の手順ファイルを先にReadし、その範囲だけ行う: <手順path>」を置き、続けて各スキルが定める入力変数・出力path指示を渡す。読み取り専用の担当には、プロンプトに「対象コード・設定・git・記憶を変更しない。出力pathが指定された場合だけそのpathへ書く」を含める。

| 担当 | model | 手順path | 権限 |
|---|---|---|---|
| explorer | sonnet | `~/.agents/skills/research/references/explorer.md` | 読み取り専用 |
| planner | opus | `~/.claude/skills/pir2codex/references/planner.md` | 読み取り専用（plan出力pathへの書込のみ） |
| implementer | sonnet | `~/.claude/skills/pir2codex/references/implementer.md` | 読み書き（所有範囲のみ） |
| reviewer | sonnet | `~/.agents/skills/code-review-guidance/SKILL.md`、`~/.agents/skills/code-review-guidance/references/result-contract.md`、担当観点の `~/.agents/skills/code-review-guidance/references/<観点>.md` | 読み取り専用 |
| ui-ux-reviewer | sonnet | reviewer と同じ2ファイル＋`~/.agents/skills/code-review-guidance/references/ui-ux.md` | 読み取り専用 |
| tester | sonnet | `~/.agents/skills/tester/references/test-procedure.md` | 読み書き（テスト出力・一時fixtureのみ） |
| refactor-advisor | sonnet | `~/.agents/skills/refactor-advisor/references/refactor-guidance.md` | 読み取り専用 |
| retrospector | opus | `~/.agents/skills/retro/references/retrospector.md` | 読み取り専用（指定レポートpathのみ） |
| meta-retrospector | opus | `~/.agents/skills/retro/references/meta-retrospector.md` | 読み取り専用（指定レポートpathのみ） |

## チーム運用

- 「エージェントチーム」「チームで作業」等の指示があった場合、Subagents ではなく Agent Teams 機能（`TeamCreate` ツールで構成する）を使うこと
- エージェント間で共有コンテキストを持ち、相互にメッセージングできる構成にすること
- 単に複数のサブエージェントを順次起動するだけの構成は「チーム」とみなさない

## サブエージェント間のファイル経由受け渡し

PIR² 系スキル（/pir2, /pir2async, /debug）では、explorer / planner / implementer / reviewer / tester の各サブエージェントが成果物本体を `${PROJECT_ROOT}/.ai-pir-runs/<YYYYMMDD-HHMMSS>-<feature>/` 配下のファイルに書き出し、呼び出し元（スキル本体）には**要約とファイルパスのみ**を返す方式を採用している。`.ai-pir-runs/` はプロジェクトローカル（`${PROJECT_ROOT}/.ai-pir-runs/`）に置く。プロジェクト配下は通常 sensitive-file 扱いされず、`.gitignore` で git 追跡外にする。retrospector 用の累積ログ（`pir_*_log.md`）は従来どおり `{PROJECT_MEMORY_DIR}/` に残す（`~/.claude/projects/` 配下・プロジェクト横断で参照するため別系統）。

目的:
- telephone-game effect（Anthropic 公式推奨の用語）の回避: オーケストレーターの context に各段階の全文が載ると後段で情報が欠落・歪曲する
- メイン Claude の context 肥大抑制: サマリー＋パスだけ保持し、必要な段で該当ファイルを Read する

運用ルール:
- スキル本体は各サブエージェント起動時に `RUN_DIR=[絶対パス]` と連番（`EXPLORATION_INDEX` / `IMPL_INDEX` / `REVIEW_INDEX` / `TEST_INDEX`）をプロンプトで渡す
- サブエージェントは成果物を `{RUN_DIR}/<kind>-<NN>.md` に書き出し、返り値は各手順ファイルの返り値フォーマットに従う
- 次段エージェントへの入力は「前段の本文」ではなく「前段が書き出したファイルのパス」で渡す。次段は必要に応じて自分で Read する
- `${PROJECT_ROOT}/.ai-pir-runs/` 配下は **per-run の内部ファイル**でユーザーには見せない。retrospector 用の累積ログ（`{PROJECT_MEMORY_DIR}/pir_*_log.md`）とは別系統で共存する

## PIR² 引継ぎ (handoff.md)

PIR² 系スキル（/pir2, /pir2async, /debug）は、複数回の実行にまたがる大きなタスクを引き継ぐために `${PROJECT_ROOT}/.ai-pir-runs/handoff.md` を使う。詳細プロトコル（ファイル位置・フォーマット・ライフサイクル・resume モード検知・誤参照防止ルール）は **`~/.claude/pir-handoff.md`** に分離した。スキル本体・planner・implementer・retrospector は handoff 関連の挙動判断で必ずこのファイルを参照すること。

## planner の能動的再探索ループ

planner は追加探索を2通りで行える（ハイブリッド）。**(a) 軽微な追加確認**（特定パターンの確認・1〜2ファイルの挙動など）は、planner が自分で explorer を「担当の起動方法」と同じ方式でネスト起動して即解決する（メイン往復不要）。**(b) プラン方針が変わる規模の再探索**は、プランレポートの `### EXPLORATION_NEEDED` セクションで要求する。スキル本体はこれを検出すると explorer を追加起動して planner を再起動し、**EXPLORATION_NEEDED が出なくなる（収束する）まで繰り返す**（ハードキャップ最大5回、到達時は最終サマリーに「planner が依然追加探索を要求中」と明記。`REPLAN_COUNT` 管理・収束判定はメインの SSOT に残す）。判断に迷ったら (b) に倒す（メインが探索の規模・回数を把握できるため）。発行ルールの詳細は **`~/.claude/skills/pir2codex/references/planner.md` の「EXPLORATION_NEEDED 発行ルール」** を参照。

## reviewer のハイブリッド並列運用

レビューを呼ぶ全てのスキル（/pir2, /pir2async, /debug, /ir, /reviewer, /review-pr, /writing-plan）は、reviewer を **correctness / consistency / quality / security / architecture の5観点** から必要なものを選択して **1〜5 体並列起動** する（ハイブリッド並列）。観点ごとの専門化と並列処理の速度を両立させつつ、不要観点を省いてコストを下げる設計。全て `sonnet` モデル。偽陰性より偽陽性を優先する方針のため、判断に迷ったら観点を増やす側に倒す。観点の選定・担当配分・結果統合は共有 **`~/.agents/skills/reviewer/SKILL.md`**、結果の意味は **`~/.agents/skills/code-review-guidance/references/result-contract.md`** を参照。

## ui-ux-reviewer の追加起動

UI / フロントエンドの変更を含むタスクでは、グローバル reviewer の 5 観点に加えて **ui-ux-reviewer を同一メッセージ内で並列追加起動** する（スタック非依存）。担当は応答性（RAIL / Nielsen / Doherty）・状態フィードバック・データ取得設計（SWR）・空 / エラー / ローディング状態・レイアウト / ビジュアル一貫性・アクセシビリティ（WCAG 2.2 AA）。判断軸 SSOT は **`~/.claude/skills/code-review-guidance/references/ui-ux-principles.md`**（shared skill package の実体。`.claude/skills/code-review-guidance` は `.agents/skills/code-review-guidance` へのシンボリックリンク）。起動条件は画面 / コンポーネント / レイアウト / インタラクション / データ取得フロー / スタイルの変更を含むとき（純ロジック・API・データ処理のみならスキップ）。VERDICT 集約は 1 体でも FAIL なら全体 FAIL。**レビューだけでなく上流（explorer の調査・planner のプラン）でも UI/UX に関わる設計・改善時に同ファイルを判断軸として参照させる**（改善案を出す段階で原則が抜けると「遅さを隠すハックの寄せ集め」になるため）。スタック固有の技術原則はプロジェクトが指定する stack adapter に分離し ui-ux-reviewer が自動で併読する。評価手順は **`~/.agents/skills/code-review-guidance/references/ui-ux.md`** を参照。

## refactor-advisor の後置運用

reviewer は「直さないといけない問題」（Critical/High）を VERDICT: PASS/FAIL で判定する役割。これとは別に、**「直したら良くなる改善余地」（Medium/Low 相当の提案）** を出す担当として refactor-advisor を用意している。reviewer 全員 PASS 確定後に直列で 1 体だけ起動し、ユーザーゲートで任意適用する設計。提案の境界と除外候補は **`~/.agents/skills/refactor-advisor/references/refactor-guidance.md`**（「提案の境界」「提案しない候補」）、提示フォーマットは **`~/.agents/skills/refactor-advisor/SKILL.md`** を参照。

## reviewer / refactor-advisor 指摘の事後照合ゲート（手順）

> ℹ️ **発火条件はグローバル `~/.claude/CLAUDE.md`「reviewer / refactor-advisor 指摘の事後処理」に常駐**している。ここに置くのは発火後に実行する手順のみ。外部 PR Reviewer Bot の指摘を取り込む場面（PIR² 外）でも同じ手順を使う。

### 自己照合手順

1. **直前ターン事実との照合**: 直前ターンで Bash / Read / grep 等で「これはこうなっている」と確認した事実があれば、reviewer / refactor-advisor の指摘がその事実と矛盾していないか確認する
2. **ユーザー明示の受容判断との照合**: ユーザーが直前ターンで「これは触らない」「この仕様で OK」「これはこのままで」と明示した範囲を、reviewer / refactor-advisor が「直すべき」と言っているケースを検出する
3. **plan 段階の判断との照合**: plan 段階で USER_DECISION_REQUIRED を通って確定した方針を、reviewer / refactor-advisor が無自覚に否定する形になっていないか確認する

### 却下根拠の自己由来チェック（矛盾判定より先に実行する）

上の 3 手順で「矛盾」と判定する前に、却下根拠が自分（スキル本体）の出力に由来していないかを確認する。

- 却下根拠が **自分がブリーフ・プラン・エージェント起動プロンプトに書いた記述**（「既存パターン準拠」「この設計で実装した」「この方針で確定」等）なら、それは照合対象の事実ではなく **指摘が争っている当の主張**。却下に使わない
- 却下に使ってよいのは (a) 自分の出力の外にある一次情報（コードの `パス:行` / コマンドの実行結果 / 実測値）、(b) **ユーザー本人の明示発話**、の 2 つだけ
- (a) も (b) も用意できない指摘は却下せず、指摘とその論点をユーザーに提示する
- `NEEDS_USER_DECISION` / `USER_DECISION_REQUIRED` は自分の判断で閉じない。**閉じられるのはユーザーの発話だけ**
- 手順 3 の「plan 段階で確定した方針」は、**ユーザーが明示的に承認したもの**に限る。自分が plan に書いて自分で採用しただけの方針はここに含めない

**違反シグナル**: 却下理由に自分が書いたプロンプト・プランの文言をそのまま引いている / `NEEDS_USER_DECISION` をユーザーに見せずに解消した / 却下根拠に `パス:行` もユーザー発話も無い。

### 比較集合はレビュアーに列挙させる

`consistency` / 既存先例照合を担当させるとき、呼び出し元は**対象と観点だけ**を渡す。

- 「既存の X と揃っているか確認して」のように**比較先を名指ししない**。比較集合を渡す必要がある場合は**列挙条件**（例: 同一ディレクトリの全ファイル / 同じ引数の形を持つ関数）で渡し、個別のファイル名・関数名は渡さない
- reviewer のレポートに列挙された比較集合が 1〜2 件しかない場合は、集合が狭いものとして扱い、列挙条件を広げて再起動する

一貫性は属性ではなく**関係**であり、比較集合を選んだ側が答えを決めてしまう。実装側が選んだ軸をレビュアーに渡すと自明に PASS する。

### 矛盾検出時の動作

- スキル本体は該当の指摘・提案を「**自己検証済み事実と矛盾**: <矛盾内容>」とラベルしてユーザーに提示する（無批判転送はしない）
- ユーザーには「reviewer の指摘 N 件のうち M 件は直前検証と矛盾」のような形で明示する
- 「直前会話の文脈を踏まえて指摘を再評価したい」というオプションをユーザーに提供する

### なぜ必要か

reviewer / refactor-advisor は単一ターンの差分だけを見ており、**直前会話で確定したユーザー方針・実機検証結果を context として持たない**。スキル本体だけがその context を持つため、ゲートを開く前に自己照合する責務はスキル本体にある。スキル本体が無批判転送すると、ユーザーは「直前ターンで話した内容を再説明する羽目になる」「これの話をしてんだよ型の叱責につながる」。本ゲートは `~/.claude/user-feedback-protocol.md` で定義する「ユーザー指摘駆動の改善プロトコル」の **入口側** の予防策で、両者は補完関係（事後発火 ↔ 事前防止）。
