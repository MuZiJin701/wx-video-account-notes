. (Join-Path $PSScriptRoot 'common.ps1')
$skillRoot = Get-SkillRoot
$venvPython = Get-VenvPython
if (-not $venvPython) { throw 'Private runtime is not initialized. Run scripts/bootstrap.ps1 first.' }
$env:PYTHONPATH = $skillRoot
& $venvPython (Join-Path $skillRoot 'runtime\verify.py') '--skill-root' $skillRoot
exit $LASTEXITCODE
