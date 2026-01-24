@echo off
cd /d "%~dp0"

echo Running headless test...
echo.

REM Mesen 2 syntax: --testRunner [lua script] [rom file]
REM Use --enableStdout to see log output in console
"tools\emulators\mesen\Mesen.exe" --testRunner --enableStdout "tools\testing\tests\sanity_test.lua" "projects\hal_demo\build\hal_demo.nes"

echo.
echo Exit code: %ERRORLEVEL%
pause
