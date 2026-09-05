# AI Workflow Architecture Spec

_Status: Adopted_
_Last updated: 2026-08-13_

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
| `.codex/agents/**` | Codex custom agents | Native overlay |
| `.codex/skills/**` | Codex-specific skills and adapted skill snapshots | Native overlay |
| `.codex/skills/worker-delegation/**` | Codex-native actor/effort ladder, promotion policy, and runner/execution contract | Native overlay |
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
13. Keep Codex-specific commander, planning, and subagent default policy in `.codex/codex-native-supplement.md`; keep the actor/effort ladder, promotion policy, and runner/execution contract in `.codex/skills/worker-delegation/SKILL.md`.

## Work-unit delegation contract

Portable work-unit delegation behavior is owned by `AGENTS.md` under `Subagent Operation`; this architecture records only the ownership boundary between primary/root orchestration and concrete unit execution.
Codex-specific commander, planning, and subagent default policy is owned by `.codex/codex-native-supplement.md`. The actor/effort ladder, promotion policy, and runner/execution contract are owned by `.codex/skills/worker-delegation/SKILL.md`.

## sync-codex.sh Contract

Default `bash etc/sync-codex.sh` does:

- Generate `.codex/config.toml`.
- Generate `.codex/AGENTS.md` by concatenating the shared `AGENTS.md` and the
  Codex-native `.codex/codex-native-supplement.md`.
- Generate Codex-readable copies of shared support documents such as `.codex/format.md`, `.codex/pir-handoff.md`, `.codex/ui-ux-principles.md`, and related protocol docs.

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

Legacy mirror regeneration is available only as an explicit operation:

```bash
SYNC_CODEX_LEGACY_MIRROR=1 bash etc/sync-codex.sh
```

Use the legacy mode only when intentionally refreshing old mirror snapshots. It is not the normal maintenance path.

## Codex execution and delegation

The ordinary parent is Astra (`gpt-6-astra`, high). It owns requirements,
architecture, bounded work allocation, integration, and final acceptance.
Small changes and work tightly coupled to evolving system context can be
implemented directly by Astra. Deterministic operations use existing scripts.

| Work | Role | Model / effort |
|---|---|---|
| Well-scoped implementation and tests | worker | gpt-5.6-luna / max |
| Difficult independent investigation or implementation | expert | gpt-5.6-sol / high |
| Particularly difficult reasoning with a stated justification | expert_max | gpt-5.6-sol / max |

The initial child concurrency value is defined by the active Codex
configuration's `max_concurrent_threads_per_session`; it is a baseline, not a
universal or mandatory worker count. Before each wave, inspect live open
threads and available capacity and use the lower effective limit. Each writer
owns distinct files; shared interface decisions precede dependent
implementation. A completed child does not by itself prove that a slot was
released, so reuse an actually available thread with `followup_task` when
exposed and do not invent a close/release API. Specialist agents are retained
when their tools, domain procedures, or review criteria are useful. Their
custom TOML model and effort take precedence over spawn defaults.

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

Phase-3 seed set (default in `etc/seed-cursor-overlay.sh`):

- Agents: phase-2 set plus `codex-runner` (Codex CLI bridge).
- Skills: phase-2 set plus `pir2codex`, `ai-design-system`, `ai-diary`, `ai-ltm`, `unity-mcp-skill`, `codex`.
- Contract test: `bash etc/test-cursor-contracts.sh` (sync `--check`, MCP filter, seed non-destructive, link refuse non-symlink, phase-3 inventory).

Use seed mode only when intentionally creating missing overlays. It is not the normal maintenance path. Existing overlays are never overwritten. `seed-cursor-overlay.sh` ends with an overlay hygiene check (blocks known-bad residues: broken `dotfiles .claude reference:`, `~/.claude/projects`, vendor model pins, Agent-as-launcher wording).

### Cursor skill / agent precedence

When both `.agents/skills/<name>` and `.cursor/skills/<name>` exist:

1. **Cursor runtime** uses `.cursor/skills/<name>` via a **real-directory materialize** into `~/.cursor/skills/<name>` (`link.sh`). Symlinks are intentionally avoided: Cursor does not discover symlinked personal skills under `~/.cursor/skills/` (upstream bug; forum #149693).
2. **`.agents/skills`** remains shared core for Codex/OpenCode and for seed/promote. Do not treat it as the live Cursor skill path.
3. Overlay `SKILL.md` / references must point at `.cursor/skills/...` paths. Cross-runtime shared rules belong in `AGENTS.md` or `.agents/skills` and are promoted intentionally. Edit SSOT in `dotfiles/.cursor/skills`, then re-run `link.sh` to refresh `~/.cursor/skills`.
4. Global Claude protocol files that remain valid via `link.sh` (e.g. `~/.claude/pir-handoff.md`) may be referenced by absolute home path; do not invent non-path “reference:” placeholders.
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

The shared, Codex, and Cursor `check-updates` packages operate only on explicitly
selected skill/plugin roots. They update independent clones through their
configured upstream with clean fast-forwards, preserve dirty/divergent/ahead
states, and report failures with a nonzero status. They do not implicitly
synchronize dotfiles or its submodules, create commits, regenerate adapters,
or push. Explicit dotfiles synchronization belongs to `etc/dotfiles-autosync.sh`.

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

## Migration State

Completed:

- `sync-codex.sh` no longer rewrites `.codex/agents/**` or `.codex/skills/**` by default.
- `.codex/agents/*.toml` were adopted as Codex-native overlays from the legacy sync snapshot.
- `.codex/skills/*/.codex-generated-from-shared` markers were removed.
- `AGENTS.md` and `AGENTS.override.md` now document the shared-core/native-overlay policy.
- Cursor design adopted: `docs/brainstorm/2026-07-13-cursor-port.md` (Rules=A, native overlays, phase-1 slice).
- `sync-cursor.sh` generates summary Rules + MCP; seed/force paths tightened; phase-1 overlays reduced to explorer/implementer/reviewer + chat.
- Cursor phase 2 (2026-07-13): `seed-cursor-overlay.sh` expanded agents/skills; orchestration overlays (`pir2`, `deepthink`, `epic`, `research`, `pir2async`, `ir`, `debug`, `writing-plan`, `brainstorm`) seeded with Cursor Task/VERDICT notes; Claude-only TeamCreate/hooks skipped; no model pins (role=reasoning|coding only). `deepthink` / `research` / `epic` seed from `.claude/skills` when absent in `.agents/skills`.
- Cursor review FAIL remediations (2026-07-13): removed repo `.codex-runtime/` (auth stays in `~/.codex`); fixed seed path rewrite; Agent→Task / vendor model sweep; epic `PROJECT_MEMORY_DIR` + `.cursor/skills/pir2` refs; hygiene guard; documented skill precedence; partial `/pir2` Task smoke recorded in `docs/plans/2026-07-13-cursor-port.md`.
- Cursor skill naming (2026-08-19): dropped `cursor-` prefix from `.cursor/skills/<name>` / `/<name>` because `.cursor/skills` takes precedence over `.claude` / `.agents`; updated seed/normalize/contracts accordingly.
- Cursor Task model (2026-08-19 / 2026-08-27): Task `model` is omit/`inherit` only (parent Auto). Do not pin vendor slugs or `model=reasoning` as a Task launch arg. Agent overlay `model` is `inherit` or a real model ID; `role: coding|reasoning` is the job class. External-File Protection: add sibling folders via a `.code-workspace` (File → Open Workspace from File), not by opening the JSON as an editor tab.
- Cursor phase 3 (2026-07-15): seeded missing overlays (`ai-design-system`, `ai-diary`, `ai-ltm`, `unity-mcp-skill`, `codex`, `pir2codex`, `codex-runner`); promoted `deepthink` / `research` / `epic` into `.agents/skills`; shared `/codex` SSOT switched to CLI + `codex-runner` (MCP path removed); fixed GNU sed brace bug in seed adapt; epic Cursor overlay reseeded; added `etc/test-cursor-contracts.sh`.

- Remaining follow-up (2026-07-15): `etc/seed-codex-overlay.sh` (agents×6 + skills×4); `etc/check-shared-drift.sh`; OpenCode stays generated; Codex skills stay full snapshots; implement smoke in `docs/plans/2026-07-15-remaining-followup.md`.

Open items:

- None blocking. Optional: longer-running full `/pir2` on an unrelated product repo for soak testing.
- OpenCode: **keep generated agents** from `.claude/agents` via `sync-opencode.sh` (native overlay deferred until runtime needs diverge).
- Codex skills: **keep full skill snapshots** as native overlays; grow with `seed-codex-overlay.sh` (missing-only). Do not re-enable default `SYNC_CODEX_LEGACY_MIRROR`. The `epic` skill is a tracked Codex-native-only overlay and is intentionally excluded from seeding; if that tracked overlay is missing, seeding fails nonzero instead of converting the generic shared/Claude source.
- Drift: **`etc/check-shared-drift.sh`** detects shared skills/agents trapped in one runtime (skill allowlist: `pir2codex`, `design-review`, `overlay-audit`; Codex-agent allowlist: `codex-runner`). `overlay-audit` has a Cursor overlay so `/overlay-audit` is discovered via `~/.cursor/skills`; Codex keeps reading `.agents/skills`. `design-review` is allowlisted because its canonical body is the external design repo SSOT; dotfiles provide only Claude/Codex discovery bootstrap and do not copy the body into Cursor overlay/shared core.

### Codex seed contract

```bash
bash etc/seed-codex-overlay.sh
bash etc/check-shared-drift.sh
```

- Agents seeded: `deliberator`, `epic-planner`, `gate`, `hypothesizer`, `synthesizer`, `thinker` (`codex-runner` omitted).
- Skills seeded from `.agents/skills`: `deepthink`, `research`, `unity-mcp-skill` (`epic` is intentionally excluded because its Codex-native orchestration contract must not be synthesized from the generic source).
- Native-only `epic` contract: `.codex/skills/epic/**` is source-controlled; if the tracked overlay is missing, `seed-codex-overlay.sh` exits nonzero and never treats the generic source as a recovery path.
- Existing overlays are never overwritten.
