"""
Window Manager Core Module

This module contains the core functionality and business logic for the window manager.
It handles window management, layouts, and monitor configurations.
"""

from .layer_manager import LayerManager
from .monitor_profiles import MonitorProfileManager
from .ultrawide_grid import UltrawideGridSystem
from .window_animator import WindowAnimator
from .app_manager import AppManager
from .temp_layout_manager import TempLayoutManager

__all__ = [
    'LayerManager',
    'MonitorProfileManager',
    'UltrawideGridSystem',
    'WindowAnimator',
    'AppManager',
    'TempLayoutManager'
]

# Core system constants
ULTRAWIDE_ASPECT_RATIO = 2.0
SUPER_ULTRAWIDE_ASPECT_RATIO = 3.5
DEFAULT_ANIMATION_DURATION = 300
DEFAULT_GRID_DIVISIONS = (6, 4)

# Event types
WINDOW_MOVED = 'window_moved'
WINDOW_RESIZED = 'window_resized'
LAYOUT_CHANGED = 'layout_changed'
PROFILE_CHANGED = 'profile_changed'

# Error messages
ERR_INVALID_MONITOR = "Invalid monitor configuration"
ERR_INVALID_LAYOUT = "Invalid layout configuration"
ERR_WINDOW_NOT_FOUND = "Window not found or no longer exists"