import win32gui
import win32con
import win32process
from typing import Tuple, Optional, List, Dict
from PyQt5.QtCore import QRect, QPoint

def is_valid_window(hwnd: int) -> bool:
    """Check if a window handle is valid and should be managed."""
    if not win32gui.IsWindow(hwnd) or not win32gui.IsWindowVisible(hwnd):
        return False
        
    # Skip windows without titles
    if not win32gui.GetWindowText(hwnd):
        return False
    
    # Skip system windows
    classname = win32gui.GetClassName(hwnd)
    if classname in ['Shell_TrayWnd', 'Windows.UI.Core.CoreWindow', 'DV2ControlHost']:
        return False
        
    style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    
    # Skip tool windows
    if ex_style & win32con.WS_EX_TOOLWINDOW:
        return False
        
    # Skip child windows
    if style & win32con.WS_CHILD:
        return False
    
    return True

def get_window_info(hwnd: int) -> Dict[str, any]:
    """Get detailed information about a window."""
    info = {
        'handle': hwnd,
        'title': win32gui.GetWindowText(hwnd),
        'class_name': win32gui.GetClassName(hwnd),
        'rect': win32gui.GetWindowRect(hwnd),
        'style': win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE),
        'ex_style': win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    }
    
    # Get process information
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        handle = win32process.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, pid)
        info['process_name'] = win32process.GetModuleFileNameEx(handle, 0).split('\\')[-1]
        info['pid'] = pid
    except Exception:
        info['process_name'] = "Unknown"
        info['pid'] = None
    
    return info

def get_all_windows() -> List[int]:
    """Get handles of all valid windows."""
    windows = []
    
    def enum_callback(hwnd, _):
        if is_valid_window(hwnd):
            windows.append(hwnd)
    
    win32gui.EnumWindows(enum_callback, None)
    return windows

def get_monitor_info() -> Dict[str, Dict]:
    """Get information about all monitors."""
    monitors = {}
    
    def callback(monitor, dc, rect, data):
        monitor_info = win32gui.GetMonitorInfo(monitor)
        device = monitor_info['Device'].split('\\')[-1]
        monitors[device] = {
            'handle': monitor,
            'device': monitor_info['Device'],
            'work_area': QRect(*monitor_info['Work']),
            'monitor_area': QRect(*monitor_info['Monitor']),
            'is_primary': monitor_info['Flags'] & win32con.MONITORINFOF_PRIMARY
        }
        return True
    
    win32gui.EnumDisplayMonitors(None, None, callback, None)
    return monitors

def set_window_position(hwnd: int, rect: QRect) -> bool:
    """Set a window's position and size."""
    try:
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOP,
            rect.x(),
            rect.y(),
            rect.width(),
            rect.height(),
            win32con.SWP_SHOWWINDOW
        )
        return True
    except Exception:
        return False

def get_window_state(hwnd: int) -> str:
    """Get window state (normal, maximized, minimized)."""
    placement = win32gui.GetWindowPlacement(hwnd)
    show_cmd = placement[1]
    
    if show_cmd == win32con.SW_SHOWMAXIMIZED:
        return 'maximized'
    elif show_cmd == win32con.SW_SHOWMINIMIZED:
        return 'minimized'
    return 'normal'

def set_window_state(hwnd: int, state: str) -> bool:
    """Set window state."""
    states = {
        'normal': win32con.SW_RESTORE,
        'maximized': win32con.SW_MAXIMIZE,
        'minimized': win32con.SW_MINIMIZE
    }
    
    try:
        if state in states:
            win32gui.ShowWindow(hwnd, states[state])
            return True
        return False
    except Exception:
        return False

def get_window_monitor(hwnd: int) -> Optional[str]:
    """Get the monitor ID containing a window."""
    try:
        monitor = win32gui.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST)
        monitor_info = win32gui.GetMonitorInfo(monitor)
        return monitor_info['Device'].split('\\')[-1]
    except Exception:
        return None