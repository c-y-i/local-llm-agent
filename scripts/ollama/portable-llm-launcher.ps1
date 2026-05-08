param()

$ErrorActionPreference = "Stop"

function Get-PortableOs {
    if ([System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform([System.Runtime.InteropServices.OSPlatform]::Windows)) {
        return "windows"
    }
    if ([System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform([System.Runtime.InteropServices.OSPlatform]::OSX)) {
        return "darwin"
    }
    if ([System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform([System.Runtime.InteropServices.OSPlatform]::Linux)) {
        return "linux"
    }
    return [System.Environment]::OSVersion.Platform.ToString().ToLowerInvariant()
}

function Get-PortableArch {
    switch ([System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString().ToLowerInvariant()) {
        "x64" { return "amd64" }
        "arm64" { return "arm64" }
        default { return [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString().ToLowerInvariant() }
    }
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..\..")
$parent = Split-Path -Parent $repoRoot

if (-not $env:OLLAMA_MODELS) {
    $env:OLLAMA_MODELS = Join-Path $parent "Ollama\models\llm"
}
if (-not $env:OLLAMA_HOST) {
    $env:OLLAMA_HOST = "127.0.0.1:11434"
}
if (-not $env:OLLAMA_KEEP_ALIVE) {
    $env:OLLAMA_KEEP_ALIVE = "10m"
}
if (-not $env:OLLAMA_NO_CLOUD) {
    $env:OLLAMA_NO_CLOUD = "1"
}
if (-not $env:OLLAMA_NUM_PARALLEL) {
    $env:OLLAMA_NUM_PARALLEL = "1"
}

$os = Get-PortableOs
$arch = Get-PortableArch
$exe = if ($os -eq "windows") { "ollama.exe" } else { "ollama" }
$bundled = Join-Path $parent "bin\ollama\$os-$arch\$exe"

if ($env:OLLAMA_BIN) {
    $ollamaBin = $env:OLLAMA_BIN
} elseif (Test-Path $bundled) {
    $ollamaBin = $bundled
} else {
    $cmd = Get-Command ollama -ErrorAction SilentlyContinue
    if ($cmd) {
        $ollamaBin = $cmd.Source
    } else {
        Write-Error @"
No compatible Ollama binary found.

Expected bundled binary:
  $bundled

Options:
  1. Install Ollama on this host and rerun this launcher.
  2. Put a matching Ollama binary under bin\ollama\$os-$arch\.
  3. Set OLLAMA_BIN to a matching Ollama executable.
"@
    }
}

$hostPort = $env:OLLAMA_HOST -replace '^https?://', ''
$portText = ($hostPort -split ':')[-1]
$port = 0
if ([int]::TryParse($portText, [ref]$port)) {
    try {
        $listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($listener) {
            Write-Error "Port $port is already in use. Set OLLAMA_HOST=127.0.0.1:11435 and retry."
        }
    } catch {
        # Get-NetTCPConnection is Windows-specific; skip this check elsewhere.
    }
}

Write-Host "Portable LLM Launcher"
Write-Host "  binary        : $ollamaBin"
Write-Host "  OLLAMA_MODELS : $env:OLLAMA_MODELS"
Write-Host "  OLLAMA_HOST   : $env:OLLAMA_HOST"
Write-Host ""
Write-Host "In another terminal:"
Write-Host "  `$env:OLLAMA_HOST='$env:OLLAMA_HOST'; & '$ollamaBin' list"
Write-Host "  `$env:OLLAMA_HOST='$env:OLLAMA_HOST'; & '$ollamaBin' run qwen3:4b"
Write-Host ""

& $ollamaBin serve
