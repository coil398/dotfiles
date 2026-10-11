#!/usr/bin/env bash
# OpenCode sync 契約テスト。
#
#   bash etc/test-opencode-contracts.sh
#
# fake HOME / OPENCODE_CONFIG_DIR での fresh sync・冪等性・AGENTS.md 補足
# セクション・plugin 孤児削除を mktemp フィクスチャで確認する。

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/opencode-contracts.XXXXXX")"
trap 'find "$WORK" -mindepth 1 -delete 2>/dev/null; rmdir "$WORK" 2>/dev/null || true' EXIT

fail=0
pass=0

ok() { echo "PASS: $*"; pass=$((pass + 1)); }
bad() { echo "FAIL: $*" >&2; fail=$((fail + 1)); }

assert_true() {
  local name="$1"
  shift
  if "$@"; then
    ok "$name"
  else
    bad "$name"
  fi
}

PLUGIN_SRC_DIR="${DOT_DIR}/.opencode/plugins"

# Dependency failures must be visible to callers (link.sh uses this status to
# stop an AI-runtime deployment). Run the real sync script with an isolated
# PATH that has no jq; no generated output is allowed to be treated as ready.
no_jq_bin="${WORK}/no-jq-bin"
missing_jq_home="${WORK}/missing-jq-home"
missing_jq_log="${WORK}/missing-jq.log"
mkdir -p "$no_jq_bin" "$missing_jq_home"
bash_bin="$(command -v bash)"
if HOME="$missing_jq_home" PATH="$no_jq_bin" "$bash_bin" "${SCRIPT_DIR}/sync-opencode.sh" >"$missing_jq_log" 2>&1; then
  bad "sync-opencode fails when jq is missing"
else
  ok "sync-opencode fails when jq is missing"
fi
assert_true "sync-opencode reaches jq dependency check" \
  grep -q 'required dependency missing: jq' "$missing_jq_log"

# --check is read-only even when HOME has never been initialized. In
# particular, the check path must not create ~/.config/opencode as a side
# effect before it reports missing/stale generated output.
empty_check_home="${WORK}/empty-check-home"
mkdir -p "$empty_check_home"
if HOME="$empty_check_home" OPENCODE_CONFIG_DIR="$empty_check_home/.config/opencode" bash "${SCRIPT_DIR}/sync-opencode.sh" --check >/dev/null 2>&1; then
  bad "sync-opencode --check rejects empty HOME"
else
  if [ -z "$(find "$empty_check_home" -mindepth 1 -print -quit 2>/dev/null)" ]; then
    ok "sync-opencode --check does not create output directories"
  else
    bad "sync-opencode --check does not create output directories"
  fi
fi

# --- B. fake HOME fresh sync + idempotency ---
fake_home="${WORK}/home"
if HOME="$fake_home" OPENCODE_CONFIG_DIR="$fake_home/.config/opencode" bash "${SCRIPT_DIR}/sync-opencode.sh" >/dev/null; then
  ok "fresh sync with fake HOME"
else
  bad "fresh sync with fake HOME"
fi

TARGET_JSON="${fake_home}/.config/opencode/opencode.json"
TARGET_AGENTS_MD="${fake_home}/.config/opencode/AGENTS.md"
TARGET_PLUGINS_DIR="${fake_home}/.config/opencode/plugins"

if HOME="$fake_home" OPENCODE_CONFIG_DIR="$fake_home/.config/opencode" bash "${SCRIPT_DIR}/sync-opencode.sh" --check >/dev/null; then
  ok "re-run is idempotent (--check passes on fresh output)"
else
  bad "re-run is idempotent (--check passes on fresh output)"
fi

# The project-scoped config-dir override receives the shared instruction file.
# --agents-only must leave the runtime's JSON and plugin state untouched.
override_config_dir="${WORK}/opencode-override"
xdg_config_home="${WORK}/xdg-config-home"
xdg_opencode_config_dir="${xdg_config_home}/opencode"
precedence_xdg_config_home="${WORK}/precedence-xdg-config-home"
mkdir -p "$override_config_dir/plugins"
printf '%s\n' 'user opencode config sentinel' >"$override_config_dir/opencode.json"
printf '%s\n' 'user plugin sentinel' >"$override_config_dir/plugins/user-plugin.js"
if HOME="$fake_home" OPENCODE_CONFIG_DIR="$override_config_dir" XDG_CONFIG_HOME="$precedence_xdg_config_home" bash "${SCRIPT_DIR}/sync-opencode.sh" --agents-only >/dev/null; then
  ok "agents-only generation honors OPENCODE_CONFIG_DIR"
else
  bad "agents-only generation honors OPENCODE_CONFIG_DIR"
fi
assert_true "agents-only writes generated AGENTS.md" test -f "$override_config_dir/AGENTS.md"
assert_true "agents-only preserves opencode.json" grep -q '^user opencode config sentinel$' "$override_config_dir/opencode.json"
assert_true "agents-only preserves plugins" grep -q '^user plugin sentinel$' "$override_config_dir/plugins/user-plugin.js"
if HOME="$fake_home" OPENCODE_CONFIG_DIR="$override_config_dir" bash "${SCRIPT_DIR}/sync-opencode.sh" --agents-only --check >/dev/null; then
  ok "agents-only check honors OPENCODE_CONFIG_DIR"
else
  bad "agents-only check honors OPENCODE_CONFIG_DIR"
fi
assert_true "OPENCODE_CONFIG_DIR takes precedence over XDG_CONFIG_HOME" test ! -e "$precedence_xdg_config_home/opencode/AGENTS.md"
if env -u OPENCODE_CONFIG_DIR HOME="$fake_home" XDG_CONFIG_HOME="$xdg_config_home" bash "${SCRIPT_DIR}/sync-opencode.sh" --agents-only >/dev/null; then
  ok "agents-only generation honors XDG_CONFIG_HOME"
else
  bad "agents-only generation honors XDG_CONFIG_HOME"
fi
assert_true "XDG_CONFIG_HOME receives generated OpenCode AGENTS.md" test -f "$xdg_opencode_config_dir/AGENTS.md"

# Generated publication must reject an existing final file symlink rather than
# replacing the link, and reject a directory symlink without placing the
# temporary output inside its target directory.
private_json="${fake_home}/.config/opencode/opencode.json"
private_json_target="${WORK}/opencode-generated-target.json"
cp "$private_json" "$private_json_target"
private_json_before="$(shasum "$private_json_target" | awk '{print $1}')"
rm -f "$private_json"
ln -s "$private_json_target" "$private_json"
if HOME="$fake_home" OPENCODE_CONFIG_DIR="$fake_home/.config/opencode" bash "${SCRIPT_DIR}/sync-opencode.sh" >/dev/null 2>&1; then
  bad "sync-opencode rejects generated file symlink"
else
  ok "sync-opencode rejects generated file symlink"
fi
[ -L "$private_json" ] && ok "sync-opencode preserves generated file symlink" || bad "sync-opencode preserves generated file symlink"
private_json_after="$(shasum "$private_json_target" | awk '{print $1}')"
[ "$private_json_before" = "$private_json_after" ] && ok "sync-opencode leaves symlink target unchanged" || bad "sync-opencode leaves symlink target unchanged"

private_json_dir="${WORK}/opencode-generated-dir"
mkdir "$private_json_dir"
rm -f "$private_json"
ln -s "$private_json_dir" "$private_json"
if HOME="$fake_home" OPENCODE_CONFIG_DIR="$fake_home/.config/opencode" bash "${SCRIPT_DIR}/sync-opencode.sh" >/dev/null 2>&1; then
  bad "sync-opencode rejects generated directory symlink"
else
  ok "sync-opencode rejects generated directory symlink"
fi
[ -L "$private_json" ] && ok "sync-opencode preserves directory symlink" || bad "sync-opencode preserves directory symlink"
if [ -z "$(find "$private_json_dir" -mindepth 1 -print -quit 2>/dev/null)" ]; then
  ok "sync-opencode leaves directory symlink target empty"
else
  bad "sync-opencode leaves directory symlink target empty"
fi
rm -f "$private_json"
mkdir "$private_json"
if HOME="$fake_home" OPENCODE_CONFIG_DIR="$fake_home/.config/opencode" bash "${SCRIPT_DIR}/sync-opencode.sh" >/dev/null 2>&1; then
  bad "sync-opencode rejects generated directory target"
else
  ok "sync-opencode rejects generated directory target"
fi
if [ -z "$(find "$private_json" -mindepth 1 -print -quit 2>/dev/null)" ]; then
  ok "sync-opencode leaves directory target empty"
else
  bad "sync-opencode leaves directory target empty"
fi
rmdir "$private_json"
cp "$private_json_target" "$private_json"

# --- C. opencode.json contract (generated file carries JSONC header comments) ---
if command -v jq >/dev/null 2>&1 && [ -f "$TARGET_JSON" ]; then
  strip_jsonc() { grep -v '^[[:space:]]*//' "$1"; }

  if strip_jsonc "$TARGET_JSON" | jq -e '."$schema" == "https://opencode.ai/config.json"' >/dev/null; then
    ok "opencode.json has \$schema"
  else
    bad "opencode.json has \$schema"
  fi

  leaked="$(jq -r --argjson out "$(strip_jsonc "$TARGET_JSON" | jq '.mcp // {}')" '
    .mcpServers
    | to_entries[]
    | select(.value.claudeCodeOnly == true or .value.codexOnly == true)
    | .key as $k
    | select($out[$k] != null)
    | $k
  ' "${DOT_DIR}/mcp-servers.json")"
  if [ -z "$leaked" ]; then
    ok "mcp excludes claudeCodeOnly/codexOnly servers"
  else
    bad "mcp leaked claudeCodeOnly/codexOnly servers: $leaked"
  fi

  if strip_jsonc "$TARGET_JSON" | jq -e '.lsp == true' >/dev/null; then
    ok "lsp explicitly enabled (OpenCode defaults to disabled)"
  else
    bad "lsp explicitly enabled (OpenCode defaults to disabled)"
  fi

  if strip_jsonc "$TARGET_JSON" | jq -e '.permission.bash["*"] == "allow"' >/dev/null; then
    ok "permission bash defaults to allow (approval-fatigue policy)"
  else
    bad "permission bash defaults to allow (approval-fatigue policy)"
  fi

  if strip_jsonc "$TARGET_JSON" | jq -e '.permission.bash["rm -rf *"] == "ask" and .permission.bash["sudo *"] == "ask" and .permission.bash["git push *"] == "ask" and .permission.edit == "allow"' >/dev/null; then
    ok "dangerous bash ops ask + edit allow"
  else
    bad "dangerous bash ops ask + edit allow"
  fi

  if strip_jsonc "$TARGET_JSON" | jq -e '.permission.external_directory["~/**"] == "allow"' >/dev/null; then
    ok "external_directory allows home (approval-fatigue policy, session-scoped always workaround)"
  else
    bad "external_directory allows home (approval-fatigue policy, session-scoped always workaround)"
  fi
else
  bad "jq + opencode.json required for MCP assertions"
fi

# --- D2. plugin sync contract ---
if [ -d "$PLUGIN_SRC_DIR" ]; then
  missing_plugins=""
  bad_plugin_header=""
  bad_plugin_syntax=""
  have_bun=""
  if command -v bun >/dev/null 2>&1; then
    have_bun=bun
  elif [ -x "${HOME}/.bun/bin/bun" ]; then
    have_bun="${HOME}/.bun/bin/bun"
  elif command -v node >/dev/null 2>&1; then
    have_bun=node
  fi
  for src in "${PLUGIN_SRC_DIR}"/*; do
    [ -f "$src" ] || continue
    case "$src" in *.js|*.ts|*.mjs) ;; *) continue ;; esac
    base="$(basename "$src")"
    dst="${TARGET_PLUGINS_DIR}/${base}"
    if [ ! -f "$dst" ]; then
      missing_plugins="${missing_plugins} ${base}"
      continue
    fi
    head -1 "$dst" | grep -q '^// AUTO-GENERATED by etc/sync-opencode.sh' || bad_plugin_header="${bad_plugin_header} ${base}"
    if [ -n "$have_bun" ]; then
      syn_dir="${WORK}/plugin-syntax"
      mkdir -p "$syn_dir"
      cp "$dst" "${syn_dir}/${base%.js}.mjs"
      case "$(basename "$have_bun")" in
        bun) "$have_bun" build --no-bundle "${syn_dir}/${base%.js}.mjs" >/dev/null 2>&1 || bad_plugin_syntax="${bad_plugin_syntax} ${base}" ;;
        *) node --check "${syn_dir}/${base%.js}.mjs" 2>/dev/null || bad_plugin_syntax="${bad_plugin_syntax} ${base}" ;;
      esac
    fi
  done
  [ -z "$missing_plugins" ] && ok "all SSOT plugins synced" || bad "plugins missing from generated dir:${missing_plugins}"
  [ -z "$bad_plugin_header" ] && ok "plugins have AUTO-GENERATED header" || bad "plugins missing header:${bad_plugin_header}"
  if [ -n "$have_bun" ]; then
    [ -z "$bad_plugin_syntax" ] && ok "plugin syntax valid ($have_bun)" || bad "plugin syntax invalid:${bad_plugin_syntax}"
  else
    ok "plugin syntax check skipped (no bun/node)"
  fi

  grep -q 'tool.execute.before' "${TARGET_PLUGINS_DIR}"/*.js 2>/dev/null \
    && ok "secret-guard hooks tool.execute.before" || bad "secret-guard hooks tool.execute.before"
else
  ok "no plugin SSOT dir (skip plugin contract)"
fi

# --- D3. secret-guard runtime contract (import the real SSOT plugin) ---
if [ -f "${PLUGIN_SRC_DIR}/secret-guard.js" ] && command -v node >/dev/null 2>&1; then
  if SECRET_GUARD_PLUGIN="${PLUGIN_SRC_DIR}/secret-guard.js" node --no-warnings --input-type=module <<'NODE'
import { pathToFileURL } from "node:url"

const pluginPath = process.env.SECRET_GUARD_PLUGIN
if (!pluginPath) throw new Error("SECRET_GUARD_PLUGIN is required")
const { SecretGuard } = await import(pathToFileURL(pluginPath).href)
if (typeof SecretGuard !== "function") throw new Error("SecretGuard export is missing")

const hooks = await SecretGuard({ project: {}, client: {}, $: {}, directory: "/tmp", worktree: "/tmp" })
const before = hooks["tool.execute.before"]
if (typeof before !== "function") throw new Error("tool.execute.before hook is missing")

let blocked = 0
let allowed = 0

async function expectBlocked(label, input, output, fragment) {
  let error
  try {
    await before(input, output)
  } catch (caught) {
    error = caught
  }
  if (!error) throw new Error(`${label}: expected rejection`)
  const message = String(error)
  if (!message.includes("[secret-guard] blocked")) {
    throw new Error(`${label}: rejection does not identify secret-guard`)
  }
  if (fragment && !message.includes(fragment)) {
    throw new Error(`${label}: rejection omitted ${fragment}`)
  }
  blocked += 1
}

async function expectAllowed(label, input, output) {
  const result = await before(input, output)
  if (result !== undefined) throw new Error(`${label}: expected undefined result`)
  allowed += 1
}

for (const tool of ["read", "edit", "write"]) {
  await expectBlocked(
    `${tool} credential path`,
    { tool },
    { args: { filePath: "/tmp/project/.env.local" } },
    "/tmp/project/.env.local",
  )
  await expectAllowed(
    `${tool} normal path`,
    { tool },
    { args: { filePath: "/tmp/project/README.md" } },
  )
}

for (const [command, token] of [
  ["cat ~/.ssh/id_rsa", "id_rsa"],
  ["cat ~/.ssh/id_ed25519", "id_ed25519"],
  ["cat ~/.ssh/id_ecdsa", "id_ecdsa"],
  ["cat ~/.zsh_secret", ".zsh_secret"],
  ["cat ~/.netrc", ".netrc"],
  ["cat ~/.aws/credentials", ".aws/credentials"],
  ["cat ./config/auth.json", "auth.json"],
]) {
  await expectBlocked("bash high-signal token", { tool: "bash" }, { args: { command } }, token)
}
for (const command of ["printf '%s\\n' ok", "git status --short", "find src -type f"]) {
  await expectAllowed("bash normal command", { tool: "bash" }, { args: { command } })
}

console.log(`secret-guard runtime assertions: ${blocked} blocked, ${allowed} allowed`)
NODE
  then
    ok "secret-guard blocks credential paths/high-signal bash and allows normal events"
  else
    bad "secret-guard blocks credential paths/high-signal bash and allows normal events"
  fi
elif [ ! -f "${PLUGIN_SRC_DIR}/secret-guard.js" ]; then
  bad "secret-guard runtime fixture (SSOT plugin missing)"
else
  bad "secret-guard runtime fixture (node is required)"
fi

# --- E. generated AGENTS.md contract ---
if [ -f "$TARGET_AGENTS_MD" ]; then
  head -1 "$TARGET_AGENTS_MD" | grep -q '<!-- AUTO-GENERATED by dotfiles/etc/sync-opencode.sh' \
    && ok "generated AGENTS.md has header" || bad "generated AGENTS.md has header"

  # 生成物は 5 行ヘッダーの直後に SSOT 全文を埋め込む。byte-count ベースで prefix 一致を検証
  ssot_bytes="$(wc -c < "$DOT_DIR/.agents/global-instructions.md")"
  tail -n +6 "$TARGET_AGENTS_MD" | head -c "$ssot_bytes" > "${WORK}/ssot-embed.tmp"
  if cmp -s "${WORK}/ssot-embed.tmp" "$DOT_DIR/.agents/global-instructions.md"; then
    ok "generated AGENTS.md embeds global source verbatim"
  else
    bad "generated AGENTS.md embeds global source verbatim"
  fi

  for section in "サブエージェント起動の読み替え" "スキルの発見経路" "スキルの適用条件" "権限と固有機能" "モデルと設定の原本"; do
    assert_true "supplement section present: $section" grep -q "^## $section" "$TARGET_AGENTS_MD"
  done

  stale=""
  grep -q "skill-creator" "$TARGET_AGENTS_MD" && stale="${stale} skill-creator"
  grep -q "claude-sonnet-[0-9]" "$TARGET_AGENTS_MD" && stale="${stale} claude-sonnet-*"
  if [ -z "$stale" ]; then
    ok "no stale references (skill-creator / old model ids)"
  else
    bad "stale references in generated AGENTS.md:${stale}"
  fi
else
  bad "generated AGENTS.md exists"
fi

# --- F. plugin orphan cleanup + hand-written protection on fake HOME ---
if [ -d "$PLUGIN_SRC_DIR" ]; then
  orphan_plugin="${fake_home}/.config/opencode/plugins/orphan-plugin.js"
  handwritten_plugin="${fake_home}/.config/opencode/plugins/hand-written-plugin.js"
  {
    printf '// AUTO-GENERATED by etc/sync-opencode.sh from gone.js. Do not edit.\n'
    printf 'export const Orphan = async () => ({})\n'
  } > "$orphan_plugin"
  printf '// HAND WRITTEN\n' > "$handwritten_plugin"
fi

HOME="$fake_home" OPENCODE_CONFIG_DIR="$fake_home/.config/opencode" bash "${SCRIPT_DIR}/sync-opencode.sh" >/dev/null

if [ -d "$PLUGIN_SRC_DIR" ]; then
  [ ! -f "$orphan_plugin" ] && ok "orphan AUTO-GENERATED plugin removed" || bad "orphan AUTO-GENERATED plugin removed"
  [ -f "$handwritten_plugin" ] && ok "hand-written plugin survives cleanup" || bad "hand-written plugin survives cleanup"
fi

codex_override="${fake_home}/.config/opencode/AGENTS.override.md"
head -1 "$codex_override" | grep -q '^<!-- AUTO-GENERATED by dotfiles/etc/sync-opencode.sh' \
  && ok "Codex override generated with marker" || bad "Codex override generated with marker"
printf '# hand-written override\n' >"$codex_override"
HOME="$fake_home" OPENCODE_CONFIG_DIR="$fake_home/.config/opencode" bash "${SCRIPT_DIR}/sync-opencode.sh" >/dev/null 2>&1
[ "$(cat "$codex_override")" = "# hand-written override" ] \
  && ok "hand-written Codex override survives sync" || bad "hand-written Codex override survives sync"

echo
echo "opencode contracts: ${pass} passed, ${fail} failed"
if [ "$fail" -ne 0 ]; then
  exit 1
fi
exit 0
