<#
Starts YT-MP3 on Windows. Started by "Start YT-MP3.bat" (and the desktop
shortcut that Setup makes).

  1. Checks that Setup has been run and the needed programs are there.
  2. Updates yt-dlp (YouTube changes often; an old yt-dlp is the usual
     reason imports and exports stop working).
  3. Starts the backend, which also serves the app, at http://localhost:8000
     (reachable only from this computer).
  4. Opens the app in the browser.

The app runs while this window is open. Close the window to stop it.
Plain ASCII only (see common.ps1).
#>

. (Join-Path $PSScriptRoot 'common.ps1')

Write-Host 'Starting YT-MP3...' -ForegroundColor Cyan

# Already running (for example, the shortcut was clicked twice)? Just open it.
if (Test-AppRunning) {
    Write-Ok 'YT-MP3 is already running. Opening it in the browser.'
    Start-Process $AppUrl
    exit 0
}

# ---- 1. Checks --------------------------------------------------------------------

$missing = @()
if (-not (Test-Path -LiteralPath $VenvPython)) { $missing += 'backend\.venv' }
if (-not (Test-Path -LiteralPath (Join-Path $Dist 'index.html'))) { $missing += 'dist\index.html' }
if (-not (Test-Path -LiteralPath $BackendEnv)) { $missing += 'backend\.env' }
if ($missing.Count -gt 0) {
    Stop-WithMessage ("YT-MP3 isn't set up on this computer yet (missing: $($missing -join ', ')). " +
        'Run "Setup YT-MP3.bat" first.')
}

Update-PathFromRegistry
if (-not (Get-NodeStatus).Ok) {
    Stop-WithMessage 'Node.js is missing or too old (yt-dlp needs it to read YouTube). Run "Setup YT-MP3.bat" again.'
}
if (-not (Test-Command 'ffmpeg')) {
    Write-Note 'FFmpeg was not found: importing works, but exporting playlists will not. Run Setup again to fix it.'
}

if (Test-PortInUse) {
    Stop-WithMessage ("Another program is using port $Port, so YT-MP3 can't start. " +
        'Close that program (or restart the computer) and try again.')
}

# ---- 2. Keep yt-dlp up to date ------------------------------------------------------

Write-Step 'Checking for a yt-dlp update'
& $VenvPython -m pip install --disable-pip-version-check --quiet --upgrade 'yt-dlp[default]'
if ($LASTEXITCODE -eq 0) {
    Write-Ok "yt-dlp $(& $VenvPython -m yt_dlp --version)"
} else {
    Write-Note 'Could not check for an update (no internet?). Starting with the installed version.'
}

# ---- 3. Start the backend, which also serves the app ----------------------------------

Write-Step "Starting YT-MP3 at $AppUrl"
$env:FRONTEND_DIST_DIR = $Dist
$server = Start-Process -FilePath $VenvPython `
    -ArgumentList @('-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', "$Port") `
    -WorkingDirectory $Backend -NoNewWindow -PassThru

# Wait until it answers (up to a minute).
$ready = $false
for ($i = 0; $i -lt 60; $i++) {
    if ($server.HasExited) { break }
    if (Test-AppRunning) { $ready = $true; break }
    Start-Sleep -Seconds 1
}
if (-not $ready) {
    if (-not $server.HasExited) { Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue }
    Stop-WithMessage 'YT-MP3 did not start. The messages above say why.'
}

# ---- 4. Open it ----------------------------------------------------------------------

Start-Process $AppUrl
Write-Host ''
Write-Host "YT-MP3 is running at $AppUrl" -ForegroundColor Green
Write-Host 'Keep this window open while you use YT-MP3. Close it to stop YT-MP3.'
Write-Host ''

$server.WaitForExit()
