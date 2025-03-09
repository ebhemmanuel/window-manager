from dataclasses import dataclass, field
from typing import Dict, List, Optional
import uuid
from copy import deepcopy
from .layer import Layer
from .window_info import WindowInfo

@dataclass
class TempLayout:
    """Represents a temporary layout with change tracking."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    monitor_id: str = ""
    name: str = ""
    
    # Store original and modified states
    original_windows: List[WindowInfo] = field(default_factory=list)
    modified_windows: List[WindowInfo] = field(default_factory=list)
    
    # Track changes
    added_windows: List[WindowInfo] = field(default_factory=list)
    removed_windows: List[WindowInfo] = field(default_factory=list)
    modified_properties: Dict[int, Dict] = field(default_factory=dict)
    
    # Grid configuration
    grid_config: Dict = field(default_factory=lambda: {
        'columns': 6,
        'rows': 4,
        'subdivisions': False,
        'ultrawide_zones': None
    })
    
    @classmethod
    def from_layer(cls, layer: Layer, monitor_id: str) -> 'TempLayout':
        """Create temporary layout from existing layer."""
        return cls(
            monitor_id=monitor_id,
            name=f"{layer.name}_temp",
            original_windows=deepcopy(layer.windows),
            modified_windows=deepcopy(layer.windows),
            grid_config=dict(layer.grid_config)
        )
    
    def apply_changes(self, changes: Dict):
        """Apply changes to the temporary layout."""
        if 'add_window' in changes:
            window = changes['add_window']
            self.modified_windows.append(window)
            self.added_windows.append(window)
        
        if 'remove_window' in changes:
            handle = changes['remove_window']
            window = self.find_window(handle)
            if window:
                self.modified_windows.remove(window)
                self.removed_windows.append(window)
        
        if 'update_window' in changes:
            handle = changes['update_window']['handle']
            props = changes['update_window']['properties']
            window = self.find_window(handle)
            if window:
                # Track modified properties
                if handle not in self.modified_properties:
                    self.modified_properties[handle] = {}
                self.modified_properties[handle].update(props)
                
                # Apply changes
                for key, value in props.items():
                    if hasattr(window, key):
                        setattr(window, key, value)
        
        if 'grid_config' in changes:
            self.grid_config.update(changes['grid_config'])
    
    def find_window(self, handle: int) -> Optional[WindowInfo]:
        """Find window info by handle."""
        for window in self.modified_windows:
            if window.handle == handle:
                return window
        return None
    
    def has_changes(self) -> bool:
        """Check if layout has any changes."""
        return bool(
            self.added_windows or
            self.removed_windows or
            self.modified_properties
        )
    
    def get_changes(self) -> Dict:
        """Get summary of changes."""
        return {
            'added': [w.to_dict() for w in self.added_windows],
            'removed': [w.to_dict() for w in self.removed_windows],
            'modified': self.modified_properties,
            'grid_changes': self._get_grid_changes()
        }
    
    def _get_grid_changes(self) -> Dict:
        """Get changes in grid configuration."""
        changes = {}
        for key, value in self.grid_config.items():
            if key not in self.original_grid_config or self.original_grid_config[key] != value:
                changes[key] = value
        return changes
    
    def revert_changes(self):
        """Revert all changes."""
        self.modified_windows = deepcopy(self.original_windows)
        self.added_windows.clear()
        self.removed_windows.clear()
        self.modified_properties.clear()
        self.grid_config = dict(self.original_grid_config)
    
    def to_layer(self) -> Layer:
        """Convert temporary layout to permanent layer."""
        return Layer(
            name=self.name.replace('_temp', ''),
            monitor_id=self.monitor_id,
            windows=deepcopy(self.modified_windows),
            grid_config=dict(self.grid_config)
        )
    
    def clone(self) -> 'TempLayout':
        """Create a copy of this temporary layout."""
        return TempLayout(
            monitor_id=self.monitor_id,
            name=f"{self.name}_copy",
            original_windows=deepcopy(self.original_windows),
            modified_windows=deepcopy(self.modified_windows),
            added_windows=deepcopy(self.added_windows),
            removed_windows=deepcopy(self.removed_windows),
            modified_properties=deepcopy(self.modified_properties),
            grid_config=dict(self.grid_config)
        )