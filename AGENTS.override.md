# Dotfiles Project Guidance

This repository uses `AGENTS.md` as the shared core for global Codex/OpenCode guidance. The same content is generated into `~/.codex/AGENTS.md`, so this project override intentionally stays small to avoid loading the shared guidance twice when Codex runs inside this repository.

## Repository Scope

- The definitive AI workflow architecture spec is `AI-WORKFLOW-SPEC.md`.
- Treat `AGENTS.md`, `.agents/skills/**`, `.codex/agents/**`, `.codex/skills/**`, `mcp-servers.json`, `.codex/config.base.toml`, `etc/sync-codex.sh`, and `etc/sync-opencode.sh` as workflow/source files.
- Do not hand-edit generated Codex files under `.codex/AGENTS.md` or `.codex/config.toml`; edit the source file or adapter script and regenerate.
- Treat `.codex/agents/*.toml` and `.codex/skills/**` as Codex-native overlays. Do not require them to match `.claude/**` or `.agents/**` byte-for-byte.
- Claude Code remains native: do not generate `.claude/**` from Codex/OpenCode sources.
- After changing generated-adapter sources, run `bash etc/sync-codex.sh`; run `bash etc/sync-opencode.sh` when OpenCode output should also update. `sync-codex.sh` no longer rewrites Codex agent/skill overlays unless `SYNC_CODEX_LEGACY_MIRROR=1` is explicitly set.
- Before committing, stage files individually and inspect `git diff --cached`.
