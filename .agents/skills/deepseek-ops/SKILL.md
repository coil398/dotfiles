---
name: deepseek-ops
description: DeepSeek V4.x Flash を複数 provider（OpenCode Go / NVIDIA Build / DeepInfra）経由で動かすときの失敗型・切り分け・運用の正本。DSML tool-call drift の検出と salvage、quota 層の確認、provider 選定に使う。「DeepSeek が応答しない」「tool call が空」「429 が続く」といった症状で使う。ユーザーが /deepseek-ops と入力したら使う。
---

# /deepseek-ops — DeepSeek V4.x Flash 運用知見

OpenCode Go / NVIDIA Build / DeepInfra に跨る DeepSeek V4.x 系の実測知識。調査期間は 2026-09-27〜29。

## provider × model の provenance（どこで何が起きたか）

| provider | modelId | 観測された事象 | 用途の結論 |
|---|---|---|---|
| OpenCode Go（`zen/go`） | `deepseek-v4.1-flash` | DSML drift は低率（完走実績あり）。唯一の壁は subscription quota | **本番本命**。quota 節で枠管理 |
| NVIDIA Build | `deepseek-ai/deepseek-v4.1-flash` | DSML drift 高率 + effort=max で 30-45min/stage、45min timeout SIGTERM あり | **検証専用**。本番・billing・publish に使わない |
| DeepInfra | `deepseek-ai/DeepSeek-V4-Flash` | **V4 ≠ V4.1（版違い）**。endpoint 生存のみ確認、pipeline 負荷は未実測 | **ユーザー明示指示があるときだけ**使う。勝手に回さない |

注意: 同名 `v4.1-flash` でも provider が違えば serving stack（chat template / tool-call parser / sampling / 量子化有無）が違う。**provider を跨いだ観測を同一モデルの実績として混同しない**。

## 失敗型: DSML tool-call drift（最重要）

**signature**（gateway event / diagnostics で判別）:

- `finishReason:"error"`、assistant text が空 or `"\n\n<｜DSML｜ calls>\n"` のような markup 残滓
- `toolCallContentObserved:true` なのに正規 tool call 0件
- pipeline 側では `RESULT_NOT_SUBMITTED` / `ASSISTANT_EMPTY` / `OUTPUT_SCHEMA_INVALID`（空 write_output submit）に化ける

**機構**: モデルは tool-call 意図を DSML 特殊トークン列として生成するが、serving 層の parser が `tool_calls[]` へ翻訳し損ねて生 markup が content に漏れる。**モデル refusal ではなく adapter 層の翻訳失敗**。量子化劣化ではなく構造破壊（二値的）。

**確率的**: 同一 wire・同一入力でも通ることがある（attempt 3 で成功の実例）。単発成否を wire 品質の証拠にしない。

**drift 率を上げる変数（実測）**:

1. 内部 schema 名の wire 露出（`article-v2-markdown.v1` / `editorial-json` 等が system/tool 応答/task に見える）→ 非表示化で有意に改善
2. topic 本文の到達（どの経路で渡しても drift 誘発、0/5）→ 宣言入力・契約に内包させる
3. L3 セレモニー全体の複雑さ（長い role prompt + 大きい入力で発生しやすい）

**効かないもの**: wire の極小化だけでは消えない（99B task でも 0/3）。除去不能な endpoint 確率事象として扱う。

**対処**:

- **salvage**: submit 未到達時、assistant text に残る**閉じタグの揃った** `<|DSML|invoke name="write_output">…</|DSML|invoke>` を parse して同じ tool handler に replay すれば成果物を救出できる（共通の salvage 処理）。切れた invoke は絶対に replay しない
- **retry 連打は正当運用**: 確率的 endpoint に対し resume を複数回回すのは設計通り。連続失敗時は時間帯・endpoint 窓を疑い間隔を空ける
- **probe**: 実 role + 実 staged inputs を gateway に直叩きする孤立 probe が endpoint sensor になる（用途に合わせた一時 probe スクリプトを使用）。pipeline 失敗と endpoint 劣化を切り分ける

## OpenCode Go の quota モデル

月額ドル枠を3層で制限: **5時間=20% / 週=50% / 月=100%**。binding 層が1つでも100%なら全 request 429。

- エラー: `429 {"type":"GoUsageLimitError","message":"Go usage limit exceeded"}`（body に reset 情報なし）
- **残量確認**: プロバイダーが公開する usage endpoint を認証付きで確認する。rolling / weekly / monthly の使用率と reset 時刻が得られる場合、429 が続いたときの切り分けに使う
- 同一 subscription の全 model で pool 共有 — Luna と DeepSeek を同時 retry すると quota を奪い合う
- 週次枯渇時の対処: 失敗 leaf への narrow scope resume と、hop 間に数分の delay を設定して回復監視窓を伸ばす。**週次 100% で reset が数日先なら素直に止める**

## 429 vs endpoint 障害の切り分け

キーなし probe: プロバイダーの chat completion endpoint が 401/0.4s を返せば endpoint 健全、401 でなければ接続層の障害。429 しか返さない場合は quota。`finishReason:"error"` に加えて、redact 済みの provider error に HTTP 詳細を記録すると原因を切り分けられる。

## provider 選定（失敗時の優先順位）

1. OpenCode Go（本番・安い）
2. NVIDIA Build（検証・無料 trial、drift 高率で遅い — 本番禁止）
3. DeepInfra（metered 課金、**ユーザー明示のみ**）

## 関連

- DSML drift の切り分け記録は、対象プロジェクトの運用ノートを参照
- quota 枯渇、journal recovery、scope 運用の記録も同じ場所に保管
