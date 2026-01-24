@echo off
cd /d "%~dp0"
echo Running minimal_test.lua... > test_output.txt
"tools\emulators\mesen\Mesen.exe" --testRunner "tools\testing\tests\minimal_test.lua" "projects\hal_demo\build\hal_demo.nes"
echo Exit code: %ERRORLEVEL% >> test_output.txt
type test_output.txt
