# UI/UX 応答性・品質の判断軸 (references)

このファイルは UI/UX 品質を評価するときの **スタック非依存の判断軸 SSOT**。`ui-ux-reviewer` エージェントの判定根拠であり、explorer / planner / reviewer が UI/UX に関わる設計・改善・レビューで参照する。

> ⚠️ **汎用性ルール**: このファイルには特定スタック（フレームワーク / エンジン / プラットフォーム）・特定プロダクト名を書かない。スタック固有の技術詳細は各プロジェクトの `.claude/ui-ux-stack-*.md` に分離し、ui-ux-reviewer がそれを併せて参照する。

---

## 0. 3 層フレームワーク（最重要・最初に分類する）

改善案・指摘を出す前に、**必ずどの層の問題かを分類する**。層を混ぜると「遅さを隠すハックの寄せ集め」になり、根本原因が放置される。

| 層 | 何をする | 代表手法 | 根拠原則 |
|---|---|---|---|
| **層1: 知覚** | 遅さを隠す・反応感を出す | 即時フィードバック / スケルトン / スピナー | RAIL Response / Nielsen 0.1s |
| **層2: 実** | 実際に処理を軽くする | ブロッキング除去 / アロケ削減 / リーク解消 | フレーム予算 / GC |
| **層3: データ設計** | そもそも待たない | キャッシュファースト / SWR / プリフェッチ | stale-while-revalidate |

> ℹ️ **判定の鉄則**: 「スピナー/スケルトンで隠せる」と判断する前に、**層2（UIスレッドブロッキング・無駄な処理）と層3（遷移ごとの無条件再フェッチ）が無いかを先に確認する**。知覚改善（層1）は「避けられない待ち」の体験向上のためのもので、根本の遅さを覆い隠す免罪符にしてはならない。1つの症状に層1だけを当てている改善案は **不完全** と判定する。

---

## 1. 応答時間の定量体系

### Nielsen の 3 つの応答時間限界（NN/g）

| 閾値 | 意味 | 推奨アクション |
|---|---|---|
| **0.1 秒 (100ms)** | 「瞬時」と感じる上限 | 特別なフィードバック不要。結果をそのまま表示 |
| **1 秒** | 思考の流れが途切れない上限 | 軽微なフィードバック。超えると「遅い」と知覚される |
| **10 秒** | 注意保持の限界 | プログレスバー（残り時間）＋キャンセルが必須 |

出典: <https://www.nngroup.com/articles/response-times-3-important-limits/>

### Google RAIL モデル（web.dev）

| フェーズ | 定量目標 |
|---|---|
| **Response** | 入力イベントを 50ms 以内に処理し、**100ms 以内にフィードバック** |
| **Animation** | 1 フレーム **10ms 以内** に生成（60fps=16ms 枠から描画分を除く） |
| **Idle** | バックグラウンド処理は 1 チャンク **50ms 以下** に分割 |
| **Load** | 初回インタラクティブ **5 秒以下**、後続 **2 秒以下** |

出典: <https://web.dev/articles/rail>

### Doherty Threshold（IBM, 1982）

**400ms 以内に応答が返るとユーザーはフロー状態を維持**し、生産性・満足度が有意に向上する。
出典: <https://lawsofux.com/doherty-threshold/>

### 実用早見

```
0ms ── 100ms ── 400ms ── 1,000ms ── 10,000ms
     瞬時感    フロー上限  思考連続上限  注意の限界
   (RAIL Resp) (Doherty)  (Nielsen)   (プログレスバー必須)
```

---

## 2. 知覚 vs 実 — 「隠してよい」か「根本を直す」かの判断基準

| 判断軸 | 知覚改善（層1）で対処してよい | 根本（層2/3）を直すべき |
|---|---|---|
| 処理の性質 | 避けられない待ち（非同期データ・ネット遅延・描画） | UIスレッドブロッキング・同期I/O・無駄な再フェッチ |
| 再現性 | 1〜数回に1回（ネット依存） | 毎回・操作するたびに同じ遅延 |
| データの性質 | 頻繁に変わらない/新鮮さ要求が低い | 金融・在庫・認証など誤表示が実害 |
| 体験の崩れ方 | 視覚的な空白・出現遅延 | タップ無反応・画面フリーズ・ANR |

---

## 3. 待ち時間を扱う手法と使い分け

### 即時フィードバック（必須）

全てのタップ/クリックに **100ms 以内** に視覚的反応を返す（Nielsen 0.1s / RAIL Response）。フィードバックがないと「無視された」と感じ複数タップを誘発する。
出典: <https://developer.android.com/topic/performance/anrs/keep-your-app-responsive>

### インジケーターの使い分け

| 種別 | 適切な待ち | 用途 | 注意 |
|---|---|---|---|
| 何も出さない | < 1秒 | 瞬時処理 | 1秒以下でインジケーターは逆効果 |
| スピナー（不定） | 2〜10秒 | 単一アクション | 最低表示 200〜300ms でフリッカー防止 |
| スケルトン | < 10秒 | コンテンツ重いフルページ | 個別コンポーネントには不向き |
| プログレスバー（定量） | > 10秒 / 進捗計算可 | アップロード・DL | 計算不能なら不定バー |

> ⚠️ **フリッカー禁止**: 1 秒以下の処理にループアニメ（スピナー）を出さない。点滅が注意を乱しかえって遅く感じさせる。出典: <https://www.nngroup.com/articles/progress-indicators/>

### 楽観的 UI（Optimistic UI）

| 使ってよい | 危険 |
|---|---|
| 成功確率が高い操作（いいね・送信・カート） | 金融・在庫・認証など失敗時の誤表示が実害 |
| on/off 等の真偽状態の即時反映 | 複数ユーザー同時操作で競合する |

実装要件: 楽観表示中のアイテムは非インタラクティブにし、失敗時はリトライ導線を出す。
出典: <https://www.jacobparis.com/content/remix-crud-ui>

---

## 4. データ / 設計層（「そもそも待たない」）

- **Stale-While-Revalidate (SWR)**: キャッシュ済みの古い値を即表示し、裏で最新を取得してサイレント差し替え。天気・フィード・設定など即座性 > 完全最新性 のデータに有効。出典: <https://web.dev/articles/stale-while-revalidate>
- **プリフェッチ**: 次に遷移しそうな画面/データを事前取得。予測確度とのトレードオフ。
- **遷移ごとの無条件再フェッチはアンチパターン**: 画面を開くたびに毎回フェッチしスピナーを見せる設計は、状態の持ち方の問題。クライアントキャッシュ + TTL で「即表示 → 裏で再検証」に変える。

---

## 5. アクセシビリティ（WCAG 2.2、実務標準は AA）

POUR = Perceivable / Operable / Understandable / Robust。法令・調達要件の多くが **AA** を参照。出典: <https://www.w3.org/TR/WCAG22/>

| 観点 | 定量閾値 | WCAG SC | レベル |
|---|---|---|---|
| テキストコントラスト（通常） | **4.5:1** 以上 | 1.4.3 | AA |
| テキストコントラスト（大: 18pt/太字14pt 以上） | **3:1** 以上 | 1.4.3 | AA |
| UI部品・グラフィックのコントラスト | **3:1** 以上 | 1.4.11 | AA |
| タップターゲット（最低） | **24×24 CSS px** 以上 | 2.5.8 (2.2新規) | AA |
| タップターゲット（推奨） | **44×44** 以上 | 2.5.5 | AAA |
| フォーカス可視 | キーボード操作時に常時表示 | 2.4.7 | AA |
| フォーカスが隠れない | sticky UI 等で完全遮蔽禁止 | 2.4.11 (2.2新規) | AA |
| Name / Role / State | 全 UI 要素に必須 | 4.1.2 | A |
| 点滅 | **3 回/秒以下** | 2.3.1 | A |
| テキストリサイズ | **200%** まで機能維持 | 1.4.4 | AA |

プラットフォーム別タップ推奨: iOS **44pt** / Android **48dp** / Web 実務 44px（24px が AA 最低）。
モーション低減（`prefers-reduced-motion` / OS 設定）への配慮は WCAG 強制ではないが事実上の業界標準。
出典: <https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/> / <https://www.w3.org/TR/wcag2mobile-22/>

---

## 6. アンチパターン早見表

| アンチパターン | なぜ悪いか | 代替 |
|---|---|---|
| 入力ブロックで無反応待機 | ANR・複数タップ誘発 | 重処理を逃がし UI を常にアンブロック + 100ms 以内フィードバック |
| 視覚フィードバックなしの沈黙 | クラッシュと誤解される | 100ms 以内に何か反応を出す |
| 遷移ごとの無条件再取得 | 毎回スピナー・帯域浪費 | SWR + クライアントキャッシュ |
| 短すぎる処理へのスピナー | フリッカーで遅く感じる | ≥1秒で表示・最低表示時間を設ける |
| 全てにスピナー（スケルトン未使用） | レイアウトシフトで体験悪化 | 構造が予測可能ならスケルトン |
| 遅さを層1だけで隠す | 根本（層2/3）が放置される | 層を分類し根本と併用 |

---

## 出典一覧

| 論点 | URL |
|---|---|
| Nielsen 3 閾値 | <https://www.nngroup.com/articles/response-times-3-important-limits/> |
| RAIL モデル | <https://web.dev/articles/rail> |
| Doherty Threshold | <https://lawsofux.com/doherty-threshold/> |
| スケルトン使い分け | <https://www.nngroup.com/articles/skeleton-screens/> |
| プログレスインジケーター | <https://www.nngroup.com/articles/progress-indicators/> |
| 楽観的 UI | <https://www.jacobparis.com/content/remix-crud-ui> |
| Stale-While-Revalidate | <https://web.dev/articles/stale-while-revalidate> |
| ANR / UIスレッド | <https://developer.android.com/topic/performance/anrs/keep-your-app-responsive> |
| WCAG 2.2 全文 | <https://www.w3.org/TR/WCAG22/> |
| WCAG 2.2 新規基準 | <https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/> |
| WCAG2Mobile | <https://www.w3.org/TR/wcag2mobile-22/> |
| コントラスト 1.4.3 | <https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html> |
| 非テキストコントラスト 1.4.11 | <https://www.w3.org/WAI/WCAG21/Understanding/non-text-contrast.html> |
| タップターゲット 2.5.8 | <https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html> |
