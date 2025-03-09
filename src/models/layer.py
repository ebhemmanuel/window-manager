from dataclasses import dataclass, field
from typing import List, Dict
from .window_info import WindowInfo

@dataclass
class Layer:
    """Represents a window layout configuration."""
    
    name: str
    monitor_id: str
    windows: List[WindowInfo] = field(default_factory=list)
    grid_config: Dict = field(default_factory=lambda: {
        'columns': 6,
        'rows': 4,
        'subdivisions': False,
        'ultrawide_zones': None
    })
    
    def add_window(self, window: WindowInfo):
        """Add a window to the layer."""
        # Check if window already exists
        for existing in self.windows:
            if existing.handle == window.handle:
                existing.rect = window.rect
                existing.is_pinned = window.is_pinned
                return
        self.windows.append(window)
    
    def remove_window(self, handle: int) -> bool:
        """Remove a window from the layer."""
        for i, window in enumerate(self.windows):
            if window.handle == handle:
                self.windows.pop(i)
                return True
        return False
    
    def get_window(self, handle: int) -> WindowInfo:
        """Get window info by handle."""
        for window in self.windows:
            if window.handle == handle:
                return window
        return None
    
    def update_window(self, handle: int, **kwargs) -> bool:
        """Update window properties."""
        window = self.get_window(handle)
        if not window:
            return False
            
        for key, value in kwargs.items():
            if hasattr(window, key):
                setattr(window, key, value)
        return True
    
    def clear_windows(self):
        """Remove all windows from the layer."""
        self.windows.clear()
    
    def get_pinned_windows(self) -> List[WindowInfo]:
        """Get all pinned windows."""
        return [w for w in self.windows if w.is_pinned]
    
    def get_unpinned_windows(self) -> List[WindowInfo]:
        """Get all unpinned windows."""
        return [w for w in self.windows if not w.is_pinned]
    
    def update_grid_config(self, **kwargs):
        """Update grid configuration."""
        self.grid_config.update(kwargs)
    
    def clone(self, new_name: str = None) -> 'Layer':
        """Create a copy of this layer."""
        return Layer(
            name=new_name or f"{self.name}_copy",
            monitor_id=self.monitor_id,
            windows=[w.clone() for w in self.windows],
            grid_config=dict(self.grid_config)
        )