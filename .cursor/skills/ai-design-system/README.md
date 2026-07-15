# ai-design-system

プロジェクト内にデザインシステムのSSOT（Single Source of Truth）を作成・維持するためのCodexスキル。

## コンセプト

デザインシステムは外部ライブラリの依存として管理されることが多い（Chakra UI、shadcn/uiなど）が、これは移行コストとロックインを生む。このスキルは異なるアプローチを取る:

- SSOTはプロジェクト内部に設定ファイルとして配置する
- スキル自体はプロジェクト非依存 — プロジェクト固有の値を含まない
- AIエージェントがSSOTを読み取り **一貫性と個性の両軸** を担保する
- **一貫性**: トークン階層・命名規則・状態網羅・アクセシビリティ
- **個性**: aesthetic direction（tone / differentiation / antiDirection）・display+body フォント分離・Motionトークン・装飾レイヤー
- generic AI aesthetics（Inter / Roboto / 紫グラデ / 中央寄せ定型ヒーロー）への無意図な収束を SSOT で禁止リスト化することで回避する

## 仕組み

```
SSOTが存在する？
  No → BOOTSTRAP.md: プロジェクトのコンテキストからSSOTを生成
  Yes → AUDIT.md: 現状とあるべき姿のgapを検出
```

あらゆる技術スタックで動作する。SSOTのフォーマットはプロジェクトに応じて決定される（Tailwind設定、ScriptableObject、デザイントークンJSONなど）。

## 前提条件

- Codex（CLI / デスクトップアプリ / IDE拡張）

## インストール

### gitサブモジュール（推奨）

リポジトリの更新を自動的に追跡できる。

```bash
git submodule add https://github.com/coil398/ai-design-system .agents/skills/design-system
```

### 手動配置

リポジトリをクローンし `.agents/skills/design-system/` に配置する。

```bash
git clone https://github.com/coil398/ai-design-system .agents/skills/design-system
```

### CLAUDE.mdへの登録

インストール後、プロジェクトの `CLAUDE.md` に以下を追記する:

```md
## Design System
See .agents/skills/design-system/SKILL.md
```

## 使い方

スキルを登録すると、以下のような操作でエージェントが自動的にスキルを参照する:

- 「デザインシステムをセットアップして」 → BOOTSTRAP.mdに従いSSOTを生成
- 「デザインの一貫性をチェックして」 → AUDIT.mdに従いgapを検出
- 「新しいコンポーネントを作って」 → SSOTのトークン・規則に従い実装
- 「トークンを追加して」 → SSOTを更新し影響範囲を確認

## ファイル構成

| ファイル | 役割 |
|---------|------|
| `SKILL.md` | エージェントのエントリーポイント |
| `IDEAL.md` | スタック非依存のデザインシステムのあるべき姿の定義（一貫性・個性の両軸を含む） |
| `AESTHETIC.md` | 美学的方向性（aesthetic direction）の指針。tone / differentiation / antiDirection・generic AI aesthetics の回避・Typography display+body 分離・Motion・装飾レイヤー |
| `BOOTSTRAP.md` | SSOTが存在しない場合の生成フロー（Aesthetic Direction Interview を含む） |
| `AUDIT.md` | あるべき姿とのgapの検出・修正フロー（generic AI aesthetics 検出・aesthetic-implementation 整合チェック） |
| `stacks/web-frontend.md` | Web フロント特化の検証基準（Typography / Motion / Background / aesthetic execution） |

## 設計思想

- IDEAL.mdは「あるべき姿」を定義する。特定の状態からの移行方法ではない。差分はエージェントが導出する
- SSOTはコードである。リンターとエージェントの両方が読める機械可読な形式でなければならない
- スキルの更新は意図的に非破壊。スキル更新時、エージェントは新しいidealに対して現状のコードベースを再評価する。移行スクリプトは不要

## 関連スキルとの統合

### frontend-design（Anthropic 公式）と並列に使う

`frontend-design` は単発の創作向け（「印象に残る一画面を作る」）。`ai-design-system` は継続的なシステム維持向け（「全コンポーネントに一貫した aesthetic を保つ」）。両者は対立せず、役割分担できる:

| シーン | 推奨スキル |
|--------|----------|
| 新プロジェクトでまず1画面の方向性を見たい | `frontend-design` でラフを生成 → 気に入ったら `BOOTSTRAP.md` で SSOT 化 |
| 既存プロジェクトの SSOT を初期化 | `BOOTSTRAP.md`（aesthetic interview を含む） |
| 1コンポーネントだけインスピレーションが欲しい | `frontend-design` を単発で叩く（SSOT は後で取り込む） |
| デザインシステム全体の audit / AI slop 度の測定 | `AUDIT.md` ＋ `audit.sh`（generic font 直書き / 紫グラデ / aesthetic 欠落を一発検出） |

**統合パス（frontend-design → ai-design-system）の例**:
1. `/frontend-design` でアイデアラフを生成（フォント・配色・装飾の素案）
2. 気に入った要素を `aesthetic.tone` / `differentiation` / 主要トークンに翻訳
3. `BOOTSTRAP.md` の Step 3 テンプレに値を流し込む
4. `AUDIT.md` ＋ `audit.sh` で全体への波及（既存コードとの整合・generic AI default の混入）を確認
