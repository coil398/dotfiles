## 監査レポート: Codex 契約・同期・worker-delegation 境界の監査

### 確認結果

- 主要契約は整合している。`AI-WORKFLOW-SPEC.md`、`AGENTS.md`、`etc/sync-codex.sh`、`etc/seed-codex-overlay.sh`、`etc/test-codex-contracts.sh`、`.codex/config.base.toml`、`.codex/skills/worker-delegation/**` の間で、共有 core と native overlay の境界は一貫している。
- default sync は `.codex/AGENTS.md`、`.codex/config.toml`、共通補助ドキュメントのみを再生成し、`.codex/agents/**` と `.codex/skills/**` は既定では触らない設計になっている。
- `worker-delegation` は共有 core ではなく Codex-native overlay として維持され、runner も `.codex/skills/worker-delegation/scripts/run-worker.sh` に閉じている。
- `seed-codex-overlay.sh` は missing-only で、既存 overlay を上書きしない。
- テストスクリプトは契約の確認として有効だが、`sync-codex.sh` と `seed-codex-overlay.sh` を実際に呼ぶため、純粋な read-only テストではない。

### 根拠

- `AI-WORKFLOW-SPEC.md:10-15` で shared core + native overlays、strict byte-for-byte sync 非既定が明示されている。
- `AI-WORKFLOW-SPEC.md:51-72` で default `sync-codex.sh` の生成対象と、`SYNC_CODEX_LEGACY_MIRROR=1` のみが旧ミラー再生成であることが明記されている。
- `AI-WORKFLOW-SPEC.md:74-107` で `worker-delegation` が Codex-native contract であり、Luna/Terra の actor ladder と自動 fallback 禁止が定義されている。
- `AGENTS.md:20-22, 41-46, 105-110` で、生成物と native overlay の扱い、及び generated files の編集禁止と native overlay の編集許容が整合している。
- `etc/sync-codex.sh:17-41` で生成対象と preserved native overlay がコメントと実装の両方で定義されている。
- `etc/sync-codex.sh:122-219` で default config 生成、`mcp-servers.json` からの再構成、既存 `config.toml` の machine-local trust 継承、TOML 検証が実装されている。
- `etc/sync-codex.sh:516-522` で `SYNC_CODEX_LEGACY_MIRROR=1` 時のみ legacy mirror を実行し、未指定では strict mirror をスキップする。
- `etc/seed-codex-overlay.sh:6-13, 166-245` で missing-only seed、worker-delegation 非 seed、codex-runner omission、既存 overlay 非上書きが実装されている。
- `.codex/config.base.toml:1-10` で shared SSOT には worker actor pin を置かず、Codex-native model routing を base config に閉じる方針が書かれている。
- `.codex/skills/worker-delegation/SKILL.md:13-19, 23-28, 47-69` で Sol/Luna/Terra の責務、no auto fallback、runner 入力検証、acceptance の分離が定義されている。
- `.codex/skills/worker-delegation/scripts/run-worker.sh:54-124` で actor→model の固定、必要引数検証、`R<number>` 要件検証、既存変更破壊禁止の注入が実装されている。
- `etc/test-codex-contracts.sh:42-53, 82-90, 94-132, 134-193` で worker package の存在、旧パス不在、auto fallback 不在、shared core への漏れ不在、default sync の overlay 保護、seed の非破壊性を検査している。

### 契約の妥当性評価

- full migration の裏取りは概ね十分。少なくとも「shared core」「generated adapters」「native overlays」の三層が明文化され、default sync と legacy mirror の切り替えもコードと文書で一致している。
- generated/native 境界は正しい。特に `.codex/skills/worker-delegation/**` を例外的に native overlay として固定し、`seed-codex-overlay.sh` と default `sync-codex.sh` の両方で上書き対象外にしている。
- docs と runtime の不一致は見当たらない。`AGENTS.md` の generated/native 方針、`AI-WORKFLOW-SPEC.md` の契約、`config.base.toml` の model routing、runner の実装が同じ方向を向いている。

### テストの脆弱性・副作用

- `etc/test-codex-contracts.sh` は `bash etc/sync-codex.sh` と `bash etc/seed-codex-overlay.sh` を実行するため、テスト自体が生成物を更新しうる。`cksum` で前後比較して non-destructive を確認する設計だが、完全な read-only ではない。
- `assert_contains` / `assert_not_contains` は文字列スキャンなので、将来の文言変更に弱い。契約の意味が残っていても表現が変わると false positive になりうる。
- `find ... | xargs -0 grep -El ...` の漏れチェックは広いが、非テキストや極端に大きいファイル、将来の新規パス命名に対しては機械的な網羅性しか持たない。
- ただし現時点では、これらは契約監査の用途として許容範囲で、直ちに破綻している箇所は見つからなかった。

### 影響範囲

- 直接影響: `AI-WORKFLOW-SPEC.md`、`AGENTS.md`、`etc/sync-codex.sh`、`etc/seed-codex-overlay.sh`、`etc/test-codex-contracts.sh`、`.codex/config.base.toml`、`.codex/skills/worker-delegation/SKILL.md`、`.codex/skills/worker-delegation/scripts/run-worker.sh`
- 間接影響: `.codex/AGENTS.md`、`.codex/config.toml`、`.codex/agents/*.toml`、`.codex/skills/**`、`~/.config/opencode/**`、`.cursor/**` の生成・運用ルール

### 依存関係

- インポート関係: `sync-codex.sh` は `AGENTS.md`、`.claude/*.md`、`mcp-servers.json`、`.codex/config.base.toml`、`.agents/skills/**` に依存する。
- 被参照関係: `worker-delegation` は `debug`、`ir`、`pir2`、`writing-plan`、`epic`、`pir2async` から参照される。`AGENTS.md` と `AI-WORKFLOW-SPEC.md` は全体方針の SSOT として参照される。

### 補足情報

- `etc/test-codex-contracts.sh` は監査対象として有用だが、副作用があるため CI/ローカルでの実行順序には注意が必要。
- `SYNC_CODEX_LEGACY_MIRROR=1` は明示的に legacy snapshot を再生成する escape hatch であり、default sync と混同しないことが重要。
- 現時点で「full migration を証明できない」「native boundary が崩れている」「worker package が shared core に漏れている」といった致命的な不整合は見つからなかった。

### 参照した外部ソース

なし
