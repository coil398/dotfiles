import assert from "node:assert/strict"
import { mkdtemp, rm, symlink, writeFile } from "node:fs/promises"
import { tmpdir } from "node:os"
import { join } from "node:path"
import test from "node:test"
import { JevPermissionPolicy } from "../.opencode/plugins/jev-permission-policy.mjs"

test("OpenCode asked events reply once for routine work and reject risky or secret paths", async () => {
  const directory = await mkdtemp(join(tmpdir(), "jev-opencode-permission-"))
  const state = join(directory, "state")
  process.env.JEV_HOOKS_MODE = "off"
  process.env.JEV_HOOKS_STATE_DIR = state
  process.env.TYPESAFE_API_KEY = ""
  const replies = []
  const plugin = await JevPermissionPolicy({
    directory,
    client: { postSessionIdPermissionsPermissionId: async (request) => replies.push(request) },
  })
  const send = (id, permission, patterns, metadata) => plugin.event({ event: {
    type: "permission.asked",
    properties: { id, sessionID: "session", permission, patterns, metadata },
  } })
  try {
    await send("read", "bash", ["ls"], { command: "ls" })
    await send("write", "bash", ["rm -rf build"], { command: "rm -rf build" })
    await send("outside", "external_directory", ["/etc/*"], { directories: ["/etc"] })
    const secret = join(directory, ".env")
    const alias = join(directory, "plain.txt")
    await writeFile(secret, "TEST_ONLY=value\n")
    await symlink(secret, alias)
    await send("secret", "edit", ["plain.txt"], { filepath: "plain.txt" })
    assert.deepEqual(replies.map((entry) => [entry.path.permissionID, entry.body.response]), [
      ["read", "once"],
      ["write", "reject"],
      ["outside", "reject"],
      ["secret", "reject"],
    ])
    assert.ok(replies.every((entry) => entry.body.response !== "always"))
  } finally {
    await rm(directory, { recursive: true, force: true })
  }
})
