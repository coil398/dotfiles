const SECRET_PATH_PATTERNS = [
  /(^|\/)\.env(\.[^/]*)?$/,
  /\.(pem|keystore|p12|pfx)$/i,
  /(^|\/)id_(rsa|ed25519|ecdsa)(\.|$)/,
  /(^|\/)\.zsh_secret/,
  /(^|\/)\.netrc$/,
  /(^|\/)auth\.json$/,
  /(^|\/)\.aws(\/|$)/,
  /(^|\/)\.ssh(\/|$)/,
]

const BASH_HIGH_SIGNAL_TOKENS = [
  "id_rsa",
  "id_ed25519",
  "id_ecdsa",
  ".zsh_secret",
  ".netrc",
  ".aws/credentials",
  "auth.json",
]

function pathOf(args) {
  return args?.filePath ?? args?.file_path ?? args?.path ?? ""
}

function isSecretPath(p) {
  return SECRET_PATH_PATTERNS.some((re) => re.test(p))
}

export const SecretGuard = async ({ project, client, $, directory, worktree }) => {
  return {
    "tool.execute.before": async (input, output) => {
      const { tool } = input
      if (tool === "read" || tool === "edit" || tool === "write") {
        const p = String(pathOf(output.args))
        if (p && isSecretPath(p)) {
          throw new Error(
            `[secret-guard] blocked ${tool} on credential-like path: ${p}. Ask the user to handle this file directly.`,
          )
        }
      }
      if (tool === "bash") {
        const cmd = String(output.args?.command ?? "")
        const lowered = cmd.toLowerCase()
        const hit = BASH_HIGH_SIGNAL_TOKENS.find((t) => lowered.includes(t))
        if (hit) {
          throw new Error(
            `[secret-guard] blocked bash command referencing '${hit}'. Ask the user to run it directly if truly needed.`,
          )
        }
      }
    },
  }
}
