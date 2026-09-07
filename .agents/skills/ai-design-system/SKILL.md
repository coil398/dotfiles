---
name: "ai-design-system"
description: "プロジェクト内のデザインシステムSSOTを生成・監査・維持する。トークン・命名・カラーパレット・スペーシングの一貫性と、aesthetic direction・Typography・Motion・装飾レイヤーによる個性を管理し、アクセシビリティ (accessibility) にも配慮しながら、Inter / 紫グラデーション / 中央寄せ定型などのgeneric AI aestheticsへの無意図な収束を避ける。自然言語トリガー例: 「デザインシステムを作って」／「デザイントークンを整理して」／「UIの見た目を揃えて」／「アクセシビリティを改善して」。該当する依頼ではスキル名がなくても使い、デザインSSOT、トークン、タイポグラフィ、モーション、装飾に関する作業でも参照する。ユーザーが /ai-design-system と入力したら必ず使う。"
---

# Design System Skill

## Overview

このスキルはプロジェクトのデザインシステムを、外部ライブラリへの依存なしに管理するためのものだ。
エージェントはこのスキルを通じて、デザインのSSOTを生成・参照・改善する。

このスキルは **2つの軸** でSSOTを管理する:

- **一貫性の軸**: トークン階層・命名規則・状態網羅・アクセシビリティ（`IDEAL.md` セクション 1–10）
- **個性（aesthetic）の軸**: tone・differentiation・Typography display+body・Motion・装飾レイヤー（`IDEAL.md` セクション 11–13、`AESTHETIC.md`）

「揃っているだけで凡庸」も「尖っているだけでバラバラ」も避ける。両方を SSOT に書く。

## 責任と読者

この入口は親が作成・評価・反映のモード、対象範囲、完了条件、最終判断を持つ。親が直接作業する場合は、同じ package の実行者資料を必要な範囲で読む。委任する場合は、親が実在確認した `BOOTSTRAP.md`、`AUDIT.md`、`IDEAL.md`、`AESTHETIC.md`、stack reference の物理 path と対象・制約を担当へ渡し、担当自身に必要な資料を Read させる。

担当は専門結果と未確認範囲だけを親へ返し、SSOT・コード・report・記憶を保存しない。保存や反映は親が明示した writer と対象 path で行う。担当へこの親用のモード選択・委任・統合手順を渡して、同じ工程を再起動させない。評価結果を別の共通契約へ変換する必要がある場合だけ、親が reviewer の正本を使って接続する。

## Entry Routing

最初に、依頼文と既存の明示承認から実行モードを決める。監査・確認・レビューだけの依頼は `評価` とし、作成や修正を暗黙に含めない。

| モード | 選択条件 | 動作 |
|--------|----------|------|
| `作成` | SSOT、デザインシステム、コンポーネントの新規作成が依頼された場合 | `BOOTSTRAP.md` を使い、必要なら Aesthetic Direction Interview を行って SSOT を作成する。 |
| `評価` | audit、レビュー、整合性確認、チェックだけが依頼された場合 | 既存の SSOT とコードを読み取り、`AUDIT.md` の結果・指摘・未確認を返す。SSOT、コード、設定は変更しない（`audit-only`）。 |
| `反映` | 修正、更新、適用が依頼され、またはその変更について既存の明示承認がある場合 | SSOT を先に更新し、依頼範囲のコードへ反映してから `AUDIT.md` で再評価する。 |

`評価` で SSOT がない場合は `BOOTSTRAP.md` を実行せず、SSOT を必要としない項目の評価を続ける。SSOTが不在で判定できない項目は不在・未確認として報告する。モードが不明で変更を伴う場合は、モードが確定するまで生成・修正を始めない。

## Entry Flow

以下の順で判断して動け。

### 1. SSOTを探す

プロジェクトルートに `design-system.config.*` が存在するか確認する。
`作成` モードで存在しない場合だけ `BOOTSTRAP.md` に従いSSOTを生成する（**Step 1.5 の Aesthetic Direction Interview を必ず通す**）。`評価` モードで存在しない場合は生成せず、評価可能な範囲を続けて不在を報告する。`反映` モードで必要なSSOTが存在しない場合は、その不足を変更の阻害として報告する。

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
| 既存コードの改善・レビュー | `評価` では `AUDIT.md` に従いgapを検出して指摘・未確認を返す。`反映` が依頼または明示承認されている場合だけ修正する（aesthetic-implementation 不整合と generic AI aesthetics も検出対象） |
| デザインシステム自体の更新 | `反映` モードで SSOTを先に更新 → 影響を受けるコンポーネントを修正 → `AUDIT.md` で整合性を確認 |
| トークン階層の見直し・テーマ対応 | `IDEAL.md` のセクション1（階層構造）とセクション6（テーマ対応）を参照 |
| WCAG準拠・アクセシビリティ確認 | `IDEAL.md` のセクション2（トークン値の品質）を参照 |
| **美学的方向性の確認・更新** | `評価` では `AESTHETIC.md` を読み、確認結果と更新提案を返す。`作成` または `反映`（既存の明示承認に作成が含まれる場合は `作成` 経路）の範囲でのみ SSOT の `aesthetic` セクションを更新し、`反映` 時にSSOTが不在でも関連しない評価・変更を続けて不足を報告する。tone / differentiation / antiDirection を明示する |
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

監査結果の報告と変更の反映を分ける。`AUDIT.md` の修正手順は `反映` モードでのみ実行し、`評価`（`audit-only`）では指摘と未確認の報告で終了する。

## Notes

- このスキル自体にプロジェクト固有の値は一切含まない（aesthetic も含めて、具体的なフォント名・色値はプロジェクトの SSOT 側で書く）
- SSOTのフォーマットはプロジェクトのスタックに依存する（詳細は `BOOTSTRAP.md`）
- スキルのバージョンが上がっても移行スクリプトは存在しない。`IDEAL.md` の更新内容に対して現状のgapを `AUDIT.md` で検出する
- frontend-design スキル（Anthropic 公式）と並列に存在することを許容する。frontend-design は単発の創作向け、このスキルは継続的なシステム維持向け。両者の思想は `AESTHETIC.md` で接続している
