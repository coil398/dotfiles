# Deviations — 経路依存性の正規化

`IDEAL.md` セクション 10「経路依存性を認識し、妥協の基準がある」を、実装可能な仕組みに落としたフォーマット仕様。
逸脱（deviation）を「忘れない」ためのレジャー。意図的な妥協を記録し、reviewBy 期日で再評価する。

---

## いつ書くか

以下のいずれかに該当した時:

- [ ] IDEAL.md / AESTHETIC.md / stacks/*.md のチェック項目を **意図的に違反** した
- [ ] 既存コードに deviation があり、即修正できないが将来見直す予定がある
- [ ] 一時的な workaround として generic AI 寄りの実装を採用した（例: Inter を読み込み中、custom font 移行はリリース後）
- [ ] aesthetic と矛盾するコンポーネントを切実な理由で残した

書かないでよい場合: そもそも IDEAL.md のチェック項目に該当しない事象（例: 既存コードの軽微なリファクタ、単純なバグ修正）

---

## どこに書くか

プロジェクトルートに **`deviations.json`** を置く（または `design-system.config.json` の `exceptions` フィールドに同一構造を埋め込む）。

```
project-root/
├── design-system.config.css
├── design-system.config.json    （aesthetic / antipatterns / conventions）
└── deviations.json              （ここ）
```

---

## フォーマット

```json
{
  "$schema": "https://github.com/coil398/ai-design-system/schemas/deviations.schema.json",
  "deviations": [
    {
      "id": "DEV-2026-001",
      "rule": "IDEAL.md §3 トークン外の値が使われていない",
      "scope": "src/components/legacy/OldButton.tsx",
      "description": "古い button が #3b82f6 を直書きしている",
      "reason": "Q2 のリリース blocker。OldButton は来月 Button 統合で削除予定なので修正コストを払わない判断",
      "owner": "@takumi",
      "addedOn": "2026-04-30",
      "reviewBy": "2026-06-15",
      "removalTrigger": "OldButton ファイルが削除されたら自動的に解消",
      "severity": "low"
    },
    {
      "id": "DEV-2026-002",
      "rule": "AESTHETIC.md generic font 禁止",
      "scope": "src/app/embed/*.tsx (third-party embed only)",
      "description": "外部ウィジェット内で Roboto を使用",
      "reason": "埋め込み先の SaaS が Roboto を強制しており、ブランド側で fallback できない",
      "owner": "@takumi",
      "addedOn": "2026-04-30",
      "reviewBy": "2027-04-30",
      "removalTrigger": "外部 SaaS 側のフォント仕様が変わった時 / embed を内製化した時",
      "severity": "low"
    }
  ]
}
```

### フィールド定義

| フィールド | 必須 | 内容 |
|-----------|-----|------|
| `id` | ✅ | `DEV-YYYY-NNN` 形式の一意 ID |
| `rule` | ✅ | 違反している IDEAL.md / AESTHETIC.md / stacks の項目 |
| `scope` | ✅ | どのファイル / ディレクトリ / コンポーネントに適用されるか |
| `description` | ✅ | 何が逸脱しているか（事実だけ書く、評価は reason 側に） |
| `reason` | ✅ | なぜ今これを許容するか（最重要フィールド。雑にしない） |
| `owner` | ✅ | 責任者。「誰に聞けばこの判断が分かるか」 |
| `addedOn` | ✅ | ISO 日付。逸脱を記録した日 |
| `reviewBy` | ✅ | ISO 日付。これを過ぎたら再評価する |
| `removalTrigger` | ⚠️ 推奨 | 何が起きたら自動的に解消するか（「○○削除時」「次メジャー」等） |
| `severity` | ⚠️ 推奨 | `low` / `medium` / `high`（Critical は許可しない — 逸脱不可） |

### 書いてはいけない reason

- ❌ 「面倒だから」「時間がない」
- ❌ 「他のプロジェクトでこう書いてあったから」
- ❌ 「とりあえず動くから」
- ❌ 空欄

書ける reason:

- ✅ 「○○リリースのブロッカー、来月 X 統合で消える予定」（具体的なコスト + 解消パス）
- ✅ 「外部 SaaS 制約、自社では変更不可」（外的要因）
- ✅ 「規模が小さく完全準拠コストが効果に見合わない」（コスト判断 + 影響範囲明示）
- ✅ 「実験中。3週間後の効果測定で削除 or 正式化」（学習目的 + 期限）

---

## ライフサイクル

```
[追加] addedOn 記録 → reason / reviewBy / removalTrigger を埋める
   ↓
[継続] reviewBy までは現状維持
   ↓
[再評価]  reviewBy を過ぎた / removalTrigger 発生
   ├─→ 解消できる → コードを修正、deviation を削除
   ├─→ 状況変化なし → reason を更新、reviewBy を再設定（ただし2回目以降は厳しめに）
   └─→ 恒久的に許容 → IDEAL.md / AESTHETIC.md 側を更新（"そもそもチェック項目から外す"）
```

reviewBy が過ぎたまま放置される deviation は **technical debt の最も典型的な姿**。`audit.sh` の将来拡張で reviewBy 超過を warning 出力する想定。

---

## 監査時の取り扱い

`AUDIT.md` の Step 2 で IDEAL.md / AESTHETIC.md と現状コードを比較する際、deviations.json に登録された逸脱は **「文書化された逸脱」として ⚠️ 扱い** にする（❌ にはしない）。
未登録の逸脱は ❌（=「気付いていない / 文書化していない」）。

両者を分離することで、「どこを直すべきか」と「すでに認識済みで意図的に残しているか」を audit レポートで区別できる。

---

## なぜこの形式か

- **id 必須**: PR や issue から具体的な deviation を参照できるようにする
- **reviewBy 必須**: 「とりあえず置いて忘れる」を物理的に防ぐ
- **owner 必須**: 「誰も知らないので触れない」状態を回避
- **removalTrigger 推奨**: 受動的な解消パスを書いておけば、無関係な変更で勝手に消える
- **severity に Critical なし**: Critical は逸脱で済ませる対象ではない（=即修正）

---

## 最小例（小規模プロジェクト用）

deviations.json を別ファイルにせず、`design-system.config.json` の `exceptions` フィールドに統合してもよい:

```json
{
  "aesthetic": { /* ... */ },
  "conventions": { /* ... */ },
  "antipatterns": [ /* ... */ ],
  "exceptions": [
    {
      "id": "DEV-2026-001",
      "rule": "AESTHETIC.md generic font 禁止",
      "scope": "src/app/embed/*",
      "reason": "外部 SaaS embed の制約",
      "owner": "@takumi",
      "addedOn": "2026-04-30",
      "reviewBy": "2027-04-30"
    }
  ]
}
```

`design-system.schema.json` の `exceptions` 配列はこのフォーマットを許容する。
