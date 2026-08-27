# 破壊的変更チェックリスト + 動作変更チェック（pir2 専用）

PIR² スキル（/pir2）のステップ 5.7。implementer 起動前に、メインエージェント（スキル本体）が plan.md と explorer レポートを Read して **2 軸の機械チェック** を行う。

注: pir2async は 5 項目単軸チェックで構造が異なるため、このファイルは pir2 専用。

## 概要

- **破壊的変更フラグ（波及範囲を測る軸）**: インタフェース・自動生成・golden 等への波及があるか
- **動作変更フラグ（ビジネスロジック変更を測る軸）**: usecase / domain / repository 等のビジネスロジックレイヤーが変わるか

両軸を独立に判定し、**マトリクスで後段のテスト戦略を決める**。「インタフェース変更あり + 動作変更なし」のような中間状態を識別し、過剰なフルスイート実行を避ける目的。

このチェックは「reviewer / tester を省略してよさそう」と判断したくなる軽量化バイアスを構造的にブロックしつつ、必要以上の安全網を張らないバランスを取る機械ゲート。出現の根拠は pir_pattern_registry の `[2026-05-13T16:30:00Z]` フラグ（H2: golden 6 ファイル未更新、H3: 直前 feedback 即時違反、H4: テストカバレッジ薄が同一 run で発生）。

## 破壊的変更フラグの判定項目（plan.md と explorer レポートを Read して機械的に判定）

- **(a) OpenAPI フィールド名のリネーム or 削除**: plan.md または explorer レポートに `docs/openapi/` 配下のフィールド `rename` / `削除` / `name change` の言及があるか
- **(b) 自動生成ファイル再生成連鎖**: `codegen` / `proto` / `openapi` / `sqlc` / `make .*gen` / `go generate` のいずれかが plan に含まれるか
- **(c) golden / snapshot テスト波及見込み**: `golden` / `snapshot` / `*_golden.json` / `__snapshots__` が plan / explorer レポートに登場するか、または (a)(b) のいずれかが ON の場合は自動的に ON
- **(d) 自動生成型変更**: `required` の追加・削除、`int32` ↔ `*int32` 等の proto3 optional 化、enum 値の追加・削除が plan に含まれるか
- **(e) controller 構造体リテラル / フィールド参照変更が 5 箇所以上**: explorer レポートに「N 箇所変更」「N+ files」のような数値があり 5 以上か、または plan に列挙された対象ファイル数が controller/ 配下で 5 以上か

→ いずれか 1 つでも ON なら **破壊的変更フラグ = ON**

## 動作変更フラグの判定項目（plan.md / explorer レポートと「破壊的変更フラグ」の結果を Read して判定）

- **(f1) business logic レイヤーへの変更**: plan.md の変更対象ファイル一覧に **business logic レイヤー**（usecase / domain / repository / service / gateway / event / websocket / batch 相当のディレクトリ）が含まれるか
  - 具体的なディレクトリ名はプロジェクト固有のため、判定時はそのプロジェクトの CLAUDE.md「Architecture」「Key Directories」セクションを参照する。レイヤー命名や Clean Architecture の構成（presentation / application / domain / infrastructure 等）はプロジェクトによって異なる
  - 「presentation layer」「controller layer」相当（HTTP/gRPC ハンドラ層）の変更だけなら (f1) OFF（ただし (f2) で別途判定）
  - テストファイル (`*_test.go` 等) や自動生成ファイル (生成物ディレクトリ 例: `gen/`, `generated/` 等) のみの変更は (f1) OFF
- **(f2) controller 5+ 箇所変更**: 破壊的変更チェックの (e) が ON の場合は (f2) も ON（5 箇所以上の controller 変更は機械的追加を超えた動作変更を含む可能性が高い）
- **(f3) OpenAPI rename/削除**: 破壊的変更チェックの (a) が ON の場合は (f3) も ON（rename は既存クライアントの動作互換を壊すため動作変更扱い）

→ (f1) OR (f2) OR (f3) のいずれか 1 つでも ON なら **動作変更フラグ = ON**

## 判定結果の書き出しと反映

判定結果を `{RUN_DIR}/destructive-change-check.md` に書き出す。フォーマット:

```markdown
# 破壊的変更チェックリスト + 動作変更チェック

## 破壊的変更フラグ（波及範囲）

- (a) OpenAPI フィールド名 rename/削除: [ON/OFF] — 根拠: <plan.md の該当箇所引用 or "該当なし">
- (b) 自動生成連鎖: [ON/OFF] — 根拠: <同上>
- (c) golden/snapshot 波及: [ON/OFF] — 根拠: <同上>
- (d) 自動生成型変更: [ON/OFF] — 根拠: <同上>
- (e) controller 5+ 箇所変更: [ON/OFF] — 根拠: <同上>

破壊的変更フラグ: [ON/OFF]

## 動作変更フラグ（ビジネスロジック変更）

- (f1) business logic レイヤー変更: [ON/OFF] — 根拠: <変更対象ファイルの一覧から business logic レイヤー該当ファイルを列挙、なければ "該当なし">
- (f2) controller 5+ 箇所変更: [ON/OFF] — 根拠: <(e) の結果を引用>
- (f3) OpenAPI rename/削除: [ON/OFF] — 根拠: <(a) の結果を引用>

動作変更フラグ: [ON/OFF]

## 適用される後段戦略（マトリクス）

| 動作変更 | 破壊性 | reviewer | refactor-advisor | tester |
|---|---|---|---|---|
| OFF | OFF | 通常運用（観点自動選定可） | 通常運用 | スキップ可（feedback_skip_tester_when_no_behavior_change 参照） |
| OFF | ON | **5 観点全起動** | **必須** | **最小スコープ + golden 整合確認のみ（フルスイートなし）** |
| ON | OFF | 通常運用 | 通常運用 | 最小スコープ起動 |
| ON | ON | **5 観点全起動** | **必須** | **最小スコープ + フルスイート（安全網）** |

今回適用される戦略: <マトリクスから該当行を引用>
```

## 軽量化したい場合の運用

破壊的変更フラグまたは動作変更フラグが ON のときに「reviewer 観点を減らしたい」「tester を省略したい」「フルスイートをスキップしたい」と判断したくなった場合、**スキル本体の独断は禁止**。必ずユーザーに以下の形式で確認する:

```
判定: 破壊性=ON / 動作変更=ON
該当項目: (a) OpenAPI rename + (c) golden 波及 + (f1) usecase 変更

通常はこの状況で reviewer 5 観点 + refactor-advisor + tester (最小スコープ + フルスイート) 必須ですが、
[省略したい工程] を省略してよろしいですか？
- yes: 省略を承認（理由をご教示ください）
- no: 全工程実行（推奨）
```

Auto mode でもこのユーザー確認は省略不可。CORE:COMMON「auto mode でも取り消し困難な操作は確認必須」原則と同じ扱い。

## スキップ条件

破壊性フラグ・動作変更フラグともに OFF のときはステップ 6 以降を通常運用で進める。`feedback_skip_tester_when_no_behavior_change` が該当する場合は tester 自体のスキップも可（その場合はユーザーに「tester スキップしますか？」と確認を取る）。

## 完了後

ステップ 5.6-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する。
