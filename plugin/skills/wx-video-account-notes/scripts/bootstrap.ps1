param([switch]$PruneCache)

. (Join-Path $PSScriptRoot 'common.ps1')

$skillRoot = Get-SkillRoot
$runtimeRoot = Ensure-Directory (Get-RuntimeRoot)
$uvCommand = Ensure-Uv
$env:UV_PROJECT_ENVIRONMENT = Join-Path $runtimeRoot '.venv'
$env:UV_PYTHON_INSTALL_DIR = Join-Path $runtimeRoot 'python'
$env:PYTHONPATH = $skillRoot
$bootstrapArgs = @('run', '--locked', '--project', $skillRoot, '--python', (Get-TargetPythonVersion), '--link-mode', 'copy', (Join-Path $skillRoot 'runtime\bootstrap.py'), '--skill-root', $skillRoot, '--runtime-root', $runtimeRoot)
if ($PruneCache) { $bootstrapArgs += '--prune-cache' }
Invoke-NativeCommand $uvCommand $bootstrapArgs
Write-Info 'Bootstrap complete.'
