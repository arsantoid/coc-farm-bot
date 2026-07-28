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
    echo [!] Make sure to check "Add Python to PATH" during install.
    pause
    exit /b
) else (
    for /f "delims=" %%i in ('python --version') do set PY_VER=%%i
    echo [OK] Found !PY_VER!
)

:: 1.5 Check and install pip if missing
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] pip is missing, installing...
    python -m ensurepip --upgrade >nul 2>&1
    if %errorlevel% neq 0 (
        echo [!] ensurepip failed, downloading get-pip.py...
        powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%TEMP%\get-pip.py'"
        python "%TEMP%\get-pip.py"
        del "%TEMP%\get-pip.py"
    )
    python -m pip --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [!] Failed to install pip! Please reinstall Python with pip enabled.
        pause
        exit /b
    )
    echo [OK] pip installed.
)

:: 2. Check and Install Requirements
echo.
echo [2/4] Checking dependencies...
python -c "import cv2, numpy, ppadb" >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Installing required Python packages...
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [!] Retrying with --user flag...
        python -m pip install --user -r requirements.txt
    )
    if %errorlevel% neq 0 (
        echo [!] Failed to install dependencies.
        echo [!] Try running manually: python -m pip install opencv-python numpy pure-python-adb
        pause
        exit /b
    )
    echo [OK] Dependencies installed.
) else (
    echo [OK] All dependencies installed.
)

:: 3. Setup ADB
echo.
echo [3/4] Setting up ADB...
set "ADB_PATH=%USERPROFILE%\platform-tools\adb.exe"
if not exist "%ADB_PATH%" (
    echo [!] ADB not found at %ADB_PATH%
    echo [!] Downloading Android platform-tools...
    
    :: Download zip
    powershell -Command "Invoke-WebRequest -Uri 'https://dl.google.com/android/repository/platform-tools-latest-windows.zip' -OutFile '%TEMP%\platform-tools.zip'"
    
    :: Extract
    echo [!] Extracting platform-tools...
    powershell -Command "Expand-Archive -Path '%TEMP%\platform-tools.zip' -DestinationPath '%USERPROFILE%' -Force"
    
    :: Cleanup
    del "%TEMP%\platform-tools.zip"
    
    if exist "%ADB_PATH%" (
        echo [OK] ADB successfully installed.
    ) else (
        echo [!] Failed to install ADB automatically.
        echo [!] Please download Android platform-tools and extract to: %USERPROFILE%\platform-tools\
        pause
        exit /b
    )
) else (
    echo [OK] ADB found.
)

:: 4. Connect Emulator
echo.
echo [4/4] Scanning emulator ports...
"%ADB_PATH%" connect 127.0.0.1:5555 >nul 2>&1
"%ADB_PATH%" connect 127.0.0.1:5556 >nul 2>&1
"%ADB_PATH%" connect 127.0.0.1:5557 >nul 2>&1
"%ADB_PATH%" connect 127.0.0.1:5558 >nul 2>&1
"%ADB_PATH%" devices

:: Make sure CoC is running
echo.
echo Checking if Clash of Clans is running...
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
