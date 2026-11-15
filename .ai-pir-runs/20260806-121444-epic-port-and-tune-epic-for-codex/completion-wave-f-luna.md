Updated only the six owned skill files:

- `.codex/skills/debug/SKILL.md`
- `.codex/skills/pir2/SKILL.md`
- `.codex/skills/ir/SKILL.md`
- `.codex/skills/writing-plan/SKILL.md`
- `.codex/skills/walkthrough/SKILL.md`
- `.codex/skills/instruction-refactor/SKILL.md`

Results:

- Forbidden-routing scan: passed.
- `git diff --check`: passed.
- Sanitized verifier: passed.
- Deterministic verifier: passed, 8/8 fixtures.
- Contract verifier: blocked by out-of-scope `.codex/skills/codex/SKILL.md` failures; 197 passed, 2 failed.
- No staging, sync, commit, or push performed.