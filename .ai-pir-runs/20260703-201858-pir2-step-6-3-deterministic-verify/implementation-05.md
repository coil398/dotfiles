## 実装完了レポート

### 変更ファイル一覧
- `.claude/skills/pir2/references/deterministic-completion-check.md` — Fable5 最終レビュー（review-04-fable.md）の Medium M-A（submodule 対応の部分リグレッション）と Low 3件（3c クォート統一・ERROR文言拡充・awk入れ子フェンス既知limitation明記）を修正。冒頭の機械検証案内も 6 シナリオに更新。
- `.claude/skills/pir2/references/verify-deterministic-check.sh` — Low 2件（実行ビット付与・submodule フィクスチャ追加）を対応。ヘッダーコメント・末尾サマリーの件数表記も6シナリオに同期。

### 実装概要
`{RUN_DIR}/review-04-fable.md` の VERDICT: PASS（Medium 1件・Low 5件）を全件解消した。

**Medium M-A（`--ignore-submodules=all` の部分リグレッション）**:
- pre-set / post-set の `git diff --name-only` を `--ignore-submodules=all` → `--ignore-submodules=dirty` に変更。これにより submodule work tree 内部の非コミット変更は引き続き無視しつつ、submodule のコミットポインタ変更（pointer bump）は親リポの1行申告として post-set に復元される（レビュー指摘の「pointer bump 申告が PHANTOM 化する」リグレッションを解消）。
- 3b の `check-ignore` 判定を if/else の2分岐から、終了コードによる3分岐（`0`=gitignore対象→untrackable / `1`=非ignore→trackable / それ以外（`128`等の fatal）=検証不能→untrackable）に変更。これにより `mysub/inner.md` のような submodule 内部パスの申告が「検証不能（untrackable）」に正しく分類され、PHANTOM hard fail の対象から除外される（レビュー指摘の「submodule 内パス申告が PHANTOM のまま」を解消）。
- 33行目の実集合説明を実挙動（pointer bump=trackable、submodule 内部パス=検証不能）に一致するよう書き換えた。

**Low 5件**:
1. 3c の `case` パターン `~*)` を 3b と同じ `"~"*)` のクォート記法に統一（機能差なし、表記統一のみ）。
2. 手順0 の ERROR 文とその直後の blockquote に「pre-set を再記録した上で実装 actor を再実行する」という具体アクションの両方を明記（従来は「戻ってやり直す」だけで具体アクションが一読で確定しなかった）。
3. CLAIMED 抽出直前のコメントに、awk フェンス除去（`awk '/^```/{c=!c;next} !c'`）が4バッククォート等の入れ子フェンスで内容漏れを起こしうる既知の限界を明記（fail-closed=偽PHANTOM方向で安全側であることも記載）。NO_OP 判定の同型フェンス除去にも同じ限界が適用される旨を一言添えた。
4. `verify-deterministic-check.sh` に実行ビット（`chmod +x`）を付与し、`verify-sanitized-cwd.sh` と表記を揃えた。
5. `verify-deterministic-check.sh` に submodule フィクスチャを追加（ローカルの submodule ソースリポジトリを `mktemp -d` 配下に作成し、ネットワーク非依存で `git submodule add` → pointer bump → 検証、の一連を実施）。以下の2点をアサート:
   - `mysub`（pointer bump）を申告 → `claimed-trackable.list` に入り `phantom.list` は空（PASS 相当）
   - `mysub/inner.md`（submodule 内部パス）を申告 → `claimed-untrackable.list` に入り、`claimed-untrackable-missing.list` は空（物理的に実在するため missing にはならない）

修正後、`bash ~/.claude/skills/pir2/references/verify-deterministic-check.sh` を実行し、構文チェック（3 ```bash ブロック）と全6フィクスチャ（PHANTOM / UNDECLARED / NO_OP / 非ASCIIファイル名 / フェンス内例示 / サブモジュール）が期待判定と一致することを確認した（exit 0）。`bash ~/.claude/skills/pir2/references/verify-sanitized-cwd.sh` も実行し10ファイル全て OK（exit 0）。`shellcheck` も `verify-deterministic-check.sh` に対し実行し0件（exit 0）。

### 注意点・未解決事項
- **診断根拠の正確性**: `--ignore-submodules=dirty` に変更したことで「submodule のコミットポインタ変更（pointer bump）」は再び親リポの delta に1行として現れるようになるが、「submodule 内部のファイル単位変更」は引き続き親リポの delta には決して現れない（git の仕様上、submodule 内部の個別ファイルパスは親リポの diff に出現しない）。したがって `mysub/inner.md` のような申告は、3b の3分岐判定により「検証不能（untrackable）」に分類されて PHANTOM hard fail を回避するが、これは「捏造でないことの証明」ではなく「git では原理的に検証できないので保留する」という設計（3c の `test -f` による物理存在確認が唯一の可視化手段）。この非対称性は Fable5 の設計 SSOT の既知の限界（残存限界④⑥）と同型であり、新規に導入したものではない。
- **submodule フィクスチャの前提**: `git submodule add` に `-c protocol.file.allow=always` を明示指定した（最近の git のローカルパス submodule 制限＝CVE-2022-39253 対策を回避し、テスト環境依存を減らす目的）。実行環境の git バージョンによらず動作することを、このマシンでの実行（exit 0）で確認済みだが、他マシンでの再現性は未検証（`verify-sanitized-cwd.sh` と同型の「前提脆弱性」として reference 側にも既にコメントで明記済み）。
- 上記以外にプラン外のスコープ逸脱はない。`git status` で変更ファイルを確認したところ、私が触ったのは上記2ファイルのみ（いずれも本 run の先行ラウンドで作成された untracked ファイル）。他の M/?? 状態のファイルは本 run の先行ラウンド（implementation-01〜04）および並行作業由来で、今回は一切触れていない。
