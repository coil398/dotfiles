# AI Lint

AI Lint scans newly added code and configuration lines for patterns that may introduce unrequested constraints, gates, options, compatibility paths, hash or provenance checks, swallowed failures, bypasses, and placeholders. It returns an advisory question to the AI; it never blocks the edit. `scan` accepts absolute and relative paths outside the current directory; paths inside the current directory are displayed relatively, and external paths are displayed absolutely. Skipped scan paths are reported to stderr, and a zero hit scan reports the scanned and skipped file counts.

## Rules

Rules live in `rules.json`. Each entry has an `id`, `category`, Python regular expressions in `patterns`, optional `exclude_patterns` and `extensions`, a short `question`, and a `why` note. Patterns are case-insensitive. Add one rule per concern and add a positive and negative unit test for it in `tests/test_ai_lint.py`.

Current rules:

- `hash-fingerprint`, `provenance-manifest`: hash, fingerprint, provenance, manifest, and ledger checks.
- `mismatch-gate`, `contract-version`, `ensure-guard`: mismatch, contract, and redundant guard gates.
- `new-option`, `feature-flag`: new CLI/environment options and on/off switches.
- `compat-path`, `fallback-default`, `swallow-error`: compatibility paths, silent defaults, and swallowed errors.
- `retry-sleep`, `test-skip`, `lint-suppress`, `placeholder`: retries, skipped tests, lint suppressions, and unfinished placeholders.
- `lock-name`, `state-marker`, `transaction-wrap`, `history-comment`: lock names, state persistence, transaction boundaries, and historical comments.
- `double-write`: mirrored or duplicate writes.
- `attempt-cap`, `missing-tool-skip`, `incident-test`, `exact-match`: attempt limits, successful skips for missing dependencies, incident-specific regression tests, and exact-content gates.

To add a rule, add its `id`, `category`, `patterns`, user-facing `question`, and reason in `rules.json`. Keep patterns focused on the requested concern and add one clear positive and one negative example to `test_each_rule_has_positive_and_negative_example` in `tests/test_ai_lint.py`. Add focused behavior tests when the rule changes path selection or hook behavior. Run `python3 -m unittest discover ai-lint/tests` and inspect scan counts against representative project files to tune overly broad patterns.

## Hook registration

- Claude Code: `.claude/settings.json` registers `bash ~/.claude/lib/ai-lint-hook.sh` for `Edit|Write|MultiEdit`.
- Codex: `etc/sync-codex.sh` generates the `PostToolUse` command `python3 <DOT_DIR>/ai-lint/ai_lint.py --hook codex`.
- Cursor: `etc/sync-cursor.sh` registers `python3 <DOT_DIR>/ai-lint/ai_lint.py --hook cursor` for `postToolUse`; `--check` reports registration drift. It reads `tool_name`, `tool_input.file_path` and edit fields, then returns the advisory as `hookSpecificOutput.additionalContext` ([Cursor Hooks](https://cursor.com/docs/hooks), `postToolUse`).
- OpenCode: `.opencode/plugins/ai-lint.js` handles `tool.execute.after` for `edit`, `write`, and `apply_patch`. It passes tool arguments and the project directory through `bash ~/.claude/lib/ai-lint-hook.sh opencode`; the wrapper resolves the dotfiles checkout and runs `python3 <DOT_DIR>/ai-lint/ai_lint.py --hook opencode`. The official plugin contract passes `{tool, sessionID, callID, args}` and a mutable `{title, output, metadata}` object; hits are appended to `output` ([OpenCode Plugins](https://opencode.ai/docs/plugins/), [plugin hook type](https://github.com/anomalyco/opencode/blob/dev/packages/plugin/src/index.ts), [tool result handling](https://github.com/anomalyco/opencode/blob/dev/packages/opencode/src/session/prompt.ts)).
- Devin CLI: `etc/sync-devin.sh` manages a `PostToolUse` command for `edit`, `write`, and `apply_patch`. The hook reads `tool_name`, `tool_input`, `cwd`, and `tool_response`, then returns `hookSpecificOutput.additionalContext` tagged `PostToolUse` ([Devin lifecycle hooks](https://docs.devin.ai/cli/extensibility/hooks/lifecycle-hooks), [hook output format](https://docs.devin.ai/cli/extensibility/hooks/overview#output-format)). `bash etc/sync-devin.sh --check` detects generated-config drift.

Claude Code, Codex, Cursor, and Devin CLI return `hookSpecificOutput.additionalContext`; OpenCode appends the advisory to the tool result output. Grok Build is not registered because its `PostToolUse` event is passive and ignores stdout ([Grok hooks](https://docs.x.ai/build/features/hooks)). Hooks emit feedback only when there are hits. Analysis errors are written to stderr and exit with status 0.

## Records

Hits are counted without storing source text at `${XDG_STATE_HOME:-~/.local/state}/ai-lint/hits.jsonl`. The directory is mode `0700` and the file is mode `0600`. `AI_LINT_DEBUG=1` enables diagnostic logging to stderr.

## CLI

```sh
python3 ai-lint/ai_lint.py scan path/to/file.py [path/to/other.go]
git diff | python3 ai-lint/ai_lint.py diff
python3 ai-lint/ai_lint.py stats [--days 30]
```

`scan` checks whole files for inventory, `diff` checks only added lines from a unified diff, and `stats` groups recorded rule counts by rule and runtime. All commands exit 0 regardless of hits.
