Completed the assigned overlay/adapter work.

Changed only:

- `.codex/agents/*.toml`
- `.codex/pir2-protocol.md`
- `etc/sync-codex.sh`
- `etc/seed-codex-overlay.sh`

Key results:

- All 17 agent TOMLs now declare themselves editable native overlays.
- Default and legacy sync preserve native agent TOMLs; legacy mode refreshes only explicitly `LEGACY-GENERATED` snapshots.
- Legacy routing uses `gpt-5.6-luna` for explorer/implementer and `gpt-5.6-terra` otherwise.
- Protocol regeneration is handled through the Codex adapter transform and now uses `.toml`, `spawn_agent`, and `agent_type`.
- Replaced all native `subagent_type` guidance with `agent_type`.
- Corrected stale native agent `.md` paths to `.toml`.

Commands run and observed:

- `bash -n etc/sync-codex.sh etc/seed-codex-overlay.sh` — succeeded.
- TOML parse of 17 agent overlays — succeeded.
- `git diff --check` (target and full worktree) — succeeded.
- Isolated sync test — default and legacy sync preserved native overlays; explicit legacy refresh used Luna/Terra routing and `agent_type`.
- Isolated seed test — emitted the native-overlay marker and current Terra route.

Blockers: none.