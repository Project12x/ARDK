@echo off
REM =============================================================================
REM Batch Process All AI Sprite Sheets
REM Processes all sprite sheets in gfx/ai_output/ using Gemini AI
REM =============================================================================

echo.
echo ========================================
echo  AI Sprite Batch Processor
echo  Powered by Gemini 2.5 Flash
echo ========================================
echo.

REM Check for API key
if "%GEMINI_API_KEY%"=="" (
    echo ERROR: GEMINI_API_KEY not set
    echo.
    echo Please set your API key:
    echo   1. Open .env file
    echo   2. Add: GEMINI_API_KEY=your_key_here
    echo.
    pause
    exit /b 1
)

REM Create output directory
if not exist "gfx\processed\batch" mkdir "gfx\processed\batch"

REM Count files
set COUNT=0
for %%f in (gfx\ai_output\*.png) do set /a COUNT+=1

echo Found %COUNT% sprite sheets to process
echo.
echo This will:
echo   - Analyze each sprite sheet with Gemini AI
echo   - Extract and label individual sprites
echo   - Organize into folders by type/action
echo   - Generate CHR files for NES
echo.
echo Press Ctrl+C to cancel, or
pause

echo.
echo Starting batch processing...
echo.

REM Process each PNG file
set PROCESSED=0
for %%f in (gfx\ai_output\*.png) do (
    set /a PROCESSED+=1
    echo.
    echo [!PROCESSED!/%COUNT%] Processing: %%~nf
    echo ----------------------------------------

    python tools\ai_sprite_processor.py "%%f" --output "gfx\processed\batch\%%~nf"

    if errorlevel 1 (
        echo WARNING: Failed to process %%~nf
        echo Continuing with next file...
    )
)

echo.
echo ========================================
echo  Batch Processing Complete!
echo  Processed %PROCESSED% sprite sheets
echo ========================================
echo.
echo Results saved to: gfx\processed\batch\
echo.
echo Next steps:
echo   1. Review organized sprites in gfx\processed\batch\
echo   2. Copy desired CHR files to src\game\assets\
echo   3. Update sprite definitions in code
echo   4. Build ROM: compile.bat
echo.
pause
