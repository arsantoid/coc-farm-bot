@echo off
setlocal EnableDelayedExpansion
title CoC Farm Bot - Setup ^& Start
color 0A

echo ==============================================================
echo                 CoC FARM BOT - AUTO SETUP
echo ==============================================================
echo.

:: 1. Check Python
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python is not installed or not in PATH!
    echo [!] Please install Python 3.9+ from python.org
    pause
    exit /b
) else (
    for /f "delims=" %%i in ('python --version') do set PY_VER=%%i
    echo [OK] Found !PY_VER!
)

:: 1.5 Check pip
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] pip is missing, installing...
    python -m ensurepip --upgrade >nul 2>&1
    python -m pip --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [!] Failed to install pip!
        pause
        exit /b
    )
    echo [OK] pip installed.
)

:: 2. Check and Install Requirements
echo.
echo [2/4] Checking dependencies...
python -c "import cv2" >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Installing opencv-python...
    python -m pip install opencv-python
)
python -c "import numpy" >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Installing numpy...
    python -m pip install numpy
)
python -c "import ppadb" >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Installing pure-python-adb...
    python -m pip install pure-python-adb
)
echo [OK] Dependencies OK.

:: 3. Setup ADB
echo.
echo [3/4] Setting up ADB...
set "ADB_PATH=%USERPROFILE%\platform-tools\adb.exe"
if not exist "%ADB_PATH%" (
    echo [!] ADB not found, downloading...
    powershell -Command "Invoke-WebRequest -Uri 'https://dl.google.com/android/repository/platform-tools-latest-windows.zip' -OutFile '%TEMP%\platform-tools.zip'"
    powershell -Command "Expand-Archive -Path '%TEMP%\platform-tools.zip' -DestinationPath '%USERPROFILE%' -Force"
    del "%TEMP%\platform-tools.zip"
)
if exist "%ADB_PATH%" (
    echo [OK] ADB found.
) else (
    echo [!] ADB install failed. Download manually: https://developer.android.com/studio/releases/platform-tools
    pause
    exit /b
)

:: 4. Connect Emulator
echo.
echo [4/4] Scanning emulator ports...
"%ADB_PATH%" connect 127.0.0.1:5555 >nul 2>&1
"%ADB_PATH%" connect 127.0.0.1:5556 >nul 2>&1
"%ADB_PATH%" connect 127.0.0.1:5557 >nul 2>&1
"%ADB_PATH%" connect 127.0.0.1:5558 >nul 2>&1
"%ADB_PATH%" devices

:: Launch CoC
echo.
echo Starting Clash of Clans...
"%ADB_PATH%" shell monkey -p com.supercell.clashofclans -c android.intent.category.LAUNCHER 1 >nul 2>&1
timeout /t 3 /nobreak >nul

echo.
echo ==============================================================
echo                    STARTING BOT...
echo ==============================================================
echo.

:: Fix OpenCV memory crashes
set OPENBLAS_NUM_THREADS=1
set OMP_NUM_THREADS=1
set MKL_NUM_THREADS=1
set NUMEXPR_MAX_THREADS=1

cd /d "%~dp0code"
python bot_farm_auto_v4.py

pause
