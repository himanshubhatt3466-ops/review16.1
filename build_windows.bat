@echo off
title Build Google Review Generator Pro
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
py -m PyInstaller --noconfirm --clean --windowed --onefile --name GoogleReviewGeneratorPro app.py
echo.
echo Build complete. EXE location: dist\GoogleReviewGeneratorPro.exe
pause
