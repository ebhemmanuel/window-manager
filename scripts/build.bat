@echo off
echo Cleaning previous build...
rmdir /s /q build dist
del /f /q *.spec

echo Installing requirements...
pip install -r requirements.txt

echo Creating necessary directories...
mkdir config 2>nul
mkdir assets 2>nul

echo Ensuring config files exist...
echo {} > config/profiles.json
echo {} > config/layers.json
echo {} > config/default_settings.json

echo Building executable...
pyinstaller --clean ^
    --add-data "config;config" ^
    --add-data "assets;assets" ^
    --hidden-import win32api ^
    --hidden-import win32gui ^
    --hidden-import win32con ^
    --hidden-import win32process ^
    --hidden-import PyQt5 ^
    --hidden-import PyQt5.QtCore ^
    --hidden-import PyQt5.QtGui ^
    --hidden-import PyQt5.QtWidgets ^
    --hidden-import keyboard ^
    --hidden-import psutil ^
    --name WindowManager ^
    src/main.py

echo Build complete!
pause