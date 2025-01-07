#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}Setting up Window Manager Project...${NC}"

# Check Python version
if ! command -v python >/dev/null 2>&1; then
    echo -e "${RED}Python is not installed. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

# Create project directory structure
echo -e "${GREEN}Creating project structure...${NC}"
mkdir -p src/{assets,utils,components,core,models,config/profiles}
mkdir -p tests
mkdir -p scripts

# Create virtual environment
echo -e "${GREEN}Creating virtual environment...${NC}"
python -m venv venv

# Activate virtual environment
source venv/Scripts/activate

# Install requirements
echo -e "${GREEN}Installing requirements...${NC}"
pip install PyQt5 pywin32 keyboard pyinstaller
pip install pytest pytest-qt pytest-cov black mypy

# Create requirements.txt
echo -e "${GREEN}Creating requirements.txt...${NC}"
cat > requirements.txt << EOL
PyQt5>=5.15.0
pywin32>=305
keyboard>=0.13.5
pyinstaller>=5.0.0
pytest>=7.0.0
pytest-qt>=4.0.0
pytest-cov>=3.0.0
black>=22.0.0
mypy>=0.900
EOL

# Create run script
echo -e "${GREEN}Creating run script...${NC}"
cat > scripts/run.sh << EOL
#!/bin/bash
source venv/Scripts/activate
python src/main.py
EOL

# Create build script
echo -e "${GREEN}Creating build script...${NC}"
cat > scripts/build.sh << EOL
#!/bin/bash
source venv/Scripts/activate
pyinstaller window_manager.spec --clean
echo "Build complete! Executable is in dist/WindowManager.exe"
EOL

# Make scripts executable
chmod +x scripts/run.sh scripts/build.sh

# Create default settings
echo -e "${GREEN}Creating default settings...${NC}"
cat > src/config/default_settings.json << EOL
{
    "overlay_opacity": 15,
    "grid_color": "#FFFFFF",
    "active_cell_color": "#FFA500",
    "preview_color": "#00FF00",
    "suggestion_color": "#4CAF50",
    "fab_size": 56,
    "grid_cols": 6,
    "grid_rows": 4,
    "marker_size": 8,
    "snap_enabled": true,
    "snap_threshold": 15,
    "animation_duration": 300,
    "preview_duration": 200
}
EOL

# Create PyInstaller spec file
echo -e "${GREEN}Creating PyInstaller spec file...${NC}"
cat > window_manager.spec << EOL
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/config/default_settings.json', 'config'),
        ('src/assets/icon.ico', 'assets')
    ],
    hiddenimports=['win32gui', 'win32con', 'win32process', 'keyboard'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WindowManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src/assets/icon.ico'
)
EOL

# Create __init__.py files
touch src/__init__.py
touch src/utils/__init__.py
touch src/components/__init__.py
touch src/core/__init__.py
touch src/models/__init__.py
touch tests/__init__.py

# Create README
echo -e "${GREEN}Creating README...${NC}"
cat > README.md << EOL
# Window Manager

A modern window management tool for Windows with multi-monitor and ultrawide support.

## Requirements

- Python 3.8 or higher
- Visual Studio Build Tools with Windows 10 SDK
- Git Bash (for Windows)

## Development Setup

1. Install Visual Studio Build Tools with Windows 10 SDK
2. Run \`./scripts/run.sh\` to start in development mode
3. Run \`./scripts/build.sh\` to create executable

## Features

- Multi-monitor support with profiles
- Ultrawide monitor optimization
- Customizable grid system
- Window layout management
- Smooth animations and transitions
- Visual feedback system

## Configuration

Settings can be modified through the UI or by editing \`config/default_settings.json\`
EOL

# Create initial git repository
echo -e "${GREEN}Initializing git repository...${NC}"
git init

# Create .gitignore
cat > .gitignore << EOL
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Project specific
*.log
config/profiles/*
!config/profiles/.gitkeep
EOL

# Keep profiles directory
touch src/config/profiles/.gitkeep

echo -e "${GREEN}Project setup complete!${NC}"
echo -e "${BLUE}To start development:${NC}"
echo "1. Activate virtual environment: source venv/Scripts/activate"
echo "2. Run the application: ./scripts/run.sh"
echo "3. Build executable: ./scripts/build.sh"