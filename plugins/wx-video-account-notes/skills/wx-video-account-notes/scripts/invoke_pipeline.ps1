param(
    [Parameter(Mandatory = $true)]
    [string]$ShareUrl,

    [Parameter(Mandatory = $false)]
    [string]$OutputDir
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'common.ps1')

$uvCommand = Get-UvCommand
$venvPython = Get-VenvPython
if (-not $uvCommand -or -not $venvPython) {
    throw 'Private runtime is not initialized. Run scripts/bootstrap.ps1 first.'
}

$skillRoot = Get-SkillRoot
$runtimeRoot = Get-RuntimeRoot
$env:PYTHONPATH = $skillRoot
$env:UV_PROJECT_ENVIRONMENT = Join-Path $runtimeRoot '.venv'
$args = @(
    'run', '--locked',
    '--project', $skillRoot,
    'python', '-m', 'runtime.pipeline',
    '--skill-root', $skillRoot,
    '--share-url', $ShareUrl
)

if ($OutputDir) {
    $args += @('--output-dir', $OutputDir)
}

Invoke-NativeCommand -FilePath $uvCommand -Arguments $args
