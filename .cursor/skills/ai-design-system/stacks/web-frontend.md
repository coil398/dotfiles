# Web Frontend ガイドライン

Web フロントエンド（React / Vue / Svelte / HTML+CSS）向けのコンポーネント設計ガイドライン。
`IDEAL.md` のスタック非依存原則を補完する、Webに特化した検証基準と設計指針。

---

## 1. コンポーネント分割

### 分割の判断基準

- [ ] コンポーネントは**単一の責務**を持っている（表示 or 操作 or レイアウトのいずれか）
- [ ] 2箇所以上で使われる、または将来使われる見込みがあるUIパーツはコンポーネントとして切り出されている
- [ ] 1つのコンポーネントファイルが200行を大幅に超えていない（超える場合は分割を検討）
- [ ] 共通化は **Rule of Three**（3回同じパターンが出てから）を目安にしている。見た目の類似だけで早すぎる共通化（Hasty Abstraction）をしていない
- [ ] 共通化の判断基準は見た目ではなく、**ふるまいとライフサイクルの類似性**に基づいている

### 階層の設計

階層モデルはプロジェクトの規模に応じて選択する。以下は代表的なパターン：

**パターンA: 2階層（小〜中規模向け）**

| 階層 | 説明 | 例 |
|------|------|-----|
| 基礎コンポーネント | 最小のUI部品。単体で意味を持つ | Button, Input, Badge, Icon |
| 複合コンポーネント | 基礎コンポーネントを組み合わせたもの | SearchBar, FormField, Card |

**パターンB: 汎用 / 機能固有（管理画面向け）**

| 階層 | 説明 | 例 |
|------|------|-----|
| 汎用コンポーネント | 機能に依存しない共通UI | Table, Modal, Tabs |
| 機能固有モジュール | 特定の機能ドメインに紐づくUI | UserProfile, OrderSummary |

**パターンC: 目的別3階層（Feature-Sliced Design）**

| 階層 | 説明 | 例 |
|------|------|-----|
| UI Kit | どのプロダクトでも使い回せる汎用UI部品 | Button, Input, Avatar |
| Features / Domain | 特定のサービスやデータに紐づくコンポーネント | ProductCard, UserProfile |
| Widgets / Templates | 上2つを組み合わせた大きなかたまり | Header, FormSection |

上位レイヤーは下位を使えるが、**逆方向の依存は禁止**（Button が ProductCard に依存してはいけない）。

- [ ] プロジェクトのコンポーネント階層が上記いずれかのパターン（または明確な代替パターン）に基づいている
- [ ] 3階層以上の場合、各階層の境界が明文化されている
- [ ] 汎用コンポーネントとドメインコンポーネントが明確に区別されている（汎用コンポーネントはビジネスロジックを内包しない）
- [ ] 依存の方向が一方通行になっている（汎用→ドメインへの依存がない）

---

## 2. Props（プロパティ）設計

### 基本の型選択

| 用途 | 推奨する型 | 避ける型 | 理由 |
|------|-----------|---------|------|
| ON/OFF の切り替え | `boolean` | `string` | `disabled`, `loading` など |
| 3つ以上の選択肢 | `union / enum` | `boolean` の複数組み合わせ | `size: "sm" \| "md" \| "lg"` |
| ユーザーが入力する自由テキスト | `string` | — | `label`, `placeholder` |
| 子要素の差し替え | `ReactNode` / `slot` / `children` | `string` で HTML を渡す | 型安全性と柔軟性 |

### 直交性

プロパティの直交性とは、あるプロパティの値を変更しても他のプロパティの意味や振る舞いが影響を受けない状態を指す。

- [ ] 2つのプロパティの全組み合わせが矛盾なく成立する（例: `size` × `variant` の全セルが有効）
- [ ] 1つのプロパティが複数の関心事を混在させていない（例: `style` に色の種類と色の強さが混在→ `variant` と `colorScheme` に分離）
- [ ] 暗黙の優先順位がない（「variant が ghost のときは colorScheme が無視される」のような隠れた依存がない）

### 組み合わせ爆発の防止

- [ ] 1つのコンポーネントの props が10個を超えていない（超える場合は分割を検討）
- [ ] booleanの props が3つ以上ある場合、`variant` や `size` のような enum に集約することを検討している
- [ ] 相互排他的な props の組み合わせ（例: `isLoading` と `isDisabled` が同時に true）のふるまいが定義されている

### Slot / Composition パターン

プロパティが10〜20個に膨らんだら、Configuration（設定型）から Composition（組み合わせ型）への切り替えを検討する。
プロパティはコンポーネントの「現在」を最適化し、スロットは「未来の不確実性」に対する防御力を提供する。

- [ ] コンポーネントの内部構造をカスタマイズする必要がある場合、props の追加ではなく children / slot で差し替え可能にしている
- [ ] アイコン・アクション・ヘッダー等の差し替え可能領域が明確に定義されている
- [ ] スロットには空の選択肢（プレースホルダー）が含まれており、不要な場面にも対応できる

### 命名の先読み

- [ ] 対になる可能性がある要素には、最初から位置や役割を含んだ名前をつけている（例: `icon` ではなく `iconStart`。後から `iconEnd` を追加しても非対称にならない）
- [ ] 位置を表す命名は物理方向（`left` / `right`）ではなく論理方向（`start` / `end`）を優先している（RTL言語・レスポンシブ対応を阻害しない）
- [ ] enum の選択肢名は見た目ではなく意味で名付けている（`Blue` ではなく `Primary`、`Red` ではなく `Destructive`）
- [ ] サイズの初期値は `default` ではなくスケール上の位置を示す名前（`medium`）にしている

---

## 3. 状態の具体的な網羅基準

`IDEAL.md` セクション9の「状態の網羅」をWebフロントエンドで具体化したもの。

### インタラクション状態

各インタラクティブコンポーネントについて、以下の状態が定義されている：

- [ ] `default` — 初期表示
- [ ] `hover` — マウスオーバー時
- [ ] `focus` / `focus-visible` — キーボードフォーカス時
- [ ] `active` / `pressed` — クリック / タップ中
- [ ] `disabled` — 操作不可

インタラクション状態の視覚表現はコンポーネント横断で統一する：
- ホバー時: 背景色へのオーバーレイ追加（例: 8%）
- 無効時: オパシティの低下（例: 38%）
- フォーカス: フォーカスリングの色・太さ・オフセットを全コンポーネントで統一

### データ状態（UIスタック）

データを表示するコンポーネントについて、UIスタック（Scott Hurff）の5状態を基準とする：

- [ ] `ideal` — 完全なデータが揃った理想状態
- [ ] `empty` — データが0件
- [ ] `loading` — データ取得中（スケルトン / スピナー）
- [ ] `partial` — 一部データが欠損した不完全状態（例: ユーザー名はあるが画像がない）
- [ ] `error` — データ取得失敗

不完全状態のフォールバックルール例:
- 画像欠損 → イニシャルアイコンまたはプレースホルダー画像
- スコア未評価 → 「—」表記で0との区別
- テキスト欠損 → セクション全体を非表示

### フォーム状態

フォーム要素について：

- [ ] `pristine` — 未入力
- [ ] `touched` / `dirty` — 入力済み
- [ ] `valid` — バリデーション通過
- [ ] `invalid` — バリデーションエラー（エラーメッセージ表示を含む）

---

## 4. レイアウトの分離

### 原則: コンポーネントの中身と置き方を分ける

コンポーネントは**自身の内部レイアウト**に責任を持つが、**自身がどこに配置されるか**には責任を持たない。
ポステルの法則: 「受け取るものには寛容に、送り出すものには厳密に」。

- **コンポーネントの責任**: padding（内側の余白）、背景色・枠線、コンテンツの配置
- **親（レイアウト）の責任**: margin（外側の余白）、要素間の間隔（gap）、画面上の位置

- [ ] コンポーネントが外側の `margin` を持っていない（margin は親またはレイアウトコンポーネントの責務）
- [ ] `width: 100%` や `flex: 1` など、親のレイアウトに依存するスタイルはコンポーネント内部にハードコードされていない
- [ ] 配置の調整にはレイアウトコンポーネント（`Stack`, `Grid`, `Flex` 等）またはユーティリティクラスを使っている
- [ ] 区切り線（Divider）はコンポーネント内部に含めず、親が制御する方式を検討している（Boolean プロパティでの制御 or 独立した Divider コンポーネント）

### 幅の振る舞い

コンポーネントの幅は以下の3パターンで定義する：

| パターン | 説明 | 適用例 |
|---------|------|--------|
| **Fill** | 親の幅いっぱいに広がる | Input, Card, Divider |
| **Hug** | 中身に合わせて自動伸縮 | Button, Tag, Badge |
| **Fixed** | 固定幅 | Icon, Avatar, Thumbnail |

- [ ] 各コンポーネントのデフォルトの幅の振る舞い（Fill / Hug / Fixed）が定義されている
- [ ] 必要に応じて `min-width` / `max-width` で振る舞いの限界値が設定されている（例: Input は Fill だが min-width: 200px）
- [ ] 文脈による幅の切り替え（例: ボタンは通常 Hug だがモバイルフォームでは Fill）は、コンポーネント自体ではなく親の Auto Layout / Flex で制御している

### オーバーフロー

- [ ] テキストのオーバーフロー戦略がコンポーネントごとに定義されている（省略 `…` / 折り返し / 行数制限 / 制限なし）
- [ ] コンテナのオーバーフロー戦略が定義されている（スクロール / ページネーション / 切り捨て）
- [ ] スクロール領域がある場合、高さの決定方法（固定高 / `max-height: Nvh`）が定義されている

### レイアウトコンポーネント

- [ ] 繰り返し現れるレイアウトパターン（等間隔の縦積み、横並び等）はレイアウトコンポーネントとして切り出されている
- [ ] レイアウトコンポーネントの `gap` / `spacing` はトークンを参照している

---

## 5. アセット管理

### コード実装 vs 画像埋め込みの判断

「このビジュアルは今後変わる可能性があるか」で判断する:
- **コード実装**（SVG + トークン）: テーマ対応が必要、色やサイズが動的に変わる → アイコン全般
- **画像埋め込み**（PNG/JPG）: 装飾的で長期間変わらない → イラスト、写真

### アイコン

- [ ] アイコンはSVGベースで管理されている（PNG/JPG のアイコン使用は避ける）
- [ ] アイコンのサイズはトークン化されている（例: `icon-sm: 16px`, `icon-md: 20px`, `icon-lg: 24px`）
- [ ] アイコンの色は `currentColor` を使い、テキスト色と連動している（SVGに固定カラーコードが埋め込まれていない）
- [ ] アイコンの命名規則が統一されている（例: `icon-{category}-{name}` または `{Name}Icon`）
- [ ] 汎用的なアイコン（矢印、ゴミ箱等）は既存ライブラリを活用し、ブランド固有のアイコンのみ自作している（ハイブリッド運用の場合、線の太さや角丸のルールをライブラリに合わせている）

### 画像・イラスト

- [ ] 装飾的な画像には `alt=""` が設定されている
- [ ] 意味を持つ画像には適切な `alt` テキストが設定されている
- [ ] 画像のアスペクト比が崩れないよう `object-fit` が適切に指定されている

---

## 6. Typography（Webでの具体化）

`IDEAL.md` セクション 13 と `AESTHETIC.md` の Typography 節をWebフロントエンドで具体化したもの。

### Display と Body の分離

- [ ] display 用フォント（見出し・hero）と body 用フォント（本文）が SSOT で別トークンとして定義されている
- [ ] 同一フォントの太さ違いだけで構成していない（generic に倒れる典型パターン）
- [ ] display フォントは distinctive な選択になっている（character のあるserif / variable font / 装飾性のあるsans 等。Inter / Roboto / system-ui に倒していない）
- [ ] aesthetic.tone と font 選択が整合している（editorial には serif の display、industrial には monospace、playful には rounded sans 等）

### フォント読み込み

- [ ] `@font-face` または `next/font` 等の framework 機構で読み込まれ、CDN 直リンクが散在していない
- [ ] `font-display: swap` または `optional` が設定されている（aestheticに応じて選ぶ。flash of unstyled text を許容するか）
- [ ] variable font を使う場合、軸（weight / optical size / slant）が SSOT のトークンとして定義されている
- [ ] 必要なグリフサブセット（latin / japanese 等）のみ読み込み、不要なサブセットを排除している

### 行間・字間・サイズ

- [ ] `line-height` がコンポーネントごとに直書きされず、用途別トークン（`leading-tight` / `leading-relaxed` 等）化されている
- [ ] `letter-spacing` が大きな display 文字とsmall caps用途で使い分けられている
- [ ] `font-size` が `rem` 等の相対単位で定義されている（pxハードコード禁止）
- [ ] 流体タイポグラフィ（`clamp()` 等）を使う場合、min/preferred/max がトークン化されている

---

## 7. Motion（Webでの具体化）

`IDEAL.md` セクション 12 と `AESTHETIC.md` の Motion 節をWebフロントエンドで具体化したもの。

### CSS / JS の使い分け

- [ ] HTML/Vanilla JS プロジェクトでは CSS-only motion を優先（`@keyframes` / `transition`）
- [ ] React プロジェクトで複雑なシーケンスが必要な場合、Motion (Framer Motion) のような専用ライブラリを使い、jQuery 風の手書き JS animation を避ける
- [ ] スクロール連動には `IntersectionObserver` または `view-timeline` (CSS) を使う。`scroll` イベントの polling を避ける

### 強度の設計

- [ ] 散発的な micro-interaction を全要素に降らせていない（fade-in だけが10種類、のような状態を避ける）
- [ ] **印象を残す1つの大きいモーション**（page load の staggered reveal / hero の特殊遷移 / 主要CTAのhover応答）が設計されている
- [ ] `animation-delay` を使った staggered reveal で、要素が時間差で現れるよう構成されている（aestheticが許す場合）
- [ ] hover/focus 状態の transition が SSOT の duration トークンを参照している

### Reduced motion / アクセシビリティ

- [ ] `@media (prefers-reduced-motion: reduce)` 内で duration を 0 または極短に倒す処理が SSOT 側にある（コンポーネント側で個別対応していない）
- [ ] 完全停止ではなく opacity/transform の最小限変化に倒すパターンが定義されている（ユーザーが状態変化を見落とさないため）
- [ ] 自動再生される animation は無限ループを避けるか、`prefers-reduced-motion` で停止する

---

## 8. Background / Decoration（Webでの具体化）

`IDEAL.md` セクション 13 と `AESTHETIC.md` の「Background & Visual Details」節をWebで具体化。

### 背景の方針

- [ ] solid color にdefaultしていない（aestheticが minimal の場合を除く）
- [ ] gradient mesh / noise texture / geometric pattern / layered transparency のいずれを採用するかが SSOT に明示されている
- [ ] ノイズテクスチャを使う場合、SVG の `<feTurbulence>` または小さい PNG の繰り返しなど、軽量な実装を選んでいる
- [ ] gradient は `oklch` / `lch` ベースで定義し、グレーになる中間段（`linear-gradient` の sRGB 補間問題）を避けている

### Shadow / Border

- [ ] `box-shadow` がコンポーネントに直書きされず、SSOTトークン（`shadow-subtle` / `shadow-standard` / `shadow-dramatic` 等）を参照している
- [ ] 装飾用 border（太い枠・二重線・破線）と機能用 border（divider・focus ring）がトークンで区別されている
- [ ] focus ring が全 interactive 要素で統一されている（色・太さ・オフセットが SSOT 経由）

### カーソル / 細部

- [ ] `cursor` の指定が aesthetic と整合している（playful には custom cursor、industrial には default を維持、等）
- [ ] selection color (`::selection`) が SSOT のアクセント色を参照している
- [ ] scrollbar styling が必要な場合、`scrollbar-width` / `scrollbar-color` または `::-webkit-scrollbar-*` でトークン経由

### Grain / Texture overlay

- [ ] grain overlay を使う場合、`pointer-events: none` で interaction を阻害していない
- [ ] mix-blend-mode を使った重ね合わせの場合、ダークモードでの見え方が確認されている
- [ ] パフォーマンス: GPU 合成 (`will-change` / `transform: translateZ(0)`) が必要な装飾レイヤーで設定されている

---

## 9. Aesthetic と実装強度の整合（Webでの具体化）

`AESTHETIC.md` Step 4 のWeb版チェック。

| aesthetic | 期待される Web 実装 | NG パターン |
|-----------|-------------------|------------|
| brutally minimal | `<div>` ネスト最小、class 数最小、animation ほぼなし、shadow なし、border は機能用のみ | drop shadow / gradient / decorative border / grain overlay |
| maximalist | 多層背景（gradient + noise + pattern）、staggered reveal、custom cursor、scroll-driven animation | 単色背景、fade-in 一切なし、defaultカーソル |
| editorial | 大胆な display タイポ、grid の意図的破壊、写真+テキストの mixed layout、generous negative space | 等間隔 grid、display と body が同一 font、column 数が均等 |
| retro-futuristic | scanline overlay、glitch effect、CRT 風 vignette、pixelated 装飾 | スムーズな fade、modern shadow、サンセリフ flat デザイン |
| playful | rounded corners 大、bouncy easing（spring 系）、原色アクセント、参加感のある hover | 直角、 linear easing、controlled grayscale |
| industrial / utilitarian | 高密度情報、monospace 多用、border による grid 表示、装飾レス | hero の余白、装飾的アイコン、過剰な animation |

- [ ] aesthetic.tone と実装の質感が一致している
- [ ] 「全部に力を入れない」: differentiation で記録した「記憶に残る一手」に集中投資し、他は restraint で支える

---

## このガイドラインの使い方

- `BOOTSTRAP.md` の Step 1 でプロジェクトがWebフロントエンドだと判定された場合、SSOTにこのガイドラインの該当項目を反映する
- `AUDIT.md` の Step 2 で `IDEAL.md` に加えてこのファイルのチェック項目も評価対象とする
- すべての項目を一度に満たす必要はない。プロジェクトの成熟度に応じて段階的に適用する
