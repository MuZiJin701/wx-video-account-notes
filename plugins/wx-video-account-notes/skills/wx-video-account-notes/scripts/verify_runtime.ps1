Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'common.ps1')

$uv = Get-UvCommand
$python = Get-PrivatePython
$venvPython = Get-VenvPython
$runtimeRoot = Get-RuntimeRoot
$skillRoot = Get-SkillRoot
$targetUvVersion = Get-TargetUvVersion
$targetPythonVersion = Get-TargetPythonVersion
$pyprojectPath = Join-Path $skillRoot 'pyproject.toml'
$uvLockPath = Join-Path $skillRoot 'uv.lock'

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

Write-Info "target-uv-version: $targetUvVersion"
Write-Info "target-python-version: $targetPythonVersion"
Write-Info "pyproject: $(Test-Path -LiteralPath $pyprojectPath)"
Write-Info "uv-lock: $(Test-Path -LiteralPath $uvLockPath)"
Write-Info "private-uv: $([bool]$uv)"
if ($uv) {
    $uvVersionText = Get-CommandVersionText -FilePath $uv
    Write-Info "private-uv-path: $uv"
    Write-Info "private-uv-version: $uvVersionText"
    Write-Info "private-uv-target-match: $($uvVersionText -and $uvVersionText.Contains($targetUvVersion))"
}
Write-Info "private-python: $([bool]$python)"
if ($python) {
    $pythonVersionText = Get-CommandVersionText -FilePath $python
    Write-Info "private-python-path: $python"
    Write-Info "private-python-version: $pythonVersionText"
    Write-Info "private-python-target-match: $($pythonVersionText -and $pythonVersionText.Contains($targetPythonVersion))"
}
Write-Info "venv-python: $([bool]$venvPython)"
if ($venvPython) {
    $venvPythonVersionText = Get-CommandVersionText -FilePath $venvPython
    Write-Info "venv-python-path: $venvPython"
    Write-Info "venv-python-version: $venvPythonVersionText"
    Write-Info "venv-python-target-match: $($venvPythonVersionText -and $venvPythonVersionText.Contains($targetPythonVersion))"
}
Write-Info "tools-size-mb: $(Get-DirectorySizeMb (Join-Path $runtimeRoot 'tools'))"
Write-Info "cache-size-mb: $(Get-DirectorySizeMb (Join-Path $runtimeRoot 'cache'))"
Write-Info "venv-size-mb: $(Get-DirectorySizeMb (Join-Path $runtimeRoot '.venv'))"
Write-Info "models-size-mb: $(Get-DirectorySizeMb (Join-Path $runtimeRoot 'models'))"
