import { spawnSync } from "node:child_process"
import { homedir } from "node:os"
import { join } from "node:path"

const HOOK = join(homedir(), ".claude", "lib", "ai-lint-hook.sh")

export const AiLint = async ({ directory }) => {
  return {
    "tool.execute.after": async (input, output) => {
      if (!["edit", "write", "apply_patch"].includes(input.tool)) return
      try {
        const payload = JSON.stringify({
          tool_name: input.tool,
          tool_input: input.args,
          cwd: directory,
        })
        const result = spawnSync("bash", [HOOK, "opencode"], {
          input: payload,
          encoding: "utf8",
          timeout: 10000,
        })
        if (result.error || result.status !== 0 || !result.stdout) return
        const response = JSON.parse(result.stdout)
        const context = response?.additional_context
        if (typeof context !== "string" || !context) return
        output.output = `${output.output ?? ""}\n\n${context}`
      } catch {
        // Advisory analysis must never change the completed edit result.
      }
    },
  }
}
