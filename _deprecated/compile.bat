@echo off
REM =============================================================================
REM ARDK Multi-Engine Build Script
REM Supports multiple platforms and build profiles
REM =============================================================================
REM Usage: compile.bat [platform] [profile]
REM   platform: nes (default), genesis
REM   profile:  STANDARD (default), FAST, FULL
REM
REM Examples:
REM   compile.bat                  - Build NES with STANDARD profile
REM   compile.bat nes FAST         - Build NES with FAST profile
REM   compile.bat genesis STANDARD - Build Genesis (stub)
REM =============================================================================

setlocal enabledelayedexpansion

echo.
echo ========================================
echo  ARDK Multi-Engine Build System
echo ========================================
echo.

REM Parse arguments
set PLATFORM=%1
set PROFILE=%2

if "%PLATFORM%"=="" set PLATFORM=nes
if "%PROFILE%"=="" set PROFILE=STANDARD

echo Platform: %PLATFORM%
echo Profile:  %PROFILE%
echo.

REM Route to appropriate build
if /i "%PLATFORM%"=="nes" goto :build_nes
if /i "%PLATFORM%"=="genesis" goto :build_genesis
echo ERROR: Unknown platform '%PLATFORM%'
echo Supported platforms: nes, genesis
goto :error

REM =============================================================================
REM NES BUILD (6502)
REM =============================================================================
:build_nes
echo Building for NES (6502)...
echo.

REM Set paths
set CC65_HOME=tools\cc65
set CA65=%CC65_HOME%\ca65.exe
set LD65=%CC65_HOME%\ld65.exe
set CFG=config\mmc3.cfg
set OUTPUT=build\neon_survivors.nes

REM Engine paths (new structure)
set ENGINE_PATH=src\engines\6502\nes
set ENGINE_OLD=src\engine

REM Profile define
set PROFILE_DEF=-D PROFILE_%PROFILE%=1

REM Check for cc65
if not exist "%CA65%" (
    echo ERROR: ca65.exe not found at %CA65%
    echo Please download cc65 from https://cc65.github.io/
    echo and extract to the tools\cc65 directory.
    goto :error
)

REM Create build directory if needed
if not exist build mkdir build

REM Determine which engine path exists (support both old and new structure)
if exist "%ENGINE_PATH%\init\header.asm" (
    set ENGINE=%ENGINE_PATH%
    set INIT_PATH=%ENGINE_PATH%\init
    set CORE_PATH=%ENGINE_PATH%\core
    set HAL_PATH=%ENGINE_PATH%\hal_native
    set UTILS_PATH=%ENGINE_PATH%\utils
    set MODULES_PATH=%ENGINE_PATH%\modules
    echo Using NEW engine structure: %ENGINE_PATH%
) else (
    set ENGINE=%ENGINE_OLD%
    set INIT_PATH=%ENGINE_OLD%
    set CORE_PATH=%ENGINE_OLD%\core
    set HAL_PATH=%ENGINE_OLD%\hal
    set UTILS_PATH=%ENGINE_OLD%\utils
    set MODULES_PATH=%ENGINE_OLD%\modules
    echo Using OLD engine structure: %ENGINE_OLD%
)
echo.

echo [1/8] Assembling Engine Init...
%CA65% -t nes %PROFILE_DEF% -D GAME_CONFIG_SURVIVOR %INIT_PATH%\header.asm -o build\header.o -I %ENGINE%
if errorlevel 1 goto :error

%CA65% -t nes %PROFILE_DEF% -D GAME_CONFIG_SURVIVOR %INIT_PATH%\zeropage.asm -o build\zeropage.o -I %ENGINE%
if errorlevel 1 goto :error

%CA65% -t nes %PROFILE_DEF% -D GAME_CONFIG_SURVIVOR %INIT_PATH%\entry.asm -o build\entry.o -I %ENGINE%
if errorlevel 1 goto :error

echo [2/8] Assembling Engine HAL...
%CA65% -t nes %PROFILE_DEF% -D GAME_CONFIG_SURVIVOR %HAL_PATH%\nmi.asm -o build\nmi.o -I %ENGINE%
if errorlevel 1 goto :error

%CA65% -t nes %PROFILE_DEF% -D GAME_CONFIG_SURVIVOR %HAL_PATH%\input.asm -o build\input.o -I %ENGINE%
if errorlevel 1 goto :error

%CA65% -t nes %PROFILE_DEF% -D GAME_CONFIG_SURVIVOR %HAL_PATH%\audio.asm -o build\audio.o -I %ENGINE%
if errorlevel 1 goto :error

echo [3/8] Assembling Engine Utils...
%CA65% -t nes %PROFILE_DEF% -D GAME_CONFIG_SURVIVOR %UTILS_PATH%\random.asm -o build\random.o -I %ENGINE%
if errorlevel 1 goto :error

echo [4/8] Assembling Engine Core...
%CA65% -t nes %PROFILE_DEF% -D GAME_CONFIG_SURVIVOR %CORE_PATH%\entity.asm -o build\entity.o -I %ENGINE%
if errorlevel 1 goto :error

echo [5/8] Assembling Action Module...
%CA65% -t nes %PROFILE_DEF% -D GAME_CONFIG_SURVIVOR %MODULES_PATH%\action\projectile.asm -o build\projectile.o -I %ENGINE%
if errorlevel 1 goto :error

%CA65% -t nes %PROFILE_DEF% -D GAME_CONFIG_SURVIVOR %MODULES_PATH%\action\spawner.asm -o build\spawner.o -I %ENGINE%
if errorlevel 1 goto :error

%CA65% -t nes %PROFILE_DEF% -D GAME_CONFIG_SURVIVOR %MODULES_PATH%\action\powerup.asm -o build\powerup.o -I %ENGINE%
if errorlevel 1 goto :error

echo [6/8] Assembling Game Code...
%CA65% -t nes %PROFILE_DEF% -D GAME_CONFIG_SURVIVOR src\game\src\debug_screen.asm -o build\debug_screen.o -I %ENGINE% -I src\game\src
if errorlevel 1 goto :error

%CA65% -t nes %PROFILE_DEF% -D GAME_CONFIG_SURVIVOR src\game\src\game_main.asm -o build\game_main.o -I %ENGINE% -I src\game\src
if errorlevel 1 goto :error

echo [7/8] Assembling Graphics...
REM Graphics might be in old or new location
if exist "%CORE_PATH%\graphics.asm" (
    %CA65% -t nes %CORE_PATH%\graphics.asm -o build\graphics.o
) else (
    %CA65% -t nes %ENGINE_OLD%\graphics.asm -o build\graphics.o
)
if errorlevel 1 goto :error

echo [8/8] Linking ROM...
%LD65% -C %CFG% -o %OUTPUT% build\header.o build\zeropage.o build\entry.o build\nmi.o build\input.o build\audio.o build\random.o build\entity.o build\projectile.o build\spawner.o build\powerup.o build\debug_screen.o build\game_main.o build\graphics.o
if errorlevel 1 goto :error

echo.
echo ========================================
echo  NES BUILD SUCCESSFUL!
echo  Platform: NES
echo  Profile:  %PROFILE%
echo  Output:   %OUTPUT%
echo ========================================
echo.

REM Show file size
for %%A in (%OUTPUT%) do echo ROM Size: %%~zA bytes

goto :end

REM =============================================================================
REM GENESIS BUILD (68K)
REM =============================================================================
:build_genesis
echo Building for Genesis (68000)...
echo.

REM Check for SGDK
if not defined GDK (
    echo ERROR: GDK environment variable not set.
    echo Please install SGDK and set GDK to the installation path.
    echo Download from: https://github.com/Stephane-D/SGDK
    goto :error
)

set OUTPUT=build\neon_survivors.bin

echo Genesis build is currently a stub.
echo Required: SGDK installation at: %GDK%
echo.

REM TODO: Implement Genesis build
REM %GDK%\bin\make -f %GDK%\makefile.gen

echo ========================================
echo  GENESIS BUILD NOT YET IMPLEMENTED
echo  This is a stub for future development.
echo ========================================
goto :end

REM =============================================================================
REM ERROR HANDLING
REM =============================================================================
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
