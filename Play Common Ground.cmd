@echo off
setlocal
cd /d "%~dp0"
if exist "Common Ground.exe" (
    start "" "%~dp0Common Ground.exe"
    exit /b 0
)
if not exist ".venv\Scripts\python.exe" (
    where py >nul 2>nul
    if errorlevel 1 (
        echo Python 3.10 or newer is required to run from source.
        echo Download Python from https://www.python.org/downloads/
        pause
        exit /b 1
    )
    py -3 -m venv .venv
    if errorlevel 1 goto :failed
)
".venv\Scripts\python.exe" -c "import pygame" >nul 2>nul
if errorlevel 1 (
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto :failed
)
".venv\Scripts\python.exe" main.py
if errorlevel 1 goto :failed
exit /b 0
:failed
echo.
echo The game could not start. This message has been kept open to help diagnose it.
pause
exit /b 1
