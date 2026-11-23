$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$failed = $false
foreach ($script in Get-ChildItem $root -Recurse -Filter "*.ps1") {
    $tokens = $null
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile(
        $script.FullName,
        [ref]$tokens,
        [ref]$errors
    ) | Out-Null
    if ($errors.Count -gt 0) {
        $failed = $true
        Write-Host "PowerShell syntax errors: $($script.FullName)"
        $errors | ForEach-Object {
            Write-Host ("  line {0}: {1}" -f $_.Extent.StartLineNumber, $_.Message)
        }
    }
}

if ($failed) {
    exit 1
}
Write-Host "PowerShell syntax: OK"
