"""
Window Manager UI Components Module

This module contains all UI-related components for the window management system.
Each component is designed to be self-contained and reusable.
"""

from .floating_button import FloatingActionButton
from .grid_overlay import GridOverlay
from .preview_rect import PreviewRect
from .layout_status_indicator import LayoutStatusIndicator
from .unsaved_dialog import UnsavedDialog

__all__ = [
    'FloatingActionButton',
    'GridOverlay',
    'PreviewRect',
    'LayoutStatusIndicator',
    'UnsavedDialog'
]

# Component configuration defaults
DEFAULT_FAB_SIZE = 56
DEFAULT_GRID_OPACITY = 0.15
DEFAULT_PREVIEW_DURATION = 200
DEFAULT_ANIMATION_DURATION = 300