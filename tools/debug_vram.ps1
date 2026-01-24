$BlastEm = "C:\Users\estee\Desktop\blastem-win32-0.6.2\blastem.exe"
$Rom = "projects/epoch/out/rom.bin"
$Gdb = "C:\sgdk\bin\gdb.exe"
$GdbScript = "tools/inspect_vdp.gdb"

Write-Host "Starting BlastEm (GDB Mode)..."
$BlastProcess = Start-Process -FilePath $BlastEm -ArgumentList "`"$Rom`" -D" -PassThru
Start-Sleep -Seconds 3

Write-Host "Running GDB..."
& $Gdb -x $GdbScript

Write-Host "Stopping BlastEm..."
Stop-Process -Id $BlastProcess.Id -Force
