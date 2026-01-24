@echo off
REM EPOCH - Genesis/Mega Drive Build Script
REM Requires SGDK installed and GDK environment variable set

if "%GDK%"=="" (
    echo ERROR: GDK environment variable not set
    echo Please install SGDK and set GDK to the installation path
    echo Example: set GDK=C:\sgdk
    exit /b 1
)

echo Building EPOCH for Sega Genesis...
echo SGDK Path: %GDK%

REM Run SGDK make
%GDK%\bin\make -f %GDK%\makefile.gen

if %ERRORLEVEL% NEQ 0 (
    echo BUILD FAILED
    exit /b 1
)

echo.
echo BUILD SUCCESSFUL
echo Output: out\rom.bin
