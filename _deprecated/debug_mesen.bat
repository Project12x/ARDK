@echo off
echo =====================================================
echo ARDK Headless Test Runner
echo =====================================================
echo.

cd /d "%~dp0"

echo Running sanity_test.lua...
"tools\emulators\mesen\Mesen.exe" --testRunner "tools\testing\tests\sanity_test.lua" "projects\hal_demo\build\hal_demo.nes"

echo.
echo =====================================================
echo Exit code: %ERRORLEVEL%
if %ERRORLEVEL%==0 (
    echo Result: PASSED - ROM boots and initializes correctly
) else (
    echo Result: FAILED - Check player/enemy initialization
)
echo =====================================================

pause
