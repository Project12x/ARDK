$BlastEm = "C:\Users\estee\Desktop\blastem-win32-0.6.2\blastem.exe"
$Rom = "C:\Users\estee\Desktop\My Stuff\Code\Antigravity\SurvivorNES\projects\epoch\out\rom.bin"
$Gdb = "C:\sgdk\bin\gdb.exe"
$GdbScript = "tools/test.gdb"

# 1. Start BlastEm suspended (-D)
Write-Host "Starting BlastEm (GDB Server Mode)..."
$BlastProcess = Start-Process -FilePath $BlastEm -ArgumentList "`"$Rom`" -D" -PassThru

# Give it a moment to open socket
Start-Sleep -Seconds 5

# 2. Run GDB
Write-Host "Running GDB Test..."
$GdbOutput = & $Gdb -x $GdbScript | Out-String

Write-Host "GDB Output:"
Write-Host $GdbOutput

# 3. Kill BlastEm
Stop-Process -Id $BlastProcess.Id -Force

# 4. Verify Output
if ($GdbOutput -match "currentHP = 100") {
    Write-Host "SUCCESS: Player HP Verified as 100."
    exit 0
}
else {
    Write-Error "FAILURE: Did not find expected Player HP in GDB output."
    exit 1
}
