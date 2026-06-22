$TaskName = "GenshinImpactBrightnessChecker"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$CheckerScript = Join-Path $ScriptDir "genshin_window_checker.py"

# Find Python executable
$PythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $PythonExe) {
    Write-Error "Python not found in PATH. Please install Python or add it to PATH."
    pause
    exit 1
}

# ----- Check if task already exists -----
$existingTask = schtasks /query /tn $TaskName 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Task '$TaskName' already exists." -ForegroundColor Yellow
    $choice = Read-Host "Do you want to replace it? (y/n)"
    if ($choice -ne "y") {
        Write-Host "Exiting without changes."
        pause
        exit 0
    }
    Write-Host "Deleting existing task..."
    schtasks /delete /tn $TaskName /f
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to delete existing task."
        pause
        exit 1
    }
}

# ----- Create the task -----
Write-Host "Creating scheduled task '$TaskName'..." -ForegroundColor Cyan

# 1. We build the exact string using string formatting. 
# 2. \" escapes the quotes perfectly so the Task Scheduler registers the paths cleanly.
$CmdString = 'schtasks /create /tn "{0}" /tr "\"{1}\" \"{2}\"" /sc minute /mo 1 /f' -f $TaskName, $PythonExe, $CheckerScript

# 3. Use cmd.exe /c to run it, bypassing PowerShell's quote-stripping behavior completely!
cmd.exe /c $CmdString

# ----- Verify creation -----
if ($LASTEXITCODE -eq 0) {
    Write-Host "Task created successfully." -ForegroundColor Green
    
    # Double-check by querying
    $verify = schtasks /query /tn $TaskName 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[Verified] Task '$TaskName' exists in Task Scheduler." -ForegroundColor Green
        
        # Show task details
        Write-Host ""
        Write-Host "Task details:" -ForegroundColor Cyan
        schtasks /query /tn $TaskName /fo LIST | Select-String -Pattern "TaskName|Next Run Time|Status"
        
        Write-Host ""
        Write-Host "To manually run it now: schtasks /run /tn '$TaskName'" -ForegroundColor Yellow
        Write-Host "To delete it later: schtasks /delete /tn '$TaskName' /f" -ForegroundColor Yellow
    } else {
        Write-Error "Task creation reported success but query failed. Something is wrong."
        pause
        exit 1
    }
} else {
    Write-Error "Failed to create scheduled task. Error code: $LASTEXITCODE"
    pause
    exit 1
}

# Pause so user can see the output
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")