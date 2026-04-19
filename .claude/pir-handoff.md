# PIR² 引継ぎ (handoff.md) プロトコル

PIR² 系スキル（`/pir2`, `/pir2async`, `/debug`）が「複数回の実行にまたがってタスクを引き継ぐ」ための仕様。このファイルは `~/.claude/CLAUDE.md` から参照される。**protocol 変更時はこのファイルを SSOT として編集する**。

---

## 🎯 目的

1. 1 回の PIR² で終わらない大きなタスクを、次回起動時に継続できるようにする
2. ユーザーが「引継いで」「続きから」と指示したら、前回の未消化 TODO を自動で引き継ぐ
3. 完了項目を確実にマークし、**古い情報の誤参照を防ぐ**

---

## 📁 ファイル位置

```
~/.ai-pir-runs/<sanitized_cwd>/handoff.md
```

- `sanitized_cwd` は `pwd | sed 's|/|-|g'` で生成（RUN_DIR と共通）
- **プロジェクト単位で 1 ファイル**（per-run ではない）。複数回の /pir2 にまたがって共有
- `.claude/` 外に置く理由: Claude Code の sensitive-file プロンプト回避（`~/.ai-pir-runs/` は既に `additionalDirectories` 済み）

---

## 📝 フォーマット

```md
# PIR² Handoff

> 最終更新: YYYY-MM-DD HH:MM (run: <RUN_DIR の basename>)
> タスク: <ユーザー指示の一行要約>

## 背景・決定事項

- <前回までに確定した設計・選定>
- <重要な制約>

## 残 TODO

- [ ] A を実装する (files: foo.ts, bar.ts)
- [x] B を修正する <!-- done: 2026-04-19 -->
- [ ] C のテストを追加する (依存: A)

## 既知の問題 / 要確認

- ⚠️ X の挙動がドキュメントと食い違う (未解決)
- ❓ Y の方式をユーザーに確認する必要あり

## 関連 artifact

- 最新 plan: ~/.ai-pir-runs/<sanitized>/<run>/plan.md
- 直前 exploration: ~/.ai-pir-runs/<sanitized>/<run>/exploration-01.md
```

セクションは **固定順序・固定見出し**。パーサ代替のため（retrospector やスキル本体が特定セクションだけ触る）。

---

## 🔄 ライフサイクル

### 1. 生成（新規 /pir2 実行時）

- スキル本体（メイン Claude）が **planner の plan.md 完成直後** に初期 handoff.md を書き出す
- 内容:
  - タスク要約（ユーザー指示から抽出）
  - plan.md の実装ステップを `[ ]` つきチェックリストで「残 TODO」に転記
  - 「背景・決定事項」「既知の問題」は空セクションで用意
- 既存 handoff.md が存在する場合の扱いは次の「resume モード」参照

### 2. 更新（implementer イテレーションごと）

- implementer は成功した実装項目について、handoff.md の対応チェックボックスを `[ ]` → `[x]` にする
- マーク時にコメント `<!-- done: YYYY-MM-DD -->` を付与
- 新たに判明した TODO があれば「残 TODO」セクションに `[ ]` で追記
- 「背景・決定事項」「既知の問題」は implementer が自動書き換えしない（ユーザー編集優先。発見事項は末尾追記のみ）

### 3. 削除 or 残置（PIR² 末尾）

- retrospector 完了後、スキル本体が handoff.md を確認
- **全項目 `[x]`** → `handoff.md` を削除（タスク完了）
- **残項目あり** → 残置 + 「最終更新」タイムスタンプを更新

---

## 🔍 resume モード検知

スキル本体が /pir2 冒頭で以下を判定:

| 条件 | 判定 | 挙動 |
|------|------|------|
| ユーザー指示に `引継い` / `続き` / `resume` / `handoff` / `carry on` のいずれか含む | **explicit resume** | ブレスト skip、planner に `HANDOFF_PATH` を渡して「未チェック項目を引き継げ」と指示 |
| 上記キーワードなし + handoff.md が存在 | **passive notice** | 「💡 前回の handoff が残っています: `<path>`」と表示し、通常の新規タスクフローで続行（handoff は触らない） |
| 上記キーワードなし + handoff.md なし | **new** | 通常の新規タスクフロー |

### explicit resume の特別処理

1. ブレストフェーズをスキップ（前回決定済みとみなす）
2. planner 起動プロンプトに以下を含める:
   - `HANDOFF_PATH=<path>`
   - 「handoff.md の未チェック項目 `[ ]` のみを planning 対象にせよ。`[x]` 項目は完了済みなので再計画しない」
3. planner は handoff.md を Read → 未チェック項目を plan.md に展開 → 新規 exploration は必要最小限
4. explicit resume の場合、スキル本体は **handoff.md を上書きしない**（既存を維持したまま implementer に渡す）

---

## 🛡️ 古い情報の誤参照防止

1. **planner は `[x]` を読まない**: 完了済み項目は参照禁止。再実装対象から除外する
2. **背景・既知の問題はユーザー編集優先**: implementer/retrospector が自動書き換えしない。追記のみ許可
3. **全完了削除**: タスク完了時に handoff.md を物理削除し、次回新規タスクへの混入を防ぐ
4. **タイムスタンプ必須**: 「最終更新」と `<!-- done: YYYY-MM-DD -->` で時系列を追跡可能にする

---

## 🔗 各コンポーネントの責務

| コンポーネント | 責務 |
|---------------|------|
| スキル本体（/pir2, /pir2async, /debug SKILL.md） | resume モード検知・初期 handoff 生成・末尾の削除判定 |
| planner | `HANDOFF_PATH` 受領時に未チェック項目のみを plan 対象にする |
| implementer | 実装完了した項目を `[x]` 化し、新規 TODO 発見時は追記 |
| retrospector | handoff には直接触らない（削除判定はスキル本体が実施）。pattern 抽出に handoff を**参考として**読むのは可 |
| reviewer / tester | handoff.md を参照しない（plan.md のみ参照） |

---

## 📋 スキル本体の擬似コード

```bash
# 冒頭（preflight と RUN_DIR 作成の後）
HANDOFF_PATH="${HOME}/.ai-pir-runs/${sanitized_cwd}/handoff.md"
RESUME_MODE="new"
if echo "${ARGUMENTS:-}" | grep -qiE '引継い|続き|resume|handoff|carry on'; then
  RESUME_MODE="resume"
elif [ -f "$HANDOFF_PATH" ]; then
  RESUME_MODE="passive-notice"
fi
```

```
# planner 呼び出し後 (RESUME_MODE=new の場合のみ)
# plan.md からチェックリストを抽出して handoff.md 初期版を Write

# implementer イテレーション中
# implementer が handoff.md を自分で更新（skill body は介入しない）

# retrospector 完了後
# handoff.md を Read → すべて [x] なら Bash rm で削除、else 最終更新タイムスタンプを更新
```

---

## ⚠️ 制約・既知の落とし穴

- handoff.md の**フォーマット破損**は各コンポーネントで検出して `echo` 警告のみ出力し、ワークフローは継続する（破損でブロックしない）
- ユーザーが手動編集して項目順を変えた場合、implementer の「対応項目」検索は**テキストマッチ**で行う。完全一致しない場合は追記扱いにする
- **resume キーワード誤検知**: タスク説明の自然文に「続き」が偶然含まれる場合など。passive notice モードはユーザーに表示するだけなので安全側に倒す（explicit resume にはキーワードが明示的に必要）
