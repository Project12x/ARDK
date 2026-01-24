$BlastEm = "C:\Users\estee\Desktop\blastem-win32-0.6.2\blastem.exe"
$Rom = "projects\epoch\out\rom.bin"
$Monitor = "tools\monitor_gamestate.py"

Write-Host "Starting BlastEm (GDB Mode)..."
# Start BlastEm and keep it running
$BlastProcess = Start-Process -FilePath $BlastEm -ArgumentList "`"$Rom`" -D" -PassThru

Write-Host "Waiting for GDB Server..."
Start-Sleep -Seconds 3

Write-Host "Starting RAM Monitor..."
python $Monitor

# Cleanup when monitor exits
Write-Host "Stopping BlastEm..."
Stop-Process -Id $BlastProcess.Id -Force
