@echo off
echo ========================================================
echo Building FreelancePilot Windows Standalone Executable...
echo ========================================================

call .\.venv\Scripts\activate.bat
pyinstaller --clean FreelancePilot.spec

echo.
echo ========================================================
echo Build Complete! Check the 'dist\FreelancePilot' directory.
echo ========================================================
pause
