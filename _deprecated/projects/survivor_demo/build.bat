@echo off
REM =============================================================================
REM TOWER SURVIVORS Demo - Build Script
REM Uses ACTION_SURVIVOR engine variant
REM =============================================================================

setlocal enabledelayedexpansion

echo.
echo ========================================
echo  Tower Survivors Demo Build
echo ========================================
echo.

REM Navigate to project root
cd /d "%~dp0..\.."

REM Set paths
set CC65_HOME=tools\cc65
set CA65=%CC65_HOME%\ca65.exe
set LD65=%CC65_HOME%\ld65.exe
set CFG=config\mmc3.cfg
set PROJECT=projects\survivor_demo
set ENGINE=src\engines\6502\nes
set OUTPUT=%PROJECT%\build\tower_survivors.nes

REM Check for cc65
if not exist "%CA65%" (
    echo ERROR: ca65.exe not found at %CA65%
    echo Please download cc65 from https://cc65.github.io/
    goto :error
)

REM Create build directory
if not exist "%PROJECT%\build" mkdir "%PROJECT%\build"

echo [1/4] Assembling Header...
%CA65% -t nes %PROJECT%\src\header.asm -o %PROJECT%\build\header.o
if errorlevel 1 goto :error

echo [2/4] Assembling Game Code with ENGINE variant...
%CA65% -t nes %PROJECT%\src\main.asm -o %PROJECT%\build\main.o -I %ENGINE% -I src\engine
if errorlevel 1 goto :error

echo [3/4] Assembling Vectors...
%CA65% -t nes %PROJECT%\src\vectors.asm -o %PROJECT%\build\vectors.o
if errorlevel 1 goto :error

echo [4/4] Assembling Graphics...
%CA65% -t nes %PROJECT%\src\graphics.asm -o %PROJECT%\build\graphics.o
if errorlevel 1 goto :error

echo Linking ROM...
%LD65% -C %CFG% -o %OUTPUT% %PROJECT%\build\header.o %PROJECT%\build\main.o %PROJECT%\build\vectors.o %PROJECT%\build\graphics.o
if errorlevel 1 goto :error

echo.
echo ========================================
echo  BUILD SUCCESSFUL!
echo  Output: %OUTPUT%
echo ========================================
echo.

for %%A in (%OUTPUT%) do echo ROM Size: %%~zA bytes

goto :end

:error
echo.
echo ========================================
echo  BUILD FAILED!
echo ========================================
echo.
pause
exit /b 1

:end
endlocal
