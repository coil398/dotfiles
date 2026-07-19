# sanitized-cwd 計算プロトコル（SSOT）

PIR² 系スキル（pir2 / pir2async / debug / ir / reviewer / review-pr / writing-plan / refactor-advisor / retro）の `PROJECT_MEMORY_DIR` 導出に使う **sanitize 正規表現の SSOT**。Codex harness の sanitize ロジックと一致させる必要があるため、変更時はこのファイルのみを更新し、参照側 9 ファイルに横展開する。

---

## 正規表現 SSOT

```text
sed 's|[^a-zA-Z0-9]|-|g'
```

意図:
- Codex harness が `~/.cursor/memories/<sanitized-cwd>/` を作成するときの sanitize ロジックと一致させる
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

## 参照側のファイル一覧

このリファレンスを参照する 9 ファイル（各ファイルで sed 式は同一・入力ソースは上記表の通り）:

| # | ファイル | 入力系統 |
|---|---|---|
| 1 | `.cursor/skills/cursor-pir2/SKILL.md` | pwd 系 |
| 2 | `.cursor/skills/cursor-pir2async/SKILL.md` | pwd 系 |
| 3 | `.cursor/skills/cursor-debug/SKILL.md` | pwd 系 |
| 4 | `.cursor/skills/cursor-ir/SKILL.md` | pwd 系 |
| 5 | `.cursor/skills/cursor-reviewer/SKILL.md` | pwd 系 |
| 6 | `.cursor/skills/cursor-review-pr/SKILL.md` | pwd 系 |
| 7 | `.cursor/skills/cursor-writing-plan/SKILL.md` | pwd 系 |
| 8 | `.cursor/skills/cursor-refactor-advisor/SKILL.md` | pwd 系 |
| 9 | `.cursor/skills/cursor-retro/SKILL.md` | target_path 系 |

---

## Codex harness 仕様変更時の更新手順

Codex harness の sanitize ロジックが変わった（例: `.` を残す、ハッシュ化に変わる、等）場合の更新手順:

1. **本ファイルの「正規表現 SSOT」セクションを更新する**（最初に SSOT を直す）
2. **検証スクリプトを実行**して、9 ファイル全てに同一式が存在することを確認:
   ```bash
   bash .cursor/skills/cursor-pir2/references/verify-sanitized-cwd.sh
   ```
3. スクリプトが揺れを検出したら、対象ファイルの sed 式を SSOT に合わせて修正する
4. 既存 `~/.cursor/memories/` 配下の旧ディレクトリ（旧 sanitize 規則で作られたもの）は **手動でマージ判断**する。retrospector N1.5「プロジェクトメモリディレクトリ整合性チェック」が並存検知を担う

---

## 検証スクリプト（機械検出）

「ルールを書いたら機械検出も同時に作る」原則（feedback_rule_with_enforcement）に従い、9 ファイルの sed 式が SSOT と一致していることを検証するスクリプトを併設する。

スクリプトパス: `.cursor/skills/cursor-pir2/references/verify-sanitized-cwd.sh`

実行方法:

```bash
bash .cursor/skills/cursor-pir2/references/verify-sanitized-cwd.sh
```

成功時の出力例:
```
OK: 9 SKILL.md files all use the SSOT sanitize regex [^a-zA-Z0-9]|-|g
```

失敗時の出力例:
```
NG: 1 file deviates from SSOT sanitize regex
  - .cursor/skills/foo/SKILL.md: expected [^a-zA-Z0-9]|-|g, found [^a-zA-Z0-9_]|-|g
```

CI/pre-commit に組み込む際は exit code 1 で停止させる設計（スクリプト内で `exit 1` を返す）。

---

## 既存の並存ディレクトリへの対処

過去の Codex harness 旧版が `.` を残す sanitize ロジックを使っていた時期があり、`~/.cursor/memories/` 配下に `github-com` 形式と `github.com` 形式の両方が並存している場合がある。

- **retrospector N1.5** が並存検知を担い、警告レポート挿入 + レジストリ自動フラグ化を行う（`~/.cursor/agents/retrospector.md` 参照）
- 自動マージは **行わない**（データ損失リスク）。ユーザー判断でマージするときは古い方の `feedback_*.md` / `MEMORY.md` / `pir_*_log.md` を新しい方に手動マージする
- 現状の式 `[^a-zA-Z0-9]|-|g` は harness 現行版と一致しており、新規ディレクトリは正しく現行系統に集約される

---

## 関連リファレンス

- `~/.cursor/agents/retrospector.md` の N1.5「プロジェクトメモリディレクトリ整合性チェック」
- `~/.cursor/memories/<sanitized-cwd>/memory/feedback_rule_with_enforcement.md`（ルールには機械検出を併設する原則）
