# Window Manager

A powerful window management tool for Windows with support for multiple monitors, ultrawide displays, and advanced layout management.

## Features

- **Multi-Monitor Support**
  - Individual layouts per monitor
  - Profile system for different monitor setups
  - Automatic monitor detection and configuration
  - Support for varying aspect ratios and resolutions

- **Layer Management**
  - Save and load window layouts
  - Temporary layout support with visual indicators
  - Quick switching between layouts
  - Application state persistence

- **Grid System**
  - Customizable grid per monitor
  - Enhanced ultrawide monitor support
  - Visual preview during window placement
  - Snap-to-grid functionality
  - Zone-based layouts for ultrawide monitors

- **Application Management**
  - Automatic application launching
  - Window state persistence
  - Support for Steam games and standard applications
  - Application position memory

## Requirements

- Windows 10 or higher
- Python 3.8+
- Visual Studio Build Tools with Windows 10 SDK
- Git (for development)

## Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/window-manager.git
cd window-manager
```

2. **Setup environment**
```bash
# Create virtual environment
python -m venv venv

# Activate environment
# On Windows (Git Bash):
source venv/Scripts/activate
# On Windows (CMD):
.\venv\Scripts\activate
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

3. **Run the application**
```bash
# Development mode
./scripts/run.sh
# or
python src/main.py

# Build executable
./scripts/build.sh
```

## Development Setup

1. Install Visual Studio Build Tools:
   - Download from [Visual Studio Downloads](https://visualstudio.microsoft.com/downloads/)
   - Select "Desktop development with C++"
   - Ensure Windows 10 SDK is included

2. Install project dependencies:
```bash
pip install -r requirements.txt
```

3. Install development dependencies:
```bash
pip install pytest pytest-qt pytest-cov black mypy
```

## Project Structure

```
window-manager/
├── src/                    # Source code
│   ├── components/         # UI components
│   ├── core/              # Core functionality
│   ├── models/            # Data models
│   └── utils/             # Utilities
├── tests/                 # Test files
├── scripts/               # Build and run scripts
└── docs/                  # Documentation
```

## Usage

1. **Basic Usage**
   - Launch the application
   - Use Ctrl+Shift+G to toggle grid
   - Drag windows while holding Ctrl to see grid
   - Save layouts using the floating action button

2. **Keyboard Shortcuts**
   - Ctrl+Shift+G: Toggle grid
   - Ctrl+Shift+Space: Show layer menu
   - Ctrl+Shift+1-9: Switch layers

3. **Layout Management**
   - Create new layouts from the radial menu
   - Save temporary layouts
   - Switch between layouts using shortcuts
   - Pin windows to keep their position

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Testing

Run the test suite:
```bash
pytest tests/
```

Run with coverage:
```bash
pytest --cov=src tests/
```

## License

This project is licensed under the MIT License - see the LICENSE file for details

## Acknowledgments

- FancyZones for inspiration
- PyQt team for the excellent framework
- Contributors and testers

## Contact

Em - ebhemmanuel@gmail.com
Project Link: https://github.com/ebhemmanuel/window-manager

# Installation Troubleshooting

## Common Issues and Solutions

### PyQt5 Installation Issues

1. **Error: Microsoft Visual C++ 14.0 or greater is required**
   ```
   error: Microsoft Visual C++ 14.0 or greater is required.
   ```
   Solution:
   - Download Visual Studio Build Tools from [Microsoft](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
   - During installation, select "Desktop development with C++"
   - Ensure "Windows 10 SDK" is selected
   - Restart your computer after installation
   - Try installing requirements again

2. **PyQt5 wheel installation failed**
   ```
   Could not find a version that satisfies the requirement PyQt5
   ```
   Solution:
   - Try installing wheel first:
     ```bash
     pip install wheel
     pip install PyQt5
     ```
   - If that fails, download the appropriate wheel from [PyQt5 Wheels](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyqt5)
     ```bash
     pip install PyQt5-5.15.0-cp38-cp38-win_amd64.whl  # Adjust version as needed
     ```

### Pywin32 Issues

1. **DLL Load Failed**
   ```
   ImportError: DLL load failed while importing win32api
   ```
   Solution:
   - Uninstall pywin32:
     ```bash
     pip uninstall pywin32
     ```
   - Run Windows Update to ensure system files are up to date
   - Reinstall pywin32:
     ```bash
     pip install pywin32
     python Scripts/pywin32_postinstall.py -install
     ```

2. **Pywin32 Post-Install Script Missing**
   ```
   Error: python Scripts/pywin32_postinstall.py not found
   ```
   Solution:
   - Find the correct path:
     ```bash
     # In your virtual environment
     dir venv/Scripts/pywin32*
     # Use the correct path
     python venv/Scripts/pywin32_postinstall.py -install
     ```

### Virtual Environment Issues

1. **Activation Script Not Found**
   ```
   source venv/Scripts/activate: No such file or directory
   ```
   Solution:
   - Check if venv was created correctly:
     ```bash
     # Remove existing venv
     rm -rf venv
     # Create new venv
     python -m venv venv --clear
     ```

2. **Permission Denied**
   ```
   Error: Permission denied: 'venv'
   ```
   Solution:
   - Run as administrator or check folder permissions
   - Try creating venv in user directory:
     ```bash
     python -m venv %USERPROFILE%\window-manager-venv
     ```

### Build Issues

1. **PyInstaller Spec File Not Found**
   ```
   Error: 'window_manager.spec' not found
   ```
   Solution:
   - Ensure you're in the correct directory
   - Recreate spec file:
     ```bash
     pyinstaller --name WindowManager src/main.py
     ```

2. **Missing Dependencies in Build**
   ```
   ModuleNotFoundError: No module named 'xyz'
   ```
   Solution:
   - Add missing imports to spec file:
     ```python
     # Edit window_manager.spec
     hiddenimports=['missing_module'],
     ```

### Runtime Issues

1. **Window Detection Not Working**
   ```
   Error: Access Denied (win32api)
   ```
   Solution:
   - Run as administrator
   - Check Windows permissions
   - Ensure antivirus isn't blocking access

2. **Grid Not Showing**
   ```
   QWidget: Cannot create a QWidget without QApplication
   ```
   Solution:
   - Ensure PyQt application is initialized:
     ```python
     app = QApplication(sys.argv)  # Add if missing
     ```

## Environment Verification

Run this script to verify your environment:

```python
# verify_env.py
import sys
import pkg_resources
import platform

def check_environment():
    print("System Information:")
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    
    required = {
        'PyQt5': '5.15.0',
        'pywin32': '305',
        'keyboard': '0.13.5',
        'psutil': '5.9.0'
    }
    
    for package, version in required.items():
        try:
            installed = pkg_resources.get_distribution(package)
            print(f"{package}: {installed.version} {'✓' if installed.version >= version else '✗'}")
        except pkg_resources.DistributionNotFound:
            print(f"{package}: Not installed ✗")

if __name__ == "__main__":
    check_environment()
```

Run with:
```bash
python verify_env.py
```

## Additional Tips

1. **Clean Installation**
   ```bash
   # Remove all traces of previous installation
   pip uninstall -r requirements.txt -y
   rm -rf venv
   rm -rf build dist
   rm -rf __pycache__
   
   # Fresh install
   python -m venv venv
   source venv/Scripts/activate
   pip install -r requirements.txt
   ```

2. **Development Environment Check**
   ```bash
   # Check Python version
   python --version
   
   # Verify pip
   pip --version
   
   # List installed packages
   pip list
   
   # Check PyQt installation
   python -c "from PyQt5.QtWidgets import QApplication; print('PyQt5 working')"
   
   # Check win32api
   python -c "import win32api; print('win32api working')"
   ```

3. **Virtual Environment Best Practices**
   - Always create a new venv for the project
   - Don't mix global and venv packages
   - Use `pip freeze > requirements.txt` to update dependencies
   - Consider using `virtualenvwrapper` for easier management

Need more help? Create an issue on GitHub with:
- Full error message
- Output of verify_env.py
- Your Windows version
- Steps to reproduce the issue