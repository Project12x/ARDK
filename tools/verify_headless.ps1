param (
    [string]$RomPath = "projects/epoch/out/rom.bin",
    [string]$BlastEmPath = "C:\Users\estee\Desktop\blastem-win32-0.6.2\blastem.exe"
)

Add-Type -AssemblyName System.Windows.Forms

$FullPath = Resolve-Path $RomPath
$Process = Start-Process -FilePath $BlastEmPath -ArgumentList "`"$FullPath`"" -PassThru

Write-Host "Launched BlastEm (PID: $($Process.Id)). Waiting 15s for boot..."
Start-Sleep -Seconds 15

Write-Host "Forcing Focus..."
$wshell = New-Object -ComObject WScript.Shell
$wshell.AppActivate($Process.Id)
Start-Sleep -Seconds 1

Write-Host "Sending Screenshot Command 'p'..."
[System.Windows.Forms.SendKeys]::SendWait("p")
Start-Sleep -Seconds 1

Write-Host "Sending Exit Command 'ESC'..."
[System.Windows.Forms.SendKeys]::SendWait("{ESC}")
Start-Sleep -Seconds 1

if (-not $Process.HasExited) {
    Write-Host "Process did not exit. Killing..."
    Stop-Process -Id $Process.Id -Force
}

# Find latest screenshot in Home
$HomeDir = [Environment]::GetFolderPath("UserProfile")
$LatestScreen = Get-ChildItem -Path $HomeDir -Filter "blastem_*.png" | Sort-Object LastWriteTime -Descending | Select-Object -First 1

if ($LatestScreen) {
    Write-Host "Found Screenshot: $($LatestScreen.FullName)"
    # Move to artifacts if needed? Or just report path.
    # We will copy it to a known location for the agent to find easily.
    $Dest = "projects/epoch/out/latest_screenshot.png"
    Copy-Item $LatestScreen.FullName -Destination $Dest -Force
    Write-Host "Copied to $Dest"
}
else {
    Write-Error "No screenshot found!"
}
