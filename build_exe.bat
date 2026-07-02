@echo off
REM ============================================================
REM  Construit Tramplers Manager.exe a partir de tramplers_manager.py
REM  A lancer sur TA machine Windows (dossier ou se trouve ce fichier).
REM  Necessite Python installe (https://python.org, coche "Add to PATH").
REM ============================================================

echo Installation de PyInstaller (si besoin)...
python -m pip install --upgrade pyinstaller

echo.
echo Construction de l'executable...
python -m PyInstaller --onefile --windowed --name "Tramplers Manager" tramplers_manager.py

echo.
echo Termine ! Ton .exe se trouve dans le dossier "dist".
pause
