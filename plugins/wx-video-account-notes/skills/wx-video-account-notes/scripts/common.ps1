Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-SkillRoot {
    return Split-Path -Parent $PSScriptRoot
}

function Get-RuntimeRoot {
    return Join-Path (Get-SkillRoot) '.runtime'
}

function Ensure-Directory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }

    return (Resolve-Path -LiteralPath $Path).Path
}

function Write-Info {
    param([string]$Message)
    "[wx-video-account-notes] $Message"
}

function Get-TargetUvVersion {
    return '0.11.25'
}

function Get-TargetPythonVersion {
    return '3.13.14'
}

function Get-CommandVersionText {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath
    )

    if (-not (Test-Path -LiteralPath $FilePath)) {
        return $null
    }

    $output = & $FilePath --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        return $null
    }

    return ($output -join "`n")
}

function Get-UvCommand {
    $runtimeUv = Join-Path (Get-RuntimeRoot) 'uv\uv.exe'
    if (Test-Path -LiteralPath $runtimeUv) {
        return (Resolve-Path -LiteralPath $runtimeUv).Path
    }

    return $null
}

function Get-PrivatePython {
    $runtimePythonRoot = Join-Path (Get-RuntimeRoot) 'python'
    if (-not (Test-Path -LiteralPath $runtimePythonRoot)) {
        return $null
    }

    $targetVersion = Get-TargetPythonVersion
    $matchingCandidate = Get-ChildItem -LiteralPath $runtimePythonRoot -Filter 'python.exe' -Recurse -ErrorAction SilentlyContinue |
        Where-Object {
            $versionText = Get-CommandVersionText -FilePath $_.FullName
            $versionText -and $versionText.Contains($targetVersion)
        } |
        Select-Object -First 1
    if ($matchingCandidate) {
        return $matchingCandidate.FullName
    }

    $rootPython = Join-Path $runtimePythonRoot 'python.exe'
    $nestedCandidate = Get-ChildItem -LiteralPath $runtimePythonRoot -Filter 'python.exe' -Recurse -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -ne $rootPython } |
        Select-Object -First 1
    if ($nestedCandidate) {
        return $nestedCandidate.FullName
    }

    if (Test-Path -LiteralPath $rootPython) {
        return $rootPython
    }

    return $null
}

function Get-VenvPython {
    $candidate = Join-Path (Get-RuntimeRoot) '.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $candidate) {
        return (Resolve-Path -LiteralPath $candidate).Path
    }

    return $null
}

function Invoke-NativeCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,

        [Parameter(Mandatory = $false)]
        [string[]]$Arguments = @()
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $FilePath $($Arguments -join ' ')"
    }
}
