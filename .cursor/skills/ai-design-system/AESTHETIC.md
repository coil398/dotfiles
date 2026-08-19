# Aesthetic Direction

デザインシステムは一貫性だけでなく **個性（aesthetic identity）** にも責任を持つ。
「壊れていない」だけのデザインは記憶に残らない。SSOTに「どう揃えるか」だけでなく **「どう尖らせるか」** をコミットさせる。

このファイルは `IDEAL.md` のセクション 11–13 と `BOOTSTRAP.md` の Aesthetic Direction Interview から参照される、美学的方向性の指針。

---

## 原則: 意図的にコミットせよ

**generic AI aesthetics（AI slop）を避ける。**
LLM が無難に倒れる方向には強い引力がある。何も決めなければ、出力は次のような均一な姿に収束する:

- フォント: Inter / Roboto / Arial / system font / Space Grotesk
- 配色: 紫グラデーション on 白背景 / ニュートラルグレースケール / 過度に均等配分されたパレット
- レイアウト: 中央寄せのヒーロー → 3カラム機能 → CTA というテンプレ
- 装飾: 単色ベタ塗り、影なし、余白の意味付けなし

これらは「悪い」のではなく「無意図」な点が問題。**プロジェクトに意図がないなら出るべき結論**ではある。だが意図があるなら SSOT に書け。

> ⚠️ このスキルは project-agnostic のため、特定のフォントや配色を「正解」として強制しない。**SSOTにaesthetic directionの欄を作り、プロジェクトごとに書く**ことを強制する。

## Step 1: Aesthetic Direction を選ぶ

プロジェクト立ち上げ時、または audit で「aesthetic direction が空欄」と判定されたとき、以下を決めて SSOT に記録する。

### 1.1 Tone（極を選ぶ）

中庸を選ばない。明確な極のいずれかにコミットする。複数の組み合わせも可（「brutalist × playful」等）だが、組み合わせの場合は支配方向を1つ決める。

| Tone | 説明 | フォント傾向 | よくある「やる」 | よくある「やらない」 |
|------|------|------|------|------|
| brutally minimal | 装飾を徹底排除、タイポと余白だけで構成 | 1〜2 family、weight 差で階層、稀に variable | 太く大きいタイポ、border のみで領域分割、hover は色置換のみ | shadow / gradient / radius 大 / アニメーション fade-in 連発 |
| maximalist | 重なり・色数・装飾を恐れずに押し込む | distinctive display + serif body + accent display | 4層以上の背景、multiple カラフルアクセント、staggered reveal、custom cursor | restraint、neutral palette、subtle micro-interaction |
| retro-futuristic | 70-90s SF / Y2K / vaporwave 等の時代感 | pixel font / monospace / 時代記号フォント | scanline / glitch / chromatic aberration / CRT vignette | modern shadow / smooth ease-out / sans-only |
| organic / natural | 不整形・手描き感・有機的曲線 | hand-drawn display / humanist serif body | 不規則な border-radius、紙質テクスチャ、温かい earthtone | rigid grid / flat solid color / sterile sans |
| luxury / refined | 余白・上質紙・thin serif・控えめな金属感 | thin serif display + refined serif body | generous whitespace、metallic accent (kintsugi gold 等)、ultra-light weight | bright primary、過剰アニメーション、装飾過多 |
| playful / toy-like | 丸み・原色・弾むようなモーション | rounded sans / character display / chunky | spring easing、原色アクセント、bouncy hover、絵文字混在許容 | sharp corner、linear motion、controlled grayscale |
| editorial / magazine | 雑誌的グリッド・タイポ強調・写真主役 | distinctive serif display + refined serif body | 大胆 grid 破壊、写真主役、column 数が均等でない、印刷的余白 | symmetric grid、display と body 同一 family、rounded card stack |
| brutalist / raw | むき出しのHTMLっぽさ・モノスペース・border強調 | system monospace / unstyled-feel sans | default browser feel、太い border、underline link、no shadow | rounded radius、polished button、material design |
| art deco / geometric | 幾何学・対称・装飾的フレーム | geometric sans display / period serif | symmetric ornament、metallic frame、step-edge motif | organic curve、fade easing、casual photo |
| soft / pastel | 低彩度・低コントラスト・柔らかいシャドウ | rounded humanist sans / handwritten display | low-saturation、generous airy spacing、subtle blur | high contrast、neon accent、sharp shadow |
| industrial / utilitarian | ターミナル/CAD風・密度高・装飾レス | monospace 多用 / condensed sans | high-density data、border grid、step easing、hairline divider | hero whitespace、装飾アイコン、過剰 animation |

このリストは出発点であり、独自の極を定義してもよい。重要なのは **「○○寄り」と一言で説明できる**こと。

### Tone を選ぶときのガードレール（generic AI 化を防ぐ）

以下の表現は tone ではない。**「描写ではあるが選択ではない」** から SSOT に書いてはいけない:

- ❌ "modern" / "clean" / "professional" / "sleek" / "minimal" 単独
- ❌ "user-friendly" / "intuitive" / "approachable"
- ❌ "elegant" / "stylish" / "polished" 単独

これらは「不在の言語」（何かを *しない* ことの記述）であり、SSOT の `aesthetic.tone` フィールドにこれらだけが入っていたら、それは未決定状態。実装が generic 方向に倒れる。
**「○○ である」と肯定形で書ける tone を選ぶこと。** 上の表のいずれか、またはその variant、または独自定義でよい。

### 1.2 Differentiation（記憶に残る一手）

> 「このプロダクトを使った人が、後日他の人に説明するとき何と言うか？」

- 例: 「ナビゲーションが scroll に応じて回転する例のサイト」
- 例: 「フォームのエラーが手書き風に書かれて消えるやつ」
- 例: 「全部 monospace で書かれてるあのダッシュボード」

**1つに絞る。** 全部に力を入れると凡庸になる。記憶に残るのは1点だけ。

### 1.3 Anti-direction（やらないこと）

選んだ tone と矛盾するパターンを明示する。
例: tone = brutally minimal なら anti-direction = グラデーション / drop shadow / 装飾アイコン。
SSOT の `antipatterns` に追記する。

### 1.4 Mixed tone（複合 tone）と tone-shift（場所別 tone）

単一 tone に収まらないプロジェクトは存在する。以下の2パターンを区別する:

#### Mixed tone（同一画面で複数 tone を混合）

例: brutalist × playful（むき出しのHTML感に原色アクセントだけが浮かぶ） / editorial × industrial（雑誌的タイポ階層 × 高密度データテーブル）。

ルール:
- **支配 tone を1つ選ぶ**（80% の表現を担う側）。SSOT には `tonePrimary` で記録
- **副次 tone も1つだけ**（最大2 tone まで。3 tone 以上は方向性の放棄に等しい）。SSOT には `toneSecondary`
- **支配と副次の境界を明示**: どの要素が副次 tone を担うか書く（例: "見出しは editorial、データテーブルは industrial"）
- 副次 tone のためのトークンは支配 tone のトークン体系に *従属* させる（独立した parallel system にしない）
- mixed tone を選ぶ理由を `aesthetic.differentiation` または `rationale.md` に記録

#### Tone-shift（route / section / page archetype ごとに tone を切り替える）

例: landing page は playful、blog は editorial、admin dashboard は industrial。

ルール:
- **共通基盤トークン（color / spacing / motion duration）は1つの SSOT で管理**。tone-shift で増えるのは Typography と装飾レイヤーのみ
- **shift する場所を SSOT で列挙**: `aesthetic.toneShifts` に `[{where, tone, reason}]` を書く
- 明示されていない箇所は支配 tone に従う
- **shift は "差し色" として扱う**。section A から B へ移ったとき視覚的にショックがあって良い、ただし「同じプロダクトの別セクション」とは認識できる程度の連続性（spacing scale / color mood）を保つ

> ⚠️ mixed tone と tone-shift は逃げ道として使わないこと。「決められないから両方」は generic に倒れる最短ルート。**「両方が必要な理由」を1文で説明できないなら単一 tone に絞る**。

---

## Step 2: SSOTにaesthetic directionを書く

`design-system.config.json`（またはスタック相当のSSOTファイル）に aesthetic セクションを追加する:

```json
{
  "aesthetic": {
    "tone": "editorial / magazine",
    "differentiation": "全ページに本文用 serif と display 用 condensed sans の極端なコントラストを敷く",
    "antiDirection": [
      "Inter / Roboto / system font の使用",
      "紫グラデーション",
      "中央寄せヒーローの定型",
      "drop shadow による浮遊表現"
    ]
  }
}
```

このセクションがあることで、コンポーネント実装時にエージェントは「このプロジェクトは○○寄りだから、ここはこう倒す」と判断できる。

---

## Step 3: トークン設計に aesthetic を反映する

aesthetic direction はトークン値そのものに影響する。以下の観点を SSOT に書く（具体値はプロジェクト依存）:

### Typography

- **Display フォントと body フォントを分離する**
  - body は読みやすさ優先（refined sans / serif）
  - display はキャラクター優先（distinctive な選択）
  - 同一フォントで太さだけ変えるのは避ける（generic に倒れる）
- **Generic フォントを SSOT で禁止リスト化**: Inter / Roboto / Arial / system-ui を `antipatterns` に明示。例外を許す場合も「○○用途のみ」と限定する
- **行間・文字間隔も aesthetic に従う**: editorial なら詰め気味、playful なら緩め

### Color

- **支配色（dominant）+ 鋭いアクセント** の構造を推奨
  - 均等配分のパレット（5色を5回ずつ使う）は generic に見える
  - 1〜2色が画面の80%を占め、アクセントが20%以下、というメリハリを作る
- **セマンティック層で「dominant / accent」を区別する**
  - `--color-dominant` / `--color-accent` のような役割を入れる
  - もしくは `--color-primary`（支配色）と `--color-highlight`（差し色）として既存トークンに意味付け
- **避ける: 紫グラデーション on 白、過度なニュートラルグレースケール、低コントラスト全面塗り**

### Motion

- **duration / easing をトークン化する**（例: `--motion-fast: 120ms`, `--motion-base: 240ms`, `--motion-deliberate: 480ms`）
- **「一発で印象を残す」モーションを設計**
  - ページロード時の staggered reveal（要素が時間差で現れる）
  - hover時の意外な反応（伸びる・ねじれる・色が滲む等）
  - 散発的な micro-interaction を10個入れるより、orchestrated な大きい1つの方が delight を生む
- **CSS-only を優先**（HTML/Vanilla の場合）。React なら Motion (Framer Motion) を許容
- **無駄な fade-in を全要素に振らない**: 「動く意味」を SSOT に書く

### Spatial Composition

- **完全対称グリッドだけに頼らない**
  - asymmetry / overlap / diagonal flow / grid-breaking を意図的に許す
- **空白の方針を選ぶ**: 「generous negative space」か「controlled density」のどちらに倒すかを SSOT に明示
- **コンポーネントごとに異なる方針が混在しないように**: 全体の支配方針に従う

### Background & Visual Details

- **solid color にデフォルトしない**
  - 必要に応じて: gradient mesh, noise texture, geometric pattern, layered transparency, dramatic shadow, decorative border, custom cursor, grain overlay
- **ただし aesthetic に矛盾するものは入れない**
  - brutally minimal で grain overlay は矛盾。tone との整合を SSOT で監督する
- **装飾レイヤーをトークン化**
  - `--texture-grain` / `--shadow-dramatic` / `--border-decorative` のような名前で再利用可能にする

---

## Step 4: Implementation 強度を aesthetic に合わせる

> Maximalist designs need elaborate code. Minimalist designs need restraint.

aesthetic direction が決まれば実装の質感も決まる。**コードの密度と aesthetic の強度を一致させる**。

| aesthetic | 期待される実装 |
|-----------|--------------|
| brutally minimal | 余計な div / class を排し、タイポと余白で構築。アニメーションは最小限、または完全になし |
| maximalist | 多層の背景、複雑なアニメーション、多数のmicro-interaction、装飾レイヤーをふんだんに |
| editorial | 大胆なタイポ階層、写真とテキストの mixed grid、印刷物的な余白 |
| retro-futuristic | scanline / glitch effect / 8-bit 風タイポ等、時代記号を意図的に配置 |

minimalist プロジェクトに maximalist な実装をしない。逆も然り。
**audit時に「aesthetic は minimal と書いてあるが、実装は装飾過多」のような不整合を検出する。**

---

## Aesthetic と一貫性は両立する

このスキルの IDEAL.md は engineering 寄り（ハードコード禁止・トークン階層・状態網羅）の checklist で構成されている。
本ファイルの aesthetic は creative 寄り。両者は対立しない:

- **一貫性は土台**: 全ページで同じトークンを使うから、aesthetic がブレずに伝わる
- **aesthetic は方向**: トークンに「なぜこの値か」の意味を与える

トークンを揃えただけで個性のないプロダクトは大量にある。
個性に振りすぎてコンポーネントごとにバラバラなプロダクトも大量にある。
両方を SSOT で管理することで、エージェントは **「揃っていて、かつ尖っている」** 出力を再現可能にする。
