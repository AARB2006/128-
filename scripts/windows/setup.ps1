<#
YT-MP3 setup for Windows. Started by "Setup YT-MP3.bat".

What it does, in order:
  1. Makes sure Python 3.10+, Node.js and FFmpeg are installed (installs any
     that are missing with winget, Windows' own package installer).
  2. Saves the two public Supabase settings (backend\.env and .env.local):
     from an earlier setup, from supabase-public.env, or by asking once.
     No secret key is needed, and an old one is removed.
  3. Installs the backend's Python packages into backend\.venv.
  4. Installs the frontend's packages and builds the app into dist\.
  5. Puts a "YT-MP3" shortcut on the desktop.

Safe to run again (for example after updating YT-MP3): it keeps existing
settings and only installs what's missing. Plain ASCII only (see common.ps1).
#>

. (Join-Path $PSScriptRoot 'common.ps1')

$LogDir = Join-Path $Root 'logs'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
try { Start-Transcript -Path (Join-Path $LogDir 'setup.log') -Force | Out-Null } catch { }

Write-Host 'YT-MP3 setup' -ForegroundColor Cyan
Write-Host "Folder: $Root"
Write-Host 'This takes a few minutes the first time. Keep this window open until it says "Setup finished".'

# Files downloaded from the internet are marked as "blocked"; unblock ours.
Get-ChildItem -LiteralPath $PSScriptRoot -File | Unblock-File -ErrorAction SilentlyContinue


# ---- 1. Programs YT-MP3 needs ---------------------------------------------------

function Install-WithWinget([string]$Id, [string]$Name) {
    if (-not (Test-Command 'winget')) {
        Stop-WithMessage ("$Name is missing, and winget (Windows' package installer) isn't available " +
            'to install it. Install "App Installer" from the Microsoft Store, or install ' +
            "$Name yourself (see INSTALL.md), then run Setup again.")
    }
    Write-Host "    Installing $Name. Windows may ask for permission; choose Yes." -ForegroundColor Yellow
    & winget install --id $Id --exact --source winget --accept-package-agreements --accept-source-agreements --silent
    if ($LASTEXITCODE -ne 0) {
        Write-Note "winget finished with code $LASTEXITCODE; checking whether $Name works anyway."
    }
    Update-PathFromRegistry
}

Write-Step 'Checking the programs YT-MP3 needs'
Update-PathFromRegistry

$python = Find-Python
if ($null -eq $python) {
    Install-WithWinget 'Python.Python.3.13' 'Python 3.13'
    $python = Find-Python
    if ($null -eq $python) {
        Stop-WithMessage ('Python was installed but this window cannot see it yet. ' +
            'Close this window and run Setup again.')
    }
}
$pythonExe = $python[0]
$pythonArgs = @($python | Select-Object -Skip 1)
Write-Ok "Python: $(& $pythonExe @pythonArgs --version)"

$node = Get-NodeStatus
if (-not $node.Ok) {
    if ($node.Found) {
        Write-Note "Node.js $($node.Version) is too old (YT-MP3 needs 22.18+ or 24.12+). Updating it."
    }
    Install-WithWinget 'OpenJS.NodeJS.LTS' 'Node.js (LTS)'
    $node = Get-NodeStatus
    if (-not $node.Ok) {
        if ($node.Found) {
            Stop-WithMessage ("Node.js $($node.Version) is still too old. Install the current LTS " +
                'version from https://nodejs.org, then run Setup again.')
        }
        Stop-WithMessage ('Node.js was installed but this window cannot see it yet. ' +
            'Close this window and run Setup again.')
    }
}
Write-Ok "Node.js: $($node.Version)"

if (-not (Test-Command 'ffmpeg')) {
    Install-WithWinget 'Gyan.FFmpeg' 'FFmpeg'
    if (-not (Test-Command 'ffmpeg')) {
        Stop-WithMessage ('FFmpeg was installed but this window cannot see it yet. ' +
            'Close this window and run Setup again.')
    }
}
Write-Ok 'FFmpeg: found'


# ---- 2. Supabase settings -------------------------------------------------------
# Only the two PUBLIC settings are needed: the project URL and the publishable
# key. YT-MP3 needs no secret key on this computer (see README, section 6).
# They come from, in order: backend\.env (if set up before), the file
# supabase-public.env in the YT-MP3 folder (if the project includes it), or
# a question.

function Read-Setting([string]$Prompt, [string]$Pattern, [string]$Example) {
    while ($true) {
        $value = (Read-Host $Prompt).Trim()
        if ($value -match $Pattern) { return $value }
        Write-Note "That doesn't look right. It should look like: $Example"
    }
}

$urlPattern = '^https://[a-z0-9-]+\.supabase\.co/?$'
$publishablePattern = '^sb_publishable_[A-Za-z0-9_-]+$'

function Test-Settings($Values) {
    return ("$($Values['SUPABASE_URL'])" -match $urlPattern) -and
           ("$($Values['SUPABASE_PUBLISHABLE_KEY'])" -match $publishablePattern)
}

Write-Step 'Supabase settings'
$fromBackend = Read-EnvFile $BackendEnv
$fromProject = Read-EnvFile (Join-Path $Root 'supabase-public.env')

if (Test-Settings $fromBackend) {
    Write-Ok 'Using the settings already in backend\.env.'
    $settings = $fromBackend
} elseif (Test-Settings $fromProject) {
    Write-Ok 'Using the settings in supabase-public.env.'
    $settings = $fromProject
} else {
    Write-Host '    Find these in Supabase: the project URL, and Project Settings > API Keys > Publishable key.'
    Write-Host '    Both are public; no secret key is needed.'
    $settings = @{
        'SUPABASE_URL' = Read-Setting '    Supabase project URL' $urlPattern 'https://abcd1234.supabase.co'
        'SUPABASE_PUBLISHABLE_KEY' = Read-Setting '    Publishable key' $publishablePattern 'sb_publishable_...'
    }
}
$supabaseUrl = "$($settings['SUPABASE_URL'])".TrimEnd('/')
$publishableKey = "$($settings['SUPABASE_PUBLISHABLE_KEY'])"

# An older version of YT-MP3 kept the secret key in backend\.env. Remove just
# that line (other settings stay), so the key is no longer on this computer.
if ((Test-Settings $fromBackend) -and $fromBackend.ContainsKey('SUPABASE_SECRET_KEY')) {
    $kept = @(Get-Content -LiteralPath $BackendEnv | Where-Object { $_ -notmatch '^\s*SUPABASE_SECRET_KEY\s*=' })
    Write-TextFile $BackendEnv (($kept -join "`r`n") + "`r`n")
    Write-Ok 'Removed the old secret key from backend\.env (YT-MP3 no longer needs it).'
}

# Write backend\.env when it's new or incomplete.
if (-not (Test-Settings $fromBackend)) {
    $backendSettings = @(
        '# YT-MP3 backend settings for this computer. Written by Setup.',
        '# Public values only: YT-MP3 needs no secret key.',
        '# Other settings and their defaults: see backend\.env.example.',
        "SUPABASE_URL=$supabaseUrl",
        "SUPABASE_PUBLISHABLE_KEY=$publishableKey",
        "ALLOWED_ORIGINS=$AppUrl,http://127.0.0.1:$Port",
        ''
    ) -join "`r`n"
    Write-TextFile $BackendEnv $backendSettings
    Write-Ok 'Saved backend\.env.'
}

if (Test-Path -LiteralPath $FrontendEnv) {
    Write-Ok 'Using the existing .env.local.'
} else {
    $frontendSettings = @(
        '# YT-MP3 frontend settings. Written by Setup. Public values only.',
        "VITE_SUPABASE_URL=$supabaseUrl",
        "VITE_SUPABASE_PUBLISHABLE_KEY=$publishableKey",
        ''
    ) -join "`r`n"
    Write-TextFile $FrontendEnv $frontendSettings
    Write-Ok 'Saved .env.local.'
}


# ---- 3. Backend packages --------------------------------------------------------

Write-Step 'Installing the backend (Python packages)'
if (-not (Test-Path -LiteralPath $VenvPython)) {
    & $pythonExe @pythonArgs -m venv $Venv
    if ($LASTEXITCODE -ne 0) { Stop-WithMessage 'Could not create backend\.venv.' }
}
& $VenvPython -m pip install --disable-pip-version-check --quiet --upgrade pip
& $VenvPython -m pip install --disable-pip-version-check -r (Join-Path $Backend 'requirements.txt')
if ($LASTEXITCODE -ne 0) {
    Stop-WithMessage 'Installing the Python packages failed. Check the internet connection and run Setup again.'
}
Write-Ok 'Backend ready.'


# ---- 4. Frontend packages and build ---------------------------------------------

Write-Step 'Building the app (this is the slow part)'
Push-Location $Root
try {
    & npm.cmd ci --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) {
        Stop-WithMessage 'Installing the frontend packages failed. Check the internet connection and run Setup again.'
    }
    # "/" = the app talks to the same address it was opened from.
    $env:VITE_API_BASE_URL = '/'
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) { Stop-WithMessage 'Building the app failed. See the messages above.' }
} finally {
    Remove-Item Env:\VITE_API_BASE_URL -ErrorAction SilentlyContinue
    Pop-Location
}
Write-Ok 'App built.'


# ---- 5. Desktop shortcut --------------------------------------------------------

Write-Step 'Adding a desktop shortcut'
try {
    $desktop = [Environment]::GetFolderPath('Desktop')
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut((Join-Path $desktop 'YT-MP3.lnk'))
    $shortcut.TargetPath = Join-Path $Root 'Start YT-MP3.bat'
    $shortcut.WorkingDirectory = $Root
    $shortcut.Description = 'Start YT-MP3'
    $shortcut.Save()
    Write-Ok 'Added "YT-MP3" to the desktop.'
} catch {
    Write-Note 'Could not add the shortcut. Start YT-MP3 with "Start YT-MP3.bat" in this folder instead.'
}

Write-Host ''
Write-Host 'Setup finished.' -ForegroundColor Green
Write-Host 'Start YT-MP3 with the "YT-MP3" shortcut on the desktop.'
try { Stop-Transcript | Out-Null } catch { }
