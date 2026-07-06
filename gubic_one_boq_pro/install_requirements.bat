@echo off
setlocal
cd /d "%~dp0"
title Install Gubic ONE BoQ Pro Requirements

cls
echo ======================================================
echo   Gubic ONE BoQ Pro v1.0 - Install Requirements
echo ======================================================
echo.

where py >nul 2>&1
if %errorlevel%==0 (
    set "PY_CMD=py -3"
) else (
    set "PY_CMD=python"
)

%PY_CMD% --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found.
    echo Please install Python 3.10 or newer, then run this file again.
    echo Download Python from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [1/4] Python detected:
%PY_CMD% --version
echo.

echo [2/4] Creating local virtual environment .venv ...
%PY_CMD% -m venv .venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)

echo.
echo [3/4] Upgrading pip ...
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [WARNING] Pip upgrade failed, but installation will continue.
)

echo.
echo [4/4] Installing project requirements ...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Requirement installation failed.
    echo Check your internet connection, Python version, or package permissions.
    echo.
    pause
    exit /b 1
)

echo.
echo ======================================================
echo   Installation completed successfully.
echo   Next step: double-click run_application.bat
echo ======================================================
echo.
pause
