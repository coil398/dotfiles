---
name: field-notes
description: >-
  短期の判断キャッシュ（decision cache）。方針が変わった・同じ無駄を避けたい・キャンペーン再開・
  長い実験や校正のあと・仮説が固まった・次の試行方針が変わった、といった場面で自動発動する。
  明示トリガー: 「学び残して」「field notes」「試行錯誤メモ」「仮説を残して」「この方針メモって」
  「lesson」「recall field notes」「field-notes triage」「/field-notes」。
  MEMORY/LTMの代替ではない。日記（/ai-diary）・横断検索（/ai-ltm）とは別。
  操作は capture / recall / triage。ユーザーが言わなくても下記の自動発動条件に該当したら使う。
---

# /field-notes — 短期の判断キャッシュ

**昇格待ちの decision cache**。MEMORY/LTM の縮小版にしない。

入れる基準は1つだけ:

> この判断を知らない状態で次の実験をすると、同じ無駄を繰り返すか？

結果ログ・日付の出来事・感想は入れない（diary / LTM）。

保存担当は親に集約する。読み取り担当や worker には、確認済みの note と返却形式だけを渡し、保存・promote・triage をさせない。親が明示した既存の保存先だけを使い、保存先を推測して新規作成しない。

## 責任と読者

親がキャンペーン、scope、capture / recall / triage の選択、保存先、次の判断への統合を持つ。親が直接 recall する場合は INDEX と今回の scope に必要な少数の note を読む。委任する場合は、親が実在確認した INDEX/note の物理 path、対象範囲、変更禁止、返却形式を読み取り担当へ渡し、担当自身に必要な note を Read させる。

読み取り担当は選んだ note の根拠だけを親へ返し、保存・promote・triage・記憶追記を行わない。子へ親用のキャンペーン進行や委任手順を渡して工程を再起動させない。capture と triage の書き込み、既存 SSOT への promote、結果の採否は親が明示した専有 path と承認範囲で行う。

## 自動発動（ユーザー指示なしでよい）

エージェントは次のとき **黙ってこのスキルに従う**（毎回「使いますか？」と聞かない）:

| いつ | 操作 | やること |
|---|---|---|
| キャンペーン再開・長時間校正/実験の作業開始 | **recall** | `field-notes/<campaign>/INDEX.md` を読み、今回の scope に関係する少数の note だけ読む。件数は内容と文脈で決める |
| 次の試行方針が変わった（プロンプト方針・評価閾値・並列制約など） | **capture** | atomic note + INDEX 1行。active が増えて選別が必要なら先に triage |
| キャンペーン区切り・active が増えて選別が必要になった | **triage** | promote / keep / discard |
| セッションを長く続けたあと、方針差分が会話に出たが未記録 | **capture** | 方針差分だけ。結果ログは書かない |

やらない自動発動:

- 毎ターン・毎コマンド成功ごと
- 単なる進捗報告（「r05 終わった」だけ）
- 感想・日記・横断検索が欲しいとき → `/ai-diary` / `/ai-ltm`

プロジェクトに `CLAUDE.md` の置き場ルールがあればそれに従う。無ければユーザー確認後に `~/field-notes/`（勝手に mkdir しない）。

## 境界

| 層 | 入れるもの | 読ませ方 |
|---|---|---|
| キャンペーン状態（例: `PROMPT_PROJECT.md`） | 今の仮説・次に試すこと | キャンペーン実行時 |
| **field-notes** | 実験後に確定した「次から判断を変える事項」 | INDEX → 今回の scope に関係する少数だけ |
| MEMORY 相当（少数の安定ルール） | 多くの作業で繰り返し必要な約束 | 原則常時（スキル/SSOT） |
| `/ai-ltm` | 過去の経緯の検索倉庫 | 必要時検索（自動: 下表） |
| references / SSOT | 一般化済みの正式仕様 | 該当 role 実行時 |
| `/ai-diary` | 感想・その日の物語 | 記録用（技術判断に使わない） |

## 操作（3つだけ）

### capture

方針が変わったときだけ書く（実験終了ごとではない）。

1. 「次の実験方針が変わったか？」→ NO なら何も残さない
2. 既存 note で表現済みなら evidence だけ更新
3. 新規なら atomic note を1件作り、INDEX に1行追加
4. active が増えて INDEX から判断しにくくなった場合は、先に triage（promote / keep / discard）して整理する

### recall

1. キャンペーン開始時は **INDEX だけ**読む
2. 今回の task の scope に関係する必要な少数を選ぶ。固定件数や active 件数だけを理由に追加しない
3. 選んだ atomic note だけ読む（active 全件を機械的に渡さない）
4. scope は YAML metadata で絞る（全文検索基盤にしない）

### triage

active の内容が重複する、古くなる、またはキャンペーンが区切られたときに、各 active note を:

- **promote** → スキル references / SSOT（ノートはリンクだけ残すか discarded）
- **keep** → active のまま
- **discard** → 不要化
- **expired** → 30日未参照の放置防止（主役は TTL ではなく「次の実験でまだ意味があるか」）

## レイアウト

プロジェクトにキャンペーンがあるとき（優先）:

```text
<field-notes>/<campaign-slug>/
  INDEX.md
  YYYY-MM-DD-<short-slug>.md
```

グローバル（キャンペーン外・ユーザー確認後のみ。勝手に mkdir しない）:

```text
~/field-notes/<campaign-or-topic>/
  INDEX.md
  YYYY-MM-DD-<short-slug>.md
```

`FIELD_NOTES_DIR` があればそれをルートにする。

### INDEX.md

箇条書きのみ（詳細は書かない）:

```markdown
# <campaign> — active decisions

- reduce-l2-input — reviewer には評価軸に必要な L2 だけ渡す
- explicit-non-goals — 対象外の明示で判断範囲を固定
```

### atomic note（200〜400語上限）

```markdown
---
decision: <一行の判断>
scope:
  role: <optional>
  perspective: <optional>
  model-family: <optional>
evidence: <ログ/スコア1行>
next_trigger: <いつ再適用するか>
invalidated_by:
  - model変更
status: active
---

# <short-slug>

## 判断
…

## 根拠（短く）
…
```

## 手順（エージェント）

1. プロジェクトの `CLAUDE.md` / `PROMPT_PROJECT.md` の置き場ルールを読む
2. 意図を capture / recall / triage に分類（自動発動表を含む）
3. 上記ルールで実行。長文日記化・全件コンテキスト投入・SQLite/embedding 追加はしない
4. 書いた／読んだパスを**短く**報告する（自動発動時も1行でよい）

## 禁則

- 単一の巨大ドキュメントに溜めない
- active 全件を worker に渡さず、今回の判断に必要な少数だけを渡す
- 秘密（`.env`）を書かない
- field-notes を検索基盤化しない（それは `/ai-ltm`）
- SSOT と二重管理しない。promote したら正式側が正
- 自動発動を理由に毎ターン書き込みしない
