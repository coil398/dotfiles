import { homedir } from "node:os"
import { join } from "node:path"
import { spawnSync } from "node:child_process"

const HOOK = join(homedir(), ".claude", "lib", "permission-request-hook.sh")

function requests(permission, patterns, metadata) {
  const action = String(permission || "").toLowerCase()
  if (action === "shell" || action === "bash") {
    const commands = typeof metadata.command === "string" && metadata.command
      ? [metadata.command]
      : []
    return commands.map((command) => ({ tool_name: "Bash", tool_input: { command } }))
  }
  const paths = (Array.isArray(patterns) ? patterns : []).filter((value) => typeof value === "string" && value)
  const filePath = typeof metadata.filepath === "string" ? metadata.filepath : paths[0]
  if (action === "edit" || action === "write") {
    return filePath ? [{ tool_name: "Write", tool_input: { file_path: filePath } }] : []
  }
  if (action === "read") return filePath ? [{ tool_name: "Read", tool_input: { file_path: filePath } }] : []
  if (action === "glob") return paths.map((pattern) => ({ tool_name: "Glob", tool_input: { pattern } }))
  if (action === "grep") return paths.map((pattern) => ({ tool_name: "Grep", tool_input: { pattern } }))
  if (action === "webfetch") return paths.map((url) => ({ tool_name: "WebFetch", tool_input: { url } }))
  if (action === "websearch") return paths.map((query) => ({ tool_name: "WebSearch", tool_input: { query } }))
  if (action === "question") return paths.map((question) => ({ tool_name: "AskUserQuestion", tool_input: { question } }))
  if (action === "task" || action === "subagent") return paths.map((agent) => ({ tool_name: "Task", tool_input: { agent } }))
  if (action === "external_directory") return paths.map((path) => ({ tool_name: "Write", tool_input: { file_path: path } }))
  if (action.includes("_")) {
    const tool = action.startsWith("mcp__") ? action : `mcp__opencode__${action}`
    return paths.map((resource) => ({ tool_name: tool, tool_input: { resource } }))
  }
  return []
}

function evaluate(input, directory) {
  const result = spawnSync("bash", [HOOK, "opencode"], {
    input: JSON.stringify({ ...input, cwd: directory }),
    encoding: "utf8",
    timeout: 20_000,
  })
  if (result.error || result.status !== 0 || !result.stdout) return { effect: "deny", message: "Jev permission hook failed; skip this operation and report it." }
  try {
    const response = JSON.parse(result.stdout)
    return response.effect === "allow"
      ? { effect: "allow" }
      : { effect: "deny", message: response.message || "Jev did not allow this operation; skip it and report the reason." }
  } catch {
    return { effect: "deny", message: "Jev permission hook returned invalid output; skip this operation and report it." }
  }
}

async function handlePermission(event, client, directory) {
  if (!event || event.type !== "permission.asked" || !event.properties) return
  const request = event.properties
  let response = "reject"
  try {
    const items = requests(request.permission, request.patterns, request.metadata || {})
    if (!items.length) throw new Error("unclassified permission request")
    for (const item of items) {
      const result = evaluate(item, directory)
      if (result.effect !== "allow") throw new Error("permission denied")
    }
    response = "once"
  } catch (error) {
    console.warn("jev_permission_decision", { runtime: "opencode", action: request.permission, decision: "deny", error: error instanceof Error ? error.name : "Error" })
  }
  try {
    await client.postSessionIdPermissionsPermissionId({
      path: { id: request.sessionID, permissionID: request.id },
      body: { response },
    })
  } catch {
    console.warn("jev_permission_reply_failed runtime=opencode pending=true")
  }
}

export const JevPermissionPolicy = async ({ client, directory }) => ({
  event: async ({ event }) => {
    if (event?.type === "permission.asked") await handlePermission(event, client, directory)
  },
})
