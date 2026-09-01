@echo off
REM ============================================================
REM  TolStack - DEV LAUNCHER (runs from source, no packaging)
REM  Keeps a console window open so tracebacks stay visible.
REM ============================================================
cd /d "%~dp0"
title TolStack (Dev)

REM Pick an interpreter: prefer the Windows launcher "py", else "python".
set "PY=py"
where py >nul 2>&1 || set "PY=python"

REM Ensure dependencies are present; install from requirements.txt if not.
%PY% -c "import numpy, matplotlib, win32com.client" >nul 2>&1
if errorlevel 1 (
    echo First run: installing required packages ^(numpy, matplotlib, pywin32^)...
    %PY% -m pip install -r requirements.txt
    echo.
)

%PY% app.py

echo.
echo ------------------------------------------------------------
echo  TolStack closed. Any error text above is dev output.
echo  Press any key to close this window.
echo ------------------------------------------------------------
pause >nul
