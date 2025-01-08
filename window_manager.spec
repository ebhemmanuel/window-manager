# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Helper function to resolve absolute paths
def resource_path(relative_path):
    return os.path.abspath(relative_path)

# Collect PyQt5 dependencies
datas, binaries, hiddenimports = collect_all('PyQt5')

# Collect assets and config directories
assets_datas = []
assets_path = resource_path('assets')
if os.path.exists(assets_path):
    for root, dirs, files in os.walk(assets_path):
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, start=assets_path)
            assets_datas.append((file_path, os.path.join('assets', relative_path)))
datas.extend(assets_datas)

config_datas = []
config_path = resource_path('config')
if os.path.exists(config_path):
    for root, dirs, files in os.walk(config_path):
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, start=config_path)
            config_datas.append((file_path, os.path.join('config', relative_path)))
datas.extend(config_datas)

# Add additional hidden imports
hiddenimports += [
    'core.layer_manager',
    'core.monitor_profiles',
    'core.ultrawide_grid',
    'core.window_animator',
    'components.floating_button',
    'components.grid_overlay',
    'components.preview_rect',
]

# Analysis and EXE definitions
a = Analysis(
    ['src/main.py'],  # Entry point
    pathex=['.', 'src'],  # Add 'src' to search path
    binaries=binaries,
    datas=datas,  # Include collected data
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
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
    console=True,  # Set to False for no console window
    icon=resource_path('assets/icon.ico') if os.path.exists(resource_path('assets/icon.ico')) else None
)
