import { spawn } from "node:child_process"
import { existsSync } from "node:fs"
import { homedir } from "node:os"
import { join } from "node:path"

// Sync dotfiles in the background when a session starts, like the
// SessionStart hooks of the other runtimes.
const SCRIPT = join(homedir(), ".claude", "lib", "dotfiles-session-sync.sh")

export const DotfilesSessionSync = async () => {
  return {
    event: async ({ event }) => {
      if (event.type !== "session.created" || !existsSync(SCRIPT)) return
      spawn("bash", [SCRIPT], { detached: true, stdio: "ignore" }).unref()
    },
  }
}
