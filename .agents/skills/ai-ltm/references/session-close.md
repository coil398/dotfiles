# セッション終了と安全な同期

ユーザーが作業を終了するとき、または親がセッション終了を記録するときだけ、この資料を読む。

## セッション終了時

ユーザーが作業を終了するとき（明示的に終了を伝えた場合、または会話が自然に終わる場合）:

1. 会話全体のサマリをepisodesに記録する
2. 埋め込みを生成する
3. `sync_memory.py push` で `memory.db` だけを同期する

```bash
EPISODE_ID=$(sqlite3 ~/ai-ltm-data/memory.db <<'EOSQL'
INSERT INTO episodes (summary, context, tags)
VALUES (
  'セッション全体の簡潔なサマリ',
  '何をやって、何が決まって、何が残っているか',
  'session-summary プロジェクト名 主要トピック'
);
SELECT last_insert_rowid();
EOSQL
)

python3 "$SKILL_DIR/scripts/vector_search.py" embed \
  --db ~/ai-ltm-data/memory.db \
  --id "$EPISODE_ID"

# 古くて使われていない記憶を自動アーカイブ
python3 "$SKILL_DIR/scripts/vector_search.py" archive \
  --db ~/ai-ltm-data/memory.db

python3 "$SKILL_DIR/scripts/sync_memory.py" push \
  --repo ~/ai-ltm-data \
  --db ~/ai-ltm-data/memory.db \
  --message "session: $(date +%Y-%m-%d) 簡潔な説明"
```

`push` は同期直前にもリモート変更を取り込み、自動マージ後の `memory.db` だけをコミット・pushする。失敗した場合は成功扱いにせず、そこで停止して表示された原因をユーザーへ報告する。

## 安全な同期と競合復旧

`sync_memory.py` は Git の通常マージに SQLite バイナリを任せず、共通祖先・ローカル・リモートの3つの DB を使って `episodes`、`meta`、`config` を3-way mergeする。双方で追加・変更された記憶を保持し、検索インデックスの整合性も検証してから DB を原子的に置換する。

同期前に次の状態を検出した場合は、安全のため Git や DB を変更せず停止する:

- `memory.db` 以外の未コミット変更がある
- `memory.db` が未ステージ変更以外の状態になっている
- merge、rebase、cherry-pick など既存の Git 操作が進行中
- detached HEAD、upstream 未設定、別の LTM 同期処理が実行中

`pull` の fetch、マージ、DB検証、またはマージ統合commitが失敗した場合は、作業前の SQLite スナップショットと開始時のGit HEADへ復元して非ゼロで終了する。`push` の同期前処理も同じ復元境界を持つが、同期後の専用commitまたはpushが失敗した場合は成功扱いにせず、作成済みのローカルcommitとDBを保持して原因を報告する。手動で片方の DB を選ぶ操作や競合中の commit は行わず、原因を解消してから同じ `pull` または `push` コマンドを改めて実行する。
