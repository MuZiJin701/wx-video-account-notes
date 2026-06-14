Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'common.ps1')

$uv = Get-UvCommand
$python = Get-PrivatePython
$venvPython = Get-VenvPython
$runtimeRoot = Get-RuntimeRoot

function Get-DirectorySizeMb {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return 'missing'
    }

    $files = @(Get-ChildItem -LiteralPath $Path -Recurse -File -ErrorAction SilentlyContinue)
    if ($files.Count -eq 0) {
        return 0
    }

    $bytes = ($files | Measure-Object Length -Sum).Sum
    return [math]::Round(($bytes / 1MB), 2)
}

Write-Info "uv: $([bool]$uv)"
Write-Info "private-python: $([bool]$python)"
Write-Info "venv-python: $([bool]$venvPython)"
Write-Info "tools-size-mb: $(Get-DirectorySizeMb (Join-Path $runtimeRoot 'tools'))"
Write-Info "cache-size-mb: $(Get-DirectorySizeMb (Join-Path $runtimeRoot 'cache'))"
Write-Info "venv-size-mb: $(Get-DirectorySizeMb (Join-Path $runtimeRoot '.venv'))"
Write-Info "models-size-mb: $(Get-DirectorySizeMb (Join-Path $runtimeRoot 'models'))"
