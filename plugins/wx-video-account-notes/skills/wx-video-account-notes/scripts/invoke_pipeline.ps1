param(
    [Parameter(Mandatory = $true)]
    [string]$ShareUrl,

    [Parameter(Mandatory = $false)]
    [string]$OutputDir
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'common.ps1')

$venvPython = Get-VenvPython
if (-not $venvPython) {
    throw 'Private runtime is not initialized. Run scripts/bootstrap.ps1 first.'
}

$skillRoot = Get-SkillRoot
$env:PYTHONPATH = $skillRoot
$args = @(
    '-m', 'runtime.pipeline',
    '--skill-root', $skillRoot,
    '--share-url', $ShareUrl
)

if ($OutputDir) {
    $args += @('--output-dir', $OutputDir)
}

Invoke-NativeCommand -FilePath $venvPython -Arguments $args
