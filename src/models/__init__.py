"""
Window Manager Data Models Module

This module contains all data models and state representations for the window manager.
Models are implemented using dataclasses for immutability and type safety.
"""

from .layer import Layer
from .monitor import MonitorInfo, MonitorGridConfig
from .window_info import WindowInfo
from .app_state import AppState
from .temp_layout import TempLayout

__all__ = [
    'Layer',
    'MonitorInfo',
    'MonitorGridConfig',
    'WindowInfo',
    'AppState',
    'TempLayout'
]

# Model validation constants
MAX_GRID_COLUMNS = 24
MAX_GRID_ROWS = 16
MIN_WINDOW_SIZE = 50
MAX_WINDOW_TITLE_LENGTH = 256

# Default values
DEFAULT_GRID_CONFIG = {
    'columns': 6,
    'rows': 4,
    'subdivisions': False,
    'ultrawide_zones': None
}

# State flags
WINDOW_STATE_NORMAL = 'normal'
WINDOW_STATE_MAXIMIZED = 'maximized'
WINDOW_STATE_MINIMIZED = 'minimized'
WINDOW_STATE_PINNED = 'pinned'