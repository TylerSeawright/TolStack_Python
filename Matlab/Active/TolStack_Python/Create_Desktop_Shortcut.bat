@echo off
REM Creates a Desktop shortcut "TolStack (Dev)" that launches the app from source.
setlocal
set "APPDIR=%~dp0"
set "TARGET=%APPDIR%TolStack_Dev.bat"
set "ICON=%APPDIR%TolStack.ico"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$d=[Environment]::GetFolderPath('Desktop');" ^
  "$sc=(New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $d 'TolStack (Dev).lnk'));" ^
  "$sc.TargetPath='%TARGET%';" ^
  "$sc.WorkingDirectory='%APPDIR%';" ^
  "if (Test-Path '%ICON%') { $sc.IconLocation='%ICON%' };" ^
  "$sc.Description='TolStack tolerance-stack tool (dev mode)';" ^
  "$sc.Save();" ^
  "Write-Host 'Created shortcut: ' (Join-Path $d 'TolStack (Dev).lnk')"

echo.
echo Done. A "TolStack (Dev)" shortcut is now on your Desktop.
pause >nul
