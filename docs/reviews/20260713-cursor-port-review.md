# Cursor port 全体レビュー

_作成: 2026-07-13 | run: 20260713-170313-cursor-port-review_

## 全体 VERDICT

**FAIL**（初回レビュー時点）→ **Critical/High は 2026-07-13 追記で remediation 済**（再レビュー未実施）

## REVIEWER_SET

correctness, consistency, quality, security, architecture

## 観点別 VERDICT（初回）

- correctness: **FAIL** — `.ai-pir-runs/20260713-170313-cursor-port-review/review-01-correctness.md`
- consistency: **FAIL** — `.ai-pir-runs/20260713-170313-cursor-port-review/review-01-consistency.md`
- quality: **FAIL** — `.ai-pir-runs/20260713-170313-cursor-port-review/review-01-quality.md`
- security: **FAIL** — `.ai-pir-runs/20260713-170313-cursor-port-review/review-01-security.md`
- architecture: **FAIL** — `.ai-pir-runs/20260713-170313-cursor-port-review/review-01-architecture.md`

## 主な指摘事項（Critical / High）と対応

### Critical

- [Critical] `.codex-runtime/auth.json` — リポ配下に Codex OAuth トークン実体。
  - **対応済**: `.gitignore` に `/.codex-runtime/`、`chmod 600`、**リポ内 `.codex-runtime/` ディレクトリ削除**。正本は `~/.codex/auth.json`（別 inode）。

### High

- [High] epic `PROJECT_MEMORY_DIR` が `~/.claude/projects` — **対応済**（`~/.cursor/projects`）。
- [High] epic が `.claude/skills` を Read — **対応済**（`.cursor/skills/pir2/references/...`）。
- [High] agents に `` `Agent` `` 残存 — **対応済**（バナーの「Claude の Agent 語彙は使わない」のみ残す）。
- [High] seed `adapt_agent_body` の壊れた path rewrite — **対応済**（破壊的置換廃止 + hygiene guard）。
- [High] `sonnet` / `opus` / `v2.1.172` 誤記 — **対応済**（role=reasoning|coding / Cursor Task 表記）。
- [High] 過剰 seed + 壊れたパス — **パス側対応済**（seed 集合自体は第2波設計どおり維持）。
- [High] `instruction-refactor` の `gpt-5.*` — **対応済**。
- [High] `.agents` ↔ `.cursor` 二重 SSOT / precedence 未契約 — **対応済**（`AGENTS.md` / `AI-WORKFLOW-SPEC.md` に Cursor precedence を明記）。
- [High] references 二重参照 — **対応済**（overlay 内は `.cursor/skills/.../references`）。
- [High] `.codex-runtime` 権限 — **対応済**（削除 + home `600`）。
- [High] SPEC Open items と plans smoke 矛盾 — **対応済**（Open items から smoke 未完を除去、plans に部分 PASS を明記）。

## Medium / Low

- brainstorm 過剰バナー — **対応済**（短縮）。
- その他 Medium/Low は各 `review-01-*.md` を参照。

## 最終成果物

- 本ファイル: `docs/reviews/20260713-cursor-port-review.md`
- 中間: `.ai-pir-runs/20260713-170313-cursor-port-review/review-01-*.md`
