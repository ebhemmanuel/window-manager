from dataclasses import dataclass, field
from typing import Optional, Dict
import uuid
from PyQt5.QtCore import QRect
from .window_info import WindowInfo

@dataclass
class AppState:
    """Tracks the state and launch information of an application."""
    
    # Core identification
    app_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    process_name: str = ""
    window_title: str = ""
    
    # Window state
    window_handle: Optional[int] = None
    window_rect: Optional[QRect] = None
    is_pinned: bool = False
    
    # Launch settings
    exe_path: Optional[str] = None
    launch_args: str = ""
    working_dir: Optional[str] = None
    requires_admin: bool = False
    
    # Additional properties
    custom_properties: Dict = field(default_factory=dict)
    
    @classmethod
    def from_window(cls, window_info: WindowInfo) -> 'AppState':
        """Create AppState from WindowInfo."""
        return cls(
            process_name=window_info.process_name,
            window_title=window_info.title,
            window_handle=window_info.handle,
            window_rect=window_info.rect,
            is_pinned=window_info.is_pinned
        )
    
    def update_from_window(self, window_info: WindowInfo):
        """Update state from WindowInfo."""
        self.window_handle = window_info.handle
        self.window_rect = window_info.rect
        self.is_pinned = window_info.is_pinned
        
        # Update title if window belongs to same process
        if self.process_name == window_info.process_name:
            self.window_title = window_info.title
    
    def to_dict(self) -> dict:
        """Convert to dictionary format."""
        return {
            'app_id': self.app_id,
            'process_name': self.process_name,
            'window_title': self.window_title,
            'window_rect': {
                'x': self.window_rect.x() if self.window_rect else 0,
                'y': self.window_rect.y() if self.window_rect else 0,
                'width': self.window_rect.width() if self.window_rect else 0,
                'height': self.window_rect.height() if self.window_rect else 0
            } if self.window_rect else None,
            'is_pinned': self.is_pinned,
            'exe_path': self.exe_path,
            'launch_args': self.launch_args,
            'working_dir': self.working_dir,
            'requires_admin': self.requires_admin,
            'custom_properties': self.custom_properties
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AppState':
        """Create from dictionary format."""
        window_rect = None
        if data.get('window_rect'):
            window_rect = QRect(
                data['window_rect']['x'],
                data['window_rect']['y'],
                data['window_rect']['width'],
                data['window_rect']['height']
            )
        
        return cls(
            app_id=data.get('app_id', str(uuid.uuid4())),
            process_name=data.get('process_name', ''),
            window_title=data.get('window_title', ''),
            window_rect=window_rect,
            is_pinned=data.get('is_pinned', False),
            exe_path=data.get('exe_path'),
            launch_args=data.get('launch_args', ''),
            working_dir=data.get('working_dir'),
            requires_admin=data.get('requires_admin', False),
            custom_properties=data.get('custom_properties', {})
        )
    
    def set_launch_info(self, exe_path: str, args: str = "", 
                       working_dir: Optional[str] = None,
                       requires_admin: bool = False):
        """Set application launch information."""
        self.exe_path = exe_path
        self.launch_args = args
        self.working_dir = working_dir
        self.requires_admin = requires_admin
    
    def is_running(self) -> bool:
        """Check if the application is currently running."""
        import win32gui
        if not self.window_handle:
            return False
        try:
            return win32gui.IsWindow(self.window_handle)
        except:
            return False
    
    def matches_window(self, window_info: WindowInfo) -> bool:
        """Check if WindowInfo matches this app state."""
        return (self.process_name == window_info.process_name and
                (self.window_handle == window_info.handle or
                self.window_title == window_info.title))
    
    def set_custom_property(self, key: str, value: any):
        """Set a custom property."""
        self.custom_properties[key] = value
    
    def get_custom_property(self, key: str, default: any = None) -> any:
        """Get a custom property."""
        return self.custom_properties.get(key, default)