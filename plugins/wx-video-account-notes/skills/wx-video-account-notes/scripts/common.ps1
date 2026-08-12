Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-SkillRoot { return Split-Path -Parent $PSScriptRoot }
function Get-PlatformId {
    if ($env:PROCESSOR_ARCHITECTURE -ne 'AMD64' -and $env:PROCESSOR_ARCHITEW6432 -ne 'AMD64') {
        throw 'Unsupported architecture. Supported architecture: x64.'
    }
    return 'windows-x64'
}
function Get-RuntimeRoot { Get-PlatformId | Out-Null; return Join-Path (Get-SkillRoot) '.runtime\windows-x64' }
function Get-TargetUvVersion { return '0.11.25' }
function Get-TargetPythonVersion { return '3.13.14' }
function Get-UvArchive { return 'uv-x86_64-pc-windows-msvc.zip' }
function Get-UvUrl { return "https://releases.astral.sh/github/uv/releases/download/$(Get-TargetUvVersion)/$(Get-UvArchive)" }
function Get-UvSha256 { return '15bfd1423b7eaa7aae949922d4712ebaac2bb44a81af64ab59bbe007090cb0d0' }

function Ensure-Directory([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Path $Path | Out-Null }
    return (Resolve-Path -LiteralPath $Path).Path
}

function Get-CommandVersionText([string]$FilePath) {
    if (-not (Test-Path -LiteralPath $FilePath)) { return $null }
    $output = & $FilePath --version 2>$null
    if ($LASTEXITCODE -ne 0) { return $null }
    return ($output -join "`n")
}

function Get-UvCommand {
    $root = Join-Path (Get-RuntimeRoot) 'uv'
    $candidate = Get-ChildItem -LiteralPath $root -Filter 'uv.exe' -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($candidate) { return $candidate.FullName }
    return $null
}

function Ensure-Uv {
    $runtimeRoot = Get-RuntimeRoot
    $uvDir = Ensure-Directory (Join-Path $runtimeRoot 'uv')
    $cacheDir = Ensure-Directory (Join-Path $runtimeRoot 'cache')
    $uvCommand = Get-UvCommand
    if ($uvCommand -and ((Get-CommandVersionText $uvCommand) -notlike "*$(Get-TargetUvVersion)*")) {
        Remove-Item -LiteralPath $uvDir -Recurse -Force
        $uvDir = Ensure-Directory (Join-Path $runtimeRoot 'uv')
        $uvCommand = $null
    }
    if (-not $uvCommand) {
        $archive = Join-Path $cacheDir (Get-UvArchive)
        $temporary = "$archive.tmp"
        try {
            Write-Info "Downloading private uv $(Get-TargetUvVersion)."
            Invoke-WebRequest -Uri (Get-UvUrl) -OutFile $temporary
            if ((Get-FileHash -Algorithm SHA256 -LiteralPath $temporary).Hash.ToLowerInvariant() -ne (Get-UvSha256)) {
                throw 'uv checksum verification failed.'
            }
            Move-Item -LiteralPath $temporary -Destination $archive -Force
            Expand-Archive -LiteralPath $archive -DestinationPath $uvDir -Force
        } finally {
            Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue
        }
        $uvCommand = Get-UvCommand
        if (-not $uvCommand) { throw 'Downloaded uv archive did not contain uv.exe.' }
    }
    return $uvCommand
}

function Get-PrivatePython {
    $root = Join-Path (Get-RuntimeRoot) 'python'
    $target = Get-TargetPythonVersion
    $matching = Get-ChildItem -LiteralPath $root -Filter 'python.exe' -Recurse -ErrorAction SilentlyContinue |
        Where-Object { (Get-CommandVersionText $_.FullName) -like "*$target*" } |
        Select-Object -First 1
    if ($matching) { return $matching.FullName }
    return $null
}

function Get-VenvPython {
    $candidate = Join-Path (Get-RuntimeRoot) '.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $candidate) { return (Resolve-Path -LiteralPath $candidate).Path }
    return $null
}

function Invoke-NativeCommand([string]$FilePath, [string[]]$Arguments = @()) {
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Command failed with exit code ${LASTEXITCODE}: $FilePath $($Arguments -join ' ')" }
}

function Write-Info([string]$Message) { Write-Output "[wx-video-account-notes] $Message" }
