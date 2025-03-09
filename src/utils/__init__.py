"""
Window Manager Utilities Module

This module contains utility functions and helper tools for window management.
Functions are designed to be pure and stateless where possible.
"""

from .window_utils import (
    is_valid_window,
    get_window_info,
    get_monitor_info,
    set_window_position,
    get_window_state,
    set_window_state
)

from .app_launch_utils import (
    find_executable_path,
    get_steam_app_path,
    get_start_menu_entries,
    resolve_shortcut,
    is_admin_required,
    get_running_apps
)

__all__ = [
    # Window utilities
    'is_valid_window',
    'get_window_info',
    'get_monitor_info',
    'set_window_position',
    'get_window_state',
    'set_window_state',
    
    # Application utilities
    'find_executable_path',
    'get_steam_app_path',
    'get_start_menu_entries',
    'resolve_shortcut',
    'is_admin_required',
    'get_running_apps'
]

# System constants
WINDOWS_SYSTEM_CLASSES = [
    'Shell_TrayWnd',
    'Windows.UI.Core.CoreWindow',
    'DV2ControlHost'
]

# Registry paths
REGISTRY_PATHS = {
    'steam': r"SOFTWARE\WOW6432Node\Valve\Steam",
    'app_paths': r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths",
    'uninstall': r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
}

# Error handling
def handle_win32_error(func):
    """Decorator for handling Win32 API errors."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Win32 API Error in {func.__name__}: {str(e)}")
            return None
    return wrapper