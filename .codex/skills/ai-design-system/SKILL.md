---
name: ai-design-system
description: プロジェクト内のデザインシステムSSOTを生成・監査・維持する。一貫性（トークン・命名）と個性（aesthetic direction・Typography・Motion・装飾レイヤー）の両軸でSSOTを管理し、generic AI aesthetics（Inter / 紫グラデ / 中央寄せ定型）への無意図な収束を回避する。UIコンポーネント作成、デザイントークン管理、スタイルの一貫性チェック、デザインシステムの構築や改善を求められたときに使う。「デザイン統一したい」「トークン整理して」「コンポーネントの色がバラバラ」「スタイルガイド作って」「テーマ対応したい」「ダークモード対応」「UIの見た目を揃えて」「WCAG対応」「アクセシビリティ改善」「AIっぽさを消したい」「もっと個性のあるUIにしたい」「フォント選びたい」「motion入れたい」といった要望にも対応する。デザイントークン・カラーパレット・タイポグラフィ・スペーシング・モーション・装飾に関する作業では積極的にこのスキルを参照すること。
---

# Design System Skill

## Overview

このスキルはプロジェクトのデザインシステムを、外部ライブラリへの依存なしに管理するためのものだ。
エージェントはこのスキルを通じて、デザインのSSOTを生成・参照・改善する。

このスキルは **2つの軸** でSSOTを管理する:

- **一貫性の軸**: トークン階層・命名規則・状態網羅・アクセシビリティ（`IDEAL.md` セクション 1–10）
- **個性（aesthetic）の軸**: tone・differentiation・Typography display+body・Motion・装飾レイヤー（`IDEAL.md` セクション 11–13、`AESTHETIC.md`）

「揃っているだけで凡庸」も「尖っているだけでバラバラ」も避ける。両方を SSOT に書く。

## Entry Flow

以下の順で判断して動け。

### 1. SSOTを探す

プロジェクトルートに `design-system.config.*` が存在するか確認する。
存在しない場合は `BOOTSTRAP.md` に従いSSOTを生成してから続行する（**Step 1.5 の Aesthetic Direction Interview を必ず通す**）。

### 2. SSOTを読む

SSOTを読み、以下を把握する：

- **Aesthetic direction**（tone / differentiation / antiDirection）— 空欄なら `AESTHETIC.md` を参照しユーザーに確認
- デザイントークン（色・スペーシング・タイポグラフィ・**Motion**・**Shadow**・装飾レイヤー）
- Typography の **display フォントと body フォントの分離**
- コンポーネントの命名規則・配置ルール
- 禁止事項・アンチパターン（**generic AI aesthetics の禁止リストを含む**）
- スタイリング手法（Tailwind / CSS Modules / その他）

### 3. タスクに応じて動く

| タスク | 参照 |
|--------|------|
| 新規コンポーネントの作成 | SSOTのトークン・規則・aesthetic direction に従い実装 |
| 既存コードの改善・レビュー | `AUDIT.md` に従いgapを検出・修正（aesthetic-implementation 不整合と generic AI aesthetics も検出対象） |
| デザインシステム自体の更新 | SSOTを先に更新 → 影響を受けるコンポーネントを修正 → `AUDIT.md` で整合性を確認 |
| トークン階層の見直し・テーマ対応 | `IDEAL.md` のセクション1（階層構造）とセクション6（テーマ対応）を参照 |
| WCAG準拠・アクセシビリティ確認 | `IDEAL.md` のセクション2（トークン値の品質）を参照 |
| **美学的方向性の確認・更新** | `AESTHETIC.md` を読み、SSOT の `aesthetic` セクションを更新。tone / differentiation / antiDirection を明示する |
| **「AIっぽさを消したい」「個性を出したい」相談** | `AESTHETIC.md` の Step 1 を実行。generic AI aesthetics を SSOT で禁止リスト化し、tone を1つに絞る |
| **Motion・アニメーション設計** | `IDEAL.md` セクション12 と stacks ガイドの Motion 節。duration / easing をトークン化し、prefers-reduced-motion 対応を SSOT に記述 |
| **Typography 整備（フォント選定）** | `AESTHETIC.md` Typography 節。display と body を分離し、generic font 禁止リストを SSOT に書く |

## Principles

SSOTがすべての起点である。コンポーネント実装中に迷ったら必ずSSOTに戻る。SSOTにない値を使う場合はSSOTを先に更新する。

スタイルはトークンで表現する。ハードコードされた色・サイズ・余白・**duration**・**shadow**は原則禁止。SSOTで定義されたトークン・変数・クラスのみ使う。

トークンは値と役割を分離する。生の値（`blue-500 = #3b82f6`）と意味の割り当て（`accent = blue-500`）を分けることで、テーマ切り替えやリブランディングに対応できる。プロジェクトの規模と要件に応じて `BOOTSTRAP.md` の判断基準に従う。

ふるまいとスタイルを分離して考える。アクセシビリティ・キーボード操作・状態管理はスタイルとは独立した問題として扱う。

**Aesthetic は意図的にコミットする。** 中庸・無難・default は選択肢ではない。tone / differentiation / antiDirection を SSOT に書き、generic AI aesthetics（Inter / 紫グラデ / 中央寄せ定型）への無意図な収束を回避する。詳細は `AESTHETIC.md`。

**Aesthetic と実装強度を一致させる。** minimalist 宣言には restraint な実装、maximalist 宣言には elaborate な実装を。差し色1色・装飾1点・印象に残るモーション1つに集中投資し、他は支える側に倒す。

IDEAL.mdを正とする。実装の判断に迷ったら `IDEAL.md` のチェックリスト（一貫性: セクション 1–10 / 個性: セクション 11–13）を参照する。

## Notes

- このスキル自体にプロジェクト固有の値は一切含まない（aesthetic も含めて、具体的なフォント名・色値はプロジェクトの SSOT 側で書く）
- SSOTのフォーマットはプロジェクトのスタックに依存する（詳細は `BOOTSTRAP.md`）
- スキルのバージョンが上がっても移行スクリプトは存在しない。`IDEAL.md` の更新内容に対して現状のgapを `AUDIT.md` で検出する
- frontend-design スキル（Anthropic 公式）と並列に存在することを許容する。frontend-design は単発の創作向け、このスキルは継続的なシステム維持向け。両者の思想は `AESTHETIC.md` で接続している
