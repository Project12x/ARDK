@echo off
REM =============================================================================
REM NEON SURVIVORS - Asset Build Pipeline
REM Converts sprites to CHR format using modern NES homebrew tools
REM =============================================================================

echo.
echo ========================================
echo  NEON SURVIVORS - Asset Pipeline
echo ========================================
echo.

REM Step 1: Generate sprites (if needed)
if not exist "gfx\generated\player_rad_dude.png" (
    echo [1/4] Generating sprites...
    python tools\gen_sprites.py
    if errorlevel 1 goto :error
) else (
    echo [1/4] Sprites already generated
)

REM Step 2: Create indexed sprite sheet
echo [2/4] Creating indexed sprite sheet...
python tools\make_indexed_sheet.py
if errorlevel 1 goto :error

REM Step 3: Convert to CHR using img2chr
echo [3/4] Converting PNG to CHR format...
call img2chr gfx\generated\neon_indexed_sheet.png src\game\assets\sprites_temp.chr
if errorlevel 1 goto :error

REM Step 4: Pad to 8KB
echo [4/4] Padding CHR to 8KB...
python -c "data = open('src/game/assets/sprites_temp.chr', 'rb').read(); padded = data + bytes([0] * (8192 - len(data))); open('src/game/assets/sprites.chr', 'wb').write(padded); print(f'  CHR size: {len(padded)} bytes')"
if errorlevel 1 goto :error

del src\game\assets\sprites_temp.chr

echo.
echo ========================================
echo  ASSET BUILD COMPLETE!
echo  Output: src\game\assets\sprites.chr
echo ========================================
echo.

echo Tile Map Reference:
echo   $00-$03: Player (rad 90s dude) - 2x2 tiles
echo   $02:     Bit Drone enemy - 1x1 tile
echo   $03-$06: Neon Skull enemy - 2x2 tiles
echo   $20:     XP Gem pickup - 1x1 tile
echo   $21:     Laser projectile - 1x1 tile
echo.

echo Next: Run compile.bat to build ROM
goto :end

:error
echo.
echo ========================================
echo  ASSET BUILD FAILED!
echo ========================================
echo.
pause
exit /b 1

:end
