<#
Shared helpers for setup.ps1 and start.ps1 (YT-MP3 on Windows).
Written for Windows PowerShell 5.1, which every Windows 10 and 11 PC has.
Keep this file plain ASCII: PowerShell 5.1 misreads other characters.
#>

$ErrorActionPreference = 'Stop'

# Folders, worked out from where this file is (scripts\windows).
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Backend = Join-Path $Root 'backend'
$Venv = Join-Path $Backend '.venv'
$VenvPython = Join-Path $Venv 'Scripts\python.exe'
$Dist = Join-Path $Root 'dist'
$BackendEnv = Join-Path $Backend '.env'
$FrontendEnv = Join-Path $Root '.env.local'

# The app runs at this address. Supabase must list it under
# Authentication > URL Configuration > Redirect URLs (see INSTALL.md).
$Port = 8000
$AppUrl = "http://localhost:$Port"
# Health checks use the IPv4 address the backend listens on; on Windows,
# "localhost" may try IPv6 (::1) first.
$HealthUrl = "http://127.0.0.1:$Port/health"

function Write-Step([string]$Text) {
    Write-Host ''
    Write-Host "==> $Text" -ForegroundColor Cyan
}

function Write-Ok([string]$Text) {
    Write-Host "    $Text" -ForegroundColor Green
}

function Write-Note([string]$Text) {
    Write-Host "    $Text" -ForegroundColor Yellow
}

function Stop-WithMessage([string]$Text) {
    Write-Host ''
    Write-Host "Stopped: $Text" -ForegroundColor Red
    Write-Host 'Nothing in the YT-MP3 folder was deleted. Fix the problem above and run this again.'
    exit 1
}

# Programs installed a moment ago aren't on this window's PATH yet:
# read it again from the registry.
function Update-PathFromRegistry {
    $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$machine;$user"
}

function Test-Command([string]$Name) {
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

# Returns the command for Python 3.10 or newer as an array, for example
# @('py', '-3') or @('python'), or $null when there isn't one.
# (Windows has a "python" that only opens the Microsoft Store; running it
# fails, so it is skipped.)
function Find-Python {
    $candidates = @()
    if (Test-Command 'py') { $candidates += , @('py', '-3') }
    if (Test-Command 'python') { $candidates += , @('python') }

    foreach ($candidate in $candidates) {
        $exe = $candidate[0]
        $extra = @($candidate | Select-Object -Skip 1)
        try {
            $version = & $exe @extra -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
            if ($LASTEXITCODE -eq 0 -and "$version" -match '^(\d+)\.(\d+)$') {
                if ([int]$Matches[1] -eq 3 -and [int]$Matches[2] -ge 10) {
                    return , $candidate
                }
            }
        } catch {
            # Not a working Python; try the next one.
        }
    }
    return $null
}

# Node.js must match package.json: 22.18 or newer in the 22 line, or 24.12+.
# Returns @{ Found; Version; Ok }.
function Get-NodeStatus {
    $status = @{ Found = $false; Version = ''; Ok = $false }
    if (-not (Test-Command 'node')) { return $status }
    try {
        $version = "$(& node --version 2>$null)".Trim()
    } catch {
        return $status
    }
    $status.Found = $true
    $status.Version = $version
    if ($version -match '^v(\d+)\.(\d+)') {
        $major = [int]$Matches[1]
        $minor = [int]$Matches[2]
        $status.Ok = (($major -eq 22) -and ($minor -ge 18)) -or
                     (($major -eq 24) -and ($minor -ge 12)) -or
                     ($major -gt 24)
    }
    return $status
}

# Reads KEY=value lines from an .env file into a hashtable.
function Read-EnvFile([string]$Path) {
    $values = @{}
    if (-not (Test-Path -LiteralPath $Path)) { return $values }
    foreach ($line in Get-Content -LiteralPath $Path) {
        if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$') {
            $values[$Matches[1]] = $Matches[2]
        }
    }
    return $values
}

# Writes text as UTF-8 without a byte-order mark. (PowerShell 5.1's
# "-Encoding UTF8" adds one, which breaks the first setting in an .env file.)
function Write-TextFile([string]$Path, [string]$Text) {
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Text, $encoding)
}

# True when YT-MP3 already answers at $AppUrl.
function Test-AppRunning {
    try {
        $response = Invoke-WebRequest -Uri $HealthUrl -UseBasicParsing -TimeoutSec 2
        return ($response.StatusCode -eq 200)
    } catch {
        return $false
    }
}

# True when something (anything) is already using the port.
function Test-PortInUse {
    $listener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Loopback, $Port)
    try {
        $listener.Start()
        return $false
    } catch {
        return $true
    } finally {
        try { $listener.Stop() } catch { }
    }
}
