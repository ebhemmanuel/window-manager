from typing import Dict, Optional, List
import os
import subprocess
from PyQt5.QtCore import QObject, pyqtSignal
import win32gui
import win32process
import win32con
from models.app_state import AppState
from models.window_info import WindowInfo
from utils.app_launch_utils import find_executable_path

class AppManager(QObject):
    """Manages application launching and state tracking."""
    
    # Signals
    app_launched = pyqtSignal(str, int)  # app_id, window_handle
    app_failed = pyqtSignal(str, str)    # app_id, error_message
    
    def __init__(self):
        super().__init__()
        self.tracked_apps: Dict[str, AppState] = {}
        self.launch_queue: List[str] = []
        self.launching: bool = False
    
    def register_app(self, window_info: WindowInfo) -> str:
        """Register an application for tracking."""
        app_state = AppState.from_window(window_info)
        self.tracked_apps[app_state.app_id] = app_state
        return app_state.app_id
    
    async def launch_app(self, app_id: str) -> bool:
        """Launch an application and wait for its window."""
        if app_id not in self.tracked_apps:
            return False
            
        app_state = self.tracked_apps[app_id]
        
        # Check if app is already running
        if self.is_app_running(app_id):
            return True
        
        try:
            # Find executable path
            exe_path = find_executable_path(app_state.process_name)
            if not exe_path:
                self.app_failed.emit(app_id, "Application not found")
                return False
            
            # Launch application
            process = subprocess.Popen(
                exe_path,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            # Wait for window to appear
            window_handle = await self.wait_for_window(
                app_state.window_title,
                app_state.process_name,
                timeout=30
            )
            
            if window_handle:
                self.tracked_apps[app_id].window_handle = window_handle
                self.app_launched.emit(app_id, window_handle)
                return True
            
            self.app_failed.emit(app_id, "Window not found after launch")
            return False
            
        except Exception as e:
            self.app_failed.emit(app_id, str(e))
            return False
    
    async def wait_for_window(self, title: str, process_name: str, 
                            timeout: int = 30) -> Optional[int]:
        """Wait for application window to appear."""
        import asyncio
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            def enum_callback(hwnd, result):
                if win32gui.IsWindowVisible(hwnd) and title in win32gui.GetWindowText(hwnd):
                    # Verify process name
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    try:
                        handle = win32process.OpenProcess(
                            win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ,
                            False, pid
                        )
                        window_process = win32process.GetModuleFileNameEx(handle, 0)
                        if process_name in window_process:
                            result.append(hwnd)
                    except:
                        pass
            
            result = []
            win32gui.EnumWindows(enum_callback, result)
            
            if result:
                return result[0]
                
            await asyncio.sleep(0.1)
        
        return None
    
    def is_app_running(self, app_id: str) -> bool:
        """Check if application is currently running."""
        if app_id not in self.tracked_apps:
            return False
            
        app_state = self.tracked_apps[app_id]
        
        if not app_state.window_handle:
            return False
            
        try:
            return win32gui.IsWindow(app_state.window_handle)
        except:
            return False
    
    def get_window_handle(self, app_id: str) -> Optional[int]:
        """Get current window handle for an application."""
        if app_id not in self.tracked_apps:
            return None
            
        app_state = self.tracked_apps[app_id]
        
        if self.is_app_running(app_id):
            return app_state.window_handle
            
        return None
    
    def update_app_state(self, app_id: str, window_info: WindowInfo):
        """Update tracked application state."""
        if app_id in self.tracked_apps:
            self.tracked_apps[app_id].update_from_window(window_info)
            
    def clear_tracking(self, app_id: str):
        """Stop tracking an application."""
        if app_id in self.tracked_apps:
            del self.tracked_apps[app_id]