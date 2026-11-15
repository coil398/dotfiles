Completed the scoped fixes. My edits were limited to the six owned files; existing unrelated worktree changes were preserved.

Changed:
- [consultation contract](/Users/kawasetakumi/dotfiles/.codex/skills/codex/SKILL.md:40)
- [normal PIR² review gate](/Users/kawasetakumi/dotfiles/.codex/skills/pir2/SKILL.md:397)
- [refactor-advisor return gate](/Users/kawasetakumi/dotfiles/.codex/skills/pir2/references/refactor-advisor-gate.md:5)
- [PIR² Async gates](/Users/kawasetakumi/dotfiles/.codex/skills/pir2async/SKILL.md:127)
- [workflow spec](/Users/kawasetakumi/dotfiles/AI-WORKFLOW-SPEC.md:106)
- [contract suite](/Users/kawasetakumi/dotfiles/etc/test-codex-contracts.sh:41)

Observed verification results:
- `bash -n etc/test-codex-contracts.sh` succeeded.
- `bash etc/test-codex-contracts.sh` → `254 passed, 0 failed`.
- The new temp fake-`codex` runner test verified Luna and Terra model pins, max effort, workspace-write sandbox, cwd, JSON/skip-git flags, stdin prompt, output report path, and unchanged worker overlay.
- Deterministic verifier: all 8 fixtures matched.
- Sanitized-CWD verifier: 9 skill files matched.
- `git diff --check` succeeded.

Blockers: none.