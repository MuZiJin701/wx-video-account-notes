param(
    [Parameter(Mandatory = $true)][string]$ShareUrl,
    [Parameter(Mandatory = $false)][string]$OutputDir
)

. (Join-Path $PSScriptRoot 'common.ps1')
$skillRoot = Get-SkillRoot
$runtimeRoot = Get-RuntimeRoot
$uvCommand = Get-UvCommand
$venvPython = Get-VenvPython
if (-not $uvCommand -or -not $venvPython) { throw 'Private runtime is not initialized. Run scripts/bootstrap.ps1 first.' }

$env:PYTHONPATH = $skillRoot
$env:UV_PROJECT_ENVIRONMENT = Join-Path $runtimeRoot '.venv'
$arguments = @('run', '--locked', '--project', $skillRoot, 'python', '-m', 'runtime.pipeline', '--skill-root', $skillRoot, '--share-url', $ShareUrl)
if ($OutputDir) { $arguments += @('--output-dir', $OutputDir) }
Invoke-NativeCommand $uvCommand $arguments
