$BlastEm = "C:\Users\estee\Desktop\blastem-win32-0.6.2\blastem.exe"
$Rom = "projects\epoch\out\rom.bin"
$Inspector = "tools\inspect_vram.py"

Write-Host "Starting BlastEm (GDB Mode)..."
$BlastProcess = Start-Process -FilePath $BlastEm -ArgumentList "`"$Rom`" -D" -PassThru

Write-Host "Waiting for GDB Server..."
Start-Sleep -Seconds 3

Write-Host "Running VRAM Inspector..."
python $Inspector

Write-Host "Stopping BlastEm..."
try {
    Stop-Process -Id $BlastProcess.Id -Force -ErrorAction SilentlyContinue
}
catch {
    # Process may have already exited
}
