@echo off
REM ============================================================
REM  Build Tramplers Manager.exe from tramplers_manager.py
REM  Run on YOUR Windows machine (folder where this file is).
REM  Requires Python installed (https://python.org, check "Add to PATH").
REM ============================================================

echo Installing PyInstaller (if needed)...
python -m pip install --upgrade pyinstaller

echo.
echo Building the executable...
python -m PyInstaller --onefile --windowed --name "Tramplers Manager" tramplers_manager.py

echo.
echo.
echo ============================================================
echo.
echo   DONE! YOUR .EXE IS IN THE "dist" FOLDER
echo.
echo ============================================================
echo.
pause
