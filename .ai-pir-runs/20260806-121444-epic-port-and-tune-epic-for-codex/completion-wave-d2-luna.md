Completed changes:

- [.codex/skills/codex/SKILL.md](/Users/kawasetakumi/dotfiles/.codex/skills/codex/SKILL.md): rewrote as a read-only consultation router using `spawn_agent`/`followup_task`, `/deepthink`, `/research`, and `worker-delegation`.
- [etc/test-codex-contracts.sh](/Users/kawasetakumi/dotfiles/etc/test-codex-contracts.sh): updated router, PIR² async, deterministic verifier, PIR² integration, and walkthrough HTML contracts; removed legacy CLI/sync assertions.

Observed results:

- `sh -n`, `bash -n`, and `git diff --check`: passed.
- Contract test: `173 passed, 0 failed`.
- Only the two owned files are modified; nothing staged, committed, pushed, or synced.
- Blockers: none.