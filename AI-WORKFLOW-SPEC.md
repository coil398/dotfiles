# AI Workflow Architecture Spec

_Status: Adopted_
_Last updated: 2026-07-13_

## Purpose

This repository supports Claude Code, Codex, OpenCode, and Cursor workflows without forcing them into identical runtime behavior.

The adopted architecture is **shared core + native overlays**:

- Shared rules and reusable workflow ideas live in common files.
- Runtime-specific behavior lives in that runtime's native files.
- Sync scripts generate only adapter/config files that are mechanically safe to generate.
- Strict byte-for-byte sync between runtimes is not the default.

## Ownership

| Area | Role | Source type |
|---|---|---|
| `AGENTS.md` | Shared global guidance for Codex/OpenCode adapters | Shared core |
| `.agents/skills/**` | Shared skill core | Shared core |
| `mcp-servers.json` | MCP server registry | Shared config |
| `.claude/**` | Claude Code native agents, skills, hooks, settings | Native source |
| `.codex/AGENTS.md` | Codex guidance generated from `AGENTS.md` | Generated adapter |
| `.codex/config.toml` | Codex config generated from base config and MCP registry | Generated adapter |
| `.codex/config.base.toml` | Hand-written Codex base config | Native source |
| `.codex/agents/**` | Codex custom agents | Native overlay |
| `.codex/skills/**` | Codex-specific skills and adapted skill snapshots | Native overlay |
| `~/.config/opencode/**` | OpenCode config and adapter layer | Adapter/native layer |
| `.cursor/rules/**` | Cursor rules generated from `AGENTS.md` | Generated adapter |
| `.cursor/mcp.json` | Cursor MCP config generated from `mcp-servers.json` | Generated adapter |
| `.cursor/agents/**` | Cursor custom subagents | Native overlay |
| `.cursor/skills/**` | Cursor-specific skills | Native overlay |

## Rules

1. Do not require `.claude/**`, `.agents/**`, `.codex/**`, `.cursor/**`, and OpenCode files to match byte-for-byte.
2. Put cross-runtime intent in `AGENTS.md` or `.agents/skills/**`.
3. Put runtime mechanics in native overlays.
4. Treat `.codex/AGENTS.md` and `.codex/config.toml` as generated files.
5. Treat `.codex/agents/**` and `.codex/skills/**` as Codex-native editable overlays.
6. Do not generate `.claude/**` from Codex, OpenCode, or Cursor sources.
7. When a runtime-specific rule becomes broadly useful, promote the portable part into the shared core and keep only the adapter/runtime details native.
8. Treat `.cursor/rules/**` and `.cursor/mcp.json` as generated files. Treat `.cursor/agents/**` and `.cursor/skills/**` as Cursor-native editable overlays.
9. Cursor shared Rules must be a **summary + pointer to `AGENTS.md`**, not a full copy (avoids double-load with repo `AGENTS.md`).

## sync-codex.sh Contract

Default `bash etc/sync-codex.sh` does:

- Generate `.codex/config.toml`.
- Generate `.codex/AGENTS.md`.
- Generate Codex-readable copies of shared support documents such as `.codex/format.md`, `.codex/pir-handoff.md`, and related protocol docs.

Default `bash etc/sync-codex.sh` does **not**:

- Regenerate `.codex/agents/*.toml` from `.claude/agents/*.md`.
- Regenerate `.codex/skills/**` from `.agents/skills/**`.

Legacy mirror regeneration is available only as an explicit operation:

```bash
SYNC_CODEX_LEGACY_MIRROR=1 bash etc/sync-codex.sh
```

Use the legacy mode only when intentionally refreshing old mirror snapshots. It is not the normal maintenance path.

## Review Policy

Reviewers should classify files before judging drift:

- Generated adapters: `.codex/AGENTS.md`, `.codex/config.toml`, OpenCode generated config/docs, `.cursor/rules/**`, `.cursor/mcp.json`.
- Shared core: `AGENTS.md`, `.agents/skills/**`, `mcp-servers.json`.
- Native overlays: `.claude/**`, `.codex/agents/**`, `.codex/skills/**`, `.cursor/agents/**`, `.cursor/skills/**`.

Valid findings:

- A generated adapter changed without a corresponding source/script change.
- A broadly reusable rule is trapped in only one native overlay.
- A runtime-specific mechanism is written into shared core when it should stay native.
- A native overlay claims generated ownership or has stale generated markers.
- Cursor Rules contain a full copy of `AGENTS.md` (should be summary + pointer only).

Invalid findings:

- `.claude/**` and `.codex/**` / `.cursor/**` differ merely because the runtimes operate differently.
- `.codex/agents/**` or `.codex/skills/**` or `.cursor/agents/**` or `.cursor/skills/**` do not match shared sources byte-for-byte.

## sync-cursor.sh Contract

Default `bash etc/sync-cursor.sh` does:

- Generate `.cursor/rules/shared-agents.mdc` as a **summary + SSOT pointer** to `AGENTS.md` (not a full copy).
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
5. **Slash-menu names**: Cursor overlay directory and frontmatter `name` are both `cursor-<source>` (e.g. folder `.cursor/skills/cursor-epic/`, slash `/cursor-epic`). Cursor requires `name` to match the parent folder; the prefix also avoids collision with Claude-compat `~/.claude/skills`. Maintain with `etc/normalize-cursor-skill-names.sh` (invoked from `seed-cursor-overlay.sh` on new seeds).

`etc/link.sh` links `.cursor/{agents,rules,mcp.json}` as symlinks (refuses to replace non-symlink destinations) and **materializes** `.cursor/skills/*` as real directories under `~/.cursor/skills/`. Never touch `~/.cursor/skills-cursor/`.

## Review Policy (Cursor)

Classify before judging drift:

- Generated adapters: `.cursor/rules/**`, `.cursor/mcp.json`
- Native overlays: `.cursor/agents/**`, `.cursor/skills/**`
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
- Cursor phase 3 (2026-07-15): seeded missing overlays (`ai-design-system`, `ai-diary`, `ai-ltm`, `unity-mcp-skill`, `codex`, `pir2codex`, `codex-runner`); promoted `deepthink` / `research` / `epic` into `.agents/skills`; shared `/codex` SSOT switched to CLI + `codex-runner` (MCP path removed); fixed GNU sed brace bug in seed adapt; epic Cursor overlay reseeded; added `etc/test-cursor-contracts.sh`.

- Remaining follow-up (2026-07-15): `etc/seed-codex-overlay.sh` (agents×6 + skills×4); `etc/check-shared-drift.sh`; `etc/test-codex-contracts.sh`; OpenCode stays generated; Codex skills stay full snapshots; implement smoke in `docs/plans/2026-07-15-remaining-followup.md`.

Open items:

- None blocking. Optional: longer-running full `/pir2` on an unrelated product repo for soak testing.
- OpenCode: **keep generated agents** from `.claude/agents` via `sync-opencode.sh` (native overlay deferred until runtime needs diverge).
- Codex skills: **keep full skill snapshots** as native overlays; grow with `seed-codex-overlay.sh` (missing-only). Do not re-enable default `SYNC_CODEX_LEGACY_MIRROR`.
- Drift: **`etc/check-shared-drift.sh`** detects shared skills/agents trapped in one runtime (allowlists: `pir2codex`, `codex-runner` on Codex).

### Codex seed contract

```bash
bash etc/seed-codex-overlay.sh
bash etc/check-shared-drift.sh
bash etc/test-codex-contracts.sh
```

- Agents seeded: `deliberator`, `epic-planner`, `gate`, `hypothesizer`, `synthesizer`, `thinker` (`codex-runner` omitted).
- Skills seeded: `deepthink`, `research`, `epic`, `unity-mcp-skill` from `.agents/skills`.
- Existing overlays are never overwritten.
