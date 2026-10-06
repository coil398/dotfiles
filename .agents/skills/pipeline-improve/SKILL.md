---
name: pipeline-improve
description: >-
  稼働中パイプラインの改善ループ。durable 実測で失敗型を確定し、deepthink(Fable)・
  swe-2 等の独立モデル腕に仮説を競わせ、lab A/B で収束形状を比較してから本番へ
  port する。「パイプラインを改善して」「収束しないループを直して」「A/Bで
  改善を測って」「lab で試してから本番に」「改善して安定化」といった依頼で使う。
  ユーザーが /pipeline-improve と入力したら使う。
---

# /pipeline-improve — 実測駆動のパイプライン改善

`/pipeline` が設計不変条件・`/pipeline-diagnose` が診断の読み方の正本。
ここは「改善を回す手順」の正本: **実測 → 仮説 → lab A/B → 本番 port → 実 run 検証**
の閉ループだけを書く。推測で本番を直さない。

## 改善の鉄則

- **LLM で実行し、実測から決定的処理へ移す**: 未確定の作業は既存契約と engine 制御の下で LLM に実行させ、入出力・失敗・判断根拠を観測する。安定した規則を fixture と受入条件にし、同じ契約の決定的処理へ段階的に置き換える。初めから規則が明確な処理は直接機械化し、意味・品質判断まで形式検査で代用しない。責務境界は `/pipeline` を参照
- **実行結果をゴールデンケースにする**: 正しさを確認した入力・出力・判断根拠・実行ログと品質・時間・token 使用量を基準として固定する。誤りを含む実行は失敗 fixture に残す。決定的な変換・集計・遷移は出力一致、生成・意味判断は必須情報と正しさを維持し品質同等以上で比較する。移行は品質退行なし・LLM 呼出数と token 使用量の削減を評価し、出力一致だけで欠陥を固定しない
- **検証経路を分ける**: 依存追跡・再利用・集計・遷移など規則の明確な修正は、失敗 fixture と対象限定の回帰テストで検証し、下記の独立モデル腕・LLM A/B を必須にしない。意味判断・生成・prompt の仮説比較に必要な場合だけモデル実験を使う。品質退行・時間・LLM 呼出数を測り、正常な実 run を止めずに適用する
- **実測が先**: durable state（journal / workflow-events / artifacts / metrics）で
  失敗型を `/pipeline` の4型（官僚ゲート / whack-a-mole / transport / evidence 死）
  ＋「品質 verdict の不収束」に分類してから動く。症状への対処療法・retry 増し・
  ゲート追加は禁止
- **1実験1変数**: A/B の腕は case を固定し、roles 版・model・prompt・transport の
  どれか1つだけを変える。複数変えた差分は帰属不能
- **lab で計測してから本番へ**: lab は production と同じ stage 契約・resume 規則で
  動くことが前提。lab 専用の別機構は作らない（`/pipeline` の不変条件）
- **失敗 run は資産**: BLOCKED/FAIL を出した実 run を lab case に fixture 化して
  計測基盤に還流させる
- **採用判定は収束形状**: 「動いた」ではなく ラウンド数・mustFix 推移・
  resolved/unresolved/regressed・patchChangeRatio・STILL_OPEN 残存 で勝敗を決める

## 手順

### 1. 失敗の実測パケットを作る

- BLOCKED/FAIL の末端 leaf を特定する（root の verdict ではなく、children ツリー
  の最深 BLOCKED ノードの `reason`/`decisionVerdict`）
- その leaf が参照する成果物・直前ラウンドの reviewer サマリー・openIssue の
  STILL_OPEN 一覧を1ファイルに集約する
- 「誰が FAIL を出し続けたか」より「**どの成果物が修正経路を持たないか**」を見る。
  指摘対象の成果物が loop の patch 対象に含まれない構造欠陥は頻出パターン
  （実例: W40 equity — patch は draft 本文しか触れず figure-spec/描画が
  round-1 のまま残り、reviewer の openIssue が永久 STILL_OPEN → r12 空転）

### 2. 仮説アームを独立モデルで競わせる

同じ証拠パケットを **互いに独立なコンテキスト** の異モデルへ渡し、修正案を
競合させる（両腕の出力を相互参照させない）:

```bash
# deepthink 腕（Fable 5.1 — deepthink/deepplan の熟考モデル）
devin -p --respect-workspace-trust false \
  --model claude-fable-5-1-high --prompt-file packet.md > arm-fable.out

# swe-2 腕
devin -p --respect-workspace-trust false \
  --model swe-2-max --prompt-file packet.md > arm-swe2.out
```

- パケットは自己完結にする（問い・観測済み事実・証拠ファイル path・rubric・
  対象コード path・不変条件の制約）
- 熟考担当には `deepthink/references/deliberator.md` の契約を path 指定で渡す
- rubric は照合可能な言葉で（「3案を比較し採用理由を述べる」「establish-once
  不変条件に違反しない形で書く」等）
- 腕の評価は「実コードを読んでいるか・不変条件を守るか・検証実験まで設計したか」
  で採点し、採用案と却下理由を記録する。一致した案は確度が高い

### 3. lab A/B を組む（writer-lab の実例）

```bash
node --experimental-strip-types scripts/writer-lab/lab.ts \
  --case scripts/writer-lab/cases/<case> \
  --roles scripts/writer-lab/roles/<vN> \
  --model <model-id> --slug <case内work名> \
  --runs-dir <arm専用dir>
```

- `--slug` は case 内 `pipeline/work/<slug>/` の実名に一致させる（勝手な slug を
  渡すと case 検査で即死する — 実測済み）
- **腕ごとに `--runs-dir` を分離する**。run dir 名は timestamp-case-roles で
  腕を区別しないため、外側の dir で腕を分ける
- roles 差分の腕は `roles/v<N>` を複製して新版を作り、差分は最小に
- 各腕の `.lab/metrics.json` が比較物: round × axis の verdict・mustFixCount・
  resolved/unresolved/regressed・elapsedMs・reviewMode(full/diff)
- 並列実行可（run dir 独立・devin セッションは cwd 単位）

### 4. 収束形状で採否を決める

| 指標 | 良い方向 |
|---|---|
| 収束ラウンド数 | 少ない（ただし FAIL 軸が残って打ち切りは不可） |
| STILL_OPEN / unresolved 残存 | 0 で収束 |
| regressed（PASS→FAIL 退行） | 0 |
| patchChangeRatio | 0.01〜0.17 の外科修正帯（全部書き直しは whack-a-mole 兆候） |
| 軸別 elapsedMs | 判定不能・timeout の混入なし |

「FAIL が減ったが openIssue が別成果物に逃げた」は未収束として扱う。

### 5. 本番へ port し、実 run で検証する

- loop 経路・座標・reentry の形状修正は **宣言層/compiler** で行う。依存追跡・
  再利用など共有制御の欠落は既存 engine の該当責務を修正し、別機構・別契約を
  複製しない。roles 修正は本番 roles dir へ port
- 回帰テストを先に通す（compiler test / correction-evidence test / resume test）
- live run への反映は **resume の live 再コンパイル**に任せる（run 途中の宣言
  変更は次回 resume で新しい形として続行される設計）。適用後の最初の resume で
  「次に起きるべきイベント」を予言して実機確認する
- port 後は同じ失敗型の再発を実 run の journal で確認してから完了とする

## 改善対象の典型パターン（W40 までの実測）

- **patch 対象外の成果物が FAIL を出し続ける**（figure-spec・描画成果物が loop の
  修正経路にない）→ patch 経路に refresh lane を足すか、openIssue を owner
  成果物の修復経路へ振り分ける。reviewer が「修正不可能な成果物」を blocking
  する構造は収束不能
- **章別字数 budget 違反・論理内部矛盾**は本文 patch で収束可能 — 軸の分類を
  間違えて構造問題扱いしない
- **親 runner の無言ハング**（生存だが子なし futex 待ち）は supervisor が
  「死亡」しか見ない設計の穴 — heartbeat/沈黙監視が別途要る（pipeline skill の
  HUNG 判定を親監視にも適用）
- **orphan dispatch**: 親死にで gateway 側に残った RUNNING は lease reclaim で
  回収される設計を実機で確認してから介入する

## 禁止

- FAIL を消すための照合・証明・承認ゲートの新設（官僚ゲート）
- 「今回だけ通す」skip・一時分岐・語彙 coerce
- lab だけで通る別機構・別契約
- 収束形状を見ずに「指摘が出なくなった」で完了宣言
- 実測なしに本番 roles / compiler を直接変更
