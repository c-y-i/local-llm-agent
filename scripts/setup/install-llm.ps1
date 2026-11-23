param(
    [switch]$AddToPath
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:LOCAL_LLM_AGENT_ROOT = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
. (Join-Path $env:LOCAL_LLM_AGENT_ROOT "scripts\common\env.ps1")

$repoRoot = $env:LOCAL_LLM_AGENT_ROOT
$venv = $env:LLM_VENV_DIR
$venvPython = Join-Path $venv "Scripts\python.exe"
$binDir = Join-Path $HOME ".local\bin"

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $python) {
    throw "Python 3.11 or newer is required and was not found on PATH."
}
$versionArgs = if ($python.Name -ieq "py.exe") { @("-3", "-c") } else { @("-c") }
& $python.Source @versionArgs "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
if ($LASTEXITCODE -ne 0) {
    throw "Python 3.11 or newer is required."
}

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating managed virtualenv: $venv"
    if ($python.Name -ieq "py.exe") {
        & $python.Source -3 -m venv $venv
    } else {
        & $python.Source -m venv $venv
    }
}

New-Item -ItemType Directory -Force -Path $binDir | Out-Null
foreach ($name in @(
    "LLM_ROOT",
    "LLAMA_CPP_ROOT",
    "OLLAMA_ROOT",
    "LLM_MODELS_DIR",
    "OLLAMA_MODELS",
    "LLM_RUN_DIR",
    "LLM_CODEX_HOME",
    "LLM_HERMES_HOME"
)) {
    New-Item -ItemType Directory -Force -Path ([Environment]::GetEnvironmentVariable($name)) | Out-Null
}

$userOllamaModels = [Environment]::GetEnvironmentVariable("OLLAMA_MODELS", "User")
if (-not $userOllamaModels) {
    [Environment]::SetEnvironmentVariable("OLLAMA_MODELS", $env:OLLAMA_MODELS, "User")
    Write-Host "Configured user OLLAMA_MODELS: $env:OLLAMA_MODELS"
} elseif ($userOllamaModels -ne $env:OLLAMA_MODELS) {
    Write-Warning "User OLLAMA_MODELS is already set to $userOllamaModels; leaving it unchanged."
}

$repoVenv = Join-Path $repoRoot ".venv"
if (-not (Test-Path $repoVenv)) {
    try {
        New-Item -ItemType Junction -Path $repoVenv -Target $venv | Out-Null
    } catch {
        Write-Warning "Could not create .venv junction. Use .\llm.cmd from the repo or the installed llm.cmd wrapper."
    }
}

function Write-CmdWrapper {
    param(
        [string]$Name,
        [string]$Content
    )
    $path = Join-Path $binDir "$Name.cmd"
    [IO.File]::WriteAllText($path, $Content, [Text.UTF8Encoding]::new($false))
}

Write-CmdWrapper "llm" @"
@echo off
"$venvPython" "$repoRoot\llm" %*
exit /b %ERRORLEVEL%
"@

foreach ($agent in @("claude", "codex", "hermes")) {
    Write-CmdWrapper "$agent-local" @"
@echo off
call "$binDir\llm.cmd" agent $agent -- %*
exit /b %ERRORLEVEL%
"@
}

$pathEntries = ($env:Path -split ";") | ForEach-Object { $_.TrimEnd("\") }
if ($AddToPath -and ($pathEntries -notcontains $binDir.TrimEnd("\"))) {
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $newPath = if ($userPath) { "$userPath;$binDir" } else { $binDir }
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    $env:Path = "$env:Path;$binDir"
    Write-Host "Added $binDir to the user PATH."
}

Write-Host "Windows installation complete."
Write-Host "  Repository : $repoRoot"
Write-Host "  Python     : $venvPython"
Write-Host "  Commands   : $binDir"
if (-not $AddToPath) {
    Write-Host "Run this script with -AddToPath, or add $binDir to PATH manually."
}
Write-Host ""
Write-Host "Next:"
Write-Host "  .\llm.cmd doctor"
Write-Host "  .\llm.cmd build llama-cpp"
Write-Host "  .\llm.cmd start llama-cpp <model-name>"
