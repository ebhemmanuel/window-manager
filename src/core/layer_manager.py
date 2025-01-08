from typing import Dict, List, Optional, Tuple
import json
from PyQt5.QtCore import QObject, pyqtSignal, QRect
from models.layer import Layer
from models.monitor import MonitorInfo
from models.window_info import WindowInfo
from utils.window_utils import (
    get_window_info, get_monitor_info, set_window_position,
    set_window_state, get_window_monitor
)
from components.preview_rect import PreviewRect
from core.window_animator import WindowAnimator

class LayerManager(QObject):
    """Manages window layouts and monitor configurations."""
    
    # Signals
    layer_changed = pyqtSignal(str, str)  # monitor_id, layer_name
    layer_updated = pyqtSignal(str)      # layer_name
    unsaved_changes = pyqtSignal(bool)   # has_unsaved
    
    def __init__(self, settings_path: str):
        super().__init__()
        self.settings_path = settings_path
        self.layers: Dict[str, Layer] = {}
        self.active_layers: Dict[str, str] = {}  # Monitor ID -> Active layer name
        self.monitors: Dict[str, MonitorInfo] = {}
        self.modified_layers = set()  # Track unsaved changes
        
        # Initialize components
        self.preview = PreviewRect()
        self.window_animator = WindowAnimator()
        
        self.refresh_monitors()
        self.load_layers()
    
    def refresh_monitors(self):
        """Update monitor information."""
        self.monitors.clear()
        monitor_info = get_monitor_info()
        
        for monitor_id, info in monitor_info.items():
            # Calculate if the monitor is ultrawide based on aspect ratio
            width = info['work_area'].width()
            height = info['work_area'].height()
            is_ultrawide = (width / height) > 2.0 if height > 0 else False
            
            # Create MonitorInfo without aspect_ratio parameter
            self.monitors[monitor_id] = MonitorInfo(
                id=monitor_id,
                name=info['device'].split('\\')[-1],
                work_area=info['work_area'],
                is_primary=info['is_primary'],
                is_ultrawide=is_ultrawide
            )
    
    def load_layers(self):
        """Load layers from settings file."""
        try:
            with open(self.settings_path, 'r') as f:
                data = json.load(f)
            
            self.layers.clear()
            self.active_layers.clear()
            
            # Load layers
            for layer_data in data.get('layers', []):
                windows = []
                for window_data in layer_data.get('windows', []):
                    windows.append(WindowInfo(
                        handle=window_data['handle'],
                        title=window_data['title'],
                        process_name=window_data['process_name'],
                        rect=QRect(
                            window_data['x'],
                            window_data['y'],
                            window_data['width'],
                            window_data['height']
                        ),
                        is_pinned=window_data.get('is_pinned', False)
                    ))
                
                self.layers[layer_data['name']] = Layer(
                    name=layer_data['name'],
                    monitor_id=layer_data['monitor_id'],
                    windows=windows,
                    grid_config=layer_data.get('grid_config', {})
                )
            
            # Load active layers
            self.active_layers = data.get('active_layers', {})
            
            # Create default layers if needed
            self._ensure_default_layers()
            
        except FileNotFoundError:
            self._ensure_default_layers()
    
    def _ensure_default_layers(self):
        """Ensure each monitor has at least one layer."""
        for monitor_id, monitor in self.monitors.items():
            default_name = f"Default-{monitor_id}"
            if not any(layer.monitor_id == monitor_id for layer in self.layers.values()):
                self.layers[default_name] = Layer(
                    name=default_name,
                    monitor_id=monitor_id,
                    windows=[],
                    grid_config=self._create_default_grid_config(monitor)
                )
            
            if monitor_id not in self.active_layers:
                self.active_layers[monitor_id] = default_name
        
        self.save_layers()
    
    def _create_default_grid_config(self, monitor: MonitorInfo) -> dict:
        """Create default grid configuration based on monitor type."""
        is_ultrawide = monitor.aspect_ratio > 2.0
        
        return {
            'columns': 12 if is_ultrawide else 6,
            'rows': 4,
            'subdivisions': is_ultrawide,
            'zones': self._calculate_zones(monitor.aspect_ratio)
        }
    
    def _calculate_zones(self, aspect_ratio: float) -> List[Tuple[float, float]]:
        """Calculate optimal zones based on aspect ratio."""
        if aspect_ratio >= 3.5:  # Super ultrawide
            return [
                (0.0, 0.25),   # Left quarter
                (0.25, 0.75),  # Center half
                (0.75, 1.0)    # Right quarter
            ]
        elif aspect_ratio >= 2.5:  # Standard ultrawide
            return [
                (0.0, 0.33),   # Left third
                (0.33, 0.67),  # Center third
                (0.67, 1.0)    # Right third
            ]
        else:  # Normal widescreen
            return [
                (0.0, 0.5),    # Left half
                (0.5, 1.0)     # Right half
            ]
    
    def save_layers(self):
        """Save layers to settings file."""
        data = {
            'active_layers': self.active_layers,
            'layers': []
        }
        
        for layer in self.layers.values():
            windows_data = []
            for window in layer.windows:
                windows_data.append({
                    'handle': window.handle,
                    'title': window.title,
                    'process_name': window.process_name,
                    'x': window.rect.x(),
                    'y': window.rect.y(),
                    'width': window.rect.width(),
                    'height': window.rect.height(),
                    'is_pinned': window.is_pinned
                })
            
            data['layers'].append({
                'name': layer.name,
                'monitor_id': layer.monitor_id,
                'windows': windows_data,
                'grid_config': layer.grid_config
            })
        
        with open(self.settings_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.modified_layers.clear()
        self.unsaved_changes.emit(False)

    def apply_layer(self, name: str, monitor_id: str, animate: bool = True) -> bool:
        """Apply a layer to a specific monitor."""
        if name not in self.layers or self.layers[name].monitor_id != monitor_id:
            return False
            
        layer = self.layers[name]
        monitor = self.monitors[monitor_id]
        current_windows = self._get_current_windows(monitor_id)
        
        # Store current positions for animation
        start_positions = {}
        if animate:
            for window in current_windows:
                start_positions[window.handle] = window.rect
        
        # First minimize windows not in the new layer
        for window in current_windows:
            if not any(w.handle == window.handle and w.is_pinned 
                      for w in layer.windows):
                try:
                    set_window_state(window.handle, 'minimized')
                except:
                    continue
        
        # Then position windows according to layer
        for window_info in layer.windows:
            try:
                if not window_info.is_valid():
                    continue
                    
                # Find matching window
                matching_window = self._find_matching_window(
                    window_info, current_windows)
                
                if matching_window:
                    if window_info.is_pinned:
                        continue
                    
                    # Calculate target position
                    target_rect = self._adjust_window_position(
                        window_info.rect, monitor)
                    
                    # Restore window if minimized
                    set_window_state(matching_window.handle, 'normal')
                    
                    # Animate or set position directly
                    if animate and matching_window.handle in start_positions:
                        self.window_animator.animate_window(
                            matching_window.handle,
                            start_positions[matching_window.handle],
                            target_rect
                        )
                    else:
                        set_window_position(matching_window.handle, target_rect)
            except:
                continue
        
        self.active_layers[monitor_id] = name
        self.layer_changed.emit(monitor_id, name)
        return True
    
    def update_window(self, hwnd: int, rect: QRect, monitor_id: str = None, 
                     is_pinned: bool = False):
        """Update window position in the active layer."""
        if not monitor_id:
            monitor_id = get_window_monitor(hwnd)
            if not monitor_id:
                return
        
        layer_name = self.active_layers.get(monitor_id)
        if not layer_name:
            return
            
        layer = self.layers[layer_name]
        window_info = WindowInfo.from_handle(hwnd)
        
        if not window_info:
            return
            
        # Adjust position relative to monitor
        monitor = self.monitors[monitor_id]
        relative_rect = QRect(
            rect.x() - monitor.work_area.x(),
            rect.y() - monitor.work_area.y(),
            rect.width(),
            rect.height()
        )
        
        # Update or add window info
        updated = False
        for existing in layer.windows:
            if existing.handle == hwnd:
                existing.rect = relative_rect
                existing.is_pinned = is_pinned
                updated = True
                break
        
        if not updated:
            window_info.rect = relative_rect
            window_info.is_pinned = is_pinned
            layer.windows.append(window_info)
        
        # Mark layer as modified
        self.modified_layers.add(layer_name)
        self.layer_updated.emit(layer_name)
        self.unsaved_changes.emit(True)
    
    def create_layer(self, name: str, monitor_id: str) -> bool:
        """Create a new layer for a specific monitor."""
        if name in self.layers or monitor_id not in self.monitors:
            return False
            
        self.layers[name] = Layer(
            name=name,
            monitor_id=monitor_id,
            windows=[],
            grid_config=self._create_default_grid_config(self.monitors[monitor_id])
        )
        
        self.save_layers()
        return True
    
    def delete_layer(self, name: str) -> bool:
        """Delete a layer."""
        if name not in self.layers:
            return False
            
        monitor_id = self.layers[name].monitor_id
        del self.layers[name]
        
        # Update active layer if needed
        if self.active_layers.get(monitor_id) == name:
            # Find another layer for this monitor
            for layer in self.layers.values():
                if layer.monitor_id == monitor_id:
                    self.active_layers[monitor_id] = layer.name
                    break
        
        self.save_layers()
        return True
    
    def rename_layer(self, old_name: str, new_name: str) -> bool:
        """Rename a layer."""
        if old_name not in self.layers or new_name in self.layers:
            return False
            
        layer = self.layers.pop(old_name)
        layer.name = new_name
        self.layers[new_name] = layer
        
        # Update active layers references
        for monitor_id, active_name in self.active_layers.items():
            if active_name == old_name:
                self.active_layers[monitor_id] = new_name
        
        self.save_layers()
        return True
    
    def toggle_window_pin(self, hwnd: int) -> bool:
        """Toggle window's pinned state."""
        monitor_id = get_window_monitor(hwnd)
        if not monitor_id:
            return False
            
        layer_name = self.active_layers.get(monitor_id)
        if not layer_name:
            return False
            
        layer = self.layers[layer_name]
        for window in layer.windows:
            if window.handle == hwnd:
                window.is_pinned = not window.is_pinned
                self.modified_layers.add(layer_name)
                self.layer_updated.emit(layer_name)
                self.unsaved_changes.emit(True)
                return window.is_pinned
        
        return False
    
    def get_layer_grid_config(self, monitor_id: str) -> dict:
        """Get grid configuration for active layer on monitor."""
        layer_name = self.active_layers.get(monitor_id)
        if layer_name:
            return self.layers[layer_name].grid_config
        return self._create_default_grid_config(self.monitors[monitor_id])
    
    def get_active_monitor(self) -> Optional[str]:
        """Retrieve the ID of the currently active monitor."""
        # Check if there is a single primary monitor
        for monitor_id, monitor in self.monitors.items():
            if monitor.is_primary:
                return monitor_id

        # Fallback to any monitor if no primary is set
        if self.monitors:
            return list(self.monitors.keys())[0]

        # Return None if no monitors are available
        return None

    def get_monitor_layers(self, monitor_id: str) -> List[str]:
        """Retrieve all layers associated with a specific monitor ID."""
        if monitor_id not in self.monitors:
            raise ValueError(f"Monitor ID {monitor_id} not found.")
        
        # Return a list of layer names associated with the monitor ID
        return [layer.name for layer in self.layers.values() if layer.monitor_id == monitor_id]

    def _get_current_windows(self, monitor_id: str) -> List[WindowInfo]:
        """Get all windows currently on a monitor."""
        monitor = self.monitors[monitor_id]
        windows = []
        
        for window in WindowInfo.enumerate_windows():
            if monitor.work_area.contains(window.rect.center()):
                windows.append(window)
        
        return windows
    
    def _find_matching_window(self, target: WindowInfo, 
                            current_windows: List[WindowInfo]) -> Optional[WindowInfo]:
        """Find matching window from current windows."""
        for window in current_windows:
            if (window.process_name == target.process_name and 
                window.title == target.title):
                return window
        return None
    
    def _adjust_window_position(self, rect: QRect, monitor: MonitorInfo) -> QRect:
        """Adjust window position relative to monitor."""
        return QRect(
            rect.x() + monitor.work_area.x(),
            rect.y() + monitor.work_area.y(),
            rect.width(),
            rect.height()
        )
    
    def has_unsaved_changes(self) -> bool:
        """Check if there are any unsaved changes."""
        return len(self.modified_layers) > 0
    
    def discard_changes(self):
        """Discard all unsaved changes."""
        self.load_layers()
        self.modified_layers.clear()
        self.unsaved_changes.emit(False)