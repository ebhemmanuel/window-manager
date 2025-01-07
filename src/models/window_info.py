from dataclasses import dataclass
from typing import List, Optional, ClassVar
from PyQt5.QtCore import QRect
import win32gui
import win32con
import win32process
from utils.window_utils import is_valid_window

@dataclass
class WindowInfo:
    """Information about a window's state and properties."""
    handle: int
    title: str
    process_name: str
    rect: QRect
    is_pinned: bool = False
    
    # Cache for process names to avoid repeated system calls
    _process_cache: ClassVar[dict] = {}
    
    @classmethod
    def from_handle(cls, hwnd: int) -> Optional['WindowInfo']:
        """Create WindowInfo from a window handle."""
        if not is_valid_window(hwnd):
            return None
            
        try:
            title = win32gui.GetWindowText(hwnd)
            rect = win32gui.GetWindowRect(hwnd)
            process_name = cls._get_process_name(hwnd)
            
            return cls(
                handle=hwnd,
                title=title,
                process_name=process_name,
                rect=QRect(*rect)
            )
        except Exception:
            return None
    
    @classmethod
    def enumerate_windows(cls) -> List['WindowInfo']:
        """Get information for all valid windows."""
        windows = []
        
        def enum_callback(hwnd, _):
            if is_valid_window(hwnd):
                window_info = cls.from_handle(hwnd)
                if window_info:
                    windows.append(window_info)
        
        win32gui.EnumWindows(enum_callback, None)
        return windows
    
    @classmethod
    def _get_process_name(cls, hwnd: int) -> str:
        """Get process name with caching."""
        if hwnd in cls._process_cache:
            return cls._process_cache[hwnd]
            
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            handle = win32process.OpenProcess(
                win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ,
                False, pid
            )
            process_name = win32process.GetModuleFileNameEx(handle, 0).split('\\')[-1]
            cls._process_cache[hwnd] = process_name
            return process_name
        except Exception:
            return "Unknown"
    
    def is_valid(self) -> bool:
        """Check if the window is still valid."""
        return is_valid_window(self.handle)
    
    def update_rect(self):
        """Update stored rectangle position."""
        if self.is_valid():
            self.rect = QRect(*win32gui.GetWindowRect(self.handle))
    
    def matches(self, other: 'WindowInfo') -> bool:
        """Check if this window matches another (same process and title)."""
        return (self.process_name == other.process_name and 
                self.title == other.title)
    
    def to_dict(self) -> dict:
        """Convert to dictionary format."""
        return {
            'handle': self.handle,
            'title': self.title,
            'process_name': self.process_name,
            'rect': {
                'x': self.rect.x(),
                'y': self.rect.y(),
                'width': self.rect.width(),
                'height': self.rect.height()
            },
            'is_pinned': self.is_pinned
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'WindowInfo':
        """Create from dictionary format."""
        rect = QRect(
            data['rect']['x'],
            data['rect']['y'],
            data['rect']['width'],
            data['rect']['height']
        )
        
        return cls(
            handle=data['handle'],
            title=data['title'],
            process_name=data['process_name'],
            rect=rect,
            is_pinned=data.get('is_pinned', False)
        )
    
    def clone(self) -> 'WindowInfo':
        """Create a copy of this window info."""
        return WindowInfo(
            handle=self.handle,
            title=self.title,
            process_name=self.process_name,
            rect=QRect(self.rect),
            is_pinned=self.is_pinned
        )
    
    def get_state(self) -> str:
        """Get window state (normal, maximized, minimized)."""
        if not self.is_valid():
            return 'invalid'
            
        placement = win32gui.GetWindowPlacement(self.handle)
        show_cmd = placement[1]
        
        if show_cmd == win32con.SW_SHOWMAXIMIZED:
            return 'maximized'
        elif show_cmd == win32con.SW_SHOWMINIMIZED:
            return 'minimized'
        return 'normal'
    
    def get_monitor_id(self) -> Optional[str]:
        """Get ID of monitor containing this window."""
        if not self.is_valid():
            return None
            
        try:
            monitor = win32gui.MonitorFromWindow(
                self.handle,
                win32con.MONITOR_DEFAULTTONEAREST
            )
            monitor_info = win32gui.GetMonitorInfo(monitor)
            return monitor_info['Device'].split('\\')[-1]
        except Exception:
            return None