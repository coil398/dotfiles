# Cursor port 全体レビュー

_作成: 2026-07-13 | run: 20260713-170313-cursor-port-review_

## 全体 VERDICT

**FAIL**

## REVIEWER_SET

correctness, consistency, quality, security, architecture

## 観点別 VERDICT

- correctness: **FAIL** — `.ai-pir-runs/20260713-170313-cursor-port-review/review-01-correctness.md`
- consistency: **FAIL** — `.ai-pir-runs/20260713-170313-cursor-port-review/review-01-consistency.md`
- quality: **FAIL** — `.ai-pir-runs/20260713-170313-cursor-port-review/review-01-quality.md`
- security: **FAIL** — `.ai-pir-runs/20260713-170313-cursor-port-review/review-01-security.md`
- architecture: **FAIL** — `.ai-pir-runs/20260713-170313-cursor-port-review/review-01-architecture.md`

## 主な指摘事項（Critical / High のみ）

### Critical

- [Critical] `.codex-runtime/auth.json` — リポ配下に Codex OAuth トークン実体が untracked。`.gitignore` 未登録（当時）かつ gitleaks 非検知。誤 commit で認証漏洩。→ `/.codex-runtime/` を ignore、権限 `600`、可能ならリポ外へ移設・コピー削除。（出典: security）
  - **対応済（レビュー直後）**: `.gitignore` に `/.codex-runtime/` 追加、`auth.json` を `chmod 600`。リポ内ディレクトリ削除は未実施（要確認）。

### High

- [High] `.cursor/skills/epic/SKILL.md` — `PROJECT_MEMORY_DIR` が `~/.claude/projects` のまま。他スキルは `~/.cursor/projects`。（correctness / architecture）
- [High] `.cursor/skills/epic/SKILL.md` — ネスト pir2 が `.claude/skills` を Read するよう指示し、Cursor overlay をバイパス。（architecture）
- [High] agents overlay — `` `Agent` `` ツール語彙が残存（sed が `` `Agent` ツール `` 形しか置換せず）。skills 注記と矛盾。（correctness / consistency）
- [High] seed `adapt_agent_body` — `~/.claude/` → `dotfiles .claude reference:` がパス・シェルを破壊（約 75 ヒット）。（correctness / quality）
- [High] agents に `sonnet` / `opus` 残存、Claude Code `v2.1.172` を Cursor 機能として誤記。（consistency）
- [High] 過剰 seed（17 agents / 19 skills）＋壊れたパスのまま deep agents を載置。（quality）
- [High] `instruction-refactor` に `gpt-5.*` モデルピン残存。（quality）
- [High] `.agents/skills` と `.cursor/skills` 同名 16 件並存、precedence 未契約のまま第2波展開。（architecture）
- [High] pir2 等が `~/.agents/skills/.../references` を参照しつつ overlay 側にも references 複製 → 二重 SSOT。（architecture）
- [High] `.codex-runtime` ファイル権限が緩い（`auth.json` が 0644 だった等）。（security）— chmod 対応済
- [High] SPEC Open items と `docs/plans` の smoke 完了表記が矛盾。（consistency）

## Medium / Low

- Medium/Low は各 `review-01-*.md` を参照（合計おおよそ Medium 10+ / Low 数件）。

## 最終成果物

- 本ファイル: `docs/reviews/20260713-cursor-port-review.md`
- 中間: `.ai-pir-runs/20260713-170313-cursor-port-review/review-01-*.md`
