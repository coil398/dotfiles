# Agent / Skill運用統一の実施報告

対象: `coil398/dotfiles`。開始HEADは `c2bc382b03e7ae98c703fdbb9c55f99ba7bb1bf7`、開始時の作業ツリーはclean。比較基準へ戻さず、現在の実装から開始した。

基準は現行実装・ユーザーの最終統一指示・従来の適用済み報告・利用可能なv3設計書。移行前の監査で解消した項目を現行の欠陥として再登録していない。

## 実装と対象

- `.agents/skills`、`.codex/skills`、`.cursor/skills`の全実体を用途ごとに確定し、責任・読者・原本・入力・結果の接続を確認する対象とした。現在の一覧は[正式文書](AI-WORKFLOW-SPEC.md#管理対象skill一覧)に保持する。
- 共通レビューの進行を共有reviewer、専門評価をcode-review-guidance、判定の意味をresult-contractに集約。呼出元は今回の入力を渡し、共通結果を消費する。
- 委任時の専門本文の不要な親先読みを除き、子が実体パスから読む。親が直接評価・分析・統合・十分性確認をする場合は必要な実行者資料を読む。
- Cursor Fable、明示CLI、長期再開・協働・記憶・HTML、必要なreadonly/互換入口を維持する。
- READMEとAI-WORKFLOW-SPECを現行の一体的な運用説明へ更新し、既存agent-skill-migrateへ同じ原則を反映する。

共通原本と例外の理由・保守場所は正式文書を参照する。本報告は作業結果を記録し、別の判定規則を持たない。

## 実行確認

今回の最終差分に対して、次を確認した。

| 確認 | 実測結果と範囲 |
|---|---|
| 全管理対象 | 現在の実体は34用途・65入口（共有31、Codex 2、Cursor 32）。正式文書の行と実体に漏れ・余分な入口なし。各用途の親・実行者・専門資料・結果消費を担当別の読み取りと親の差分照合で確認 |
| 共通原本の接続 | reviewerの進行、code-review-guidanceの専門評価、result-contractの結果意味、tester procedureを追跡。呼出元は同じ親が手順を読み、評価子へ親工程を渡さない |
| 資料の一本化 | Cursorから削除した付属資料28件は全件共有実体に対応。薄い入口から共有Skill・script・referenceへ接続 |
| 代表評価 | 整数IDの一致だけを許可するfixtureで、評価担当が修正前の比較反転をP1/FAILと判断。修正後の限定再評価はPASS。親もguidance/correctnessを読み、4入力を実行して修正前0/4・修正後4/4を確認 |
| 欠落・途中終了 | 実在しない必須資料をINCOMPLETE、合成の途中終了返却をINCOMPLETEとして集約することを契約とfixtureで確認。実timeoutの発生試験ではない |
| 観点と独立性 | 未知観点の保持、複数観点と担当数の分離、明示五観点の別コンテキスト・容量不足時のwaveを共有reviewerで静的確認。新規runtimeでの一連のTask実行は未確認 |
| Cursor deepthink | 委任時は子が専門referenceを読む。親の直接統合・十分性確認は親が該当資料を読む。親のFable指定、single/panel、deepplan委任時の同指定を静的確認 |
| sync hook | `bash etc/test-sync-hooks.sh`成功。必要な生成元だけで同期し、対象外編集で起動しないfixtureを含む |
| Cursor seed・配布契約 | 最終配布後の`bash etc/test-cursor-contracts.sh`: **128 passed, 0 failed**。thin seed、metadata保持、専門本文・Claude専用集合の再作成防止、既存entry保持を含む |
| 配置 | `bash etc/check-shared-drift.sh`: **1 passed, 0 failed**。`python3 -B etc/audit-skill-agent-layout.py --cwd /Users/kawasetakumi/dotfiles --dotfiles /Users/kawasetakumi/dotfiles`: **fails=0**。native本文とClaude本文の差は必要なoverlay差分として残る |
| 生成とhome配布 | `bash etc/link.sh --codex-cursor-only`成功。再実行でCursorの再配置・追加backupなし。全Cursor配布ファイルは原本と一致。共有変更に伴う`bash etc/sync-opencode.sh`と`--check`も成功 |
| 新規Codexの発見 | モデル実行なしの`codex debug prompt-input`でreviewer・code-review-guidance・researchを共有側、codex・worker-delegationをnative側から発見。deepthink入口は含まれない。明示専用agent-skill-migrateは当診断で本文注入を確認できず、実際の明示起動は未確認 |
| 正式文書 | READMEから正式文書と報告への導線、相対リンクの実在、全入口一覧を確認。`git check-ignore`は3文書とも非ignore、`git diff --check`成功 |

五観点の新規独立起動・複数観点の同一担当配分・未知指定・途中終了をまとめた外部Codex CLIの代表実行は、read-onlyの起動前に自動承認審査が拒否した。理由は「非公開Skill本文を外部モデルの認証先へ送るpayloadと送信先の明示承認がない」。送信対象と宛先を説明した確認を提示したが、完了時点で追加承認を受け取っていないため再実行していない。この未実行分を静的確認や既存担当の返却で実行済みへ読み替えていない。

## 未確認と対象外

- Cursor TaskでのFable実呼出、Cloud同期、Windows実機、外部アプリ操作、公開されていないモデルmetadataは、今回の静的接続・配置確認から実行済みとは扱わない。
- Claude専用Skill・Agent本文、管理外plugin、認証、課金先、親モデル、承認方式、実験機能、未指定repoの実装は対象外。
- `.claude/lib`内の既存Codex/OpenCode生成hookは、関連adapterとして生成元の選択条件だけを対象にする。Claude専用本文を移行しない。

## Gitと配布の保全

今回の新しいcommit/pushは依頼されていないため実施しない。生成物は原本から生成し、home配布は既存のbackup・リンク保全処理を使う。最終HEADは開始時と同じで、staged差分は0件。今回の変更は作業ツリーに残し、本報告は非ignoreの新規ファイルとして保存した。認証・課金・親モデル・承認・実験機能の原本と生成configに差分はない。復元が必要な場合は対象差分と配布前backupを個別に選び、ユーザーの他の変更や設定を一括して戻さない。
