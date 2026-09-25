# Jev hooks 実装計画

最新状態: ユーザーの接続実行指示を受け、自動承認レビューを通過してai-ltmの任意Jev注記を接続済み。以下の承認待ち記載は作業履歴。

接続後のrecall18テストと接続差分の独立レビューPASS。キーなし・空白キー・注記成功・注記例外・検索予算切れを確認し、失敗時にも候補と検索成功状態を保持。管理Skill/ai-ltm Skill/README/doctorを現行接続へ更新。

## 要件
- Jev判定を独立ディレクトリへ集約。APIキーは TYPESAFE_API_KEY 環境変数のみ。未設定・障害時は既存の操作を妨げない。
- 完了/質問/再試行/差分/スキル/記憶の判定を利用可能なイベントに接続。新しい判定は助言、既存Stopは回数制限付き継続。
- ai-ltmは存在するときのみ任意連携。検索/記録の非Jev経路とDBを保持する。
- API呼び出し/スキップ/失敗/入力トークン/推定USD/待ち時間を永続集計。未知の利用量・価格をゼロ費用扱いしない。CLIとローカルHTMLで可視化。
- .zshrc既存変更には触れない。commit/pushしない。

## 所有と順序
1. 親: 既存パッケージ移設、config/Stop/trust/配備/文書/統合。
2. guard担当: 新規guards/runtimeモジュールと専用テスト。
3. telemetry担当: service/telemetry/reportと専用テスト。
4. memory担当: 任意ai-ltm連携と専用テスト。
5. 独立レビュー、対象テスト、配備確認。

## 受入
- キーなし・API障害でhook出力に不要なブロックがなく、ai-ltm検索結果も維持。
- Stopの説明成果物、正当な質問、明示停止、継続上限の対照を確認。
- ランタイムごとの入出力と非対応差をテスト。
- 同時呼び出しの記録欠落/重複、未知費用、HTMLエスケープを検証。
- 既存Stopテストと影響するsync fixtureを実行。実API精度と実ハーネス発火をモック成功と区別。

## 状態
- 既存Stop移設・env-only・成果物判定: 実装、既存重点65テストPASS。
- 利用量/CLI/HTML: 実装、担当15テストPASS。実API評価31呼出しを別の一時stateへ記録。
- Codex生成fixture: PASS。キーなしlauncher/インストール保全: 4テストPASS。
- 新guard/skill候補: 実装済み。最終修正後のguard/runtime/skills 37テストPASS。架空入力の実APIでSkill候補提示と不要承認への助言を確認。
- 管理skill `.agents/skills/jev/SKILL.md`: 追加、quick_validate PASS。
- ai-ltm: 外部送信の自動接続がauto_reviewに拒否され未適用。その後ユーザーが連携方法の再検討を依頼。helpersは架空データ/モック7テストPASS、実記憶送信なし。接続案を「候補本文→main、任意Jev注記」へ再検討。既存vector_search/session_recallは未変更。
- Stop実API: 最終基準の既存14例は不要継続0/見逃し2、追加の回答/質問3例は不要継続0/見逃し1。確率判定の見逃しを残す試行版として明記し、閾値引下げや例外で隠さない。
- 第一範囲(Stop/service/telemetry/配備)・第二範囲(guard/skill/memory)の独立レビューPASS。
- 統合単体145件PASS、その後の修正は影響する37テストで確認。Cursor契約130/130 PASS、Codex生成fixture PASS、Devin他handler保全/冪等性PASS。
- Codex/Cursorはlink --codex-cursor-only、Devin sync、Grok installerで実配備済。Grok inspectで3イベント発見、共有/jev skill発見を確認。
- インストール済入口を架空会話1件で実API確認。既定usage DBへ1回/1,505入力tokens/$0.00006321を記録。実クライアントが新sessionで自動発火することは未確認。
- 起動20回実測中央値: キーなし3.5ms、キーありread対象外44.3ms。前者は通信/状態書込なし。Rust化は未実施。
- 実装・対象検証・独立レビュー完了。実クライアントの新session自動発火とai-ltm自動接続は未確認・未適用。

## ai-ltm連携の実装追補

ユーザーの「全部やれ」を受け、上位最大5件のID・要約・短い抜粋・タグ・スコアをmainへ届ける処理と任意注記を実装中。Jevなしでもこの候補提示は成立させる。

Jevを使う場合は候補の関連性・前提の相違・現在の指示との衝突・判断不能を型付きラベルで補足する。候補を削除せず、採否と説明はmainが担当し、実際に使った記憶だけmark-usedする。キーなし・API障害なら注記なしで同じ候補を届ける。保存時の重複・矛盾分類は別の改善として分ける。

例: 古い記憶に秘密ファイルからAPIキーを読む手順があり、現在の依頼が環境変数限定なら、衝突の注記を参考にmainが現在の依頼を優先する。実記憶を送信する自動接続は、具体的な送信範囲を確定するまで有効化しない。

- 所有: recall/bridge/ai-ltm SKILLはmemory担当、memory.annotateと専用試験はtelemetry担当、管理CLI/doctor/README/配備は親。
- 受入: 候補・順序・元fieldを保持、キーなし/障害/observe/低confidenceで候補を返す、検索予算内で注記、API1回につき集計1件。
- 自動送信を有効化する管理Skill変更がauto_reviewで拒否。TypeSafeへの検索文と最大5件の要約/本文各1200文字・タグ・スコアの自動送信について具体的承認を問い合わせ中。外部送信のない候補返却と架空データ試験は継続。
- 既存セッションの旧Codex入口削除によるエラーを修正。Cursor/Devinも同じ現行launcherへ委譲する入口を保持。3入口のキーなし・書込なし確認PASS。実セッションのStop判定とusage記録を確認。
- memory.annotate実装と関連service計14テストPASS。その後、無効timeout・空白キー・既存注記保持を修正しannotate専用8テストPASS。架空記憶「旧secret file fallback」と現在指示「env-only」の実API試験でrelevant/conflict/mismatchを確認。元候補を保持し1API/749入力tokens/146出力tokens/$0.000031458/554msを一時stateへ1件記録。実記憶は送信していない。
- 候補本文main返却を実装。recall17テスト/bridge11テスト/ai-ltm Skill検証PASS。候補上限5件・全result_ids保持・DB hash/mtime不変を確認。自動注記の接続は未適用。
- 旧3入口は現行登録と同じPATH上のshへexec。3実プロセスと起動argv確認PASS、hook_io13テストPASS。memory-annotate管理CLIのdispatch確認PASS。
- 追加差分の独立レビューPASS。bridgeの全入口とloaderも空白キーを未設定扱いに統一。自動送信の本番接続は引き続き承認待ちで未適用。
- レビュー用接続差分: `/private/tmp/jev-ltm-annotation-connection.patch`。git apply --check成功。一時コピーにだけ適用し、キーなし/空白キーでimport・APIなし、mockキーで許可fieldのみ送信・候補ID/順序保持・注記付加を確認。検索予算3秒の残り2.731秒がAPIへ渡ることを確認。本番接続は実施していない。
