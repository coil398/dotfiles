# sanitized-cwd 計算プロトコル（SSOT）

PIR² 系スキル（pir2 / pir2async / debug / ir / reviewer / review-pr / writing-plan / refactor-advisor / retro）の `PROJECT_MEMORY_DIR` 導出に使う **sanitize 正規表現の SSOT**。Codex harness の sanitize ロジックと一致させる必要があるため、変更時はこのファイルのみを更新し、参照側 9 ファイルに横展開する。

Codex-native SSOT path: `${CODEX_SKILLS_DIR}/pir2/references/sanitized-cwd.md`

`CODEX_SKILLS_DIR` は、読み込み済みの本 `SKILL.md` の実体パスから親の親として解決します。対象アプリケーションの `PROJECT_ROOT` とは別の場所であり、対象 repo 内に `.codex/skills` が存在することを仮定しません。

---

## 正規表現 SSOT

```text
sed 's|[^a-zA-Z0-9]|-|g'
```

意図:
- Codex harness が `~/.codex/memories/<sanitized-cwd>/` を作成するときの sanitize ロジックと一致させる
- ASCII 英数字 (`a-zA-Z0-9`) 以外の **すべての文字**（`/`・`.`・`-`・スペース等）を `-` に置換する
- これにより `/home/user/ghq/github.com/org/repo` → `-home-user-ghq-github-com-org-repo` のような変換になる

---

## 入力ソース（呼び出し側で選択する）

入力ソースは利用箇所によって 2 系統存在する:

| 系統 | 入力 | 採用スキル | 用途 |
|---|---|---|---|
| **pwd 系** | `pwd` の出力 | pir2 / pir2async / debug / ir / reviewer / review-pr / writing-plan / refactor-advisor | スキル起動時の現在ディレクトリを sanitize して `PROJECT_MEMORY_DIR` を導出 |
| **target_path 系** | `$target_path` 変数 | retro | `/retro` トリガーから渡された対象ディレクトリパスを sanitize（current dir と異なる場合がある） |

利用箇所のコード例:

```bash
# pwd 系（pir2 等）
sanitized_cwd="$(pwd | sed 's|[^a-zA-Z0-9]|-|g')"

# target_path 系（retro）
sanitized_cwd="$(echo "$target_path" | sed 's|[^a-zA-Z0-9]|-|g')"
```

**両系統で sed 正規表現 `[^a-zA-Z0-9]|-|g` は完全に一致する**。揺れさせてはならない。

---

## Codex-native artifact run override（epic → PIR²）

この SSOT の sanitize 式は `PROJECT_MEMORY_DIR` 専用です。実行 artifact の root を
sanitize してリポジトリ内へ戻してはいけません。epic / PIR² の標準 artifact root は
常に `$HOME/.ai-pir-runs` とし、起動時に次を確認します。

- root は実体のある directory で、root entry 自体が symlink ではないこと。存在しない
  場合の作成は `umask 077` と atomic `mkdir` を使い、既存 path を再利用しないこと。
- epic の `EPIC_RUN_DIR` と各 Ti の `SUB_RUN_DIR` はこの root の下で atomic `mkdir`
  により一意に予約し、衝突した path、file、symlink を再利用しないこと。
- 親 epic が起動 prompt に明示する `PIR2_RUN_DIR` は、子 PIR² が Phase 0 で採用する
  override です。子は canonical root 配下、実体 parent、symlink component なし、
  既存 ledger/artifact と衝突しないことを検証し、検証失敗時に別の run path へ
  silent fallback しません。`PIR2_PARENT_EPIC_RUN_DIR` が渡された場合は、子 path が
  その親 epic path の下にあることも確認します。
- override がない場合だけ PIR² が標準 root 直下に一意の `RUN_DIR` を生成します。
  acceptance、worker/reviewer/tester report、user decision は常に採用済みの
  実体 `RUN_DIR`（親 override 時は実体 `SUB_RUN_DIR`）を使います。

path 境界、owner/mode、symlink、runner provenance sidecar、ledger schema の実装は
`${CODEX_SKILLS_DIR}/worker-delegation/SKILL.md` と
`${CODEX_SKILLS_DIR}/worker-delegation/scripts/record-observation.sh` を
SSOT とします。ここでは sanitize と artifact-root の責務境界だけを定め、helper の
TSV schema や append 実装を重複記載しません。

---

## 参照側のファイル一覧

このリファレンスに対応する 9 ファイル（メモリ導出を行うファイルでは sed 式と入力ソースを上記表に合わせる。メモリ導出を行わないファイルは式を重複記載しない）:

| # | ファイル | 入力系統 |
|---|---|---|
| 1 | `${CODEX_SKILLS_DIR}/pir2/SKILL.md` | pwd 系 |
| 2 | `${CODEX_SKILLS_DIR}/pir2async/SKILL.md` | pwd 系 |
| 3 | `${CODEX_SKILLS_DIR}/debug/SKILL.md` | pwd 系 |
| 4 | `${CODEX_SKILLS_DIR}/ir/SKILL.md` | pwd 系 |
| 5 | `${CODEX_SKILLS_DIR}/reviewer/SKILL.md` | pwd 系 |
| 6 | `${CODEX_SKILLS_DIR}/review-pr/SKILL.md` | pwd 系 |
| 7 | `${CODEX_SKILLS_DIR}/writing-plan/SKILL.md` | pwd 系 |
| 8 | `${CODEX_SKILLS_DIR}/refactor-advisor/SKILL.md` | pwd 系 |
| 9 | `${CODEX_SKILLS_DIR}/retro/SKILL.md` | target_path 系 |

---

## Codex harness 仕様変更時の更新手順

Codex harness の sanitize ロジックが変わった（例: `.` を残す、ハッシュ化に変わる、等）場合の更新手順:

1. **本ファイルの「正規表現 SSOT」セクションを更新する**（最初に SSOT を直す）
2. **検証スクリプトを実行**して、9 ファイルの path 解決と、メモリ導出を行うファイルの実際の式を確認:
   ```bash
   bash "${CODEX_SKILLS_DIR}/pir2/references/verify-sanitized-cwd.sh"
   ```
3. スクリプトが揺れを検出したら、対象ファイルの sed 式を SSOT に合わせて修正する
4. 既存 `~/.codex/memories/` 配下の旧ディレクトリ（旧 sanitize 規則で作られたもの）は **手動でマージ判断**する。retrospector N1.5「プロジェクトメモリディレクトリ整合性チェック」が並存検知を担う

---

## 検証スクリプト（機械検出）

「ルールを書いたら機械検出も同時に作る」原則（feedback_rule_with_enforcement）に従い、9 ファイルの path 解決と、メモリ導出を行うファイルの sed 式が SSOT と一致していることを検証するスクリプトを併設する。

スクリプトパス: `${CODEX_SKILLS_DIR}/pir2/references/verify-sanitized-cwd.sh`

実行方法:

```bash
bash "${CODEX_SKILLS_DIR}/pir2/references/verify-sanitized-cwd.sh"
```

成功時の出力例:
```
OK: <N> Codex skill paths resolved from CODEX_SKILLS_DIR; <M> sanitize consumers use [^a-zA-Z0-9]|-|g
```

失敗時の出力例:
```
NG: 1 Codex sanitized-cwd check failed
  - ${CODEX_SKILLS_DIR}/foo/SKILL.md: expected [^a-zA-Z0-9]|-|g, found [^a-zA-Z0-9_]|-|g
```

CI/pre-commit に組み込む際は exit code 1 で停止させる設計（スクリプト内で `exit 1` を返す）。

---

## 既存の並存ディレクトリへの対処

過去の Codex harness 旧版が `.` を残す sanitize ロジックを使っていた時期があり、`~/.codex/memories/` 配下に `github-com` 形式と `github.com` 形式の両方が並存している場合がある。

- **retrospector N1.5** が並存検知を担い、警告レポート挿入 + レジストリ自動フラグ化を行う（`~/.codex/agents/retrospector.toml` 参照）
- 自動マージは **行わない**（データ損失リスク）。ユーザー判断でマージするときは古い方の `feedback_*.md` / `MEMORY.md` / `pir_*_log.md` を新しい方に手動マージする
- 現状の式 `[^a-zA-Z0-9]|-|g` は harness 現行版と一致しており、新規ディレクトリは正しく現行系統に集約される

---

## 関連リファレンス

- `~/.codex/agents/retrospector.toml` の N1.5「プロジェクトメモリディレクトリ整合性チェック」
- `~/.codex/memories/<sanitized-cwd>/memory/feedback_rule_with_enforcement.md`（ルールには機械検出を併設する原則）
