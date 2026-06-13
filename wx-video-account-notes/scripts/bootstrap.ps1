param(
    [switch]$PruneCache
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'common.ps1')

$skillRoot = Get-SkillRoot
$runtimeRoot = Ensure-Directory (Get-RuntimeRoot)
$runtimeUvDir = Ensure-Directory (Join-Path $runtimeRoot 'uv')
$runtimePythonDir = Ensure-Directory (Join-Path $runtimeRoot 'python')
$runtimeLogsDir = Ensure-Directory (Join-Path $runtimeRoot 'logs')
$runtimeCacheDir = Ensure-Directory (Join-Path $runtimeRoot 'cache')
$runtimeToolsDir = Ensure-Directory (Join-Path $runtimeRoot 'tools')
$runtimeModelsDir = Ensure-Directory (Join-Path $runtimeRoot 'models')

$uvCommand = Get-UvCommand
if (-not $uvCommand) {
    Write-Info 'uv not found, downloading private copy from GitHub releases.'
    $uvZipPath = Join-Path $runtimeCacheDir 'uv-windows-x86_64.zip'
    $uvZipUrl = 'https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip'
    Invoke-WebRequest -Uri $uvZipUrl -OutFile $uvZipPath
    Expand-Archive -LiteralPath $uvZipPath -DestinationPath $runtimeUvDir -Force

    $downloadedUv = Get-ChildItem -LiteralPath $runtimeUvDir -Filter 'uv.exe' -Recurse | Select-Object -First 1
    if (-not $downloadedUv) {
        throw 'Downloaded uv archive did not contain uv.exe'
    }

    Copy-Item -LiteralPath $downloadedUv.FullName -Destination (Join-Path $runtimeUvDir 'uv.exe') -Force
    $uvCommand = Join-Path $runtimeUvDir 'uv.exe'
}

$privatePython = Get-PrivatePython
if (-not $privatePython) {
    Write-Info 'Installing managed Python with uv.'
    Invoke-NativeCommand -FilePath $uvCommand -Arguments @('python', 'install', '3.11', '--install-dir', $runtimePythonDir)

    $privatePython = Get-PrivatePython
    if (-not $privatePython) {
        throw 'uv finished but private python.exe was not found.'
    }
}

$venvPython = Get-VenvPython
if (-not $venvPython) {
    Write-Info 'Creating private virtual environment.'
    Invoke-NativeCommand -FilePath $uvCommand -Arguments @('venv', (Join-Path $runtimeRoot '.venv'), '--python', $privatePython)
    $venvPython = Get-VenvPython
}

Write-Info 'Syncing Python dependencies into private virtual environment.'
Invoke-NativeCommand -FilePath $uvCommand -Arguments @('pip', 'install', '--python', $venvPython, '--link-mode', 'copy', '-r', (Join-Path $skillRoot 'runtime\requirements.txt'))

Write-Info 'Ensuring declared runtime assets are present.'
$env:PYTHONPATH = $skillRoot
$bootstrapArgs = @((Join-Path $skillRoot 'runtime\bootstrap.py'), '--skill-root', $skillRoot)
if ($PruneCache) {
    $bootstrapArgs += '--prune-cache'
}
Invoke-NativeCommand -FilePath $venvPython -Arguments $bootstrapArgs

Write-Info 'Removing downloaded asset archives (already extracted).'
Remove-Item -LiteralPath (Join-Path $runtimeRoot 'cache') -Recurse -Force -ErrorAction SilentlyContinue

Write-Info 'Bootstrap complete.'
