# AI Workflow Architecture Spec

_Status: Adopted_

## Purpose

This repository supports Claude Code, Codex, OpenCode, Cursor, Grok, and Antigravity workflows without forcing them into identical runtime behavior.

The adopted architecture is **shared core + native overlays**:

- Shared rules and reusable workflow ideas live in common files.
- Runtime-specific behavior lives in that runtime's native files.
- Sync scripts generate only adapter/config files that are mechanically safe to generate.
- Strict byte-for-byte sync between runtimes is not the default.

## Ownership

| Area | Role | Source type |
|---|---|---|
| `AGENTS.md` | Shared runtime-neutral global guidance for supported adapters | Shared core |
| `.agents/skills/**` | Shared skill core | Shared core |
| `mcp-servers.json` | MCP server registry | Shared config |
| `.claude/**` | Claude Code native agents, skills, hooks, settings | Native source |
| `.codex/AGENTS.md` | Codex guidance generated from `AGENTS.md` and `.codex/codex-native-supplement.md` | Generated adapter |
| `.codex/config.toml` | Codex config generated from base config and MCP registry | Generated adapter |
| `.codex/config.base.toml` | Hand-written Codex base config | Native source |
| `.codex/<name>.config.toml` | Hand-written Codex named profile selected explicitly by a launcher | Native source |
| `.codex/codex-native-supplement.md` | Codex commander, planning, and subagent default policy | Native source |
| `.codex/agent-delegation.md` | Codex exploration delegation and integration procedures | Native overlay |
| `.codex/agents/**` | Optional short execution exceptions; built-in agents are the default | Native overlay |
| `.codex/skills/**` | Codex-specific skills and adapted skill snapshots | Native overlay |
| `.codex/skills/worker-delegation/**` | Codex-native task handoff and explicit runner contract | Native overlay |
| `~/.config/opencode/**` | OpenCode config and adapter layer | Adapter/native layer |
| `.cursor/rules/**` | Cursor rules generated from `AGENTS.md` | Generated adapter |
| `.cursor/mcp.json` | Cursor MCP config generated from `mcp-servers.json` | Generated adapter |
| `.cursor/agents/**` | Cursor custom subagents | Native overlay |
| `.cursor/skills/**` | Cursor-specific skills | Native overlay |
| `.grok/rules/**` | Grok-native runtime guidance; linked by `etc/link.sh` | Native overlay |
| `~/.grok/config.toml` | User-owned Grok models, compatibility and runtime settings | Machine-local configuration |
| `.gemini/config/rules/**` | Antigravity rules generated from `AGENTS.md` | Generated adapter |
| `.gemini/config/mcp_config.json` | Antigravity MCP config generated from `mcp-servers.json` | Generated adapter |
| `.gemini/config/hooks.json` | Antigravity lifecycle hooks configuration | Native source |
| `.gemini/config/scripts/**` | Antigravity helper scripts (e.g. auto-gate) | Native source |

## Rules

1. Do not require `.claude/**`, `.agents/**`, `.codex/**`, `.cursor/**`, `.gemini/**`, and OpenCode files to match byte-for-byte.
2. Put cross-runtime intent in `AGENTS.md` or `.agents/skills/**`.
3. Put runtime mechanics in native overlays.
4. Treat `.codex/AGENTS.md` and `.codex/config.toml` as generated files.
5. Treat `.codex/agents/**` and `.codex/skills/**` as Codex-native editable overlays.
6. Do not generate `.claude/**` from Codex, OpenCode, Cursor, or Antigravity sources.
7. When a runtime-specific rule becomes broadly useful, promote the portable part into the shared core and keep only the adapter/runtime details native.
8. Treat `.cursor/rules/**` and `.cursor/mcp.json` as generated files. Treat `.cursor/agents/**` and `.cursor/skills/**` as Cursor-native editable overlays.
9. Cursor shared Rules must be a **summary + pointer to `AGENTS.md`**, not a full copy (avoids double-load with repo `AGENTS.md`).
10. Treat `.gemini/config/rules/**` and `.gemini/config/mcp_config.json` as generated files. Treat `.gemini/config/hooks.json` and `.gemini/config/scripts/**` as Antigravity-native sources.
11. Antigravity shared Rules must be a **summary + pointer to `AGENTS.md`**, not a full copy.
12. Codex named profiles are native runtime overlays. Their source is `.codex/<name>.config.toml`, `etc/link-codex-runtime.sh` owns the corresponding `~/.codex/<name>.config.toml` runtime link, and a dedicated launcher selects the profile with `-p <name>`. Profiles are opt-in; the ordinary generated/default Codex configuration remains unchanged.
13. Keep Codex commander and model selection policy in `.codex/codex-native-supplement.md`, child defaults in `.codex/config.base.toml`, and concrete task handoff and runner contracts in `.codex/skills/worker-delegation/SKILL.md`.

## Work-unit delegation contract

Portable work-unit delegation behavior is owned by `AGENTS.md` under `Subagent Operation`; this architecture records only the ownership boundary between primary/root orchestration and concrete unit execution.
Codex-specific planning and model selection policy is owned by `.codex/codex-native-supplement.md`. Task handoff and the explicit runner contract are owned by `.codex/skills/worker-delegation/SKILL.md`.

## Skill expertise and evaluation

The parent owns scope, planning, model selection, file ownership, integration
and acceptance. A built-in child or generic Task receives the physical path
of the relevant execution Skill/reference together with the target version,
facts, constraints and completion criteria. Shared expertise lives under
`.agents/skills`. Use that shared entry directly when no runtime-specific
execution is needed. Cursor-only model workflows live in `.cursor/skills`;
Codex native packages are limited to actual Codex execution differences,
such as its CLI runner. Do not keep wrappers that only read a shared Skill.
A child does not run the parent's recursive
orchestration workflow.

`pir2` coordinates development. `reviewer` selects coverage, allocates work
and integrates evidence. `code-review-guidance` is the evaluator's source,
with perspective-specific references and a shared `result-contract.md`.
Review callers and consumers use that contract: coverage is
`complete|partial|none`; verdict is `PASS|FAIL|INCOMPLETE|NOT_APPLICABLE`.
Severity and completion blocking are separate. Required P2 fixes, unread
references, timeouts and missing perspectives cannot become PASS merely
because no P0/P1 was reported. Out-of-scope findings retain their severity.

Choose required perspectives separately from reviewer count. Explicitly
independent perspectives use separate fresh contexts, in waves if necessary.
One evaluator may otherwise cover multiple specified perspectives. The
parent verifies each finding against the same target state and reruns only
the checks affected by a later change. Format or a child's PASS alone is not
acceptance.

Readers return findings to the parent without writing reports or memory.
Tests, reproductions and builds with generated output are writer work.
Non-modification instructions and enforced permissions are distinct; names
and unsupported configuration keys do not establish isolation. Preserve
required isolation and explicit external CLI bridges.

Short tasks need no private run directory or duplicate plan/report/queue.
Long tasks, explicit records and resumption use the existing state storage;
the parent records current decisions, unfinished work and actual verification
there. Resume from those facts rather than repeating completed steps. Record
only established learning; a successful task does not require a rule change.

`agent-skill-migrate` is an explicit audit/apply entry. It uses existing
designs and audit findings instead of repeating a completed whole-system
audit. Its Codex invocation policy and Cursor frontmatter disable implicit
invocation. It changes only the requested roots and runtimes, then checks the
affected source, callers, result consumers, seed, generation and deployment.
It creates no permanent audit database, routing layer or ledger.

`deepthink` and its expert references live only in `.cursor/skills/deepthink`.
Shared and Codex skill trees do not expose that entry. Codex `deepplan` uses
parent-owned planning without invoking it. Cursor uses the Fable 5.1 model
reference in that native package for `deepthink` and `deepplan`.

## sync-codex.sh Contract

Default `bash etc/sync-codex.sh` does:

- Generate `.codex/config.toml`.
- Generate `.codex/AGENTS.md` by concatenating the shared `AGENTS.md` and the
  Codex-native `.codex/codex-native-supplement.md`.
- Generate Codex support documents such as `.codex/format.md`, `.codex/pir-handoff.md`, and related protocol docs. UI/UX expertise is read from the shared evaluation Skill rather than a separate home copy.

`.codex/pir-handoff.md` is generated from the Codex-native
`.codex/skills/pir2/references/handoff-protocol.md`: parent-owned updates,
private run paths and recoverable completion storage differ from other runtimes.
`.codex/pir2-protocol.md` is generated from the native sibling `protocol.md`,
so regeneration preserves native delegation, risk-based review and real artifacts.

Both instruction inputs are required for the generated `.codex/AGENTS.md`;
missing inputs are reported by the script's existing precondition warning and
the sync exits before generating a partial instruction file. Re-running with
the same inputs is deterministic.

Required-input, generation, validation, and publication failures exit nonzero.
`etc/link.sh` propagates a runtime sync or link failure and stops that
deployment before treating later runtime work as complete. Adapter branches
that preserve a hand-written generated target with a warning are explicit
exceptions in the corresponding script; they do not turn other failures into
success.

Default `bash etc/sync-codex.sh` does **not**:

- Regenerate `.codex/agents/*.toml` from `.claude/agents/*.md`.
- Regenerate `.codex/skills/**` from `.agents/skills/**`.
- Regenerate `.codex/agent-delegation.md` from Claude-specific exploration rules.

The default sync therefore preserves Codex-native sources and overlays,
including `.codex/codex-native-supplement.md` and
`.codex/skills/worker-delegation/**`. The worker package is not a shared-skill
seed and Codex actor/model routing is not copied into `AGENTS.md` or
`.agents/**`.

Native Agent/Skill sources are not regenerated from another runtime's
specialist bodies. Missing required native sources are reported; shared
expertise is consumed through the selected Skill's references.

## Codex execution and delegation

The ordinary parent is Astra (`gpt-6-astra`, medium). It owns requirements,
architecture, bounded work allocation, integration, and final acceptance.
Small changes and work tightly coupled to evolving system context can be
implemented directly by Astra. Deterministic operations use existing scripts.

Use built-in `default`, `worker` or `explorer` as appropriate. The ordinary
child defaults come from `[agents]` in `.codex/config.base.toml`; difficult
work uses explicit model/effort arguments under the native supplement's
selection policy. Specialist knowledge is supplied as Skill references,
not as a custom role for each profession or model.

The initial child concurrency value is defined by the active Codex
configuration's `max_concurrent_threads_per_session`; it is a baseline, not a
universal or mandatory worker count. Before each wave, inspect live open
threads and available capacity and use the lower effective limit. Each writer
owns distinct files; shared interface decisions precede dependent
implementation. A completed child does not by itself prove that a slot was
released, so reuse an actually available thread with `followup_task` when
exposed and do not invent a close/release API. A custom Agent is justified
only by an execution condition unavailable through the standard interface.
Its fixed model/effort can override spawn defaults; dynamic selection must
not be claimed while such an override remains.

Terra is outside standard routing. A workload-specific exception requires
observed benefit. Sol can be selected initially or after a reasoning failure;
neither a failed Luna attempt nor a Terra attempt is a prerequisite. Missing
inputs, permission errors, and environment failures are diagnosed as such,
not treated as evidence that a stronger model will fix them.

Native collaboration is the normal execution mechanism. Jobs requiring an
explicit CLI invocation and saved execution artifacts may use
`.codex/skills/worker-delegation/scripts/run-worker.sh`. Its supported inputs,
security boundaries, evidence format, and limitations are owned by
`.codex/skills/worker-delegation/SKILL.md` and its references. Shared
`.agents/**` instructions do not acquire Codex model pins or runner mechanics.

Astra verifies actual diffs and relevant command results against the task.
Independent reviews focus on correctness, security, behavior regressions, and
data loss; meaningful tests target the changed behavior. A worker report or
runner exit alone does not establish acceptance. Run the runner's own fixture
tests when changing the runner, not after every unrelated implementation job.
Repeat checks only for integration changes or unresolved risks. Fixes return
to the affected work unit rather than restarting unrelated completed work.

User authorization carries through execution. Workflow skills resolve routine
choices from evidence and ask only for blocking decisions or actions beyond
that authorization. Actual security and release boundaries remain in force.
`AGENTS.md` under `Execution And Skill Priority` owns the portable rules for
preparing a reviewable result before approval, user directions over optional
skill advice, and reporting the exact skill rule or observed environment
constraint behind a pause. Reports distinguish explicit rules from agent
interpretation and omit secrets, private higher-priority instructions, and
internal reasoning. Claude adapts these rules in its native `CLAUDE.md`;
Cursor and Grok carry the portable intent through their native guidance.

### Official documentation and API scope

Use the available official `openai-docs` skill for OpenAI model and API
specifications. If unavailable, consult official documentation directly;
neither a duplicate local skill nor additional account access is required.
A Codex configuration task does not authorize migrating application code.
Inspect API wrappers and automation within the requested development scope,
and record unrelated application compatibility findings separately.

Codex subagents select models using spawn/config precedence, subject to any
custom-definition overrides. Responses API Multi-agent shares the request's model and tools
with its children; enabling it does not implement the Astra/Luna/Sol routing.
Separate API requests require application-owned routing and result handling.
API concurrency limits and Codex thread limits are independent.

For an in-scope wrapper that actually calls Astra, check the emitted request,
including SDK/proxy defaults: tool calling requires Responses, unsupported
sampling/logprob parameters must be removed for Astra only, and `none` or
`minimal` effort needs a supported value. Preserve other workloads' effective
effort. Check cache options and input/read/write/output usage separately.
Async tools, steering, `configuration_update`, and Programmatic Tool Calling
are optional API mechanisms, not Codex configuration keys. Adopt them only
for an existing use or explicit requirement, with their documented ownership,
cancellation, mode, and compaction constraints. No direct API integration
means these implementation changes are not applicable.

Sources: [Astra guide](https://developers.openai.com/api/docs/guides/latest-model),
[Multi-agent](https://developers.openai.com/api/docs/guides/responses-multi-agent),
and [Prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching).

### Operational measurement

Use existing task reports and runtime logs to record task type, actual model
and effort, reassignment reason, elapsed time, checks, rework, and available
usage. Compare Astra direct work with Luna/Sol delegation under the same
acceptance criteria, including parent preparation, review, and retries.
Report unavailable usage as unavailable, never zero or estimated savings.
For direct API integrations, distinguish ordinary input, `cached_tokens`,
`cache_write_tokens`, output, and retries; do not map API cache pricing to
Codex subscription usage. Existing runner artifacts remain runner-specific;
native collaboration and direct work need no new ledger or completion gate.

Configuration ownership is `.codex/config.base.toml` plus
`etc/sync-codex.sh`; regenerate with `bash etc/sync-codex.sh`.
User runtime configuration and agents are linked by `etc/link-codex-runtime.sh`.
Profiles use `.codex/<name>.config.toml` and explicit `--profile <name>`.
Machine-specific project trust and existing hook trust must survive generation.
For supported personal ChatGPT accounts, experimental context management uses
`features.context_management.experimental_mode`; it is separate from Memories.
Local long-running work enables `features.prevent_idle_sleep`.
New sessions are required to verify changed configuration and custom agents.

## Review Policy

Reviewers should classify files before judging drift:

- Generated adapters: `.codex/AGENTS.md`, `.codex/config.toml`, OpenCode generated config/docs, `.cursor/rules/**`, `.cursor/mcp.json`, `.gemini/config/rules/**`, `.gemini/config/mcp_config.json`.
- Shared core: `AGENTS.md`, `.agents/skills/**`, `mcp-servers.json`.
- Native sources and overlays: `.claude/**`, `.codex/codex-native-supplement.md`, `.codex/agents/**`, `.codex/skills/**`, `.cursor/agents/**`, `.cursor/skills/**`, `.gemini/config/hooks.json`, `.gemini/config/scripts/**`.

Valid findings:

- A generated adapter changed without a corresponding source/script change.
- A broadly reusable rule is trapped in only one native overlay.
- A runtime-specific mechanism is written into shared core when it should stay native.
- A native overlay claims generated ownership or has stale generated markers.
- Cursor Rules contain a full copy of `AGENTS.md` (should be summary + pointer only).
- Antigravity Rules contain a full copy of `AGENTS.md` (should be summary + pointer only).

Invalid findings:

- `.claude/**` and `.codex/**` / `.cursor/**` differ merely because the runtimes operate differently.
- `.codex/agents/**` or `.codex/skills/**` or `.cursor/agents/**` or `.cursor/skills/**` do not match shared sources byte-for-byte.

## sync-opencode.sh Contract

Default `bash etc/sync-opencode.sh` does:

- Generate `~/.config/opencode/opencode.json` from `mcp-servers.json` (excluding `claudeCodeOnly` and `codexOnly`; `openCodeOnly` servers are included), an OpenCode-specific permission policy owned by the script (bash allow-by-default with dangerous-command asks, edit allow, read deny list inherited from `.claude/settings.json#permissions.deny`, and `external_directory: {"~/**": "allow"}` because OpenCode defaults it to ask and "always" approvals are session-scoped, which caused approval fatigue for any out-of-cwd reference; the Claude Code allow allowlist is intentionally not carried over), and `lsp: true` (OpenCode disables LSP when the key is omitted).
- Sync OpenCode plugins from the repo-native SSOT `.opencode/plugins/*` to `~/.config/opencode/plugins/` with a provenance header. OpenCode has no settings.json-style hooks; PreToolUse / PostToolUse / Stop equivalents are implemented as plugins (`tool.execute.before`, `tool.execute.after`, `session.idle`). Orphan cleanup and hand-written-file protection follow the same rules as agents.
- Generate `~/.config/opencode/AGENTS.md`: full copy of shared `AGENTS.md` plus an OpenCode-specific supplement owned by the script itself (tool-name remap table, skill availability classification, compatibility gaps, model alias mapping notes).
- Convert `.claude/agents/*.md` to `~/.config/opencode/agents/<name>.md`: frontmatter reduced to `description` / `mode: subagent` / `model` (bare aliases mapped by `map_model_name`: `sonnet`→`anthropic/claude-sonnet-5`, `opus`→`anthropic/claude-opus-4-8`, `fable`→`anthropic/claude-fable-5-1`); body copied verbatim. Orphan AUTO-GENERATED agents are removed.
- Support `bash etc/sync-opencode.sh --check` (no write; exit non-zero if generated outputs would change or an orphan agent would be removed).

Default `bash etc/sync-opencode.sh` does **not**:

- Convert agent-frontmatter `tools:` restrictions or per-agent permissions. Bodies claiming tools-based role isolation are not enforced by the runtime; the generated AGENTS.md supplement states this explicitly.
- Create repo-side native overlays (`.opencode/**`). OpenCode stays fully generated under `~/.config/opencode/**`; a native overlay remains deferred until runtime needs diverge.

Contract test: `bash etc/test-opencode-contracts.sh` (live `--check`, fake-HOME fresh sync + idempotency, MCP/permission shape, agent frontmatter + verbatim-body contract, supplement sections, stale-reference regression, orphan cleanup + hand-written protection). It is included in the `etc/test-all-contracts.sh` aggregate runner.

Skills are not registered via an `opencode.json#skills` key. Discovery relies on OpenCode's external-skill autoload of `~/.agents/skills/**` and `~/.claude/skills/**`, backed by the `~/.agents` symlink created by `etc/link.sh`.

## sync-cursor.sh Contract

Desktop global guidance is registered through Cursor Settings → Customize → Rules → User. The User Rule instructs each session to read the actual dotfiles checkout's `AGENTS.md`, `~/.cursor/rules/shared-agents.mdc`, and applicable project `AGENTS.md` files, with `~/.cursor/skills` preferred for Cursor skills. `link.sh` deploys the referenced adapter file; neither linking nor `sync-cursor.sh --check` verifies registration in Cursor's User Rules. Verify the saved User Rule in Cursor's UI after initial setup.

Default `bash etc/sync-cursor.sh` does:

- Generate `.cursor/rules/shared-agents.mdc` as a **summary + SSOT pointer** to `AGENTS.md` (not a full copy).
- Keep Cursor's Task and agent model policy in the generated summary, owned by
  `etc/sync-cursor.sh`; Cursor generation does not read the Codex-native
  `.codex/codex-native-supplement.md`.
- Generate `.cursor/mcp.json` from `mcp-servers.json` (excluding `claudeCodeOnly`, `openCodeOnly`, and `codexOnly` servers). Convert `type: "remote"` entries to url-only objects for Cursor compatibility.
- Support `bash etc/sync-cursor.sh --check` (no write; exit non-zero if generated outputs would change).

Default `bash etc/sync-cursor.sh` does **not**:

- Regenerate `.cursor/agents/**` from `.claude/agents/**`.
- Regenerate `.cursor/skills/**` from `.agents/skills/**`.
- Overwrite existing native overlays (no force-seed path).

One-time seed is available as an explicit operation:

```bash
SYNC_CURSOR_SEED=1 bash etc/sync-cursor.sh
# or
bash etc/seed-cursor-overlay.sh
```

Seed operates on the current native sources and never requires a fixed
profession-role inventory or recreates specialist bodies from another
runtime. Existing native files are preserved. The existing contract tests
exercise generation, filtering, non-destructive distribution and valid
minimal Agent configurations in isolated fixtures.

### Cursor skill / agent precedence

When both `.agents/skills/<name>` and `.cursor/skills/<name>` exist:

1. **Cursor runtime** uses `.cursor/skills/<name>` via a **real-directory materialize** into `~/.cursor/skills/<name>` (`link.sh`). Symlinks are intentionally avoided: Cursor does not discover symlinked personal skills under `~/.cursor/skills/` (upstream bug; forum #149693).
2. **`.agents/skills`** remains shared core for Codex/OpenCode and for seed/promote. Do not treat it as the live Cursor skill path.
3. Native invocation references resolve from the loaded Skill. Shared expertise resolves to an existing shared Skill source or a parent-supplied physical path, independent of the target repo. Edit the owning source, then use the existing link script to refresh the home copy.
4. Cursor also discovers `.claude/agents` and `.codex/agents`; `.cursor` wins for the same name. Short native adapters preserve the intended shared expertise and required `readonly` behavior where a same-name compatibility definition would otherwise be selected. Agent frontmatter may omit `model` or use `inherit`; a custom `role` field is not mandatory. Do not infer global MCP isolation from `readonly` alone.
5. **Slash-menu names**: Cursor overlay directory and frontmatter `name` share the bare skill basename (e.g. folder `.cursor/skills/epic/`, slash `/epic`). Cursor requires `name` to match the parent folder. `.cursor/skills` precedence makes a `cursor-` prefix unnecessary. Maintain with `etc/normalize-cursor-skill-names.sh` (invoked from `seed-cursor-overlay.sh` on new seeds).

`etc/link.sh` links `.cursor/{agents,rules,mcp.json}` as symlinks (refuses to replace non-symlink destinations) and **materializes** `.cursor/skills/*` as real directories under `~/.cursor/skills/`. Never touch `~/.cursor/skills-cursor/`.

### Cursor Codex bridge

Cursor Task retains its own inherited model. `/codex` and `/pir2codex` use an
explicit Codex CLI bridge, not Codex-native collaboration inside Cursor. CLI
jobs select Luna max for bounded ordinary work, Sol high/max for difficult
work, and Terra only with workload evidence. The bridge retains private run
artifacts, completion monitoring and session boundary checks. Review/test
scope follows actual risk rather than a fixed number of agents.

## Grok runtime boundary

Grok uses shared project guidance and its own `.grok/rules/runtime.md`.
`etc/link.sh` links individual native rules into `~/.grok/rules` without
replacing real user files or unrelated links. It does not generate Grok
credentials, model settings, permission policy, MCP or hooks.

Grok can discover shared `.agents/skills` and vendor-compatible Cursor/Claude
skills. Compatibility discovery does not make their tool names, model IDs or
agent roles native Grok interfaces. The Grok rule preserves portable intent
while requiring the actual Grok tool schema for execution. Existing Grok
models and compatibility settings remain user-owned; the Codex model ladder
and Cursor Fable exception do not apply to Grok.

`grok inspect --json` checks discovery without starting a model task. Inspect
output can include sensitive configuration; expose only needed path/name and
compatibility fields. Foreign-session resume is explicit and does not confer
authority from historical instructions.

## Review Policy (Cursor)

Classify before judging drift:

- Generated adapters: `.cursor/rules/**`, `.cursor/mcp.json`
- Native overlays: `.cursor/agents/**`, `.cursor/skills/**`
- Shared core: `AGENTS.md`, `.agents/skills/**`, `mcp-servers.json`

## Skill/plugin updates

The shared, Claude, and Cursor `check-updates` packages operate only on explicitly
selected skill/plugin roots. They update independent clones through their
configured upstream with clean fast-forwards, preserve dirty/divergent/ahead
states, and report failures with a nonzero status. They do not implicitly
synchronize dotfiles or its submodules, create commits, regenerate adapters,
or push. Explicit dotfiles synchronization belongs to `etc/dotfiles-autosync.sh`.

Claude SessionStart does not run `check-updates` without selected roots.
Claude's PostToolUse Codex/OpenCode sync hooks report producer success or failure
as `hookSpecificOutput.additionalContext` while remaining non-blocking.

## sync-antigravity.sh Contract

Default `bash etc/sync-antigravity.sh` does:

- Generate `.gemini/config/rules/shared-agents.md` as a **summary + SSOT pointer** to `AGENTS.md` (not a full copy).
- Generate `.gemini/config/mcp_config.json` from `mcp-servers.json` (excluding `claudeCodeOnly`, `openCodeOnly`, `codexOnly`, and `cursorOnly` servers).
- Warn if the native `.gemini/config/hooks.json` or `.gemini/config/scripts/auto-gate.py` is missing; request executable permissions for the script during generation. This adapter does not validate the native hook schema. `etc/test-auto-gate.py` verifies the configured command and gate behavior.
- Ensure `.gemini/config/skills` symlink points to `.agents/skills`.
- Support `bash etc/sync-antigravity.sh --check` (no write; exit non-zero if generated outputs would change).

`etc/link.sh` deploys Antigravity configuration to `~/.gemini/config/` and symlinks `~/.agents/skills` to ensure all shared skills are discovered.
If Antigravity sync or any required link operation fails, `etc/link.sh` exits
nonzero and does not report the deployment as complete.

## Review Policy (Antigravity)

Classify before judging drift:

- Generated adapters: `.gemini/config/rules/**`, `.gemini/config/mcp_config.json`
- Native sources/overlays: `.gemini/config/hooks.json`, `.gemini/config/scripts/**`
- Shared core: `AGENTS.md`, `.agents/skills/**`, `mcp-servers.json`

## Seed and distribution

Native sources are maintained in Git. Seed and sync must not reconstruct
removed Codex profession/model presets or enforce a matching Claude/Agent
inventory. Shared execution Skills may be used without an equal number of
native Skill copies or Agent definitions. A missing required native source
is reported rather than synthesized from an unrelated runtime's body.

`etc/check-shared-drift.sh` and `etc/audit-skill-agent-layout.py` check the
applicable source and distribution rules. They do not use Agent count,
fixed role names, or verbatim expert prose as success conditions.
`etc/link-codex-runtime.sh` owns Codex home links; `etc/link.sh` owns Cursor
materialization. Real user files, credentials and unrelated plugins are
preserved. New shared specialist references must remain reachable through
both the source checkout and deployed entrypoints.

`bash etc/link.sh --codex-cursor-only` generates and deploys those two
runtimes and their shared Skill entry without deploying other runtimes.
It reuses the existing backup, link and materialization operations.

OpenCode retains its generated adapters and native source boundary; this
Codex/Cursor design does not require rewriting Claude/OpenCode workflows.

Public runtime references: [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents),
[Cursor subagents](https://cursor.com/docs/subagents), and
[Cursor skills](https://cursor.com/docs/skills). Configuration, discovery and
actual execution are verified separately; unsupported or unavailable runtime
checks are reported as unverified.
