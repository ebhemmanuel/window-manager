import os
import winreg
import win32process
import win32con
import win32gui
from typing import Optional, List, Dict
import psutil
from pathlib import Path

def find_executable_path(process_name: str) -> Optional[str]:
    """Find the executable path for a given process name."""
    # Check if process name includes extension
    if not process_name.lower().endswith('.exe'):
        process_name += '.exe'
    
    # Common paths to search
    search_paths = [
        os.environ.get('PROGRAMFILES', ''),
        os.environ.get('PROGRAMFILES(X86)', ''),
        os.environ.get('LOCALAPPDATA', ''),
        os.environ.get('APPDATA', ''),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs'),
        os.path.join(os.environ.get('APPDATA', ''), 'Programs'),
    ]
    
    # First check running processes
    for proc in psutil.process_iter(['name', 'exe']):
        try:
            if proc.info['name'].lower() == process_name.lower():
                return proc.info['exe']
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # Search common paths
    for base_path in search_paths:
        for root, _, files in os.walk(base_path):
            if process_name.lower() in (f.lower() for f in files):
                return os.path.join(root, process_name)
    
    # Check Windows Registry
    return find_in_registry(process_name)

def find_in_registry(process_name: str) -> Optional[str]:
    """Search Windows Registry for application path."""
    registry_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths")
    ]
    
    for hkey, path in registry_paths:
        try:
            with winreg.OpenKey(hkey, os.path.join(path, process_name)) as key:
                return winreg.QueryValue(key, None)
        except WindowsError:
            continue
    
    return None

def get_steam_app_path(app_id: str) -> Optional[str]:
    """Find path for Steam application."""
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                           r"SOFTWARE\WOW6432Node\Valve\Steam") as key:
            steam_path = winreg.QueryValueEx(key, "InstallPath")[0]
            
        library_folders = [steam_path]
        
        # Check additional library folders
        vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
        if os.path.exists(vdf_path):
            with open(vdf_path, 'r') as f:
                for line in f:
                    if '"path"' in line.lower():
                        path = line.split('"')[3].replace("\\\\", "\\")
                        library_folders.append(path)
        
        # Search for app manifest
        manifest_name = f"appmanifest_{app_id}.acf"
        for library in library_folders:
            manifest_path = os.path.join(library, "steamapps", manifest_name)
            if os.path.exists(manifest_path):
                return os.path.join(library, "steamapps", "common")
                
    except WindowsError:
        pass
    
    return None

def get_start_menu_entries() -> List[Dict[str, str]]:
    """Get list of Start Menu entries."""
    entries = []
    start_menu_paths = [
        os.path.join(os.environ.get('PROGRAMDATA', ''), 'Microsoft', 'Windows', 
                    'Start Menu', 'Programs'),
        os.path.join(os.environ.get('APPDATA', ''), 'Microsoft', 'Windows',
                    'Start Menu', 'Programs')
    ]
    
    for base_path in start_menu_paths:
        for root, _, files in os.walk(base_path):
            for file in files:
                if file.lower().endswith('.lnk'):
                    try:
                        target = resolve_shortcut(os.path.join(root, file))
                        if target:
                            entries.append({
                                'name': os.path.splitext(file)[0],
                                'path': target,
                                'shortcut': os.path.join(root, file)
                            })
                    except Exception:
                        continue
    
    return entries

def resolve_shortcut(shortcut_path: str) -> Optional[str]:
    """Resolve Windows shortcut (.lnk) to target path."""
    import pythoncom
    from win32com.shell import shell, shellcon
    
    try:
        shortcut = pythoncom.CoCreateInstance(
            shell.CLSID_ShellLink,
            None,
            pythoncom.CLSCTX_INPROC_SERVER,
            shell.IID_IShellLink
        )
        shortcut.QueryInterface(pythoncom.IID_IPersistFile).Load(shortcut_path)
        
        target_path = shortcut.GetPath(shell.SLGP_UNCPRIORITY)[0]
        if os.path.exists(target_path):
            return target_path
    except Exception:
        pass
    
    return None

def is_admin_required(exe_path: str) -> bool:
    """Check if application requires admin privileges."""
    try:
        import win32security
        import ntsecuritycon
        
        # Get file security descriptor
        sd = win32security.GetFileSecurity(
            exe_path, win32security.OWNER_SECURITY_INFORMATION |
            win32security.GROUP_SECURITY_INFORMATION |
            win32security.DACL_SECURITY_INFORMATION
        )
        
        # Get DACL
        dacl = sd.GetSecurityDescriptorDacl()
        if not dacl:
            return True
        
        # Get current user SID
        user_sid = win32security.GetTokenInformation(
            win32security.OpenProcessToken(
                win32process.GetCurrentProcess(),
                win32security.TOKEN_QUERY
            ),
            win32security.TokenUser
        )[0]
        
        # Check if user has execute permission
        for i in range(dacl.GetAceCount()):
            ace = dacl.GetAce(i)
            if ace[2] == user_sid and \
               ace[1] & ntsecuritycon.FILE_EXECUTE:
                return False
        
        return True
        
    except Exception:
        # If we can't determine, assume no admin required
        return False

def get_running_apps() -> List[Dict[str, any]]:
    """Get information about currently running applications."""
    apps = []
    
    def enum_windows_callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                process = psutil.Process(pid)
                
                apps.append({
                    'handle': hwnd,
                    'title': win32gui.GetWindowText(hwnd),
                    'process_name': process.name(),
                    'exe_path': process.exe(),
                    'pid': pid
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    
    win32gui.EnumWindows(enum_windows_callback, None)
    return apps