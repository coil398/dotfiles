# 破壊的変更チェック + 動作変更チェック

対象: ワークフロー定義文書（SKILL.md / references / agent 定義）の編集。実行コード・DB・API は対象外。

## 破壊的変更フラグ（a〜e）

| フラグ | 判定 | 根拠 |
|--------|------|------|
| a. データ削除・破壊 | OFF | ファイル削除なし。全て追加 or 置換（pir2codex 6-1 bullet の置換は等価機能の共通 reference 参照化＝機能損失なし） |
| b. 公開 API/シグネチャ削除 | OFF | 該当なし（instruction doc） |
| c. 破壊的マイグレーション | OFF | なし |
| d. 不可逆操作 | OFF | 全編集は git で可逆。自動 restore は設計に一切書かない |
| e. 外部副作用 | 限定的 | implementer.md 編集で PostToolUse hook が `.codex/agents/implementer.toml` 等を再生成（想定内・sync 機構どおり）。SKILL.md/references 編集は sync SSOT 外で副作用なし |

## 動作変更フラグ（f1〜f3）

| フラグ | 判定 | 根拠 |
|--------|------|------|
| f1. 既存フローの挙動変更 | **ON（意図的）** | (1) pir2 に新ブロッキングゲート 6-3 が加わり、全 pir2 run で implementer→reviewer 間に決定論検証が挟まる。(2) pir2codex 実集合定義が HEAD 比較→unstaged+untracked に変わる（untracked 検知が増える＝strictly better、staged は Codex 非 stage 前提で対象外）。→ reviewer に申し送り |
| f2. デフォルト値変更 | OFF | なし |
| f3. 出力フォーマット変更 | 限定的 | 両 SKILL.md step12 最終サマリーに検証結果ブロックが1つ増える（追加のみ） |

## 後段戦略（マトリクス判定）
- 破壊的フラグ主要 OFF・動作変更 f1 ON（意図的・strictly better）→ reviewer は correctness/consistency を厚めに。tester は「reference bash の構文チェック＋実データ 1 回ドライラン」の最小スコープ（テストスイート非対象リポ）。
- 軽量化なし（全観点フル）。ユーザー確認不要（意図的動作変更は plan で確定済み・ユーザーゲート通過済み）。
