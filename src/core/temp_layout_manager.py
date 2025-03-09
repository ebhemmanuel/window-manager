from typing import Dict, Optional, Set
from PyQt5.QtCore import QObject, pyqtSignal
from models.temp_layout import TempLayout
from models.layer import Layer

class TempLayoutManager(QObject):
    """Manages temporary layout states and changes."""
    
    # Signals
    layout_modified = pyqtSignal(str)  # layout_id
    temp_created = pyqtSignal(str)     # layout_id
    temp_discarded = pyqtSignal(str)   # layout_id
    temp_committed = pyqtSignal(str)   # layout_id
    
    def __init__(self):
        super().__init__()
        self.temp_layouts: Dict[str, TempLayout] = {}
        self.modified_layouts: Set[str] = set()
        
    def create_temp_layout(self, base_layer: Layer, monitor_id: str) -> str:
        """Create a temporary layout based on an existing layer."""
        temp_layout = TempLayout.from_layer(base_layer, monitor_id)
        self.temp_layouts[temp_layout.id] = temp_layout
        self.temp_created.emit(temp_layout.id)
        return temp_layout.id
    
    def modify_temp_layout(self, layout_id: str, **changes) -> bool:
        """Apply changes to a temporary layout."""
        if layout_id not in self.temp_layouts:
            return False
            
        temp_layout = self.temp_layouts[layout_id]
        temp_layout.apply_changes(changes)
        
        self.modified_layouts.add(layout_id)
        self.layout_modified.emit(layout_id)
        return True
    
    def commit_temp_layout(self, layout_id: str) -> Optional[Layer]:
        """Convert temporary layout to permanent layer."""
        if layout_id not in self.temp_layouts:
            return None
            
        temp_layout = self.temp_layouts[layout_id]
        permanent_layer = temp_layout.to_layer()
        
        # Clean up temporary state
        del self.temp_layouts[layout_id]
        self.modified_layouts.discard(layout_id)
        
        self.temp_committed.emit(layout_id)
        return permanent_layer
    
    def discard_temp_layout(self, layout_id: str):
        """Discard a temporary layout."""
        if layout_id in self.temp_layouts:
            del self.temp_layouts[layout_id]
            self.modified_layouts.discard(layout_id)
            self.temp_discarded.emit(layout_id)
    
    def get_temp_layout(self, layout_id: str) -> Optional[TempLayout]:
        """Get a temporary layout by ID."""
        return self.temp_layouts.get(layout_id)
    
    def has_unsaved_changes(self, layout_id: str) -> bool:
        """Check if a temporary layout has unsaved changes."""
        return layout_id in self.modified_layouts
    
    def preview_changes(self, layout_id: str) -> Optional[Dict]:
        """Get preview of changes in temporary layout."""
        if layout_id not in self.temp_layouts:
            return None
            
        temp_layout = self.temp_layouts[layout_id]
        return temp_layout.get_changes()
    
    def revert_changes(self, layout_id: str) -> bool:
        """Revert changes in a temporary layout."""
        if layout_id not in self.temp_layouts:
            return False
            
        temp_layout = self.temp_layouts[layout_id]
        temp_layout.revert_changes()
        
        self.modified_layouts.discard(layout_id)
        self.layout_modified.emit(layout_id)
        return True
    
    def get_modified_layouts(self) -> Set[str]:
        """Get IDs of all modified temporary layouts."""
        return self.modified_layouts.copy()
    
    def cleanup(self):
        """Clean up all temporary layouts."""
        layout_ids = list(self.temp_layouts.keys())
        for layout_id in layout_ids:
            self.discard_temp_layout(layout_id)