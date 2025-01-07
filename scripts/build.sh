#!/bin/bash
source venv/Scripts/activate
pyinstaller window_manager.spec --clean
echo "Build complete! Executable is in dist/WindowManager.exe"
