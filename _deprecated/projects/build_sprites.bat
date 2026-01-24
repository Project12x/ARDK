@echo off
REM =============================================================================
REM HAL Demo - Sprite Build Script
REM Converts PNG sprites to CHR format with correct tile ordering
REM =============================================================================

setlocal enabledelayedexpansion

echo.
echo ========================================
echo  HAL Demo - Sprite Build
echo ========================================
echo.

cd /d "%~dp0..\.."

set TOOLS=tools
set ASSETS=projects\hal_demo\assets
set SPRITES=%ASSETS%\sprites
set OUTPUT=%ASSETS%\processed

REM Create output directory
if not exist "%OUTPUT%" mkdir "%OUTPUT%"

echo [1/4] Converting player.png to CHR...
python "%TOOLS%\png2chr.py" "%SPRITES%\player.png" "%OUTPUT%\player.chr"
if errorlevel 1 goto :error

echo [2/4] Converting enemy.png to CHR...
python "%TOOLS%\png2chr.py" "%SPRITES%\enemy.png" "%OUTPUT%\enemy.chr"
if errorlevel 1 goto :error

echo [3/4] Converting bullet.png to CHR...
python "%TOOLS%\png2chr.py" "%SPRITES%\bullet.png" "%OUTPUT%\bullet.chr"
if errorlevel 1 goto :error

echo [4/4] Combining into sprites.chr...
python "%TOOLS%\combine_chr.py" "%OUTPUT%\sprites.chr" "%OUTPUT%\player.chr" "%OUTPUT%\enemy.chr" "%OUTPUT%\bullet.chr"
if errorlevel 1 goto :error

echo.
echo ========================================
echo  SPRITE BUILD SUCCESSFUL!
echo ========================================
echo.
echo Tile Layout:
echo   $00-$03: Player (16x16 metasprite)
echo   $04-$07: Enemy (16x16 metasprite)
echo   $08:     Bullet (8x8 tile)
echo.

goto :end

:error
echo.
echo ========================================
echo  SPRITE BUILD FAILED!
echo ========================================
echo.
pause
exit /b 1

:end
endlocal
