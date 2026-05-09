# Audit

現状のコードベースを `IDEAL.md` のチェックリストで評価し、gapを検出・修正するフロー。

---

## 実行タイミング

- 定期的なデザインシステムの健全性確認
- 新機能実装後の整合性チェック
- スキルのバージョン更新後
- 「デザインが統一されていない」という問題意識が生まれたとき

---

## Step 1: SSOTを読む

`design-system.config.*` を読み、以下を把握する：

- 定義されているトークンの一覧
- 禁止されているアンチパターン
- コンポーネントの配置・命名規則
- **aesthetic セクション**（tone / differentiation / antiDirection）— 存在しない場合は `BOOTSTRAP.md` Step 1.5 を促す

---

## Step 2: ideal.mdとスタック別ガイドラインで評価する

`IDEAL.md` の全チェック項目を現状のコードベースに対して評価する。
プロジェクトの技術スタックに対応する `stacks/` 配下のガイドラインが存在する場合、そのチェック項目も併せて評価する（例: Web フロントエンドなら `stacks/web-frontend.md`）。

各項目を ✅ / ⚠️ / ❌ で記録し、以下の形式でレポートを会話内に出力する（ファイルへの保存は不要）：

```
## Audit Report

### ✅ 準拠
- SSOTが存在し機能している
- コンポーネントの命名規則が統一されている
- aesthetic セクションに tone と differentiation が記録されている

### ⚠️ 部分的
- トークン外の値: `src/components/Card.tsx` でハードコードされた色が3箇所
- インラインスタイル: `src/pages/Dashboard.tsx` で2箇所（意図的かどうか不明）
- Generic AI aesthetics: `font-family: Inter` が globals.css に直書き（aestheticには editorial/serif と書かれている）

### ❌ 非準拠
- 重複コンポーネント: `Button.tsx` と `PrimaryButton.tsx` が同じ責務を持っている
- Aesthetic-implementation 不整合: aesthetic.tone = "brutally minimal" だが Hero.tsx に gradient mesh と drop shadow が積層されている
- Motion 未トークン化: `transition: all 200ms` がコンポーネント内に直書きで散在（duration がトークン化されていない）
```

---

## Step 3: 修正の優先度を決める

以下の基準で優先度を判断する：

**即修正**
- SSOTにないトークン値のハードコード（増殖リスク）
- 重複コンポーネントの存在（どちらが正解か不明確になる）
- アンチパターンとして明記されているものの使用
- aesthetic-implementation 不整合（aesthetic.tone と実装の質感が真逆になっている。例: minimal宣言なのに装飾過多 / playful宣言なのに無音）
- generic AI aesthetics の混入で aesthetic.tone と矛盾するもの（例: aesthetic = editorial なのに Inter / system font 直書き）

**次のタイミングで修正**
- インラインスタイル（意図的かどうかをオーナーに確認）
- ⚠️ 判定の項目全般

**SSOTを更新して対応**
- 現状のコードが正しく、IDEAL.mdが古い場合
- 意図的な例外をSSOTのアンチパターン欄に追記する

---

## Step 4: 修正を実施する

修正は以下の順で行う：

1. SSOTに影響する変更（トークン追加・削除）を先に行う
2. コンポーネントの修正を行う
3. 修正後に再度 Step 2 を実行し、全項目が ✅ になることを確認する

---

## Step 5: SSOTを更新する（必要な場合）

auditの結果、SSOTが現実に追いついていない箇所があれば更新する：

- 新たに必要になったトークンを追加
- 実際には使われていないトークンを削除
- 判明したアンチパターンを `antipatterns` に追記

SSOTの更新はコンポーネントの修正より前に行うこと。



## 補足: 自動化の方針

以下はauditの手順ではなく、チェック項目をlintに移行する際の参考情報。

| チェック項目 | lintで担保できるか |
|------------|-----------------|
| トークン外の色値 | ✅ ESLint / Stylelint カスタムルール |
| インラインスタイル | ✅ ESLint |
| 命名規則 | ✅ ESLint |
| 重複コンポーネント | ⚠️ 部分的（静的解析の限界あり） |
| アクセシビリティ属性 | ✅ eslint-plugin-jsx-a11y |
| Generic AI aesthetics（フォント直書き等） | ⚠️ 部分的（grep で検出可・aestheticとの整合判定は人間/AI） |
| Aesthetic-implementation 不整合 | ❌ lint不可（aestheticの意図を読む必要があるため AI audit 必須） |

lintで担保できる項目を移行すれば、auditはlintでカバーできない項目に集中できる。

---

## 補足: Generic AI aesthetics 検出のための grep / 観察ポイント

aestheticセクションを読んだ上で、以下のパターンが aesthetic.tone と矛盾する形で出現していないか確認する。
全プロジェクトで一律に禁止する性質のものではないため、aesthetic との整合で判断する。

| 検出対象 | grep の例（参考。実際のスタックに合わせて調整） | 問題化する条件 |
|---------|------------------------------------------|------------|
| Generic font 直書き | `rg -i "Inter\|Roboto\|Arial\|system-ui\|Space Grotesk" src/` | aesthetic に書かれた display/body フォントと不一致、または SSOT 経由でない直書き |
| 紫グラデーション | `rg -i "linear-gradient.*purple\|#a855f7\|#8b5cf6\|violet" src/` | aesthetic = brutally minimal / industrial 等で矛盾 |
| 中央寄せヒーロー定型 | 視覚チェック（`min-h-screen` + `text-center` + 大きい `<h1>` の組み合わせ） | aesthetic = editorial / brutalist 等の場合に矛盾 |
| 単色 background defaulting | `rg "bg-white\|bg-gray-50\|background:\s*#fff" src/` | aesthetic に背景方針（gradient mesh / noise 等）が書かれているのに採用されていない |
| Motion 直書き | `rg "transition:\s*all\|transition-duration:\s*\d+ms\|animation:.*\d+ms" src/` | duration トークンが SSOT にあるのに参照されていない |
| Typography 単一フォント | `font-family` 宣言が1種類しかない、または display と body が同一 | SSOT で display/body 分離が定義されているのに無視されている |

これらは「即 NG」ではなく、**aestheticとの整合性を問う出発点**として使う。

---

## 補足: コンポーネント実装時のCSS落とし穴チェックリスト

新規コンポーネントを実装するとき、または既存コンポーネントを拡張するときに必ず確認するパターン。design-reviewer の観点6（コンポーネント単位のピクセル整合性）と対になる、**実装側の予防チェック**。

これらは aesthetic / SSOT の問題ではなく、CSS 仕様自体に内在する罠。視覚レビュー（especially 上位観点で評価する読者目線レビュー）では catch しにくいので、実装時に踏まないことが最重要。

### 1. `position: absolute` × `overflow` の clip

| パターン | 罠 | 回避策 |
|---|---|---|
| 親 `position: relative; overflow-x: auto` + 子 `position: absolute; top: -10px` | CSS 仕様: `overflow-x` か `overflow-y` のどちらかが `visible` 以外になると、もう片方の `visible` も `auto` 相当に強制される。結果として上下にはみ出す absolute 子が clip される | overflow を持つコンテナを内側に分離し、絶対配置要素は外側ラッパー（overflow なし）に置く |
| 親 `overflow: hidden` + 子の hover でツールチップ表示 | hover で出すツールチップが親の境界で切れる | ツールチップを portal に逃がす、または親の overflow を visible にする |

### 2. stacking context の意図しない生成

以下のいずれかを親に設定すると新規 stacking context が生成され、子要素の `z-index` が外側の z-index 体系と切り離される:

- `transform` (any value other than `none`)
- `filter` (any value other than `none`)
- `opacity < 1`
- `will-change` (transform / opacity / filter のいずれか)
- `isolation: isolate`
- `backdrop-filter` (any value other than `none`)
- `mix-blend-mode` (other than `normal`)
- `position: fixed`

**症状**: モーダル / dropdown / ツールチップが想定の最前面より下に表示される、ホバー時のシャドウが他要素に隠れる、など。

**回避策**: 重なり順が重要な要素は stacking context を作らない親に置く。それが難しい場合は portal で document.body 直下に逃がす。

### 3. `flex` / `grid` 親による予期しない overflow

- `flex` / `grid` の子は `min-width: auto`（既定値）で、内容の `min-content` 幅まで縮まない
- 長いテキスト・長いコード・幅広テーブルが子にあると、親の幅をはみ出して横スクロールが発生する
- 親が `overflow: hidden` ならコンテンツが切れる

**回避策**: はみ出しうる子に `min-width: 0` を明示する。テキストには `overflow-wrap: anywhere` / `word-break: break-word` を設定。

### 4. `border-radius` × `overflow: visible` でのクリッピング期待外れ

- 角丸を効かせるには親に `overflow: hidden` が必要なケースがある（特に内部の `<img>` など子要素を角丸で抜きたい場合）
- 一方で `overflow: hidden` を付けると 1 や 2 の罠を踏みやすい

**回避策**: 角丸が必要な要素と overflow が必要な要素を別レイヤーに分離する。

### 5. `inline-block` / `inline-flex` のベースライン揃え崩れ

- `inline-*` 要素の下に謎の余白が出る（フォントの descender 領域）
- アイコン + テキストの揃えが画像読み込みでズレる

**回避策**: 親に `vertical-align: middle` または `display: flex; align-items: center` を使う。

### 6. 新規追加要素の単独確認

実装直後は **「変更前後の比較」ではなく「現状の単独凝視」** を行う:

- 新規バッジ・ラベル・装飾線・ホバー要素を一つずつブラウザで確認
- 上下左右が切れていないか、角丸の内側に納まっているか
- 親要素との位置関係が意図通りか
- ライト / ダークモード両方で正しく表示されているか
- ホバー / focus / 開閉トグル等のインタラクションを実際に発火

> **ヒント**: 「コンポーネントを `npm run dev` で開いて目視」だけでは catch しにくい。Playwright や DevTools で **要素を画面中央にスクロール → 拡大スクショ** を撮ると、上半分 clip / 半透明の重なり等がはっきり見える。

---

これらの罠は CSS 仕様レベルのため、フレームワーク非依存で発生する。Tailwind / styled-components / CSS Modules いずれでも同じ。**新規コンポーネント着手前に該当パターンが含まれていないか確認** することで、レビュー段階での FAIL を予防できる。
