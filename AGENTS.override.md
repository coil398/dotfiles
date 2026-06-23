# Dotfiles Project Guidance

This repository uses `AGENTS.md` as the portable source for global Codex/OpenCode guidance. The same content is generated into `~/.codex/AGENTS.md`, so this project override intentionally stays small to avoid loading the portable guidance twice when Codex runs inside this repository.

## Repository Scope

- Treat `AGENTS.md`, `.agents/skills/**`, `mcp-servers.json`, `.codex/config.base.toml`, `etc/sync-codex.sh`, and `etc/sync-opencode.sh` as workflow/source files.
- Do not hand-edit generated Codex files under `.codex/AGENTS.md`, `.codex/config.toml`, `.codex/agents/*.toml`, or `.codex/skills/**`; edit the source file or adapter script and regenerate.
- Claude Code remains native: do not generate `.claude/**` from Codex/OpenCode sources.
- After changing workflow sources, run `bash etc/sync-codex.sh`; run `bash etc/sync-opencode.sh` when OpenCode output should also update.
- Before committing, stage files individually and inspect `git diff --cached`.
