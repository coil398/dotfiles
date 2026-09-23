# PIR² 実験レジストリ

PIR² の運用を恒久採用する前に検証している実験の定義。全 runtime（Claude Code・Codex・Cursor）がこのファイルを共有する。実験の担当名・指標は観測対象であり、通常 workflow の既定・必須人数・完了条件ではない。

## 観測の手順

PIR² の終了時（SKILL.md の「任意の改善と振り返り」）に、親が次を行う。

1. 下の `Status: Active` の実験のうち、今回の run が「対象になる run」に当てはまるものを選ぶ。当てはまらなければ何もしない。
2. 当てはまる実験ごとに、観測ログへ1件追記する。
   - 記録先：`~/.ai-pir-runs/experimental-observations.md`（全プロジェクト共通、git 管理外）。ファイルがなければ作る。
   - 形式：`## <日付> <実験名>` の見出しの下に、`project`、`runtime / 親のモデル`、各実験の「記録する項目」、`所見`（1〜3行）を箇条書きで書く。
   - 材料は、実際の計画・diff・担当の返却・focused check・review/test の結果だけにする。取得できない値（時間、トークン、費用など）は `未計測` と書き、推測で埋めない。
3. 同じ run で、このファイルの `Evidence Summary` の件数を更新する。`Recommendation` の変更は候補としてユーザーに示し、採否はユーザーが決める。

## Experiment: pir2-parallel-implementation-shards

- Status: Active
- Started: 2026-06-22
- Owner: user
- Recommendation: Continue observing

### 仮説
所有範囲と依存を厳密に分けられる実装を複数の担当へ並列に渡すと、review/test の品質を落とさずに待ち時間を短縮できる。review FAIL 後の修正は指摘箇所が明確なため、初回実装よりも並列化しやすい。

### 対象になる run
初回実装または review FAIL 後の修正で、親が「並列化するかどうか」を判断した run（並列化しなかった場合も、判断材料と理由を記録する）。

### 並列化の条件
- 担当間で書き込みファイルが重ならない。
- 共通型、API schema、migration、lockfile、生成物、golden、共有 config、共通 helper を複数の担当が触らない。
- 担当間に順序依存がなく、別担当の未確定の命名・抽象・データ形状に依存しない。
- 全担当の完了後に、親が統合後の差分と必要な確認を行う。
- 条件が曖昧なら単一担当か親の直接実装に戻す。

### 記録する項目
- 並列化の有無、初回の担当数、review-fix の担当数
- 担当の実装経路（Codex の Luna / Sol、Claude の担当、親の直接実装）
- 境界の衝突、重複した抽象、未接続の実装、手戻りの有無
- review / test の FAIL と、その再発の有無
- 待ち時間の変化（取得できなければ `未計測`）

### 採用・廃止の目安
- 採用：並列化した run が3回以上あり、並列化が原因の競合・品質低下・再実装の増加がなく、統合確認の手間が短縮効果を上回っていない。ユーザーが採用を決める。
- 廃止：同じファイル・共有契約・生成物で衝突した、分割で方針がずれて review/test の失敗や統合修正が増えた、または品質は同等でも運用の複雑さが短縮効果に見合わない。

### Evidence Summary
- 並列化を判断した run：0
- 並列化した run：0
- review-fix を並列化した run：0
- 並列化が原因の問題：0

## Experiment: orchestrator-and-codex-hands

- Status: Active
- Started: 2026-09-06（2026-09-23 に現行の構成へ合わせて観測対象を更新）
- Owner: user
- Recommendation: Continue observing

### 仮説
親（Claude Code の Opus 5.5、または Codex の Astra）が計画・統合・受入に専念し、手を動かす実装・修正を Codex の Luna Max（難所は Sol）へ渡すと、親が自分で実装する場合より品質を保ったまま手戻りと親の負担を減らせる。

### 対象になる run
実装・修正を含む run すべて。Codex へ委譲した場合（`/codex` の実装経路、`/pir2 --codex`、Codex の native collaboration）と、委譲しなかった場合（親の直接実装、Codex を使えず Claude の担当が実装した場合）の両方を記録する。

### 記録する項目
- 親の runtime・モデル・effort、実装担当のモデル・effort
- 委譲した範囲と、委譲しなかった場合はその理由
- 品質：見つかった欠陥・回帰、review / test の結果、Codex の変更申告と実差分の食い違い
- 手戻り：review / test の再実行回数、担当の再実行、親が肩代わりした作業
- 負担：完了までの時間、トークン・費用、ユーザーの介入（取得できなければ `未計測`）
- 交絡：同じ run でモデル以外の条件（workflow・review 構成・割当）も変えた場合はそれを書き、モデルの効果とみなさない

### Evidence Summary
- 対象になった run：0
- Codex へ委譲した run：0
- 委譲しなかった run：0
