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
$venvDir = Join-Path $runtimeRoot '.venv'

$targetUvVersion = Get-TargetUvVersion
$targetPythonVersion = Get-TargetPythonVersion

$uvCommand = Get-UvCommand
if ($uvCommand) {
    $uvVersionText = Get-CommandVersionText -FilePath $uvCommand
    if (-not $uvVersionText -or -not $uvVersionText.Contains($targetUvVersion)) {
        Write-Info "Private uv exists but is not version $targetUvVersion; replacing it."
        Remove-Item -LiteralPath $runtimeUvDir -Recurse -Force
        $runtimeUvDir = Ensure-Directory (Join-Path $runtimeRoot 'uv')
        $uvCommand = $null
    }
}

if (-not $uvCommand) {
    Write-Info "Downloading private uv $targetUvVersion from GitHub releases."
    $uvZipPath = Join-Path $runtimeCacheDir "uv-$targetUvVersion-windows-x86_64.zip"
    $uvZipUrl = "https://github.com/astral-sh/uv/releases/download/$targetUvVersion/uv-x86_64-pc-windows-msvc.zip"
    Invoke-WebRequest -Uri $uvZipUrl -OutFile $uvZipPath
    Expand-Archive -LiteralPath $uvZipPath -DestinationPath $runtimeUvDir -Force

    $downloadedUv = Get-ChildItem -LiteralPath $runtimeUvDir -Filter 'uv.exe' -Recurse | Select-Object -First 1
    if (-not $downloadedUv) {
        throw 'Downloaded uv archive did not contain uv.exe'
    }

    $uvCommand = Join-Path $runtimeUvDir 'uv.exe'
    if ($downloadedUv.FullName -ne $uvCommand) {
        Copy-Item -LiteralPath $downloadedUv.FullName -Destination $uvCommand -Force
    }
}

$uvVersionText = Get-CommandVersionText -FilePath $uvCommand
if (-not $uvVersionText -or -not $uvVersionText.Contains($targetUvVersion)) {
    throw "Private uv version check failed. Expected $targetUvVersion, got: $uvVersionText"
}

$privatePython = Get-PrivatePython
if ($privatePython) {
    $privatePythonVersionText = Get-CommandVersionText -FilePath $privatePython
    if (-not $privatePythonVersionText -or -not $privatePythonVersionText.Contains($targetPythonVersion)) {
        Write-Info "Private Python exists but is not version $targetPythonVersion; installing target Python."
        $privatePython = $null
    }
}

if (-not $privatePython) {
    Write-Info "Installing managed Python $targetPythonVersion with private uv."
    Invoke-NativeCommand -FilePath $uvCommand -Arguments @('python', 'install', $targetPythonVersion, '--install-dir', $runtimePythonDir)

    $privatePython = Get-PrivatePython
    if (-not $privatePython) {
        throw 'uv finished but private python.exe was not found.'
    }
}

$privatePythonVersionText = Get-CommandVersionText -FilePath $privatePython
if (-not $privatePythonVersionText -or -not $privatePythonVersionText.Contains($targetPythonVersion)) {
    throw "Private Python version check failed. Expected $targetPythonVersion, got: $privatePythonVersionText"
}

$venvPython = Get-VenvPython
if ($venvPython) {
    $venvPythonVersionText = Get-CommandVersionText -FilePath $venvPython
    if (-not $venvPythonVersionText -or -not $venvPythonVersionText.Contains($targetPythonVersion)) {
        Write-Info "Private virtual environment is not Python $targetPythonVersion; recreating it with uv sync."
        Remove-Item -LiteralPath $venvDir -Recurse -Force
        $venvPython = $null
    }
}

Write-Info 'Syncing locked Python project into private virtual environment.'
$env:UV_PROJECT_ENVIRONMENT = $venvDir
Invoke-NativeCommand -FilePath $uvCommand -Arguments @('sync', '--locked', '--project', $skillRoot, '--python', $privatePython, '--link-mode', 'copy')

$venvPython = Get-VenvPython
if (-not $venvPython -or -not (Test-Path -LiteralPath $venvPython)) {
    throw "Private virtual environment Python was not found after uv sync: $venvPython"
}

$venvPythonVersionText = Get-CommandVersionText -FilePath $venvPython
if (-not $venvPythonVersionText -or -not $venvPythonVersionText.Contains($targetPythonVersion)) {
    throw "Private virtual environment version check failed. Expected $targetPythonVersion, got: $venvPythonVersionText"
}

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
