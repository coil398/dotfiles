# HTML モード（`--html`）

`/walkthrough` に `--html` を付けたとき、md に加えて **単一ファイル完結の HTML 版** を生成する。本ファイルは HTML 版の仕様・デザイン方針・生成手順の SSOT。雛形の実体は `references/html-template.html`。

---

## 0. 位置づけ（最初に読む）

| 項目 | 決定 |
|------|------|
| SSOT | **md が SSOT**。HTML は同じ素材から書き起こした「読みやすい版」 |
| キャッシュ判定 | 常に md のフロントマターを見る。HTML はキャッシュ判定に使わない |
| 情報量 | md と HTML は **同一内容**。HTML だから削る、は禁止（SKILL.md ステップ6の分量目安をそのまま適用） |
| 生成方法 | `references/html-template.html` をコピーし、`{{...}}` と `<main>` 内だけ差し替える。CSS / JS は編集しない |
| 外部リクエスト | **0 件**。CDN・Web フォント・外部画像・`fetch` を追加しない |

外部リクエスト 0 を守る理由は 2 つ。`file://` で開いてもオフラインで完全に動くこと、そして CSP の厳しい環境（Artifact 公開など）へそのまま持っていけること。Mermaid も外部ライブラリなので **HTML 版では使わない**（代替は §4）。

---

## 1. デザイン方針

対象は常に「知らないコードを読む人」。ページの仕事はひとつ、**どこから読み始めて何に気をつければいいかを掴ませること**。装飾はそこに寄与する分だけ入れる。

### 固定トークン（毎回発明しない）

テンプレートの `:root` に定義済み。**色・フォント・スケールを対象コードに合わせて変えない**。ウォークスルーは横断的に読まれる資料なので、対象ごとに見た目が変わるほうが害になる。

- **ベース**: 青みのあるクールなインク（light `#f4f5f7` / dark `#0f1319`）。AI 生成物の定番であるクリーム地・純黒地を意図的に外している
- **アクセント**: 琥珀（light `#a8631a` / dark `#e0a458`）。アンバー CRT の系譜で、対象世界（端末）から引いた色
- **緑 / 赤は diff 専用**。ナビゲーションや強調には使わない。「色が意味を持つ」状態を壊さない
- **表示書体はモノスペース**（`Cica` 優先）。読み物の主役がコードであることを書体自体で示す。本文は日本語対応 sans

### シグネチャ要素 — 読む順序レール

`.wt-rail` は「読む順序」を **コードの gutter** として描く。ステップ番号が行番号の位置に右揃えで並び、縦罫がそれを貫き、スクロールに追従して琥珀色が伸びる。これが本ページの唯一の "見せ場"。**ここ以外は静かに保つ**。

### 禁止

- ヒーローの巨大数字＋グラデーション、絵文字の乱用、意味のない `01 / 02 / 03` 装飾
- 対象ごとの独自配色・独自フォント
- レールの進捗以外のスクロール連動アニメーション

### 品質フロア

セマンティック HTML／`:focus-visible`／`prefers-reduced-motion` 尊重／900px 以下でサイドバーが上部に畳まれる／印刷時にナビが消える。いずれもテンプレート側で担保済みなので、**構造を崩さなければ勝手に満たされる**。

---

## 2. ページ構造

`<main class="wt-main">` の中身は md のセクションと 1:1 対応させる。

| md のセクション | HTML | id |
|---|---|---|
| （タイトル・メタ行） | `<header class="wt-head">` の `{{TITLE}}` / `{{CHIPS}}` | — |
| 変更の全体像 | `<section>` + `<h2>` | `overview` |
| コミット構成 | `<section>` + `.wt-table` | `commits` |
| 読む順序 | `<section>` + `.wt-rail` | `order`、各ステップ `step-1`… |
| データフロー図 | `<section>` + `.wt-flow` か inline SVG | `flow` |
| 影響範囲サマリ | `<section>` + `.wt-table` | `impact` |
| 設計上の注意点・落とし穴 | `<section>` + `.wt-note trap` の連続 | `traps` |
| 詳細化メニュー | `<section>` + `.wt-menu` | `menu` |
| 詳細化ログ | `<section>` + `.wt-log-entry` の連続 | `log` |

`{{TOC}}` はこの `<h2>` 群（＋読む順序の各ステップを `class="lv3"` で）から生成する。`href` の id と本文の id を必ず一致させる。

---

## 3. コンポーネント早見

### コードブロック

```html
<figure class="wt-code" data-lang="go" data-start="118" data-mark="4,7-9">
  <figcaption><span class="wt-path">internal/order/handler.go</span></figcaption>
  <pre><code>func (h *Handler) Create(w http.ResponseWriter, r *http.Request) {
	...
}</code></pre>
</figure>
```

| 属性 | 意味 |
|------|------|
| `data-lang` | ハイライト言語。`js/ts/go/rust/java/kotlin/swift/c/cpp/cs/php/py/rb/sh/yaml/toml/sql/lua/css/html/json/diff/md` に対応。未知の値でも文字列・数値・共通キーワードは色が付く |
| `data-start` | 先頭行の行番号（既定 1）。実ファイルの行番号を入れる |
| `data-mark` | 強調行。`"4,7-9"` の形式。**解説文で名指しする行は必ず mark する** |
| `data-diff` | 付けると各行頭の `+` / `-` を緑 / 赤で着色（`data-lang="diff"` でも同じ） |

コード本文は **エスケープせず素のまま**書く（`<` `&` もそのまま）。JS 側が `textContent` から読んで安全にエスケープする。行番号とコピーボタンは自動付与されるので手で書かない。

`<figcaption>` は必須。省くとコピーボタンもファイルパス表示も出ない。差分でも `data-lang` に元の言語（`go` 等）を入れる — `+` / `-` の着色と言語ハイライトは併用できる。

### 読む順序（レール）

```html
<ol class="wt-rail">
  <li class="wt-step" id="step-1">
    <div class="wt-step-mark">1</div>
    <span class="wt-step-path">internal/order/handler.go</span>
    <h3>入口 — リクエストの受け口がどう変わったか</h3>
    <p>…なぜこの順で読むべきか…</p>
    <figure class="wt-code" …>…</figure>
    <p>…引用コードの読み方ガイド…</p>
  </li>
</ol>
```

`.wt-step-mark` は `.wt-step` に対する絶対配置なので、本文をラップする追加の `<div>` は要らない（テンプレートに対応する CSS も無い）。

`.wt-rail-fill` は JS が挿入するので書かない。

### 落とし穴

```html
<div class="wt-note trap">
  <span class="wt-note-label">落とし穴</span>
  <p>…</p>
</div>
```

`trap`（琥珀・非自明な判断や罠）／`danger`（赤・壊れる・互換を切る）／無指定（灰・補足）の 3 種。md の `> ⚠️` `> ❌` `> ℹ️` に対応する。

### 表

```html
<div class="wt-table-wrap"><table class="wt-table"><thead>…</thead><tbody>…</tbody></table></div>
```

`wt-table-wrap` を省くと狭い画面で横スクロールできず本文がはみ出す。必ず包む。

### 詳細化メニュー（HTML を入力として使う唯一の箇所）

チェックボックスで選んで `copy as prompt` を押すと `A, C を詳しく` の形でクリップボードに入る。ユーザーはそれをそのままチャットに貼れる。**ページを読む → 次の指示を作る** をブラウザ内で完結させるための仕掛けで、read-only な資料から一歩出る部分。

```html
<form class="wt-menu-form">
  <ol class="wt-menu">
    <li>
      <label>
        <input type="checkbox" value="A">
        <span class="key">A</span>
        <span><b>認可判定の分岐</b><span class="desc">3 経路のうち 2 経路がフォールバックに落ちる条件がわかる</span></span>
      </label>
    </li>
  </ol>
  <div class="wt-menu-bar">
    <input type="text" class="wt-menu-free" placeholder="自然文で追加（任意）">
    <button type="button" class="wt-menu-copy">copy as prompt</button>
    <output class="wt-menu-out" aria-live="polite"></output>
  </div>
</form>
```

守るべき点:

- `<input type="checkbox">` の `value` は md 側のメニューラベル（`A` / `B` …）と一致させる
- 説明文には `class="desc"` を付ける（付けないと本文色になって階層が消える）
- `.wt-menu-bar` のブロックは**メニュー 1 つにつき 1 つ**。`<output>` は空で置き、JS が結果を書く
- `[Z] その他、気になる箇所を自然文で` の行は不要。自由入力欄がその役割を果たす

### 折りたたみ

長いコード（40 行超）や補助情報は `<details class="wt-fold"><summary>…</summary>…</details>` に入れる。**本筋の情報を畳まない** — 畳んでいいのは "参考として全文も置いておく" 類だけ。

---

## 4. 図（Mermaid の代替）

外部ライブラリを使えないので次の 2 手段で描く。

### 線形の流れ → `.wt-flow`

```html
<div class="wt-flow">
  <div class="wt-node">handler<small>リクエスト検証</small></div>
  <div class="wt-arrow">dto</div>
  <div class="wt-node accent">usecase<small>ここが今回の主戦場</small></div>
  <div class="wt-arrow">entity</div>
  <div class="wt-node">repository</div>
</div>
```

矢印のラベルはテキストとして書く（`→` は CSS が付ける）。狭い画面では自動で縦積み＋`↓` に切り替わる。段組みが縦のほうが自然なら `class="wt-flow vertical"`。

### 分岐・状態遷移・シーケンス → インライン SVG

`class="wt-svg"` を付け、`viewBox` を指定し、線と枠は **`stroke="currentColor"`**、文字は `<text>`（CSS が `fill: var(--text)` を当てる）。色を直接書かない限りライト／ダーク両方で成立する。`width` / `height` 属性は付けず `viewBox` だけにする（レスポンシブになる）。

```html
<svg class="wt-svg" viewBox="0 0 480 140" role="img" aria-label="状態遷移: pending → paid → shipped">
  <rect x="8" y="40" width="110" height="40" rx="4" fill="none" stroke="currentColor"/>
  <text x="63" y="64" text-anchor="middle">pending</text>
  …
</svg>
```

図が 2 つを超えるなら、たいてい本文の構造化不足。図より表のほうが速いことも多い。

---

## 5. 生成手順

SKILL.md ステップ6で md を保存した直後に実行する。

1. `references/html-template.html` を Read する
2. 全文をコピーし、以下を差し替えて `docs/walkthrough/<md と同じ basename>.html` に Write する

   | プレースホルダ | 中身 |
   |---|---|
   | `{{TITLE}}` | ウォークスルーの見出し（md の `# ` と同じ） |
   | `{{MODE}}` / `{{WORK_MODE}}` | `pr` / `single` など。eyebrow に出る |
   | `{{CHIPS}}` | `<li>target <b>#123</b></li>` 形式で 3〜5 個（target / 規模 / 生成日時 / base..head 等） |
   | `{{TOC}}` | サイドバー目次の `<li>` 群 |
   | `{{CONTENT}}` | §2 の `<section>` 群 |
   | `{{MD_PATH}}` / `{{GENERATED_AT}}` | フッタ表示用 |

3. 生成後に **セルフチェック**（§6）を通す
4. `SendUserFile` で `display: "render"` を指定して HTML を渡し、保存パスも文字で伝える
5. **ブラウザで開く**（下記）

### ブラウザで開く

HTML を生成したら既定のブラウザで開く。プラットフォームごとにコマンドが違うので、次の 1 行で振り分ける（`WT_HTML` は生成した HTML の**リポジトリルート相対パス**）:

```bash
WT_HTML="docs/walkthrough/<file>.html"; if [ -n "${WSL_DISTRO_NAME:-}" ] && command -v wslview >/dev/null 2>&1; then wslview "$WT_HTML"; elif command -v open >/dev/null 2>&1; then open "$WT_HTML"; elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$WT_HTML"; else echo "自動で開けませんでした。手動で開いてください: $WT_HTML"; fi
```

`open` / `xdg-open` / `wslview` のいずれも無い環境では**エラーにせずパスを伝えて終わる**。ブラウザが開けないことは作業の失敗ではない。

### 生成のタイミング — 「使い捨て」に寄せる

HTML は**読むために吐く成果物**で、md のように継続同期する台帳ではない。詳細化 1 件ごとに再生成すると重いだけで誰も得しないので、**生成は 3 点に絞る**。

| タイミング | 挙動 |
|---|---|
| ステップ6（冒頭ウォークスルー保存直後） | フル生成 → `SendUserFile` → **ブラウザで開く** |
| ステップ7の詳細化ループ中 | **何もしない**。md にだけ追記する |
| ステップ7でユーザーが「HTML 見せて」「更新して」と言った | その時点の md 全体からフル再生成 → `SendUserFile` → ブラウザで開く |
| ステップ8（終了時） | 最終版をフル再生成 → `SendUserFile` → **開かず「タブをリロードして」と伝える**（ステップ6で開いたタブが残っているのが通常なので、タブを増やさない） |

ステップ8で開かないのは、同じ `file://` を再度 `open` するとブラウザが新規タブを積む環境が多いため。ユーザーがタブを閉じていた場合は「開き直す？」と 1 行添えれば足りる。

ループ中は HTML が md より古い状態になる。これは意図した割り切りで、**md が SSOT** なので情報は失われない。ユーザーに提示するときも「HTML はステップ6時点／最終版」と分かる形にする（フッタの生成時刻がそれを担う）。

詳細化ログのエントリの形（フル生成時に全件出力する）:

```html
<div class="wt-log-entry" id="log-2">
  <h3>テーマ名</h3>
  <p class="wt-log-meta">2026-07-30 14:22 ／ 要求: "A"</p>
  …対象コード（figure.wt-code）と解説…
</div>
```

キャッシュヒットで `[1] そのまま表示` を選び HTML が存在しない場合も、md からフル生成する。

### フラグの相互作用

| 組み合わせ | 挙動 |
|---|---|
| `--html` のみ | md と HTML の両方を保存 |
| `--html --no-save` | 矛盾。**`--html` を優先**し「`--no-save` と併用されたため HTML のみ生成し md は保存しません」と 1 行告知して HTML だけ書く（詳細化ループの追記先が無いので、詳細化はチャット内提示のみ） |
| `--html --fresh` | md の連番退避に合わせて HTML も同じ basename で退避する |
| `--html --team` | 影響なし（調査体制のフラグ） |

### Artifact 公開

テンプレートは外部リクエスト 0 なので Artifact としてそのまま公開できる。ただし claude.ai へのアップロードは外部送信なので、**ユーザーが明示的に求めたときだけ**行い、その前に `artifact-design` skill を読む。既定はローカルファイルのみ。

---

## 6. セルフチェック（Write 直後に必ず通す）

1. `{{` が 1 つも残っていない
2. `http://` / `https://` で始まる `src` / `href` / `@import` が無い（サイト外リンクを本文に書く場合を除き、**読み込み**は 0 件）
3. サイドバーの `href="#id"` が全部本文の `id` に着地する
4. `.wt-code` に `data-lang` があり、解説で名指しした行が `data-mark` に入っている
5. すべての `<table class="wt-table">` が `.wt-table-wrap` に包まれている
6. `.wt-rail-fill` を手書きしていない（JS が作る）
7. `<style>` と `<script>` をテンプレートから改変していない
8. `class="wt-..."` に **テンプレートの CSS に存在しないクラスを使っていない**（存在しないクラスは静かに無視されるだけで、見た目の崩れとして気づけない）
9. `<figure>` `<section>` `<details>` の閉じタグが揃っている
10. md 版に書いた事実が HTML 側から落ちていない（セクション単位で突き合わせる）
