param(
    [ValidateSet("auto", "ON", "OFF")]
    [string]$Cuda = "auto",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:LOCAL_LLM_AGENT_ROOT = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
. (Join-Path $env:LOCAL_LLM_AGENT_ROOT "scripts\common\env.ps1")

if ($Cuda -eq "auto" -and $env:LLAMA_CUDA) {
    $Cuda = $env:LLAMA_CUDA
}
if ($Cuda -notin @("auto", "ON", "OFF")) {
    throw "Invalid LLAMA_CUDA value '$Cuda' (use auto, ON, or OFF)."
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "git is required."
}
if (-not (Get-Command cmake -ErrorAction SilentlyContinue)) {
    throw "CMake is required. Install it with: winget install --id Kitware.CMake -e"
}

if ($Cuda -eq "auto") {
    $Cuda = if ((Get-Command nvcc -ErrorAction SilentlyContinue) -or $env:CUDA_PATH) {
        "ON"
    } else {
        "OFF"
    }
}

$source = Join-Path $env:LLAMA_CPP_ROOT "src"
$build = Join-Path $env:LLAMA_CPP_ROOT "build"

function Invoke-Step {
    param([string[]]$Arguments)
    Write-Host "+ $($Arguments -join ' ')"
    if (-not $DryRun) {
        $command = $Arguments[0]
        $rest = @($Arguments | Select-Object -Skip 1)
        & $command @rest
        if ($LASTEXITCODE -ne 0) {
            throw "Command failed with exit code $LASTEXITCODE: $($Arguments -join ' ')"
        }
    }
}

New-Item -ItemType Directory -Force -Path $env:LLAMA_CPP_ROOT | Out-Null
if (-not (Test-Path (Join-Path $source ".git"))) {
    Invoke-Step @("git", "clone", "--depth", "1", "https://github.com/ggml-org/llama.cpp.git", $source)
} else {
    Invoke-Step @("git", "-C", $source, "pull", "--ff-only")
}

Invoke-Step @(
    "cmake",
    "-B", $build,
    "-S", $source,
    "-DGGML_CUDA=$Cuda",
    "-DCMAKE_BUILD_TYPE=Release"
)
Invoke-Step @("cmake", "--build", $build, "--config", "Release", "--parallel")

$binaryCandidates = @(
    (Join-Path $build "bin\Release\llama-server.exe"),
    (Join-Path $build "bin\llama-server.exe")
)
$binary = $binaryCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($binary) {
    $env:LLAMA_SERVER_BIN = $binary
}
Write-Host ""
Write-Host "llama.cpp build path: $build"
Write-Host "CUDA: $Cuda"
if ($binary) {
    Write-Host "llama-server: $binary"
}
