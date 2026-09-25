---
name: "ai-ltm"
description: >-
  過去の学び・失敗・意思決定・中断点を横断検索し、確定した知見を長期記憶へ記録する。セッション開始・再開、過去の経緯の参照、知見の確定、終了時の要約で自動利用する。短期の判断差分は /field-notes、感想は /ai-diary に分ける。ユーザーが /ai-ltm と入力したら使う。
---

# AI Long-Term Memory (ai-ltm)

`~/ai-ltm-data/memory.db` (SQLite) に、プロジェクト横断で再利用する学び・失敗・意思決定・中断点を蓄積する。

## 責任と読者

親が発動判断、query/summary、作業への反映、記録・同期の最終判断を持つ。直接実行する場合は、必要な script と reference だけをこの Skill の実体から読む。委任する場合は、親が実在確認した物理 path、対象範囲、起動権限、返却形式を worker に渡し、worker 自身に必要な資料を読ませる。

起動時の recall worker は bounded な recall だけを担当し、親の工程を再委任・再起動しない。worker は stage event と terminal record だけを返し、記録・embed・`mark-used`・同期を代行しない。利用できない非同期 API や未確認の path は本命を止める根拠にせず、未実行として返す。

## 自動発動とモード routing

承認済みの自動モードは毎回確認せず、条件に該当したモードだけを実行する。単なる進捗や毎回のツール成功では発動しない。

| 条件 | モード | 参照 |
|---|---|---|
| DB または repository の初回セットアップ、`setup-needed` の解消 | setup | [`references/setup.md`](references/setup.md) |
| セッション開始・長い中断からの再開 | bounded な非同期 recall | [`references/session-recall.md`](references/session-recall.md) |
| 前回の続き、過去の失敗、類似問題の参照 | 必要な範囲の search | [`references/search.md`](references/search.md) |
| 学び・失敗・意思決定・中断点の確定 | episode の record と embed | [`references/recording.md`](references/recording.md) |
| セッション終了・自然な会話終了・おやすみ・長く離れる旨 | summary、embed、同期 | [`references/session-close.md`](references/session-close.md) |
| 記憶の削除・修正・一覧・archive | 明示された management | [`references/maintenance.md`](references/maintenance.md) |
| cleanup の明示依頼 | 対話的な cleanup | [`references/cleanup.md`](references/cleanup.md) |

短期の判断差分は `/field-notes`、感想・日記は `/ai-diary` に分け、同じ内容を二重に記録しない。cleanup は自動発動しない。

## 共通の前提

親はロードした `SKILL.md` の実体パスの親を `SKILL_DIR` とし、そこから script と reference の絶対 path を確定する。検索は既存 DB を read-only で開き、`init.sql` をスキーマの SSOT として不足や不正を自動補完しない。書き込みは親が明示した範囲で行い、recall の terminal record を観測する前の insert、embed、`mark-used`、archive、同期は defer または skip する。

## 注意事項

- 記録は簡潔に。1つのepisodeのsummaryは1-2文に収める
- contextには再現に必要な情報を入れるが、コード全体のコピーは避ける
- 機密情報（パスワード、トークン、秘密鍵）は絶対に記録しない
- 検索は控えめに。毎回全検索するのではなく、関連しそうなときだけ引く
- SQLにユーザー入力を埋め込む際は、シングルクォートを `''` にエスケープする
