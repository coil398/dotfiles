## 背景ブリーフ（context）: W0+W1（6-3 決定論的完了検証）の最終深レビュー

探索3系統: 01（最終状態の逐語ダンプ＝`exploration-01.md` 995行に reference/verify スクリプト全文）/ 02（設計適合）/ 03（システミック影響＋外部）。**逐語の全文は `{RUN_DIR}/exploration-01.md`**。deliberator は必要に応じてそれを Read してよい（新規探索ではなく準備済み集約の参照）。

### 確定的な事実（出典あり）

**設計適合（exp-02, 部分適合が3件）**
- **問い1: 事象X の連鎖を断つか＝部分適合**。「implementer claim と reviewer verdict の矛盾に解決経路なく19分迷走」の後半は 6-3（reviewer 起動前に PHANTOM を hard fail）で断てる。**だが事象X の捏造は「implementer の tool 呼び出しが transcript に存在しない完全捏造」で、しかも L0（メイン Claude）自身が resume 直後に捏造・迷走した事象**。6-3 は L0 が prose 指示どおり bash を実際に呼ぶことに依存し、**外部 hook による独立検証がない** → 「6-3 自身の実行を誰が検証するか」という**再帰的信頼の盲点**（両 deepthink レポート未記載の新規論点）。加えて pir2 の `RESUME_MODE`（スラッシュ再起動）と事象X の「API 中断からの継続」は別レイヤーで、6-3 は後者専用の手当てを持たない。
- **問い2: W1 移行パス整合＝部分適合**。Fable5 §1-3 の L0 検証パイプライン6手順のうち実装 6-3 がカバーは「git 集合照合」**1手順のみ**（契約見出し grep・ARTIFACTS 検証・hook floor・STATUS 不変条件・台帳記録は未実装＝plan で明示スコープ外）。W2 は情報源フォーマット（`変更ファイル一覧` vs `EPIC_TELEMETRY`）もスコープ粒度（1 implementer vs ネスト pir2 全体）も異なり、**コード単純再利用は不可・技術（git 集合演算パターン）の再利用に留まる**。
- **問い3: 決定1=(A) 最小スコープ＝部分適合**。事象X の実インシデントは**初回実装点**（新規ファイル作成）で発生＝6-3 の適用範囲内。ただし 7-4/8-2/6.5-2(C)/refactor-advisor-gate の4種の再実装 entry は無検証（plan に follow-up 記録・意図的限定）。同型捏造が再実装で起きたら INNER_LOOP_COUNT 上限が部分的安全網になるが、6-3 の「reviewer 5体起動という高コストを回避する早期・安価検知」の価値は及ばない。

**システミック影響（exp-03, 新規偽陽性2件を実機発見）**
- **偽陽性(1) staged 変更の不可視化**: `git add`（ステージ済み）した変更は `git diff --name-only`（unstaged）にも `ls-files --others`（untracked）にも**一切現れない**。Claude implementer は Bash フル権限を持つのに `implementer.md` に git add 禁止が**0件**。plan のリスク開示は Codex（apply_patch）側のみ根拠で、**Claude implementer 側は一度も検証されていない**。→ 申告したファイルを stage すると PHANTOM hard fail（再実行で直らない）。
- **偽陽性(2) case-only rename**: macOS APFS（環境既定 FS）で大文字小文字のみの rename は git のあらゆるシグナルが空。→ PHANTOM hard fail 経路。両者ともレビュー4ラウンド（review-01〜04）で未言及。
- **統治の非対称**: `experimental.md` は shards/sequential/explorer-nesting/epic を `Status: Active` で追跡するが **6-3 に該当実験エントリは存在しない**（全文検索確認）。同日設計の epic は実験 track・6-3 は無条件本採用。
- **設計内の一貫性欠如**: 完成形設計では hook 側は log-only 段階導入（Stage A→B）なのに、**git-diff 側（6-3）はいきなり blocking**。
- **複雑性は sanitized-cwd 系先例比 2.4〜5倍**。self-verify スクリプトは CI/hook 未配線・手動実行依存。

**外部ベストプラクティス（exp-03, 一次情報）**
- Anthropic の Outcome verification / State check パターンに**整合**（発話でなく状態を見る設計は妥当）。出典: Anthropic 公式。
- Unit 42 調査「agent-skill の 80% が宣言と挙動不一致」＝決定論検証ゲート一般の必要性を裏付け。
- 既知の落とし穴3つ: **alert fatigue**（偽陽性で信頼空洞化）/ **eval saturation・brittle grading** / **Verification Theatre**（検証の体裁と実効性の乖離）―― 発見した偽陽性2件と重なる。
- git working-tree を oracle にすること自体は健全（通常編集・削除・mode 変更・非ステージ rename は実機で正常）。穴は staged 変更と case-insensitive FS の2点に限定。
- YAGNI（Fowler）は品質投資を否定しないが、設計内の blocking/log-only 非対称は指摘対象。

### 探索で見えた対立・論点（deliberation の焦点）
- **論点A（再帰的信頼）**: 「6-3 の実行を誰が検証するか（L0 が捏造・スキップしたら？）」は新規の本質的盲点か、それとも「どこかで人間/決定論に錨を下ろすしかない」不可避な信頼境界で残存限界に包含すべきか。
- **論点B（無条件採用 vs 実験 track）**: 6-3 を experimental.md の Active 実験として登録し観測すべきか、本採用でよいか。同日の epic は実験扱いなのに 6-3 だけ本採用の非対称は正当か。
- **論点C（staged 変更 FP は must-fix か）**: `git add` 不可視化は実運用頻度が低い（implementer は通常 stage しない）が「再実行で直らない hard fail」。implementer.md への git add 禁止1行 or 実集合に staged を含める、で塞ぐべきか、受容済み残存限界か。
- **論点D（過剰/過小）**: executions 0 の文脈で 5 実装ラウンド＋verify スクリプト＋6 フィクスチャは過剰か。一方 L0 パイプライン6手順中1手順しか無いのは過小か（両方向の緊張）。

### まだ埋まっていない空白
- 6-3 が実運用で通常 run の完走率をどれだけ下げるか（偽陽性の実発生頻度）は実 run 蓄積が無く未測定。
- L0 が 6-3 bash を実際に毎回正しく走らせるかの実証（再帰的信頼の実挙動）は未観測。

### 詳細資料（核心 bash 抜粋・逐語。全文は exploration-01.md）

集合照合の中核（`deterministic-completion-check.md`）:

```bash
# 実集合: git diff --name-only --ignore-submodules=dirty （unstaged）＋ ls-files --others （untracked）
# staged は対象外（implementer/Codex は stage しない前提）← exp-03 が反例を発見
{ git -C "$PROJECT_ROOT" -c core.quotePath=false diff --name-only --ignore-submodules=dirty
  git -C "$PROJECT_ROOT" -c core.quotePath=false ls-files --others --exclude-standard
} | sort -u > "$RUN_DIR/verify-${IMPL_INDEX}-post.list"
comm -13 pre.list post.list > delta.list          # delta = post - pre
# CLAIMED 抽出（フェンス除去 → 変更ファイル一覧セクション → `- \`path\`` 行）
awk '/^```/{c=!c;next} !c' "$f" | awk '/^### 変更ファイル一覧/{f=1;next} (/^## /||/^### /){if(f)exit} f' | grep -E '^- *`'
# 3b: claimed を trackable/untrackable に分岐（/*|~* → untrackable, check-ignore exit 0/1/128）
# PHANTOM = claimed-trackable - post（追跡可能なのに dirty でない＝捏造・hard fail）
# UNDECLARED = delta - claimed（申告外の実変更・warn 非ブロッキング）
```

判定規則（抜粋）: `phantom.list` 非空 → **PHANTOM_CLAIM = hard fail**。`claimed-trackable` 空 ∧ `delta` 空 ∧ NO_OP 免除なし → PHANTOM。`undeclared` 非空 → UNDECLARED = warn。失敗パス: PHANTOM → 検証レポート逐語注入で再実行1回 → 2回目 PHANTOM で reviewer 起動せずユーザーゲート（自動 restore なし）。適用: 初回実装点（6-1）のみ・main スキップ・pir2codex は report Write 後に検証。
