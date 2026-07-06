@echo off
setlocal
cd /d "%~dp0"
title Gubic ONE BoQ Pro v1.0

cls
echo ======================================================
echo   Starting Gubic ONE BoQ Pro v1.0
echo ======================================================
echo.

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=%CD%\.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

"%PYTHON_EXE%" --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found.
    echo Please install Python, then run install_requirements.bat again.
    echo.
    pause
    exit /b 1
)

"%PYTHON_EXE%" -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Streamlit is not installed.
    echo Please double-click install_requirements.bat first.
    echo.
    pause
    exit /b 1
)

echo Opening application at: http://localhost:8501
echo Press Ctrl+C in this window to stop the app.
echo.

"%PYTHON_EXE%" -m streamlit run app.py --server.address localhost --server.port 8501 --server.headless false

echo.
echo Application stopped.
pause
