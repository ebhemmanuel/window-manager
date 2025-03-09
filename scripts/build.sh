#!/bin/bash

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "Error: Please run this script from the project root directory"
    exit 1
fi

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

source venv/Scripts/activate

# Install/update requirements
echo "Installing requirements..."
pip install -r requirements.txt
pip install pyinstaller  # Ensure PyInstaller is installed

# Create and initialize directories
echo "Setting up directories and files..."

# Create config directory and files
mkdir -p config
if [ ! -f "config/profiles.json" ]; then
    echo "{\"profiles\": []}" > config/profiles.json
fi
if [ ! -f "config/layers.json" ]; then
    echo "{\"active_layers\": {}, \"layers\": []}" > config/layers.json
fi
if [ ! -f "config/default_settings.json" ]; then
    echo "{
        \"overlay_opacity\": 15,
        \"grid_color\": \"#FFFFFF\",
        \"active_cell_color\": \"#FFA500\",
        \"preview_color\": \"#00FF00\",
        \"suggestion_color\": \"#4CAF50\",
        \"fab_size\": 56,
        \"grid_cols\": 6,
        \"grid_rows\": 4,
        \"marker_size\": 8,
        \"snap_enabled\": true,
        \"snap_threshold\": 15,
        \"animation_duration\": 300,
        \"preview_duration\": 200
    }" > config/default_settings.json
fi

# Create assets directory (even if empty)
mkdir -p assets

# Clean previous build
echo "Cleaning previous build..."
rm -rf build dist

# Run PyInstaller
echo "Building executable..."
pyinstaller window_manager.spec --clean --noconfirm

# Check if build was successful
if [ -f "dist/WindowManager.exe" ]; then
    echo "Build complete! Executable is in dist/WindowManager.exe"
else
    echo "Build failed! Check the error messages above."
    exit 1
fi