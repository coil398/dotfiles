# CSS-in-JS（styled-components / Emotion / vanilla-extract / Stitches）

CSS-in-JS は **runtime と build-time の二系統** に分かれる。SSOT の置き方も二系統で異なる。

`IDEAL.md` のスタック非依存原則を補完する、CSS-in-JS 系で SSOT をどう配置するかのガイド。
runtime 系（styled-components, Emotion, Stitches）と zero-runtime 系（vanilla-extract, Linaria, Panda）で扱いが分かれる。

---

## 1. 推奨される SSOT 配置

| ライブラリ | runtime / zero-runtime | 推奨 SSOT ファイル | 注釈 |
|---------|----------------------|----------------|------|
| styled-components | runtime | `design-system.config.ts` + `ThemeProvider` | `ThemeProvider` 経由で reference + system tokens を注入 |
| Emotion | runtime | `design-system.config.ts` + `ThemeProvider` | 同上 |
| Stitches | hybrid | `stitches.config.ts`（兼 SSOT） | `createStitches({ theme, media })` がそのまま SSOT になる |
| vanilla-extract | zero-runtime | `design-system.config.ts` + `theme.css.ts` | `createTheme` で contract → CSS 変数を生成 |
| Linaria | zero-runtime | `design-system.config.ts` + CSS 変数 export | runtime テーマ切替が必要なら CSS 変数経由 |
| Panda CSS | zero-runtime | `panda.config.ts`（兼 SSOT） | `defineConfig` のテーマ部分を SSOT として扱う |

> 共通原則: **どのライブラリでも、reference tokens（生の値）と system tokens（役割割り当て）を同一ファイルに混ぜない**。runtime 系は theme オブジェクトの2階層プロパティで分離、zero-runtime 系は contract と implementation で分離。

---

## 2. 共通の落とし穴

- [ ] **テーマ未提供のコンポーネントが存在しない**: `useTheme()` / `useStyle()` で fallback を書いているコンポーネントは SSOT 違反予備軍（テーマ未注入時にハードコード値を返す）。fallback ではなく、テーマ注入を保証する責務を上位に置く
- [ ] **直接の hex 値が `styled` 内に直書きされていない**: `color: '#3b82f6'` のような直書きは `theme.colors.accent` 等のトークン参照に置き換える
- [ ] **メディアクエリも SSOT 経由**: `@media (min-width: 768px)` のような直書きを排し、theme.breakpoints を経由する。Stitches なら `media` 設定、vanilla-extract なら token 経由
- [ ] **コンポーネント変種の表現が styled の variants 機能経由**: 「props を受けて `style` を変える if 文の塊」になっていないか。Stitches `variants` / styled-components の attrs / Emotion の compose を使う

---

## 3. Aesthetic 観点の特別な注意

### Theme 切替が aesthetic に従属するか

CSS-in-JS のテーマ切替（`<ThemeProvider theme={dark}>`）は強力だが、**aesthetic.tone と整合する範囲でしか切り替えない**。

- ✅ light/dark の色値だけが変わる（spacing / typography / motion は不変）
- ⚠️ light は editorial、dark は brutalist のように tone そのものが変わる切替 — `aesthetic.toneShifts` で明示しない限り避ける
- ❌ ユーザー設定で全 tone を切り替え可能にする（その時点で aesthetic コミットメントが瓦解する）

### Display + body フォントの注入

runtime 系（styled-components / Emotion）では `<GlobalStyle>` で font-face と base font-family を注入する。**display と body を別の theme key で持つ**:

```ts
const theme = {
  font: {
    display: '"Distinctive Display", serif',
    body: '"Refined Body", sans-serif',
    mono: '"JetBrains Mono", monospace',
  },
  // ...
};
```

「`theme.font.primary` だけ存在し、weight 違いで頑張る」は IDEAL.md セクション 13 違反。display / body を別キーで持たせる。

### Motion トークン

Framer Motion / Motion / React Spring 等を使う場合、duration と easing は `theme.motion` 経由で注入する:

```ts
const theme = {
  motion: {
    duration: { fast: 0.12, base: 0.24, deliberate: 0.48 }, // seconds (Framer Motion はs単位)
    easing: { standard: [0.2, 0, 0, 1], emphasized: [0.3, 0, 0, 1.2] },
  },
};
```

コンポーネント側で `motion.div` に `transition={{ duration: 0.3 }}` のような直書きをしていたら SSOT 違反。

---

## 4. zero-runtime 系特有の事情

vanilla-extract / Panda / Linaria は build-time に CSS 変数 + クラスを生成する。

- [ ] **テーマ contract が SSOT として機能している**: `createTheme` / `defineTokens` のシグネチャが reference tokens の役割を果たす
- [ ] **生成された CSS 変数の命名がプロジェクト全体で衝突しない**: prefix 設定を必ず行う
- [ ] **build-time の制約で書けないパターン**（runtime プロパティ参照等）を避けている

vanilla-extract での display + body 分離例:

```ts
// theme.css.ts
import { createTheme } from '@vanilla-extract/css';

export const [themeClass, vars] = createTheme({
  font: {
    display: '"Fraunces", serif',
    body: '"IBM Plex Sans", sans-serif',
  },
  motion: {
    durationFast: '120ms',
    durationBase: '240ms',
    easeStandard: 'cubic-bezier(0.2, 0, 0, 1)',
  },
  // ...
});
```

---

## 5. 監査時の追加チェック

`AUDIT.md` の grep 例を CSS-in-JS 用に置き換える:

| 検出対象 | grep 例 |
|---------|---------|
| Generic font 直書き | `rg -tts -ttsx 'font-family.*Inter\|fontFamily.*Inter'` |
| theme バイパス（直書き） | `rg -tts -ttsx 'styled\.[a-z]+`[\s\S]*?(#[0-9a-f]\|px\|rem)'` |
| Inline `style=` 残存 | `rg -ttsx 'style=\{\{'` |
| Motion 直書き | `rg -ttsx 'transition:\s*all\|duration:\s*\d'` |

---

## このガイドラインの使い方

- `BOOTSTRAP.md` Step 1 で CSS-in-JS スタックと判定された場合、上の表から SSOT 配置を選ぶ
- Web 共通の項目は `stacks/web-frontend.md` を併読
- Astro/Next.js/Remix のような mixed framework では「どの境界までが CSS-in-JS テーマ提供範囲か」を SSOT に明記する
