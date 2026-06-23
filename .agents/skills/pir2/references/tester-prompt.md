# tester 実行プロンプト

PIR² 系スキル共通の tester 実行仕様。スキル本体（メイン Codex）は tester subagent を起動する、またはメイン Codex が直接テストする **前に** TEST_SCOPE を構築して明示する。

## TEST_SCOPE 構築（スキル本体の責務）

tester 起動前に、スキル本体は以下の手順で `TEST_SCOPE`（実行するテストコマンドの配列）を組み立てる:

1. **plan.md から最小スコープを抽出**
   - `{RUN_DIR}/plan.md` を Read し、`### テスト・検証方法` セクションの **「tester が実行する最小スコープのテストコマンド」** ブロックに列挙されたコマンドを抽出する
   - 例: `go test ./controllertest -run TestFoo -v`
2. **破壊性フラグ + 動作変更フラグを参照**
   - `{RUN_DIR}/destructive-change-check.md` を Read し、`破壊的変更フラグ: ON/OFF` と `動作変更フラグ: ON/OFF` の両方を確認する
3. **TEST_SCOPE を最終決定（マトリクス）**

   | 動作変更 | 破壊性 | TEST_SCOPE |
   |---|---|---|
   | OFF | OFF | tester 自体スキップ可（プロンプト構築不要） |
   | **OFF** | **ON** | **plan の最小スコープのみ**（golden 整合確認のため最小限）|
   | ON | OFF | plan の最小スコープのみ |
   | **ON** | **ON** | **plan の最小スコープ + プロジェクト規約のフルスイート（安全網）** |

   - **フルスイート付与の判定**: 動作変更フラグ ON **かつ** 破壊性フラグ ON のときのみ。「OFF + ON」のケース（純粋なフィールド追加で動作が変わらないが golden に波及するケース）ではフルスイートを付与しない（最小スコープで golden 整合だけ確認すれば十分）
   - **フルスイートのコマンド出典**: プロジェクト CLAUDE.md の Testing セクションで定義されているものを使う。SKILL.md / tester-prompt.md に直書きしない
   - プロジェクト CLAUDE.md に明確な「CI 同等コマンド」が無い場合、フルスイートを付与せず最小スコープのみで進める（過剰な安全網よりプロジェクト規約を尊重する）
4. **TEST_SCOPE の由来を tester プロンプト内に明示**
   - 各コマンドに「最小スコープ由来」「動作変更+破壊性 ON のためフルスイート安全網由来」のコメントを添える。tester がレポートで引用しやすくする
   - 動作変更フラグ OFF + 破壊性フラグ ON の場合は「動作変更なしのためフルスイートは付与せず、golden 整合確認のため最小スコープのみ」と一文添える

## tester 実行コマンド

subagent が利用可能なら `tester` を起動する。利用できない場合はメイン Codex が同じプロンプト項目に従ってテストを実行し、同じ `{RUN_DIR}/test-{TEST_INDEX}.md` を書き出す:

- **model**: `gpt-5.5`
- **プロンプト**（必須項目）:
  - `PROJECT_MEMORY_DIR=[パス]`
  - `RUN_DIR=[パス]`
  - `TEST_INDEX=01`（初回。再テスト時はインクリメント）
  - `{RUN_DIR}/plan.md` のパス
  - `{RUN_DIR}/implementation-{最新}.md` のパス
  - `TEST_SCOPE=` 以下に上記で組み立てたコマンドを **改行区切りで列挙**:

    ```
    TEST_SCOPE=
    - go test ./controllertest -run TestFoo -v
    - go test ./... -shuffle=on -timeout=20m  # 破壊性フラグ ON のため安全網として追加
    ```

    各行に「最小スコープ由来」「破壊性安全網由来」のコメントを添えると tester が判断しやすい。
  - 指示文: 「`TEST_SCOPE` に列挙されたコマンドを実行してください。**`TEST_SCOPE` に含まれないコマンドを実行する場合は、実行前に必ずテストレポートに『拡大が必要な理由』を書いてユーザー確認を待つこと**。範囲拡大の自己判断は禁止」
  - 「テストレポート本体は `{RUN_DIR}/test-{TEST_INDEX}.md` に書き出し、チャットには VERDICT + 要約のみ返してください。テストデータのクリーンアップはユーザー明示指示まで実行しないこと」

## 例 1: 動作変更 OFF + 破壊性 OFF（純粋なドキュメント変更等）

tester 自体スキップ可。ユーザーに「tester スキップしますか？」と確認を取った上でスキップ。

## 例 2: 動作変更 OFF + 破壊性 ON（純粋なフィールド追加・OpenAPI 末端編集等）

```
TEST_SCOPE=
- go test ./controllertest -run TestPutHome -v  # 最小スコープ（plan 由来）
# 動作変更なしのためフルスイートは付与せず、golden 整合確認のため最小スコープのみ
```

tester は上記コマンドだけ実行する。`go test ./...` への拡大はしない。

## 例 3: 動作変更 ON + 破壊性 OFF（usecase ロジック微修正等）

```
TEST_SCOPE=
- go test ./controllertest -run TestFoo -v  # 最小スコープ（plan 由来）
- go test ./usecase -run TestFooUsecase -v  # 最小スコープ（plan 由来）
```

tester は上記コマンドだけ実行する。フルスイートは付与しない。

## 例 4: 動作変更 ON + 破壊性 ON（usecase + OpenAPI を同時変更等）

```
TEST_SCOPE=
- go test ./controllertest -run TestFoo -v  # 最小スコープ（plan 由来）
- go test ./usecase -run TestFooUsecase -v  # 最小スコープ（plan 由来）
- go test ./... -shuffle=on -timeout=20m  # 動作変更+破壊性 ON のためフルスイート安全網由来
```

tester は全て実行する。これでも `TEST_SCOPE` に列挙されていない `make golden-all` 等は実行しない。

## 再テスト時 (`TEST_INDEX >= 02`) の TEST_SCOPE

`TEST_INDEX=02` 以降の差し戻し再テスト時も **初回と同じ TEST_SCOPE 構築ロジック**を再実行する。golden 更新等で plan.md の最小スコープ部分が更新されていれば、その更新後の値を抽出する。破壊性フラグは ON のままなら ON、ループ中に変わることはない。
