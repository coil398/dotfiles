[CmdletBinding()]
param(
    [string]$Cwd,
    [string]$TaskFile,
    [string]$RequirementsFile,
    [string]$OutputFile,
    [switch]$Help
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Show-Usage {
    [Console]::Error.WriteLine(
        "Usage: run-luna-max.ps1 -Cwd DIR -TaskFile FILE " +
        "-RequirementsFile FILE -OutputFile FILE")
}

function Exit-WithError {
    param(
        [string]$Message,
        [int]$Code = 2
    )

    [Console]::Error.WriteLine("ERROR: $Message")
    exit $Code
}

if ($Help) {
    Show-Usage
    exit 0
}

if ([string]::IsNullOrWhiteSpace($Cwd)) {
    Exit-WithError "-Cwd is required"
}
if ([string]::IsNullOrWhiteSpace($TaskFile)) {
    Exit-WithError "-TaskFile is required"
}
if ([string]::IsNullOrWhiteSpace($RequirementsFile)) {
    Exit-WithError "-RequirementsFile is required"
}
if ([string]::IsNullOrWhiteSpace($OutputFile)) {
    Exit-WithError "-OutputFile is required"
}
if (-not (Test-Path -LiteralPath $Cwd -PathType Container)) {
    Exit-WithError "cwd is not a directory: $Cwd"
}
if (-not (Test-Path -LiteralPath $TaskFile -PathType Leaf) -or
    (Get-Item -LiteralPath $TaskFile).Length -eq 0) {
    Exit-WithError "task file is missing or empty: $TaskFile"
}
if (-not (Test-Path -LiteralPath $RequirementsFile -PathType Leaf) -or
    (Get-Item -LiteralPath $RequirementsFile).Length -eq 0) {
    Exit-WithError "requirements file is missing or empty: $RequirementsFile"
}

$requirements = [IO.File]::ReadAllText(
    (Resolve-Path -LiteralPath $RequirementsFile).Path)
if ($requirements -notmatch '(?m)^[\t ]*-[\t ]+R[0-9]+:') {
    Exit-WithError `
        'requirements must contain at least one "- R<number>:" criterion'
}

$outputPath = [IO.Path]::GetFullPath($OutputFile)
$outputDir = [IO.Path]::GetDirectoryName($outputPath)
if ([string]::IsNullOrWhiteSpace($outputDir) -or
    -not (Test-Path -LiteralPath $outputDir -PathType Container)) {
    Exit-WithError "output directory does not exist: $outputDir"
}
if (Test-Path -LiteralPath $outputPath) {
    Exit-WithError "output file already exists: $outputPath"
}

$codexBin = $env:LUNA_MAX_CODEX_BIN
if ([string]::IsNullOrWhiteSpace($codexBin)) {
    $npmCodex = if ([string]::IsNullOrWhiteSpace($env:APPDATA)) {
        $null
    }
    else {
        Join-Path $env:APPDATA "npm\codex.cmd"
    }

    $codexBin = if ($null -ne $npmCodex -and
        (Test-Path -LiteralPath $npmCodex -PathType Leaf)) {
        $npmCodex
    }
    else {
        "codex"
    }
}

$codexCommand = Get-Command -Name $codexBin -ErrorAction SilentlyContinue
if ($null -eq $codexCommand) {
    Exit-WithError "codex command not found: $codexBin" 127
}

$scratchDir = Join-Path (
    [IO.Path]::GetTempPath()) (
    "luna-max-worker." + [Guid]::NewGuid().ToString("N"))
$null = New-Item -ItemType Directory -Path $scratchDir
$promptFile = Join-Path $scratchDir "prompt.md"

try {
    $task = [IO.File]::ReadAllText((Resolve-Path -LiteralPath $TaskFile).Path)
    $prompt = @"
# Role

You are the execution worker for a task already planned by the parent Sol agent.
Perform only the concrete task below. Do not redesign the task, expand scope, invoke luna-max-worker, or spawn other agents.
Do not commit, push, discard existing user changes, or use destructive git commands.
If the instructions are insufficient or require a new decision, stop and report the exact blocker.

# Task

$task

# Acceptance criteria

$requirements

# Completion report

Report changed files, commands run, observed results, and blockers. Your report is not the acceptance decision; the parent Sol agent verifies every criterion independently.
"@
    [IO.File]::WriteAllText(
        $promptFile,
        $prompt,
        [Text.UTF8Encoding]::new($false))

    # Windows PowerShell 5.1 defaults native-command stdin to ASCII.
    # Codex expects UTF-8, so preserve non-ASCII task and requirement text.
    $OutputEncoding = [Text.UTF8Encoding]::new($false)
    [Console]::OutputEncoding = $OutputEncoding
    [IO.File]::ReadAllText($promptFile) |
        & $codexCommand.Source exec `
            --json `
            --skip-git-repo-check `
            -m gpt-5.6-luna `
            -c 'model_reasoning_effort="max"' `
            -s workspace-write `
            -C $Cwd `
            -o $outputPath `
            -
    $exitCode = $LASTEXITCODE
    if ($null -eq $exitCode) {
        $exitCode = 0
    }
    exit $exitCode
}
finally {
    if (Test-Path -LiteralPath $promptFile) {
        Remove-Item -LiteralPath $promptFile -Force
    }
    if (Test-Path -LiteralPath $scratchDir) {
        Remove-Item -LiteralPath $scratchDir -Force
    }
}
