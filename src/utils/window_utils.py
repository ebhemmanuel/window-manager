import win32gui
import win32con
import win32process
import win32api
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
    """Get information about all monitors using win32api."""
    monitors = {}

    def get_default_monitor():
        """Get primary monitor information as fallback."""
        width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)

        # Ensure non-zero dimensions
        if width <= 0 or height <= 0:
            width = 1920  # Default fallback width
            height = 1080  # Default fallback height

        work_area = win32api.GetMonitorInfo(
            win32api.MonitorFromPoint((0, 0), win32con.MONITOR_DEFAULTTOPRIMARY)
        )['Work']

        # Ensure work area has valid dimensions
        if work_area[2] - work_area[0] <= 0:
            work_area = (0, 0, width, height)

        return {
            'handle': None,
            'device': 'DISPLAY1',
            'work_area': QRect(work_area[0], work_area[1],
                               work_area[2] - work_area[0],
                               work_area[3] - work_area[1]),
            'monitor_area': QRect(0, 0, width, height),
            'is_primary': True
        }

    try:
        monitor_handles = set()
        screen_width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
        screen_height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)

        # Scan points across the virtual screen to find monitors
        scan_points = [
            (0, 0),  # Top-left
            (screen_width - 1, 0),  # Top-right
            (0, screen_height - 1),  # Bottom-left
            (screen_width - 1, screen_height - 1),  # Bottom-right
            (screen_width // 2, screen_height // 2)  # Center
        ]

        for point in scan_points:
            monitor = win32api.MonitorFromPoint(point, win32con.MONITOR_DEFAULTTONULL)
            if monitor:
                monitor_handles.add(monitor)

        # Process each unique monitor
        for i, monitor in enumerate(monitor_handles):
            try:
                info = win32api.GetMonitorInfo(monitor)
                work_area = info['Work']
                monitor_area = info['Monitor']

                # Ensure dimensions are valid
                if (work_area[2] - work_area[0] <= 0 or
                        work_area[3] - work_area[1] <= 0):
                    continue

                device = f"DISPLAY{i+1}"
                monitors[device] = {
                    'handle': monitor,
                    'device': device,
                    'work_area': QRect(
                        work_area[0], work_area[1],
                        work_area[2] - work_area[0],
                        work_area[3] - work_area[1]
                    ),
                    'monitor_area': QRect(
                        monitor_area[0], monitor_area[1],
                        monitor_area[2] - monitor_area[0],
                        monitor_area[3] - monitor_area[1]
                    ),
                    'is_primary': info['Flags'] & win32con.MONITORINFOF_PRIMARY
                }
            except Exception as e:
                print(f"Error processing monitor {i}: {str(e)}")
                continue
    except Exception as e:
        print(f"Error enumerating monitors: {str(e)}")

    # If no valid monitors were found, use fallback
    if not monitors:
        monitors['DISPLAY1'] = get_default_monitor()

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
        monitor_info = get_monitor_info()
        window_rect = QRect(*win32gui.GetWindowRect(hwnd))

        # Find monitor containing window center
        window_center = QPoint(
            window_rect.x() + window_rect.width() // 2,
            window_rect.y() + window_rect.height() // 2
        )

        for monitor_id, info in monitor_info.items():
            if info['monitor_area'].contains(window_center):
                return monitor_id

        # Return closest monitor if none contain the window center
        closest_monitor = None
        min_distance = float('inf')

        for monitor_id, info in monitor_info.items():
            monitor_center = info['monitor_area'].center()
            distance = (window_center.x() - monitor_center.x()) ** 2 + \
                       (window_center.y() - monitor_center.y()) ** 2

            if distance < min_distance:
                min_distance = distance
                closest_monitor = monitor_id

        return closest_monitor

    except Exception:
        return None
