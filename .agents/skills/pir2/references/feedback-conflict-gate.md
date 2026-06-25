# 直前追加 feedback の自己照合ゲート

PIR² 系スキル（/pir2, /pir2async 共有）の feedback 照合ゲート。実装フェーズ（または pir2async チーム）を開始する前に、メイン Codex（スキル本体）が直前に追加した feedback との矛盾を照合する機械ゲート。

「直前 /retro で追加した feedback を、その直後の実装プロンプト作成時に参照せずに矛盾する除外指示を書いてしまう」即時違反パターン（pir_pattern_registry `[2026-05-13T16:30:00Z]` フラグの根拠 H3）を構造的にブロックする。

## ステップ 1: 直前 N 日分の追加 feedback を Read

1. `{PROJECT_MEMORY_DIR}/MEMORY.md` を Read（最新 feedback 一覧の把握）
2. 過去 14 日以内に追加・更新された `{PROJECT_MEMORY_DIR}/feedback_*.md` を `ls -t` で抽出（新しい順 5 件まで）
3. 各 feedback の冒頭・「Why」「How to apply」セクションからキーフレーズ（除外対象になりやすい固有名・命名規則・スコープ指定の単語）を抽出

## ステップ 2: 実装プロンプト案の自己照合

実装プロンプト案の中の以下の記述を、抽出した feedback のキーフレーズと逐一突合する:

- 「除外指示」: 「〇〇は変更しない」「〇〇には触らない」「〇〇は対象外」のような明示的除外
- 「変更しないファイル/フィールド」: 「〇〇は素直な命名のため」「〇〇は既存のままで OK」のような正当化付き保留
- 「スコープ縮小」: 「軽量に〇〇だけ」「最小限の〇〇のみ」のような範囲限定

突合方法は単純な部分一致 grep で十分。feedback ファイル名のキーワード（例: `cross_layer_naming_symmetry`）と implementer プロンプト案の関連語（例: `命名`, `naming`, `レイヤー`, `field`）を交差させる。

## ステップ 3: 矛盾検出時の動作

矛盾が **1 件でも見つかったら実装開始を中断**する。

1. 該当 feedback と矛盾箇所を `{RUN_DIR}/feedback-conflict.md` に書き出す:

```markdown
# 直前 feedback との矛盾検出

- 矛盾 feedback: <ファイル絶対パス>
- 該当キーフレーズ: <feedback から抽出した語>
- 矛盾箇所（実装プロンプト案）: <該当行の引用>
- 推奨アクション: <除外指示取り下げ / plan 再策定 / 範囲拡大>
```

2. ユーザーに以下の形式で通知（Auto mode でも省略不可）:

```
直前 feedback との矛盾を検出しました。
- 矛盾 feedback: <ファイルパス>
- 矛盾箇所: <実装プロンプト案の該当行>
- 推奨アクション: 除外指示を取り下げて plan を再策定

このまま実装を開始しますか？（pir2async の場合: チームを起動しますか？）
- yes: 矛盾を承認して開始（理由をご教示ください）
- no: plan 再策定（推奨）
```

## ステップ 4: 照合結果の記録（矛盾なしの場合も必須）

矛盾なしの場合も `{RUN_DIR}/feedback-conflict.md` に「照合した feedback: N 件、矛盾なし」を記録する。retrospector N4.4 の自動測定（D 案で追加予定）で読み取り可能にするための痕跡。

## スキップ条件

過去 14 日以内に追加・更新された `feedback_*.md` が 0 件の場合のみスキップ。それ以外は必須。`{PROJECT_MEMORY_DIR}` 自体が存在しない場合は `feedback-conflict.md` に「project memory なし、照合スキップ」と記録してスキップ。

## 完了後（スキル別）

- pir2: ステップ 5.6-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する
- pir2async: ステップ 4.85-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する
- debug: ステップ 2.85-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox を `[x]` に更新する
