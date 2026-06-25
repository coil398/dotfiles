# PIR² 系スキルの内部プロトコル

> このファイルは `~/.claude/CLAUDE.md` 「エージェント関連ルール」節のうち、PIR² 系スキル（/pir2, /pir2async, /debug, /ir 等）の実行時にのみ必要な内部プロトコルの詳細。**PIR² 系スキル実行時・UI 変更を含むタスク・チーム作業指示時に Read すること**。各エージェント固有の挙動ルールは `~/.claude/agents/<name>.md` 側に集約されている。

## チーム運用

- 「エージェントチーム」「チームで作業」等の指示があった場合、Subagents ではなく Agent Teams 機能（`TeamCreate` ツールで構成する）を使うこと
- エージェント間で共有コンテキストを持ち、相互にメッセージングできる構成にすること
- 単に複数のサブエージェントを順次起動するだけの構成は「チーム」とみなさない

## サブエージェント間のファイル経由受け渡し

PIR² 系スキル（/pir2, /pir2async, /debug）では、explorer / planner / implementer / reviewer / tester の各サブエージェントが成果物本体を `~/.ai-pir-runs/<sanitized-cwd>/<YYYYMMDD-HHMMSS>-<feature>/` 配下のファイルに書き出し、呼び出し元（スキル本体）には**要約とファイルパスのみ**を返す方式を採用している。`~/.ai-pir-runs/` を `~/.claude/` 外に置く理由: Claude Code が `~/.claude/` 配下を sensitive-file 扱いし、allowlist があってもディレクトリ作成・書き込みごとに permission プロンプトが出るため。retrospector 用の累積ログ（`pir_*_log.md`）は従来どおり `{PROJECT_MEMORY_DIR}/` に残す（書き込み頻度が低く sensitive 扱いでも困らない）。

目的:
- telephone-game effect（Anthropic 公式推奨の用語）の回避: オーケストレーターの context に各段階の全文が載ると後段で情報が欠落・歪曲する
- メイン Claude の context 肥大抑制: サマリー＋パスだけ保持し、必要な段で該当ファイルを Read する

運用ルール:
- スキル本体は各サブエージェント起動時に `RUN_DIR=[絶対パス]` と連番（`EXPLORATION_INDEX` / `IMPL_INDEX` / `REVIEW_INDEX` / `TEST_INDEX`）をプロンプトで渡す
- サブエージェントは成果物を `{RUN_DIR}/<kind>-<NN>.md` に書き出し、返り値は各エージェント定義の「呼び出し元への返り値フォーマット」に従う
- 次段エージェントへの入力は「前段の本文」ではなく「前段が書き出したファイルのパス」で渡す。次段は必要に応じて自分で Read する
- `~/.ai-pir-runs/` 配下は **per-run の内部ファイル**でユーザーには見せない。retrospector 用の累積ログ（`{PROJECT_MEMORY_DIR}/pir_*_log.md`）とは別系統で共存する

## PIR² 引継ぎ (handoff.md)

PIR² 系スキル（/pir2, /pir2async, /debug）は、複数回の実行にまたがる大きなタスクを引き継ぐために `~/.ai-pir-runs/<sanitized_cwd>/handoff.md` を使う。詳細プロトコル（ファイル位置・フォーマット・ライフサイクル・resume モード検知・誤参照防止ルール）は **`~/.claude/pir-handoff.md`** に分離した。スキル本体・planner・implementer・retrospector は handoff 関連の挙動判断で必ずこのファイルを参照すること。

## planner の能動的再探索ループ

planner は追加探索を2通りで行える（ハイブリッド）。**(a) 軽微な追加確認**（特定パターンの確認・1〜2ファイルの挙動など）は、planner が自分で explorer を `Agent` ツールでネスト起動して即解決する（v2.1.172〜。メイン往復不要）。**(b) プラン方針が変わる規模の再探索**は、プランレポートの `### EXPLORATION_NEEDED` セクションで要求する。スキル本体はこれを検出すると explorer を追加起動して planner を再起動し、**EXPLORATION_NEEDED が出なくなる（収束する）まで繰り返す**（ハードキャップ最大5回、到達時は最終サマリーに「planner が依然追加探索を要求中」と明記。`REPLAN_COUNT` 管理・収束判定はメインの SSOT に残す）。判断に迷ったら (b) に倒す（メインが探索の規模・回数を把握できるため）。発行ルールの詳細は **`~/.claude/agents/planner.md` の「EXPLORATION_NEEDED 発行ルール」** を参照。

## reviewer のハイブリッド並列運用

レビューを呼ぶ全てのスキル（/pir2, /pir2async, /debug, /ir, /reviewer, /review-pr, /writing-plan）は、reviewer エージェントを **correctness / consistency / quality / security / architecture の5観点** から必要なものを選択して **1〜5 体並列起動** する（ハイブリッド並列）。観点ごとの専門化と並列処理の速度を両立させつつ、不要観点を省いてコストを下げる設計。全て `claude-sonnet-4-6` モデル。偽陰性より偽陽性を優先する方針のため、判断に迷ったら観点を増やす側に倒す。詳細プロトコル（観点マッピング、観点セット決定ルール、自動選定アルゴリズム、共通の運用ルール、後方互換）は **`~/.claude/agents/reviewer.md` の「呼び出し元（スキル本体）への運用ガイド」** を参照。

## ui-ux-reviewer の追加起動

UI / フロントエンドの変更を含むタスクでは、グローバル reviewer の 5 観点に加えて **`ui-ux-reviewer` エージェントを同一メッセージ内で並列追加起動** する（スタック非依存）。担当は応答性（RAIL / Nielsen / Doherty）・状態フィードバック・データ取得設計（SWR）・空 / エラー / ローディング状態・レイアウト / ビジュアル一貫性・アクセシビリティ（WCAG 2.2 AA）。判断軸 SSOT は **`~/.claude/ui-ux-principles.md`**。起動条件は画面 / コンポーネント / レイアウト / インタラクション / データ取得フロー / スタイルの変更を含むとき（純ロジック・API・データ処理のみならスキップ）。VERDICT 集約は 1 体でも FAIL なら全体 FAIL。**レビューだけでなく上流（explorer の調査・planner のプラン）でも UI/UX に関わる設計・改善時に `~/.claude/ui-ux-principles.md` を判断軸として参照させる**（改善案を出す段階で原則が抜けると「遅さを隠すハックの寄せ集め」になるため）。スタック固有の技術原則はプロジェクトの `.claude/ui-ux-stack-*.md` に分離し ui-ux-reviewer が自動で併読する。詳細プロトコルは **`~/.claude/agents/ui-ux-reviewer.md` の「呼び出し元（スキル本体）への運用ガイド」** を参照。

## refactor-advisor の後置運用

reviewer は「直さないといけない問題」（Critical/High）を VERDICT: PASS/FAIL で判定する役割。これとは別に、**「直したら良くなる改善余地」（Medium/Low 相当の提案）** を出す専任エージェントとして `refactor-advisor` を用意している。reviewer 全員 PASS 確定後に直列で 1 体だけ起動し、ユーザーゲートで任意適用する設計。詳細プロトコル（役割分離、起動タイミング、VERDICT 集約への影響、ユーザーゲートの運用、言語イディオムガードレール）は **`~/.claude/agents/refactor-advisor.md` の「呼び出し元（スキル本体）への運用ガイド」** および同ファイル内の「除外する候補」セクションを参照。
