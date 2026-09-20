# Session Recall

セッション開始時または長い中断からの再開時だけ、この資料を読む。recall は本命タスクを補助する作業であり、本命タスクを block してはならない。

## 実行契約

会話の最初のターンまたは長い中断からの再開で、本命タスクを開始する直前に専任 recall subagent を 1 体だけ起動する。main は起動後に worker を await、blocking read、wait、完了待ちの follow-up をせず、直ちに本命タスクへ進む。recall の起動失敗、未実行、遅延、pull/search/schema/timeout の失敗はいずれも本命を block しない。

親は、ロードした `SKILL.md` の実体を基準にその親ディレクトリを `SKILL_DIR` とし、`SKILL_DIR/scripts/session_recall.py` を `SESSION_RECALL_SCRIPT` の絶対パスとして確定する。現在のユーザータスクから具体的な plain-text の `CURRENT_TASK_QUERY` と `CURRENT_TASK_SUMMARY` を作り、runtime の UTF-8 standard base64 primitive でそれぞれをエンコードする。worker message には親が確定した絶対パスと `CURRENT_TASK_QUERY_B64` / `CURRENT_TASK_SUMMARY_B64` だけを埋め込み、raw query / summary を埋め込まない。

shared core は特定 runtime の API 名を仮定せず、runtime が提供する native one-shot / no-fork async subagent API に worker message を渡す。message には次の引数を持つ `session_recall.py` の起動を 1 回だけ含める:

```text
python3 "<絶対パス SESSION_RECALL_SCRIPT>" \
  --repo ~/ai-ltm-data --db ~/ai-ltm-data/memory.db \
  --query-b64 "<CURRENT_TASK_QUERY_B64>" \
  --summary-b64 "<CURRENT_TASK_SUMMARY_B64>" --limit 5
```

worker は親から受け取った絶対 script path と encoded 値をそのまま使い、`session_recall.py` をちょうど 1 回だけ実行する。worker が main へ返すのはスクリプトが出力した JSONL の stage event と最後の terminal record だけであり、個別の git / vector search command や別の fallback search を重ねない。親は worker の結果を待たず本命タスクを続ける。

処理順は **preflight → optional pull → read-only combined search → report**。preflight で repository が無ければ `setup-needed`、dirty なら pull を skip して search を続ける。DB が無い場合や schema / IDF が不足する場合は search stage の明示的な failure とする。pull は非対話・bounded・最大 1 回の分類済み transient retry、search は既存 DB を read-only で開く。許可する terminal status は `completed` / `dirty` / `setup-needed` / `pull-failed` / `search-failed` / `timed-out` / `failed` のみとし、preflight failure は `failed` に stage detail を付けて報告する。stage の失敗詳細には固定カテゴリと終了コードなどのプロセスメタデータだけを残し、child stdout/stderr は含めない。

script は preflight / pull / search の間、repository 外の advisory lock を保持する。これは協調する ai-ltm writer に対する advisory protection であり、協調しない外部 writer までは保護しない。recall の terminal record を観測するまで、episodes の insert、embed、`mark-used`、archive、git 同期などの ai-ltm write は defer または skip する。検索結果を実際に本命タスクへ反映した場合だけ、`mark-used` は recall とは別の非同期処理として扱い、その完了を待たない。lock の取得も小さな bounded deadline で打ち切り、busy は `timed-out` として報告する。native subagent API を利用できない場合も recall を省略して本命を継続する。
