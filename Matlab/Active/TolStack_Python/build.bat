@echo off
REM ===========================================================
REM  Build TolStack.exe (standalone, no Python install needed)
REM  Run this on Windows from inside the TolStack_Python folder.
REM ===========================================================
setlocal

echo.
echo === Ensuring build dependencies are installed ===
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

echo.
echo === Building TolStack.exe ===
python -m PyInstaller --noconfirm --clean TolStack.spec

echo.
if exist "dist\TolStack.exe" (
    echo SUCCESS: dist\TolStack.exe
    echo You can copy dist\TolStack.exe anywhere and double-click to run.
) else (
    echo BUILD FAILED - see messages above.
)

echo.
pause
endlocal
