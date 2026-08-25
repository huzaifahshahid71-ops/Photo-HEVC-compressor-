@echo off
setlocal EnableExtensions
title HEIC Drop Converter - Build EXE

cd /d "%~dp0"

set "APP_NAME=HEIC-Drop-Converter"
set "SCRIPT=heic_drop_converter.py"
set "ICON=HEIC-Drop-Converter.ico"

echo.
echo ============================================================
echo        HEIC Drop Converter - One Click EXE Builder
echo ============================================================
echo.

if not exist "%SCRIPT%" (
    echo [ERROR] %SCRIPT% was not found in:
    echo %CD%
    echo.
    pause
    exit /b 1
)

where py >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python launcher "py" was not found.
    echo Install Python 3 from python.org and enable the Python launcher.
    echo.
    pause
    exit /b 1
)

echo [1/4] Checking Python...
py -3 --version
if errorlevel 1 (
    echo [ERROR] Python 3 could not be started.
    pause
    exit /b 1
)

echo.
echo [2/4] Installing/updating build dependencies...
py -3 -m pip install --upgrade pip
if errorlevel 1 goto :build_error

py -3 -m pip install --upgrade PySide6 Pillow pillow-heif pyinstaller
if errorlevel 1 goto :build_error

echo.
echo Generating application icon...
if exist "generate_icon.py" (
    py -3 "generate_icon.py"
    if errorlevel 1 goto :build_error
)

if not exist "%ICON%" (
    echo [ERROR] %ICON% was not found and could not be generated.
    goto :build_error
)

echo.
echo [3/4] Cleaning previous build...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "%APP_NAME%.spec" del /q "%APP_NAME%.spec"

echo.
echo [4/4] Building %APP_NAME%.exe...
py -3 -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --windowed ^
    --onefile ^
    --name "%APP_NAME%" ^
    --icon "%ICON%" ^
    --add-data "%ICON%;." ^
    --collect-all pillow_heif ^
    "%SCRIPT%"

if errorlevel 1 goto :build_error

if not exist "dist\%APP_NAME%.exe" goto :build_error

echo.
echo ============================================================
echo BUILD COMPLETE
echo ============================================================
echo EXE:
echo %CD%\dist\%APP_NAME%.exe
echo.
echo Opening the dist folder...
start "" "%CD%\dist"
echo.
pause
exit /b 0

:build_error
echo.
echo ============================================================
echo BUILD FAILED
echo ============================================================
echo Check the messages above for the cause.
echo.
pause
exit /b 1
