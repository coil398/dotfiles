# Bootstrap

SSOTが存在しない場合にデザインシステムのSSOTを生成するフロー。

---

## Step 1: プロジェクトのコンテキストを把握する

以下を調査せよ：

**技術スタック**
- フロントエンドフレームワーク（React / Vue / Unity / その他）
- スタイリング手法（Tailwind / CSS Modules / CSS-in-JS / UXML / その他）
- 既存のUIライブラリ（shadcn / Chakra / MUI / なし）

**現状のデザイン資産**
- 既存コンポーネントで使われている色・スペーシング・フォントを収集する
- 繰り返し現れる値をトークン候補とする
- ハードコードされた値の一覧を作る

**プロジェクトの性質**
- Web / ゲーム / モバイル / デスクトップ → SSOTのフォーマット選択とトークンの粒度に影響する
- レスポンシブ対応の有無 → ブレークポイントトークンを定義するか判断する
- ダークモード/テーマ切り替えの有無 → セマンティックトークンの階層設計に影響する

**スタック別ガイドラインの適用**
- プロジェクトの技術スタックに対応する `stacks/` 配下のガイドラインが存在する場合、SSOTの設計時にその内容も参照する
- 例: Web フロントエンド（React / Vue / Svelte）の場合 → `stacks/web-frontend.md`

**トークン構造の判断**
- 以下のいずれかに該当する場合、2層構造（値の定義 + セマンティックな役割割り当て）を推奨する：
  - ダークモード/テーマ切り替えがある
  - 複数プラットフォーム（Web + モバイル等）で同じデザイン言語を使う
  - チームが複数人で、デザイナーとの協業がある
- 上記に該当しない小規模プロジェクトでは、フラットなトークン定義で十分な場合がある
- コンポーネント固有のトークン層（3層目）は、共有UIライブラリを外部に公開する場合やホワイトラベル対応が必要な場合にのみ検討する

---

## Step 1.5: Aesthetic Direction Interview

トークン値を決める前に、**プロジェクトの美学的方向性をユーザーに聞き取る**。
詳細は `AESTHETIC.md` を参照。SSOT に「どう揃えるか」だけでなく「どう尖らせるか」を書くための入力を集める。

ユーザーに以下を質問する（質問の言い回しはプロジェクトの文脈に応じて調整してよい）:

1. **Tone — 極を1つ選ぶ**: brutally minimal / maximalist / retro-futuristic / organic / luxury / playful / editorial / brutalist / art deco / soft pastel / industrial — または独自の極。「中庸」「無難」「普通」は選択肢に入れない
2. **Differentiation — 記憶に残る一手**: このプロダクトを使った人が、後日他人に説明するとき何と言うか？1つに絞る
3. **Anti-direction — やらないこと**: 上記のtoneと矛盾するパターンを2〜3個挙げる（例: brutally minimal なら「グラデーション」「ドロップシャドウ」「装飾アイコン」）
4. **Generic AI aesthetics の許容範囲**: Inter / Roboto / system font / 紫グラデーション / 中央寄せ定型ヒーローを SSOT で禁止リスト化してよいか確認する。「とりあえず Inter でいい」と言われても一度立ち止まる — 本当に Inter が aesthetic に合うのか問う

ユーザーの回答が曖昧でも、エージェントが draft を提示して合意を取る方式で進めてよい。**SSOT の `aesthetic` セクションが空のまま bootstrap を終わらせない**。

回答が得られたら、`aesthetic` セクションとして SSOT に書き出す（フォーマット詳細は Step 3）。

---

## Step 2: SSOTのフォーマットを決定する

スタックに応じて以下のフォーマットを選択する：

| スタック | 推奨フォーマット | ファイル名 |
|---------|----------------|----------|
| Tailwind v4 | CSS Custom Properties | `design-system.config.css` + `design-system.config.json` |
| Tailwind v3 | TypeScript / JS | `design-system.config.ts` |
| CSS Modules | CSS Custom Properties | `design-system.config.css` |
| Unity | C# static class | `DesignSystem.cs` |
| CSS-in-JS (styled-components, Emotion) | TypeScript | `design-system.config.ts` |
| Vue (SFC + scoped CSS) | CSS Custom Properties | `design-system.config.css` |
| スタック非依存 | JSON | `design-system.config.json` |
| 複合 | TypeScript（他形式を生成するスクリプト込み） | `design-system.config.ts` |

---

## Step 3: SSOTを生成する

### Tailwind v4 プロジェクトの場合

v4はCSS-firstのアプローチを取る。`design-system.config.css` をSSOTとし、`@theme` で値を定義、`:root` でセマンティックな役割を割り当てる2層構造にする：

```css
/* design-system.config.css */

/* --- Reference tokens（値の定義） --- */
@theme {
  /* Color: 支配色 + 鋭いアクセント構造を意識する。aestheticに応じて値を選ぶ */
  --color-blue-500: oklch(0.55 0.20 260);
  --color-blue-700: oklch(0.40 0.20 260);
  --color-gray-50: oklch(0.98 0 0);
  --color-gray-900: oklch(0.15 0 0);

  /* Spacing */
  --spacing-1: 0.25rem;
  --spacing-2: 0.5rem;
  --spacing-4: 1rem;

  /* Typography: display用とbody用を分ける（同一フォント太さ違いに倒さない） */
  --font-display: "替えるべきdistinctive な選択", serif;
  --font-body: "読みやすいrefined sans", sans-serif;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;

  /* Motion: aestheticに応じてduration/easingを選ぶ。
     brutally minimalなら ramp を短く、playfulなら spring 系の easing を選ぶ等 */
  --motion-fast: 120ms;
  --motion-base: 240ms;
  --motion-deliberate: 480ms;
  --ease-standard: cubic-bezier(0.2, 0, 0, 1);
  --ease-emphasized: cubic-bezier(0.3, 0, 0, 1.2);

  /* Shadow / Decoration: solid colorにdefaultしないための装飾レイヤー */
  --shadow-subtle: 0 1px 2px rgb(0 0 0 / 0.06);
  --shadow-standard: 0 4px 12px rgb(0 0 0 / 0.10);
  --shadow-dramatic: 0 24px 48px -12px rgb(0 0 0 / 0.30);
}

/* --- System tokens（役割の割り当て） --- */
:root {
  --color-dominant: var(--color-gray-50);    /* 画面の支配色 */
  --color-on-dominant: var(--color-gray-900);
  --color-accent: var(--color-blue-500);     /* 強調・アクセント */
  --color-accent-hover: var(--color-blue-700);
}
.dark {
  --color-dominant: var(--color-gray-900);
  --color-on-dominant: var(--color-gray-50);
}

/* --- Reduced motion: prefers-reduced-motion 時の方針を必ず記述する --- */
@media (prefers-reduced-motion: reduce) {
  :root {
    --motion-fast: 0ms;
    --motion-base: 0ms;
    --motion-deliberate: 0ms;
  }
}
```

`app.css` での読み込み：

```css
@import "./design-system.config.css";
@import "tailwindcss";
```

conventions・antipatterns・aesthetic は `design-system.config.json` に分離する：

```json
{
  "aesthetic": {
    "tone": "（必ず1つ書く: editorial / brutally minimal / playful 等）",
    "differentiation": "（記憶に残る一手を1つ）",
    "antiDirection": [
      "（このプロジェクトでやらないことを2〜3個）"
    ]
  },
  "conventions": {
    "componentDir": "src/components/ui",
    "namingPattern": "PascalCase"
  },
  "antipatterns": [
    "インラインスタイルの使用",
    "tailwind.configで定義されていない任意値 (text-[#xxx])",
    "コンポーネント外でのスタイル定義",
    "generic AI aesthetics: Inter / Roboto / Arial / system-ui / Space Grotesk のSSOT外使用",
    "generic AI aesthetics: 紫グラデーション on 白 の安易な使用",
    "generic AI aesthetics: 中央寄せヒーロー → 3カラム機能 → CTA の定型レイアウトを意図なく採用",
    "solid color にdefaultした背景（aesthetic で minimal を選んだ場合を除く）"
  ]
}
```

### Tailwind v3 プロジェクトの場合

`design-system.config.ts` をSSOTとし、`tailwind.config.ts` からimportする構成にする。2層構造はCSS Custom Propertiesとの併用で実現する：

```ts
// design-system.config.ts
export const designSystem = {
  // Aesthetic Direction（プロジェクトの美学的方向性）
  aesthetic: {
    tone: "（必ず1つ書く: editorial / brutally minimal / playful 等）",
    differentiation: "（記憶に残る一手を1つ）",
    antiDirection: [
      "（このプロジェクトでやらないことを2〜3個）",
    ],
  },
  // Reference tokens（値の定義）
  reference: {
    colors: {
      blue: { 500: "#2563eb", 700: "#1d4ed8" },
      gray: { 50: "#f9fafb", 900: "#111827" },
    },
    spacing: { 1: "0.25rem", 2: "0.5rem", 4: "1rem" },
    typography: {
      // display と body を分ける（同一フォント太さ違いに倒さない）
      fontFamily: {
        display: ['"Distinctive Display"', "serif"],
        body: ['"Refined Body"', "sans-serif"],
      },
      fontSize: { sm: "0.875rem", base: "1rem" },
    },
    motion: {
      duration: { fast: "120ms", base: "240ms", deliberate: "480ms" },
      easing: {
        standard: "cubic-bezier(0.2, 0, 0, 1)",
        emphasized: "cubic-bezier(0.3, 0, 0, 1.2)",
      },
    },
    shadow: {
      subtle: "0 1px 2px rgb(0 0 0 / 0.06)",
      standard: "0 4px 12px rgb(0 0 0 / 0.10)",
      dramatic: "0 24px 48px -12px rgb(0 0 0 / 0.30)",
    },
  },
  // System tokens（役割の割り当て）はCSS Custom Propertiesで定義する
  conventions: {
    componentDir: "src/components/ui",
    namingPattern: "PascalCase",
  },
  antipatterns: [
    "インラインスタイルの使用",
    "tailwind.configで定義されていない任意値 (text-[#xxx])",
    "コンポーネント外でのスタイル定義",
    "generic AI aesthetics: Inter / Roboto / Arial / system-ui / Space Grotesk のSSOT外使用",
    "generic AI aesthetics: 紫グラデーション on 白 の安易な使用",
    "generic AI aesthetics: 中央寄せヒーロー → 3カラム機能 → CTA の定型レイアウトを意図なく採用",
    "solid color にdefaultした背景（aesthetic で minimal を選んだ場合を除く）",
  ],
} as const;
```

```ts
// tailwind.config.ts
import { designSystem } from "./design-system.config";

export default {
  theme: {
    extend: {
      colors: designSystem.reference.colors,
      spacing: designSystem.reference.spacing,
    },
  },
};
```

```css
/* globals.css — System tokens */
:root {
  --color-primary: theme('colors.blue.500');
  --color-primary-hover: theme('colors.blue.700');
  --color-surface: theme('colors.gray.50');
  --color-on-surface: theme('colors.gray.900');
}
.dark {
  --color-surface: theme('colors.gray.900');
  --color-on-surface: theme('colors.gray.50');
}
```

### Unity プロジェクトの場合

`Assets/Scripts/UI/DesignSystem.cs` を生成する：

```csharp
public static class DesignSystem
{
    // Aesthetic Direction（このプロジェクトの美学的方向性）
    public static class Aesthetic
    {
        public const string Tone = "（必ず1つ書く: brutally minimal / retro-futuristic / playful 等）";
        public const string Differentiation = "（記憶に残る一手を1つ）";
        public static readonly string[] AntiDirection = {
            "（このプロジェクトでやらないことを2〜3個）",
        };
    }

    public static class Colors
    {
        public static readonly Color Dominant = new Color32(245, 245, 247, 255);  // 支配色
        public static readonly Color Accent = new Color32(37, 99, 235, 255);      // アクセント
        public static readonly Color AccentHover = new Color32(29, 78, 216, 255);
    }

    public static class Spacing
    {
        public const float SM = 8f;
        public const float MD = 16f;
        public const float LG = 24f;
    }

    // Motion: Tween Duration / Easing をトークン化する
    public static class Motion
    {
        public const float DurationFast = 0.12f;
        public const float DurationBase = 0.24f;
        public const float DurationDeliberate = 0.48f;
        // EasingはAnimationCurveまたはDOTween Easeで参照
    }
}
```

### 既存UIライブラリがある場合

既存ライブラリのトークンをSSOTに取り込む形にする。
ライブラリの値をSSOTが「再エクスポート」することで、将来的にライブラリを剥がす際の移行コストを下げる。

---

## Step 4: 既存コードを検証する

生成したSSOTに対して `AUDIT.md` を実行し、既存コードとのgapを確認する。
bootstrap直後は多くの⚠️・❌が出ることが想定される。全て即修正する必要はない。

---

## Step 5: CLAUDE.mdに記録する

プロジェクトの `CLAUDE.md` に以下を追記せよ：

```md
## Design System

SSOTは `design-system.config.ts`（またはスタックに応じたファイル）。
新しいスタイル値を追加する場合は必ずSSOTを先に更新すること。
詳細はデザインシステムスキルの `SKILL.md` を参照。
```
