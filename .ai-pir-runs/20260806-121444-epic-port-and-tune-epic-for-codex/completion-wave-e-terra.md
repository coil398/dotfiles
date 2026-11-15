Completed the scoped correction.

Changed:

- [.codex/skills/pir2async/SKILL.md](/Users/kawasetakumi/dotfiles/.codex/skills/pir2async/SKILL.md:37) — restored the canonical `${PROJECT_ROOT}/.codex/skills/pir2/references/sanitized-cwd.md` SSOT comment directly before the existing calculation.
- [etc/test-codex-contracts.sh](/Users/kawasetakumi/dotfiles/etc/test-codex-contracts.sh:237) — restored the exact-reference assertion.

Commands run, all exited successfully:

- `sh -n` / `bash -n` for both contract and sanitized-cwd verifier scripts
- `git diff --check`
- `bash .codex/skills/pir2/references/verify-sanitized-cwd.sh`
  - `OK: 9 Codex SKILL.md files use the SSOT sanitize expression…`
- `bash etc/test-codex-contracts.sh`
  - `codex contracts: 174 passed, 0 failed`

Scoped Git status lists only the two owned files. The worktree already contained unrelated changes on entry; I left them untouched. No sync, staging, commit, push, or blockers.